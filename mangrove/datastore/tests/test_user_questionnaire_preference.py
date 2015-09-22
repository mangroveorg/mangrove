from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.datastore.user_preference import UserQuestionnairePreference
from mangrove.form_model.project import Project

class UserQuestionnairePreferenceTest(MangroveTestCase):

    def setUp(self):
        MangroveTestCase.setUp(self)

    def test_should_save_preference(self):
        preference = UserQuestionnairePreference(self.manager, 1, 'project_id')
        preference.analysis_fields = {'id':'Eid', 'visibility':True}
        doc_id = preference.save()
        self.assertIsNotNone(doc_id)

    def test_should_return_analysis_fields(self):
        analysis_fields = [{'id':'Eid', 'visibility':True}]
        preference = UserQuestionnairePreference(self.manager, 1, 'project_id')
        preference.analysis_fields = analysis_fields
        preference.save()
        self.assertEqual(preference.analysis_fields, analysis_fields)

    def test_should_hide_fields(self):
        analysis_fields = [{'id':'Eid', 'visibility':True}, {'id':'q1', 'visibility':True}, {'id':'q2', 'visibility':True}]
        expected = [{'id':'Eid', 'visibility':True}, {'id':'q1', 'visibility':False}, {'id':'q2', 'visibility':True}]
        preference = UserQuestionnairePreference(self.manager, 1, 'project_id')
        preference.analysis_fields = analysis_fields
        preference.save()
        self.assertEqual(preference.analysis_fields, analysis_fields)
        preference.hide_fields(['q1'])
        preference.save()
        self.assertEqual(preference.analysis_fields, expected)

    def test_should_show_fields(self):
        analysis_fields = [{'id':'Eid', 'visibility':False}, {'id':'q1', 'visibility':False}, {'id':'q2', 'visibility':False}]
        expected = [{'id':'Eid', 'visibility':True}, {'id':'q1', 'visibility':False}, {'id':'q2', 'visibility':True}]
        preference = UserQuestionnairePreference(self.manager, 1, 'project_id')
        preference.analysis_fields = analysis_fields
        preference.save()
        self.assertEqual(preference.analysis_fields, analysis_fields)
        preference.show_fields(['q2', 'Eid'])
        preference.save()
        self.assertEqual(preference.analysis_fields, expected)