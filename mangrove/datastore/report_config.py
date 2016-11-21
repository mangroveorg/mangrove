from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import ReportConfigDocument


def get_report_configs(manager):
    rows = manager.load_all_rows_in_view('all_report_configs')
    if len(rows):
        return [ReportConfig.new_from_doc(manager, ReportConfigDocument.wrap(row['value'])) for row in rows]
    return None


def get_report_config(manager, id):
    rows = manager.load_all_rows_in_view('all_report_configs', key=id)
    if len(rows):
        return ReportConfig.new_from_doc(manager, ReportConfigDocument.wrap(rows[0]['value']))
    return None


class ReportConfig(DataObject):
    __document_class__ = ReportConfigDocument

    def __init__(self, dbm, **kwargs):
        super(ReportConfig, self).__init__(dbm)
        DataObject._set_document(self, ReportConfigDocument())

    @property
    def id(self):
        return self._doc.id

    @property
    def name(self):
        return self._doc.name

    @property
    def questionnaires(self):
        return self._doc.questionnaires

    def template(self):
        return self.get_attachment(self._doc.id, filename="index.html")

    def stylesheet(self):
        try:
            return self.get_attachment(self._doc.id, filename="styles.css")
        except LookupError:
            return ''