# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from collections import OrderedDict
from mangrove.form_model.form_model import get_form_model_by_entity_type
from mangrove.contrib.registration_validators import MobileNumberValidationsForReporterRegistrationValidator
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.form_model.validators import MandatoryValidator

from mangrove.datastore.documents import FormModelDocument
from mangrove.datastore.entity_type import  define_type
from mangrove.form_model.field import  TextField, IntegerField, SelectField
from mangrove.errors.MangroveException import QuestionCodeAlreadyExistsException, EntityQuestionAlreadyExistsException, DataObjectAlreadyExists, QuestionAlreadyExistsException
from mangrove.form_model.form_model import FormModel
from mangrove.datastore.datadict import DataDictType
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint, RegexConstraint
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase


class TestFormModel(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        self._create_form_model()

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def test_create_form_model(self):
        self.assertTrue(self.form_model__id)

    def test_get_form_model(self):
        form = self.manager.get(self.form_model__id, FormModel)
        self.assertTrue(form.id)
        self.assertTrue(form.type == "survey")
        constraints = form.fields[1].constraints
        self.assertEqual(10, constraints[0].max)
        self.assertEqual(5, constraints[0].min)
        self.assertEqual("\w+", constraints[1].pattern)


    def test_should_add_name_of_form_model(self):
        saved = self.manager.get(self.form_model__id, FormModel)
        self.assertTrue(saved.name == "aids")


    def test_should_add_label(self):
        saved = self.manager.get(self.form_model__id, FormModel)
        self.assertTrue(saved.label == "Aids form_model")

    def test_should_add_short_ids(self):
        saved = self.manager.get(self.form_model__id, FormModel)
        self.assertTrue(saved.form_code == "1")

    def test_should_add_entity_id(self):
        saved = self.manager.get(self.form_model__id, FormModel)
        self.assertListEqual(saved.entity_type, self.entity_type)

    def test_should_add_fields(self):
        saved = self.manager.get(self.form_model__id, FormModel)
        self.assertTrue(len(saved.fields) == 4)
        self.assertTrue(saved.fields[1].name == "question1_Name")
        self.assertTrue(saved.fields[2].name == "Father's age")

    def test_should_add_integer_field_with_constraints(self):
        integer_question = self.manager.get(self.form_model__id, FormModel).fields[2]
        range_constraint = integer_question.constraints[0]
        self.assertTrue(integer_question.name == "Father's age")
        self.assertTrue(range_constraint.min, 15)
        self.assertTrue(range_constraint.max, 120)

    def test_should_add_select1_field(self):
        select_question = self.manager.get(self.form_model__id, FormModel).fields[3]
        option_constraint = select_question.options

        self.assertEquals(len(option_constraint), 2)
        self.assertEquals(option_constraint[0].get("val"), 1)

    def test_should_add_new_field(self):
        form_model = self.manager.get(self.form_model__id, FormModel)
        question = TextField(name="added_question", code="Q4", label="How are you", ddtype=self.default_ddtype)
        form_model.add_field(question)
        form_model.save()

        added_question = self.manager.get(self.form_model.id, FormModel).fields[4]
        self.assertEquals(added_question.code, "Q4")

    def test_should_delete_field(self):
        form_model = self.manager.get(self.form_model__id, FormModel)
        form_model.delete_field(code="Q3")
        form_model.save()
        form_model = self.manager.get(self.form_model__id, FormModel)
        self.assertEquals(len(form_model.fields), 3)

    def test_should_add_english_as_default_language(self):
        activeLanguages = self.form_model.activeLanguages
        self.assertTrue("en" in activeLanguages)

    def test_should_delete_all_fields_from_document(self):
        form_model = self.manager.get(self.form_model__id, FormModel)
        form_model.delete_all_fields()
        self.assertEquals(len(form_model.fields), 0)

    def test_should_delete_all_fields_from_questions(self):
        form_model = self.manager.get(self.form_model__id, FormModel)
        form_model.delete_all_fields()
        self.assertEquals(len(form_model.fields), 0)

    def test_should_raise_exception_if_entity_field_already_exist(self):
        with self.assertRaises(EntityQuestionAlreadyExistsException):
            form_model = self.manager.get(self.form_model__id, FormModel)
            question = TextField(name="added_question", code="Q5", label="How are you",
                                 entity_question_flag=True, ddtype=self.default_ddtype)
            form_model.add_field(question)
            form_model.save()

    def test_should_raise_exception_if_code_is_not_unique(self):
        with self.assertRaises(QuestionCodeAlreadyExistsException):
            form_model = self.manager.get(self.form_model__id, FormModel)
            question = TextField(name="added_question", code="q1", label="How are you",
                                 ddtype=self.default_ddtype)
            form_model.add_field(question)
            form_model.save()

    def test_should_raise_exception_if_label_is_not_unique(self):
        with self.assertRaises(QuestionAlreadyExistsException):
            form_model = self.manager.get(self.form_model__id, FormModel)
            question = TextField(name="added_question", code="q5", label="What is your name",
                                 ddtype=self.default_ddtype)
            form_model.add_field(question)
            form_model.save()

    def test_should_set_form_code(self):
        form_model = self.manager.get(self.form_model__id, FormModel)
        form_model.form_code = "xyz"
        self.assertEquals(form_model.form_code, "xyz")

    def test_should_persist_ddtype(self):
        form_model = self.manager.get(self.form_model__id, FormModel)

        self.assertEqual(form_model.fields[0].ddtype.slug, self.default_ddtype.slug)
        self.assertEqual(form_model.fields[0].ddtype.id, self.default_ddtype.id)
        self.assertEqual(form_model.fields[0].ddtype.name, self.default_ddtype.name)

        self.assertEqual(form_model.fields[1].ddtype.slug, self.default_ddtype.slug)
        self.assertEqual(form_model.fields[1].ddtype.id, self.default_ddtype.id)
        self.assertEqual(form_model.fields[1].ddtype.name, self.default_ddtype.name)

        self.assertEqual(form_model.fields[2].ddtype.slug, self.default_ddtype.slug)
        self.assertEqual(form_model.fields[2].ddtype.id, self.default_ddtype.id)
        self.assertEqual(form_model.fields[2].ddtype.name, self.default_ddtype.name)

        self.assertEqual(form_model.fields[3].ddtype.slug, self.default_ddtype.slug)
        self.assertEqual(form_model.fields[3].ddtype.id, self.default_ddtype.id)
        self.assertEqual(form_model.fields[3].ddtype.name, self.default_ddtype.name)

    def test_should_set_entity_type(self):
        form_model = self.manager.get(self.form_model__id, FormModel)
        form_model.entity_id = "xyz"
        self.assertEquals(form_model.entity_id, "xyz")


    def test_should_create_a_questionnaire_from_dictionary(self):
        fields = [
                {
                    "name": "What are you reporting on?",
                    "defaultValue": "",
                    "label": "Entity being reported on",
                    "entity_question_flag": True,
                    "type": "text",
                    "ddtype": self.default_ddtype.to_json(),
                    "code": "eid",
                    "constraints": [("length", {"min": 1, "max": 10})],
                    "required":True
                },
                {
                    "constraints": [('range', {
                        "max": 10,
                        "min": 0
                        })],
                    "label": "",
                    "type": "integer",
                    "ddtype": self.default_ddtype.to_json(),
                    "name": "What is your age?",
                    "code": "AGE",
                    "required":False
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
                    "ddtype": self.default_ddtype.to_json(),
                    "name": "Where do you live?",
                    "code": "PLC",
                    "required":False
                    }
                ]
        document = FormModelDocument()
        document.json_fields = fields
        document.entity_type = ["Reporter"]
        document.document_type = "FormModel"
        document.form_code = "F1"
        document.name = "New Project"
        document.type = "survey"
        document.type = "survey"
        entityQ = TextField(name="What are you reporting on?", code="eid",
                            label="Entity being reported on", entity_question_flag=True,
                            constraints=[TextLengthConstraint(min=1, max=10)], ddtype=self.default_ddtype)
        ageQ = IntegerField(name="What is your age?", code="AGE", label="",
                            constraints=[NumericRangeConstraint(min=0, max=10)], ddtype=self.default_ddtype,required=False)
        placeQ = SelectField(name="Where do you live?", code="PLC", label="",
                             options=[{"text": "Pune"}, {"text": "Bangalore"}],
                             single_select_flag=False, ddtype=self.default_ddtype,required=False)
        questions = [entityQ, ageQ, placeQ]
        questionnaire = FormModel.new_from_doc(self.manager, document)
        self.maxDiff = None
        self.assertListEqual(questionnaire.entity_type, ["Reporter"])
        self.assertEqual(questionnaire.name, "New Project")
        self.assertEqual(questionnaire.type, "survey")
        for i in range(len(questions)):
            self.assertEqual(questionnaire.fields[i]._to_json(), questions[i]._to_json())

    def test_should_set_name(self):
        self.form_model.name = 'test_name'
        self.assertEquals(self.form_model.name, 'test_name')


    def test_should_set_entity_type_in_doc(self):
        self.form_model.entity_type = ["WaterPoint", "Dam"]
        self.assertEqual(self.form_model.entity_type, ["WaterPoint", "Dam"])

    def test_should_raise_exception_if_form_code_already_exists_on_creation(self):
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
                              entity_question_flag=True, ddtype=self.default_ddtype)
        form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
                               form_code="1", type='survey', fields=[question1])
        with self.assertRaises(DataObjectAlreadyExists):
            form_model.save()


    def test_should_raise_exception_if_form_code_already_exists_on_updation(self):
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
                              entity_question_flag=True, ddtype=self.default_ddtype)
        form_model2 = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                form_code="2", type='survey', fields=[question1])
        form_model2.save()
        with self.assertRaises(DataObjectAlreadyExists):
            form_model2.form_code = "1"
            form_model2.save()

    def test_should_not_raise_exception_if_form_code_is_updated(self):
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
                              entity_question_flag=True, ddtype=self.default_ddtype)
        form_model2 = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                form_code="2", type='survey', fields=[question1])
        form_model2.save()
        form_model2.form_code = "2"
        form_model2.save()

    def test_should_return_none_if_no_registraion_form_found_for_entity_type(self):
        self.assertIsNone(get_form_model_by_entity_type(self.manager, ['test']))

    def test_should_return_the_registration_form_model_for_the_entity_type(self):
        field1 = TextField(name="entity_question", code="ID", label="What is associated entity",
            entity_question_flag=True, ddtype=self.default_ddtype)
        expected_form_model = FormModel(self.manager, 'registration_form', 'registration_form', 'foo', fields=[field1],
            entity_type=self.entity_type, is_registration_model=True)
        expected_form_model.save()

        reg_form_model = get_form_model_by_entity_type(self.manager, self.entity_type)
        self.assertEqual(expected_form_model.id, reg_form_model.id)
        self.assertEqual(expected_form_model.name, reg_form_model.name)

    def test_should_save_form_model_with_validators(self):
        fields = [TextField('name', 'eid', 'label', self.default_ddtype, entity_question_flag=True)]
        form = FormModel(self.manager, 'test_form', 'label', 'foo', fields=fields, entity_type=['Clinic'], validators=[MandatoryValidator(), MobileNumberValidationsForReporterRegistrationValidator()])
        form.save()
        form = get_form_model_by_code(self.manager, 'foo')
        self.assertEqual(2, len(form.validators))
        self.assertTrue(isinstance(form.validators[0], MandatoryValidator))
        self.assertTrue(isinstance(form.validators[1], MobileNumberValidationsForReporterRegistrationValidator))

    def test_should_get_string_rep_of_form_model(self):
        submission = {"ID": "id", "Q1": "12345", "Q2": "25", "Q3": "a"}
        stringified_dict = self.form_model.stringify(values=self.form_model.validate_submission(submission)[0])
        self.assertEquals("id",stringified_dict.get("ID"))
        self.assertEquals("12345",stringified_dict.get("Q1"))
        self.assertEquals("25",stringified_dict.get("Q2"))
        self.assertEquals("RED",stringified_dict.get("Q3"))

        

    def _create_form_model(self):
        self.entity_type = ["HealthFacility", "Clinic"]
        define_type(self.manager, ["HealthFacility", "Clinic"])
        self.default_ddtype = DataDictType(self.manager, name='Default String Datadict Type', slug='string_default',
            primitive_type='string')
        self.default_ddtype.save()
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
            entity_question_flag=True, ddtype=self.default_ddtype)
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
            defaultValue="some default value",
            constraints=[TextLengthConstraint(5, 10), RegexConstraint("\w+")],
            ddtype=self.default_ddtype)
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
            constraints=[NumericRangeConstraint(min=15, max=120)], ddtype=self.default_ddtype)
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
            options=[("RED", 1), ("YELLOW", 2)], ddtype=self.default_ddtype)
        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
            form_code="1", type='survey', fields=[
                question1, question2, question3, question4])
        self.form_model__id = self.form_model.save()
