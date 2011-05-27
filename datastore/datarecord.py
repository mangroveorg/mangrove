# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from documents import SubmissionLogDocument
from entity import Entity
from mangrove.utils.types import is_sequence
from mangrove.utils.dates import utcnow


def register(manager, entity_type, data, location, source, aggregation_paths=None, short_code=None):
#    manager = get_db_manager()
    e = Entity(manager, entity_type=entity_type, location=location, aggregation_paths=aggregation_paths,
               short_code=short_code)
    saved_entity_id = e.save()
    submit(manager, entity_id=saved_entity_id, data=data, source=source)
    return e


def submit(manager, entity_id, data, source):
    """
        create and persist a submission doc.
        source will have channel info ie. Web/SMS etc,,
        source will also have the reporter info.
    """
    assert entity_id is not None
    assert is_sequence(data) and len(data) > 0
    e = manager.get(entity_id, Entity)
    submission_log = SubmissionLogDocument(source=source)
    submission_log = manager._save_document(submission_log)
    data_record_id = e.add_data(data=data, event_time=utcnow(), submission_id=submission_log.id)
    return data_record_id, submission_log.id
