from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import UserPermissionDocument


def get_user_permission(user_id, dbm):
    rows = dbm.load_all_rows_in_view('user_permission', key=user_id, include_docs=True)
    if not len(rows):
        return None
    return UserPermission.new_from_doc(dbm, UserPermissionDocument.wrap(rows[0]['doc']))

def _decorate_questionnaire_for_user(result):
    questionnaire = result.get('doc')
    questionnaire.update({'is_project_manager':True})
    return questionnaire


def default_get_project_info(dbm, x):
    return x


def get_questionnaires_for_user(user_id, dbm, project_info_function=default_get_project_info, **values):
    rows = dbm.load_all_rows_in_view('all_questionnaire_by_user_permission',
                                     key=user_id, include_docs=True, **values)
    questionnaires = []
    if rows:
        questionnaires = [project_info_function(dbm, _decorate_questionnaire_for_user(row)) for row in rows if not row.get('doc').get('void',False)]
    return questionnaires

def grant_user_permission_for(user_id, questionnaire_id, manager):
    user_permission = get_user_permission(user_id=user_id, dbm=manager)
    if user_permission is not None:
        user_permission.project_ids.append(questionnaire_id)
        user_permission.save()
        
def update_user_permission(manager, user_id, project_ids=[]):
    user_permission = get_user_permission(user_id=user_id, dbm=manager)
    if user_permission is None:
        user_permission = UserPermission(manager, user_id)
    user_permission.set_project_ids(project_ids)
    user_permission.save()

def has_permission(manager, user_id, project_id):
    rows = manager.load_all_rows_in_view('user_permission', key=user_id)
    if not len(rows):
        return False
    return project_id in rows[0]['value'].get('project_ids')
    
class UserPermission(DataObject):
    __document_class__ = UserPermissionDocument

    def __init__(self, dbm, user_id=None, project_ids=[]):
        super(UserPermission, self).__init__(dbm)
        doc = UserPermissionDocument()
        doc.user_id = user_id
        doc.project_ids = project_ids
        DataObject._set_document(self, doc)

    @property
    def user_id(self):
        return self._doc.user_id

    @property
    def project_ids(self):
        return self._doc.project_ids

    def set_project_ids(self, project_ids=None):
        self._doc.project_ids = project_ids
