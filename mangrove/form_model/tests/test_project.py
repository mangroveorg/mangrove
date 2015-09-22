from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.form_model.project import Project, get_entity_type_fields
from mangrove.form_model.field import UniqueIdField, TextField, IntegerField, SelectField
from mangrove.form_model.validation import TextLengthConstraint, RegexConstraint, NumericRangeConstraint
from mangrove.form_model.form_model import EntityFormModel
from mock import Mock, patch

class ProjectTest(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        self._create_project()

    def tearDown(self):
         self.check_uniqueness_patch.stop()

    def _create_project(self):
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
        
        self.entity_type = ["HealthFacility", "Clinic"]
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
        self.project = Project(self.manager, name='test project', form_code='test01', fields=fields)

        self.project.save()
        self.project_id = self.project.id



    def test_should_return_preference(self):
        self.check_uniqueness_patch.start()
        preference = self.project.get_user_preference(1)
        expected = [{'id': u'ID_code', 'visibility': True},
                {'id': 'Q1', 'visibility': True},
                {'id': 'Q2', 'visibility': True},
                {'id': 'Q3', 'visibility': True},
                {'id': u'hf_code', 'visibility': True},
                {'id': u'hf_loc', 'visibility': True}]
        self.assertEqual(preference.analysis_fields, expected)
