from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.datastore.user_permission import UserPermission,\
    get_user_permission

class UserPermissionTest(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)

    def test_should_save_user_permission(self):
        user_permission = UserPermission(self.manager, 1, ["q1", "q2"])
        user_permission_id = user_permission.save()
        self.assertIsNotNone(user_permission_id,"Id not present. User Permission is not saved")

    def test_should_get_user_permission(self):
        user_permission = UserPermission(self.manager, 1, ["q1", "q2"])
        user_permission.save()
        saved_user_permission = get_user_permission(1, self.manager)
        self.assertEquals(saved_user_permission.project_ids, ["q1", "q2"], "Questionnaires doesn't match")
        self.assertEquals(saved_user_permission.user_id, 1,
                          "User id doesn't match")
           