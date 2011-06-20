# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore import entity
from mangrove.form_model.form_model import get_form_model_by_code, LOCATION_TYPE_FIELD_NAME, GEO_CODE
from mangrove.errors.MangroveException import  NoQuestionsSubmittedException, DataObjectNotFound
from mangrove.utils.geo_utils import convert_to_geometry
from mangrove.utils.types import is_string


class SubmissionRequest(object):
    def __init__(self, form_code, submission, transport, source, destination):
        assert form_code is not None
        assert submission is not None
        assert transport is not None
        assert source is not None
        assert destination is not None

        self.form_code = form_code
        self.submission = submission
        self.transport = transport
        self.source = source
        self.destination = destination


class SubmissionResponse(object):
    def __init__(self, success, submission_id, errors=None, datarecord_id=None, short_code=None, processed_data=None):
        assert success is not None
        assert submission_id is not None

        self.success = success
        self.submission_id = submission_id
        self.errors = {} if errors is None else errors
        self.datarecord_id = datarecord_id
        self.short_code = short_code
        self.processed_data = processed_data


class SubmissionHandler(object):
    def __init__(self, dbm):
        assert isinstance(dbm, DatabaseManager)
        self.dbm = dbm

    def accept(self, request):
        assert isinstance(request, SubmissionRequest)
        form_code = request.form_code
        values = request.submission

        logger = SubmissionLogger(self.dbm)
        submission_id, denormalized_submission_data = logger.create_submission_log(channel=request.transport,
                                                                                   source=request.source,
                                                                                   destination=request.destination,
                                                                                   form_code=form_code,
                                                                                   values=values)

        form = get_form_model_by_code(self.dbm, form_code)
        form_submission = form.validate_submission(values)
        if form_submission.is_valid:
            if len(form_submission.values) == 1:
                raise NoQuestionsSubmittedException()
            if form._is_registration_form():
                e = entity.create_entity(dbm=self.dbm, entity_type=form_submission.entity_type.lower(),
                                         location=[form_submission.cleaned_data.get(LOCATION_TYPE_FIELD_NAME)],
                                         short_code=form_submission.short_code,
                                         geometry=convert_to_geometry(form_submission.cleaned_data.get(GEO_CODE)))

                data_record_id = e.add_data(data=form_submission.values, submission=denormalized_submission_data)

                logger.update_submission_log(submission_id=submission_id, status=True, errors=[],
                                             data_record_id=data_record_id)

                return SubmissionResponse(True, submission_id, {}, data_record_id, e.short_code, form_submission.cleaned_data)
            else:
                try:
                    data_record_id = entity.add_data(dbm=self.dbm, short_code=form_submission.short_code,
                                                     data=form_submission.values, entity_type=form.entity_type,
                                                     submission=denormalized_submission_data)

                    logger.update_submission_log(submission_id=submission_id, data_record_id=data_record_id, status=True
                                                 , errors=[])
                    return SubmissionResponse(True, submission_id, {}, data_record_id, processed_data=form_submission.cleaned_data)
                except DataObjectNotFound as e:
                    logger.update_submission_log(submission_id=submission_id, status=False, errors=e.message)
                    raise DataObjectNotFound('Entity','short_code',form_submission.short_code)
        else:
            _errors = form_submission.errors
            logger.update_submission_log(submission_id=submission_id, status=False, errors=_errors.values())
            return SubmissionResponse(False, submission_id, _errors, processed_data=form_submission.cleaned_data)


class SubmissionLogger(object):

    def __init__(self, dbm):
        assert isinstance(dbm, DatabaseManager)
        self.dbm = dbm

    def void_data_record(self, submission_id):
        submission_log = self.dbm._load_document(submission_id, SubmissionLogDocument)
        submission_log.data_record_id = None
        submission_log.voided = True
        self.dbm._save_document(submission_log)

    def update_submission_log(self, submission_id, status, errors, data_record_id=None):
        error_message = ""
        for each in errors:
            error_message = error_message + each + "  "
        log = self.dbm._load_document(submission_id, SubmissionLogDocument)
        log.status = status
        log.voided = not status
        log.data_record_id = data_record_id
        log.error_message = log.error_message + (error_message or "")
        self.dbm._save_document(log)

    def create_submission_log(self, channel, source, destination, form_code, values):
        submission_id = self.log(channel, source, destination, form_code, values, False, "")
        denormalized_submission_data = dict(submission_id=submission_id, form_code=form_code)
        return submission_id, denormalized_submission_data

    def log(self, channel, source, destination, form_code, values, status, error_message):
        return self.dbm._save_document(SubmissionLogDocument(channel=channel, source=source,
                                                             destination=destination, form_code=form_code,
                                                             values=values, status=status,
                                                             error_message=error_message, voided=True))


def get_submissions_made_for_form(dbm, form_code, page_number=0, page_size=20, count_only=False):
    assert is_string(form_code)
    if count_only:
        rows = dbm.load_all_rows_in_view('submissionlog', startkey=[form_code], endkey=[form_code, {}],
                                         group=True, group_level=1, reduce=True)
    else:
        rows = dbm.load_all_rows_in_view('submissionlog', reduce=False, descending = True, startkey=[form_code, {}],
                                         endkey=[form_code], skip=page_number * page_size, limit=page_size)
    answers, ids = list(), list()
    for each in rows:
        answers.append(each.value)
        if not count_only:
            ids.append(each.value["data_record_id"])
    return answers, ids
