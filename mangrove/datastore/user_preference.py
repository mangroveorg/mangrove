from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import UserQuestionnairePreferenceDocument

class UserQuestionnairePreference(DataObject):
    __document_class__ = UserQuestionnairePreferenceDocument

    def __init__(self, dbm, user_id, project_id, **kwargs):
        super(UserQuestionnairePreference, self).__init__(dbm)
        doc = UserQuestionnairePreferenceDocument()
        doc.user_id = user_id
        doc.project_id = project_id
        DataObject._set_document(self, doc)


    @property
    def analysis_fields(self):
        return self._doc.analysis_fields

    @analysis_fields.setter
    def analysis_fields(self, value):
        self._doc.analysis_fields = value

    def show_fields(self, fields):
        self._change_visibility(fields, True)

    def hide_fields(self, fields):
        self._change_visibility(fields, False)

    def _change_visibility(self, fields, visibility, preference='analysis_fields'):
        if not isinstance(fields, list):
            fields = [fields]
        for field in getattr(self, preference):
            if field.get('id') in fields:
                field['visibility'] = visibility

