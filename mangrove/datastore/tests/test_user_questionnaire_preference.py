from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.datastore.user_questionnaire_preference import UserQuestionnairePreference
from mangrove.form_model.project import Project, get_entity_type_fields
from mangrove.form_model.field import UniqueIdField, TextField, IntegerField, SelectField
from mangrove.form_model.validation import TextLengthConstraint, RegexConstraint, NumericRangeConstraint
from mangrove.form_model.form_model import EntityFormModel
from mock import Mock, patch
from mangrove.contrib.registration import construct_global_registration_form
from mangrove.datastore.user_questionnaire_preference import get_analysis_field_preferences
from mangrove.datastore.user_questionnaire_preference import detect_visibility

class UserQuestionnairePreferenceTest(MangroveTestCase):

    def setUp(self):
        MangroveTestCase.setUp(self)

    def test_should_save_preference(self):
        preference = UserQuestionnairePreference(self.manager, 1, 'project_id')
        preference.analysis_fields = {'id':'Eid', 'visibility':True}
        doc_id = preference.save()
        self.assertIsNotNone(doc_id)

    def test_should_use_visibility_rules_when_no_preference_exists(self):
        self.assertTrue(detect_visibility(None, "guid-idnr_details.q2"))
        self.assertFalse(detect_visibility(None, "guid-idnr_details.q5"))
        self.assertTrue(detect_visibility(None, "blah"))

    def test_should_use_visibility_rules_when_preference_exists_but_not_for_a_given_field(self):
        preference = UserQuestionnairePreference(self.manager, 1, 'project_id')
        preference.analysis_fields = {'guid-idnr_details.q2' : True}
        self.assertFalse(detect_visibility(preference, "guid-idnr_details.q5"))
        self.assertTrue(detect_visibility(preference, "guid-idnr_details.q6"))
        preference.analysis_fields = {'guid-idnr_details.q2' : False}
        self.assertTrue(detect_visibility(preference, "guid-idnr_details.q6"))
        self.assertTrue(detect_visibility(preference, "blah"))

    def test_should_use_user_preference(self):
        preference = UserQuestionnairePreference(self.manager, 1, 'project_id')
        preference.analysis_fields = {'guid-idnr_details.q3' : True}
        self.assertTrue(detect_visibility(preference, "guid-idnr_details.q3"))
        preference.analysis_fields = {'guid-idnr_details.q3' : False}
        self.assertFalse(detect_visibility(preference, "guid-idnr_details.q3"))

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
        
    def test_should_get_user_questionnaire_preference(self):
        project = self._create_project()
        preferences = get_analysis_field_preferences(self.manager, 1, project, self.display_messages_helper)
        self.assertEqual(len(preferences), 7)
    
    def display_messages_helper(self,label):
        #In actual application, this will return i18n translated messages
        return label
        
    def _create_project(self):
        registration_form = construct_global_registration_form(self.manager)
        registration_form.save()
        
        self.check_uniqueness_patch = patch.object(Project, '_check_if_project_name_unique')
        self.check_uniqueness_patch.start()
        clinic_form_model = EntityFormModel(self.manager, name='clinic', label='Entity Form Model',
                                            form_code='clin', fields=[TextField('name','code','label')],
                                            language="en", is_registration_model=True,
                                            enforce_unique_labels=True, entity_type=['clinic'])
        clinic_form_model.save()

        hf_form_model = EntityFormModel(self.manager, name='health', label='Entity Form Model',
                                            form_code='hf1', fields=[TextField('name','code','label'),
                                                                     TextField('location','loc','Where is it?')],
                                            language="en", is_registration_model=True,
                                            enforce_unique_labels=True, entity_type=['healthfacility'])
        hf_form_model.save()
        
        entity_type = ["HealthFacility", "Clinic"]
        question1 = UniqueIdField('clinic', name="entity_question", code="ID", label="What is associated Clinic")
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
                              defaultValue="some default value",
                              constraints=[TextLengthConstraint(5, 10), RegexConstraint("\w+")])
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
                                 constraints=[NumericRangeConstraint(min=15, max=120)])
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
                                options=[("RED", 'a'), ("YELLOW", 'b')])
        question5 = UniqueIdField('healthfacility', name="health facility", code="hf", label="For which HF is it?")
        fields = [question1, question2, question3, question4, question5]
        project = Project(self.manager, name='test project', form_code='test01', fields=fields)

        project.save()
        return project
