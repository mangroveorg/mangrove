from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import ReportConfigDocument, ReportConfigDocumentBase, ExternalReportConfigDocument


def get_report_configs(manager):
    rows = manager.load_all_rows_in_view('all_report_configs')
    if len(rows):
        return [ReportConfigBase.config(manager, ReportConfigDocumentBase.document(row['value'])) for row in rows]
    return None


def get_report_config(manager, id):
    rows = manager.load_all_rows_in_view('all_report_configs', key=id)
    if len(rows):
        return ReportConfigBase.config(manager, ReportConfigDocumentBase.document(rows[0]['value']))
    return None


class ReportConfigBase(DataObject):
    @classmethod
    def config(cls, dbm, document):
        if isinstance(document, ExternalReportConfigDocument):
            return ExternalReportConfig.new_from_doc(dbm, document)
        else:
            return ReportConfig.new_from_doc(dbm, document)

    @property
    def id(self):
        return self._doc.id

    @property
    def name(self):
        return self._doc.name

    def template(self):
        return self._get_attachment("index.html")

    def stylesheet(self):
        return self._get_attachment("styles.css")

    def font_file(self, file_name):
        return self._get_attachment(file_name)

    def _get_attachment(self, file_name):
        try:
            return self.get_attachment(self._doc.id, filename=file_name)
        except LookupError:
            return ''


class ReportConfig(ReportConfigBase):
    __document_class__ = ReportConfigDocument

    def __init__(self, dbm, name=None, questionnaires=None, **kwargs):
        super(ReportConfig, self).__init__(dbm)
        DataObject._set_document(self, ReportConfigDocument())
        self._create_new_report_config_doc(name, questionnaires)

    def _create_new_report_config_doc(self, name, questionnaires):
        self._doc.name = name
        self._doc.questionnaires = questionnaires

    @property
    def questionnaires(self):
        return self._doc.questionnaires

    @property
    def date_filter(self):
        return self._doc.date_filter

    @property
    def filters(self):
        return self._doc.filters

    @property
    def sort_fields(self):
        return self._doc.sort_fields


class ExternalReportConfig(ReportConfigBase):
    __document_class__ = ExternalReportConfigDocument

    def __init__(self, dbm, **kwargs):
        super(ExternalReportConfig, self).__init__(dbm)
        DataObject._set_document(self, ExternalReportConfigDocument())

    @property
    def url(self):
        return self._doc.url

    @property
    def description(self):
        return self._doc.description

