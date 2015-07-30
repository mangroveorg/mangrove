from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import UserPermissionDocument


def get_user_permission(user_id,dbm):
    rows = dbm.load_all_rows_in_view('user_permission', key=user_id, include_docs=True)
    if not len(rows):
        return None
    return UserPermission.new_from_doc(dbm, UserPermissionDocument.wrap(rows[0]['doc']))
    

class UserPermission(DataObject):
    __document_class__ = UserPermissionDocument
    
    def __init__(self,dbm,user_id=None,project_ids=None):
        super(UserPermission,self).__init__(dbm)
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
    
        