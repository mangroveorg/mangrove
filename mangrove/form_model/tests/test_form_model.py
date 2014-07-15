from datetime import *
# from mangrove.form_model.form_model import get_form_model_by_entity_type
from mangrove.form_model.form_model import list_form_models_by_code
from mangrove.contrib.registration_validators import MobileNumberValidationsForReporterRegistrationValidator
from mangrove.form_model.form_model import get_form_model_by_code, EntityFormModel
from mangrove.form_model.validators import MandatoryValidator

from mangrove.datastore.documents import FormModelDocument
from mangrove.form_model.field import TextField, IntegerField, SelectField, DateField, UniqueIdField, ShortCodeField
from mangrove.errors.MangroveException import QuestionCodeAlreadyExistsException, EntityQuestionAlreadyExistsException, DataObjectAlreadyExists, QuestionAlreadyExistsException
from mangrove.form_model.form_model import FormModel
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint, RegexConstraint
from mangrove.utils.form_model_builder import FormModelBuilder
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase


class FormModelTest(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        self._create_form_model()

    #def tearDown(self):
    #    MangroveTestCase.tearDown(self)

    def test_get_form_model(self):
        form = FormModel.get(self.manager, self.form_model_id)
        self.assertIsNotNone(form.id)
        constraints = form.fields[1].constraints
        self.assertEqual(10, constraints[0].max)
        self.assertEqual(5, constraints[0].min)
        self.assertEqual("\w+", constraints[1].pattern)

    def test_should_add_name_of_form_model(self):
        saved = FormModel.get(self.manager, self.form_model_id)
        self.assertTrue(saved.name == "aids")

    def test_should_add_label(self):
        saved = FormModel.get(self.manager, self.form_model_id)
        self.assertTrue(saved.label == "Aids form_model")

    def test_should_add_short_ids(self):
        saved = FormModel.get(self.manager, self.form_model_id)
        self.assertTrue(saved.form_code == "1")

    def test_should_add_entity_id(self):
        saved = FormModel.get(self.manager, self.form_model_id)
        self.assertListEqual(saved.entity_type, ['clinic'])

    def test_should_add_fields(self):
        saved = FormModel.get(self.manager, self.form_model_id)
        self.assertTrue(len(saved.fields) == 4)
        self.assertTrue(saved.fields[1].name == "question1_Name")
        self.assertTrue(saved.fields[2].name == "Father's age")

    def test_should_add_snapshot_when_modifying(self):
        original_form = self.form_model

        original_form.create_snapshot()
        original_form.save()
        updated_form = FormModel.get(self.manager, self.form_model_id)
        self.assertTrue(len(updated_form.snapshots) == 1)

    def test_should_get_oldest_field_if_no_revision_provided(self):
        self.form_model.save()
        for i in range(15):
            self.form_model.create_snapshot()
            self.form_model.delete_field(code="Q3")
            field = SelectField(name="New Name%s" % i, code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)])
            self.form_model.add_field(field)
            self.form_model.save()
        updated_form = FormModel.get(self.manager, self.form_model_id)
        self.assertEqual("Color", updated_form.get_field_by_code_and_rev("Q3").name)

    def test_should_get_latest_field_if_no_revision_provided_and_no_snapshots(self):
        self.form_model.delete_field(code="Q3")
        field = SelectField(name="New Name", code="Q3", label="What is your favourite color",
                            options=[("RED", 1), ("YELLOW", 2)])
        self.form_model.add_field(field)
        self.form_model.save()
        updated_form = FormModel.get(self.manager, self.form_model_id)
        self.assertEqual("New Name", updated_form.get_field_by_code_and_rev("Q3").name)

    def test_should_get_revision_field_if_revision_provided(self):
        rev = self.form_model.revision
        self.form_model.create_snapshot()
        self.form_model.delete_field(code="Q3")
        field = SelectField(name="New Name", code="Q3", label="What is your favourite color",
                            options=[("RED", 1), ("YELLOW", 2)])
        self.form_model.add_field(field)
        self.form_model.save()
        updated_form = FormModel.get(self.manager, self.form_model_id)
        self.assertEqual("Color", updated_form.get_field_by_code_and_rev("Q3", rev).name)

    def test_should_add_integer_field_with_constraints(self):
        integer_question = FormModel.get(self.manager, self.form_model_id).fields[2]
        range_constraint = integer_question.constraints[0]
        self.assertTrue(integer_question.name == "Father's age")
        self.assertTrue(range_constraint.min, 15)
        self.assertTrue(range_constraint.max, 120)

    def test_should_add_select1_field(self):
        select_question = FormModel.get(self.manager, self.form_model_id).fields[3]
        option_constraint = select_question.options

        self.assertEquals(len(option_constraint), 2)
        self.assertEquals(option_constraint[0].get("val"), 1)

    def test_should_add_new_field(self):
        form_model = FormModel.get(self.manager, self.form_model_id)
        question = TextField(name="added_question", code="Q4", label="How are you")
        form_model.add_field(question)
        form_model.save()

        added_question = self.manager.get(self.form_model.id, FormModel).fields[4]
        self.assertEquals(added_question.code, "Q4")

    def test_should_delete_field(self):
        form_model = FormModel.get(self.manager, self.form_model_id)
        form_model.delete_field(code="Q3")
        form_model.save()
        form_model = FormModel.get(self.manager, self.form_model_id)
        self.assertEquals(len(form_model.fields), 3)

    def test_should_add_english_as_default_language(self):
        activeLanguages = self.form_model.activeLanguages
        self.assertTrue("en" in activeLanguages)

    def test_should_delete_all_fields_from_questions(self):
        form_model = FormModel.get(self.manager, self.form_model_id)
        form_model.delete_all_fields()
        self.assertEquals(len(form_model.fields), 0)

    #def test_should_raise_exception_if_entity_field_already_exist(self):
    #    with self.assertRaises(EntityQuestionAlreadyExistsException):
    #        form_model = FormModel.get(self.manager, self.form_model_id)
    #        question = UniqueIdField('health facility', name="added_question", code="Q5", label="How are you")
    #        form_model.add_field(question)
    #        form_model.save()

    def test_should_raise_exception_if_code_is_not_unique(self):
        with self.assertRaises(QuestionCodeAlreadyExistsException):
            form_model = FormModel.get(self.manager, self.form_model_id)
            question = TextField(name="added_question", code="q1", label="How are you")
            form_model.add_field(question)
            form_model.save()

    def test_should_raise_exception_if_label_is_not_unique(self):
        with self.assertRaises(QuestionAlreadyExistsException):
            form_model = FormModel.get(self.manager, self.form_model_id)
            question = TextField(name="added_question", code="q5", label="What is your name")
            form_model.add_field(question)
            form_model.save()

    def test_should_set_form_code(self):
        form_model = FormModel.get(self.manager, self.form_model_id)
        form_model.form_code = "xyz"
        self.assertEquals(form_model.form_code, "xyz")

    def test_should_set_entity_type(self):
        form_model = FormModel.get(self.manager, self.form_model_id)
        form_model.entity_id = "xyz"
        self.assertEquals(form_model.entity_id, "xyz")


    def test_should_create_a_questionnaire_from_dictionary(self):
        #entityQ = UniqueIdField('reporter', name="What are you reporting on?", code="eid",
        #                        label="Entity being reported on", )
        ageQ = IntegerField(name="What is your age?", code="AGE", label="",
                            constraints=[NumericRangeConstraint(min=0, max=10)], required=False)
        placeQ = SelectField(name="Where do you live?", code="PLC", label="",
                             options=[{"text": "Pune"}, {"text": "Bangalore"}],
                             single_select_flag=False, required=False)
        questions = [ageQ, placeQ]
        document = self.get_form_model_doc()
        questionnaire = FormModel.new_from_doc(self.manager, document)
        self.maxDiff = None
        self.assertListEqual(questionnaire.entity_type, [])
        self.assertEqual(questionnaire.name, "New Project")
        for i in range(len(questions)):
            self.assertEqual(questionnaire.fields[i]._to_json(), questions[i]._to_json())

    def test_should_set_name(self):
        self.form_model.name = 'test_name'
        self.assertEquals(self.form_model.name, 'test_name')


    def test_should_set_entity_type_in_doc(self):
        entity_form_model = EntityFormModel(self.manager)
        entity_form_model._doc = FormModelDocument()
        entity_form_model.entity_type = ["WaterPoint", "Dam"]
        self.assertEqual(entity_form_model.entity_type, ["WaterPoint", "Dam"])

    def test_should_raise_exception_if_form_code_already_exists_on_creation(self):
        question1 = UniqueIdField('clinic', name="entity_question", code="ID", label="What is associated entity")
        form_model = FormModel(self.manager,  name="aids", label="Aids form_model",
                               form_code="1", fields=[question1])
        with self.assertRaises(DataObjectAlreadyExists):
            form_model.save()

    def test_should_raise_exception_if_form_code_already_exists_on_updation(self):
        question1 = UniqueIdField('clinic', name="entity_question", code="ID", label="What is associated entity")
        form_model2 = FormModel(self.manager,  name="aids", label="Aids form_model",
                                form_code="2", fields=[question1])
        form_model2.save()
        with self.assertRaises(DataObjectAlreadyExists):
            form_model2.form_code = "1"
            form_model2.save()

    def test_should_not_raise_exception_if_form_code_is_updated(self):
        question1 = UniqueIdField('clinic', name="entity_question", code="ID", label="What is associated entity")
        form_model2 = FormModel(self.manager, name="aids", label="Aids form_model",
                                form_code="2", fields=[question1])
        form_model2.save()
        form_model2.form_code = "2"
        form_model2.save()

    def test_should_save_form_model_with_validators(self):
        fields = [ShortCodeField('name', 'eid', 'label')]
        form = EntityFormModel(self.manager, 'test_form', 'label', 'foo', fields=fields, entity_type=['Clinic'],
                         validators=[MandatoryValidator(), MobileNumberValidationsForReporterRegistrationValidator()])
        form.save()
        form = get_form_model_by_code(self.manager, 'foo')
        self.assertEqual(2, len(form.validators))
        self.assertTrue(isinstance(form.validators[0], MandatoryValidator))
        self.assertTrue(isinstance(form.validators[1], MobileNumberValidationsForReporterRegistrationValidator))

    def test_should_batch_get_form_models(self):
        fields = [ShortCodeField('name', 'eid', 'label')]
        form = EntityFormModel(self.manager, 'test_form', 'label', 'form_code1', fields=fields, entity_type=['Clinic'],
                         validators=[MandatoryValidator(), MobileNumberValidationsForReporterRegistrationValidator()])
        form.save()

        fields = [ShortCodeField('name', 'eid', 'label')]
        form = EntityFormModel(self.manager, 'test_form', 'label', 'form_code2', fields=fields, entity_type=['Clinic'],
                         validators=[MandatoryValidator(), MobileNumberValidationsForReporterRegistrationValidator()])
        form.save()

        forms = list_form_models_by_code(self.manager, ['form_code1', 'form_code2'])

        self.assertEqual(2, len(forms))
        self.assertEqual('form_code1', forms[0].form_code)
        self.assertEqual('form_code2', forms[1].form_code)

    def test_should_get_string_rep_of_form_model(self):
        submission = {"ID": "id", "Q1": "12345", "Q2": "25", "Q3": "a"}
        stringified_dict = self.form_model.stringify(values=self.form_model.validate_submission(submission)[0])
        self.assertEquals("Clinic(id)", stringified_dict.get("ID"))
        self.assertEquals("12345", stringified_dict.get("Q1"))
        self.assertEquals("25", stringified_dict.get("Q2"))
        self.assertEquals("RED", stringified_dict.get("Q3"))

    def _create_form_model(self):
        self.entity_type = ["HealthFacility", "Clinic"]
        question1 = UniqueIdField('clinic', name="entity_question", code="ID", label="What is associated entity")
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
                              defaultValue="some default value",
                              constraints=[TextLengthConstraint(5, 10), RegexConstraint("\w+")])
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
                                 constraints=[NumericRangeConstraint(min=15, max=120)])
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)])
        self.form_model = FormModelBuilder(self.manager, self.entity_type, "1").label("Aids form_model").name(
            "aids").add_fields(question1,
                               question2, question3, question4).build()
        self.form_model_id = self.form_model.id


    def test_should_get_entity_form_model(self):
        entity_form_model = EntityFormModel(self.manager, name='entity_form_model', label='Entity Form Model',
                                            form_code='entity_form_code', fields=[TextField('name','code','label')],
                                            language="en", is_registration_model=True,
                                            enforce_unique_labels=True, entity_type=['clinic'])
        id = entity_form_model.save()
        saved_entity = EntityFormModel.get(self.manager,id)
        self.assertEquals(saved_entity.entity_type,['clinic'])

    def test_form_model_bound_values(self):
        field1 = UniqueIdField('clinic', 'uniqueid', 'q1', 'wat is unique id')
        field2 = SelectField('singleselect', 'q2', 'select among this', [('one', 1),('two', 2)])
        field3 = TextField('word', 'q3', 'wat is word')
        form_model = FormModelBuilder(self.manager, ['clinic'], "form1").label("Aids form_model").name(
            "aids").add_fields(*[field1, field2, field3]).build()
        form_model.bind({'q1': 'CID001', 'q2':'a','q3':'word'})

        bound_values = form_model.bound_values()

        expected = {'q1':'cid001', 'q2': 'a', 'q3':'word'}
        self.assertEqual(bound_values, expected)

    def get_form_model_doc(self):
        fields = [
            {
                "constraints": [('range', {
                    "max": 10,
                    "min": 0
                })],
                "label": "",
                "type": "integer",
                "name": "What is your age?",
                "code": "AGE",
                "required": False
            },
            {
                "choices": [
                    {
                        "text": "Pune"
                    },
                    {
                        "text": "Bangalore"
                    }
                ],
                "label": "",
                "type": "select",
                "name": "Where do you live?",
                "code": "PLC",
                "required": False
            }
        ]
        document = FormModelDocument()
        document.json_fields = fields
        document.document_type = "FormModel"
        document.form_code = "F1"
        document.name = "New Project"
        document.type = "survey"
        document.type = "survey"
        return document

    def test_should_set_is_open_datasender(self):
        document = self.get_form_model_doc()
        form_model = FormModel.new_from_doc(self.manager, document)
        self.assertFalse(form_model.is_open_datasender)
        document['is_open_datasender'] = True
        self.assertTrue(form_model.is_open_datasender)
