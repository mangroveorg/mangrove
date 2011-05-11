# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

#  This is an integration test.
# Send sms, parse and save.

from unittest.case import TestCase
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.documents import SubmissionLogDocument
from mangrove.datastore.entity import define_type, Entity
from mangrove.datastore import datarecord
from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel, RegistrationFormModel
from mangrove.form_model.validation import IntegerConstraint, TextConstraint
from mangrove.transport.submissions import SubmissionHandler, Request, get_submissions_made_for_questionnaire
from mangrove.datastore.datadict import DataDictType


class TestShouldSaveSMSSubmission(TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test1')
        self.entity_type = ["HealthFacility", "Clinic"]
        define_type(self.dbm, self.entity_type)
        self.reporter_type = define_type(self.dbm, ["Reporter"])

        self.name_type = DataDictType(self.dbm, name='Name', slug='Name', primitive_type='string')
        self.first_name_type = DataDictType(self.dbm, name='telephone_number', slug='telephone_number',
                                            primitive_type='string')
        self.telephone_number_type = DataDictType(self.dbm, name='first_name', slug='first_name',
                                                  primitive_type='string')
        self.ddtype =  DataDictType(self.dbm, name='Default Datadict Type', slug='default', primitive_type='string')

        self.entity = datarecord.register(self.dbm, entity_type="HealthFacility.Clinic",
                                          data=[("Name", "Ruby", self.name_type)], location=["India", "Pune"],
                                          source="sms")

        datarecord.register(self.dbm, entity_type=["Reporter"],
                            data=[("telephone_number", '1234', self.telephone_number_type),
                                  ("first_name", "Test_reporter", self.first_name_type)], location=[],
                            source="sms")

        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.ddtype)
        question2 = TextField(name="Name", question_code="NAME", label="Clinic Name",
                              defaultValue="some default value", language="eng", length=TextConstraint(4, 15), ddtype=self.ddtype)
        question3 = IntegerField(name="Arv stock", question_code="ARV", label="ARV Stock",
                                 range=IntegerConstraint(min=15, max=120), ddtype=self.ddtype)
        question4 = SelectField(name="Color", question_code="COL", label="Color",
                                options=[("RED", 1), ("YELLOW", 2)], ddtype=self.ddtype)

        self.form_model = FormModel(self.dbm, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code="CLINIC", type='survey', fields=[question1, question2, question3])
        self.form_model.add_field(question4)
        self.form_model__id = self.form_model.save()

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_save_submitted_sms(self):
        text = "CLINIC +ID %s +NAME CLINIC-MADA +ARV 50 +COL a" % self.entity.id
        s = SubmissionHandler(self.dbm)

        response = s.accept(Request("sms", text, "1234", "5678"))

        self.assertTrue(response.success)
        data = self.entity.values({"Name": "latest", "Arv stock": "latest", "Color": "latest"})
        self.assertEquals(data["Name"], "CLINIC-MADA")
        self.assertEquals(data["Arv stock"], 50)

    def test_should_give_error_for_wrong_integer_value(self):
        text = "CLINIC +ID %s +ARV 150 " % self.entity.id
        s = SubmissionHandler(self.dbm)

        response = s.accept(Request("sms", text, "1234", "5678"))
        self.assertFalse(response.success)
        self.assertEqual(len(response.errors), 1)

    def test_should_give_error_for_wrong_text_value(self):
        text = "CLINIC +ID CID001 +NAME ABC"
        s = SubmissionHandler(self.dbm)
        response = s.accept(Request("sms", text, "1234", "5678"))
        self.assertFalse(response.success)
        self.assertEqual(len(response.errors), 1)

    def test_get_submissions_for_form(self):
        submission_id1 = self.dbm._save_document(SubmissionLogDocument(channel="transport", source=1234,
                                                                destination=12345, form_code="abc", values={'Q1': 'ans1', 'Q2': 'ans2'},
                                                                status=False, error_message="")).id
        submission_id2 = self.dbm._save_document(SubmissionLogDocument(channel="transport", source=1234,
                                                                destination=12345, form_code="abc", values={'Q1': 'ans12', 'Q2': 'ans22'},
                                                                status=False, error_message="")).id
        submission_id3 = self.dbm._save_document(SubmissionLogDocument(channel="transport", source=1234,
                                                                destination=12345, form_code="def", values={'defQ1': 'defans12', 'defQ2': 'defans22'},
                                                                status=False, error_message="")).id

        submission_list = get_submissions_made_for_questionnaire(self.dbm, "abc")
        self.assertEquals(2, len(submission_list))
        self.assertEquals({'Q1': 'ans1', 'Q2': 'ans2'}, submission_list[0]['values'])
        self.assertEquals({'Q1': 'ans12', 'Q2': 'ans22'}, submission_list[1]['values'])

    def test_error_messages_are_being_logged_in_submissions(self):
        text = "CLINIC +ID %s +ARV 150 " % self.entity.id
        s = SubmissionHandler(self.dbm)
        response = s.accept(Request("sms", text, "1234", "5678"))
        submission_list = get_submissions_made_for_questionnaire(self.dbm, "CLINIC")
        self.assertEquals(1, len(submission_list))
        self.assertEquals("Answer 150 for question ARV is greater than allowed.\n", submission_list[0]['error_message'])

    def test_should_create_new_entity_on_registration(self):
        question1 = TextField(name="entity_type", question_code="ET", label="What is associated entity type?",
                          language="eng", entity_question_flag=False)
        question2 = TextField(name="name", question_code="N", label="What is the entity's name?",
                              defaultValue="some default value", language="eng")
        question3 = TextField(name="short_name", question_code="S", label="What is the entity's short name?",
                              defaultValue="some default value", language="eng")
        question4 = TextField(name="location", question_code="L", label="What is the entity's location?",
                              defaultValue="some default value", language="eng")
        question5 = TextField(name="description", question_code="D", label="Describe the entity",
                              defaultValue="some default value", language="eng")
        question6 = TextField(name="short_name", question_code="M", label="What is the associated mobile number?",
                              defaultValue="some default value", language="eng")

        form_model = RegistrationFormModel(self.dbm, name="REG", form_code="REG", fields=[
                        question1, question2, question3, question4, question5, question6])
        qid = form_model.save()

        text = "REG +ET dog"
        s = SubmissionHandler(self.dbm)
        response = s.accept(Request("sms", text, "1234", "5678"))
        print response.success
        assert response.success
        entity_id = response.datarecord_id
        e = self.dbm.get(entity_id, Entity)
        assert e
