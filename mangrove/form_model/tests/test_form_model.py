# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from datetime import *
from mangrove.form_model.form_model import get_form_model_by_entity_type, list_form_models_by_code
from mangrove.contrib.registration_validators import MobileNumberValidationsForReporterRegistrationValidator
from mangrove.form_model.form_model import get_form_model_by_code
from mangrove.form_model.validators import MandatoryValidator

from mangrove.datastore.documents import FormModelDocument
from mangrove.form_model.field import  TextField, IntegerField, SelectField, DateField
from mangrove.errors.MangroveException import QuestionCodeAlreadyExistsException, EntityQuestionAlreadyExistsException, DataObjectAlreadyExists, QuestionAlreadyExistsException
from mangrove.form_model.form_model import FormModel
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint, RegexConstraint
from mangrove.utils.form_model_builder import FormModelBuilder, create_default_ddtype
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase


class FormModelTest(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        self._create_form_model()

    def tearDown(self):
        MangroveTestCase.tearDown(self)

    def test_get_form_model(self):
        form = FormModel.get(self.manager, self.form_model_id)
        self.assertIsNotNone(form.id)
        self.assertEqual(form.type, "survey")
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
        self.assertListEqual(saved.entity_type, self.entity_type)

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
                options=[("RED", 1), ("YELLOW", 2)], ddtype=self.default_ddtype)
            self.form_model.add_field(field)
            self.form_model.save()
        updated_form = FormModel.get(self.manager, self.form_model_id)
        self.assertEqual("Color", updated_form.get_field_by_code_and_rev("Q3").name)

    def test_should_get_latest_field_if_no_revision_provided_and_no_snapshots(self):
        self.form_model.delete_field(code="Q3")
        field = SelectField(name="New Name", code="Q3", label="What is your favourite color",
            options=[("RED", 1), ("YELLOW", 2)], ddtype=self.default_ddtype)
        self.form_model.add_field(field)
        self.form_model.save()
        updated_form = FormModel.get(self.manager, self.form_model_id)
        self.assertEqual("New Name", updated_form.get_field_by_code_and_rev("Q3").name)

    def test_should_get_revision_field_if_revision_provided(self):
        rev = self.form_model.revision
        self.form_model.create_snapshot()
        self.form_model.delete_field(code="Q3")
        field = SelectField(name="New Name", code="Q3", label="What is your favourite color",
            options=[("RED", 1), ("YELLOW", 2)], ddtype=self.default_ddtype)
        self.form_model.add_field(field)
        self.form_model.save()
        updated_form = FormModel.get(self.manager, self.form_model_id)
        self.assertEqual("Color", updated_form.get_field_by_code_and_rev("Q3", rev).name)

    def test_should_get_fields_excludes_reporting_period_field(self):
        dateField = DateField(name="f2", code="c2", label="f2", date_format="dd.mm.yyyy", ddtype=self.default_ddtype,
            event_time_field_flag=True)
        self.form_model.add_field(dateField)
        self.form_model.save()
        form_model = FormModel.get(self.manager, self.form_model_id)

        self.assertEqual(5, len(form_model.fields))
        self.assertEqual(4, len(form_model.non_rp_fields_by()))

    def test_should_get_fields_excludes_reporting_period_field_if_revision_provided(self):
        dateField = DateField(name="f2", code="c2", label="f2", date_format="dd.mm.yyyy", ddtype=self.default_ddtype,
            event_time_field_flag=True)
        rev = self.form_model.revision
        self.form_model.add_field(dateField)
        self.form_model.create_snapshot()
        self.form_model.delete_field("c2")
        self.form_model.save()
        form_model = FormModel.get(self.manager, self.form_model_id)

        self.assertEqual(4, len(form_model.fields))
        self.assertEqual(4, len(form_model.non_rp_fields_by(rev)))

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
        question = TextField(name="added_question", code="Q4", label="How are you", ddtype=self.default_ddtype)
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

    def test_should_raise_exception_if_entity_field_already_exist(self):
        with self.assertRaises(EntityQuestionAlreadyExistsException):
            form_model = FormModel.get(self.manager, self.form_model_id)
            question = TextField(name="added_question", code="Q5", label="How are you", entity_question_flag=True,
                ddtype=self.default_ddtype)
            form_model.add_field(question)
            form_model.save()

    def test_should_raise_exception_if_code_is_not_unique(self):
        with self.assertRaises(QuestionCodeAlreadyExistsException):
            form_model = FormModel.get(self.manager, self.form_model_id)
            question = TextField(name="added_question", code="q1", label="How are you", ddtype=self.default_ddtype)
            form_model.add_field(question)
            form_model.save()

    def test_should_raise_exception_if_label_is_not_unique(self):
        with self.assertRaises(QuestionAlreadyExistsException):
            form_model = FormModel.get(self.manager, self.form_model_id)
            question = TextField(name="added_question", code="q5", label="What is your name",
                ddtype=self.default_ddtype)
            form_model.add_field(question)
            form_model.save()

    def test_should_set_form_code(self):
        form_model = FormModel.get(self.manager, self.form_model_id)
        form_model.form_code = "xyz"
        self.assertEquals(form_model.form_code, "xyz")

    def test_should_persist_ddtype(self):
        form_model = FormModel.get(self.manager, self.form_model_id)

        for field in form_model.fields:
            self.assertEqual(field.ddtype.slug, self.default_ddtype.slug)
            self.assertEqual(field.ddtype.id, self.default_ddtype.id)
            self.assertEqual(field.ddtype.name, self.default_ddtype.name)

    def test_should_set_entity_type(self):
        form_model = FormModel.get(self.manager, self.form_model_id)
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
                "required": True
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
                "ddtype": self.default_ddtype.to_json(),
                "name": "Where do you live?",
                "code": "PLC",
                "required": False
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
            constraints=[NumericRangeConstraint(min=0, max=10)], ddtype=self.default_ddtype, required=False)
        placeQ = SelectField(name="Where do you live?", code="PLC", label="",
            options=[{"text": "Pune"}, {"text": "Bangalore"}],
            single_select_flag=False, ddtype=self.default_ddtype, required=False)
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
        form = FormModel(self.manager, 'test_form', 'label', 'foo', fields=fields, entity_type=['Clinic'],
            validators=[MandatoryValidator(), MobileNumberValidationsForReporterRegistrationValidator()])
        form.save()
        form = get_form_model_by_code(self.manager, 'foo')
        self.assertEqual(2, len(form.validators))
        self.assertTrue(isinstance(form.validators[0], MandatoryValidator))
        self.assertTrue(isinstance(form.validators[1], MobileNumberValidationsForReporterRegistrationValidator))

    def test_should_batch_get_form_models(self):
        fields = [TextField('name', 'eid', 'label', self.default_ddtype, entity_question_flag=True)]
        form = FormModel(self.manager, 'test_form', 'label', 'form_code1', fields=fields, entity_type=['Clinic'],
            validators=[MandatoryValidator(), MobileNumberValidationsForReporterRegistrationValidator()])
        form.save()

        fields = [TextField('name', 'eid', 'label', self.default_ddtype, entity_question_flag=True)]
        form = FormModel(self.manager, 'test_form', 'label', 'form_code2', fields=fields, entity_type=['Clinic'],
            validators=[MandatoryValidator(), MobileNumberValidationsForReporterRegistrationValidator()])
        form.save()

        forms = list_form_models_by_code(self.manager, ['form_code1', 'form_code2'])

        self.assertEqual(2, len(forms))
        self.assertEqual('form_code1', forms[0].form_code)
        self.assertEqual('form_code2', forms[1].form_code)

    def test_should_get_string_rep_of_form_model(self):
        submission = {"ID": "id", "Q1": "12345", "Q2": "25", "Q3": "a"}
        stringified_dict = self.form_model.stringify(values=self.form_model.validate_submission(submission)[0])
        self.assertEquals("id", stringified_dict.get("ID"))
        self.assertEquals("12345", stringified_dict.get("Q1"))
        self.assertEquals("25", stringified_dict.get("Q2"))
        self.assertEquals("RED", stringified_dict.get("Q3"))

    def _create_form_model(self):
        self.entity_type = ["HealthFacility", "Clinic"]
        self.default_ddtype = create_default_ddtype(self.manager)
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
            entity_question_flag=True, ddtype=self.default_ddtype)
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
            defaultValue="some default value", constraints=[TextLengthConstraint(5, 10), RegexConstraint("\w+")],
            ddtype=self.default_ddtype)
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
            constraints=[NumericRangeConstraint(min=15, max=120)], ddtype=self.default_ddtype)
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
            options=[("RED", 1), ("YELLOW", 2)], ddtype=self.default_ddtype)
        self.form_model = FormModelBuilder(self.manager, self.entity_type, "1", 'survey').label("Aids form_model").name(
            "aids").add_fields(question1,
            question2, question3, question4).build()
        self.form_model_id = self.form_model.id

    def test_event_time_value_should_return_datetime(self):
        entity_type = ["HealthFacility", "Clinic"]
        default_ddtype = create_default_ddtype(self.manager)
        date_question = DateField("entity_question", "ID", "What is the reporting date", 'dd.mm.yyyy', default_ddtype,
            event_time_field_flag=True)
        form_model = FormModelBuilder(self.manager, entity_type, "2", 'survey').label("Aids form_model").name(
            "aids").add_fields(date_question).build()
        form_model.bind({'id':'12.12.2001'})
        expected_date = datetime.strptime('12.12.2001', date_question.DATE_DICTIONARY.get('dd.mm.yyyy'))
        self.assertEqual(expected_date,form_model._get_event_time_value())
