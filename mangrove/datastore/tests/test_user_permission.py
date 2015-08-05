from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.datastore.user_permission import UserPermission,\
    get_user_permission,get_questionnaires_for_user
from mangrove.form_model.field import IntegerField
from mangrove.form_model.validation import NumericRangeConstraint
from mangrove.utils.form_model_builder import FormModelBuilder
from mangrove.form_model.form_model import FormModel

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

    def test_should_get_questionnaires_for_user(self):
        entity_type = []
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
                                 constraints=[NumericRangeConstraint(min=15, max=120)])
        form_model = FormModel(self.manager, name='New survey', label='Survey122',
            form_code='S122', fields=[question3], is_registration_model=False)
        form_model_id = form_model.save()
        user_permission = UserPermission(self.manager, 1, [form_model_id])
        user_permission.save()

        questionnaires = get_questionnaires_for_user(1, self.manager)
        self.assertEquals(questionnaires[0]['_id'], form_model_id,
                          'Unable to fetch correct questionnaire')

