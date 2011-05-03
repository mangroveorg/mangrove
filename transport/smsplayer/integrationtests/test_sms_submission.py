# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
#  This is an integration test.
# Send sms, parse and save.
from unittest.case import TestCase
from mangrove.datastore.database import get_db_manager, remove_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.entity import define_type
from mangrove.datastore import datarecord
from mangrove.datastore.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel
from mangrove.transport.submissions import SubmissionHandler, Request
from mangrove.datastore.datadict import DataDictType

class TestShouldSaveSMSSubmission(TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        self.entity_type = define_type(self.dbm, ["HealthFacility", "Clinic"])
        self.reporter_type = define_type(self.dbm, ["Reporter"])
        self.name_type = DataDictType(self.dbm, name='Name', slug='Name', primitive_type='string')
        self.first_name_type = DataDictType(self.dbm, name='telephone_number', slug='telephone_number', primitive_type='string')
        self.telephone_number_type = DataDictType(self.dbm, name='first_name', slug='first_name', primitive_type='string')
        self.entity = datarecord.register(self.dbm, entity_type="HealthFacility.Clinic",
                                                   data=[("Name", "Ruby", self.name_type)], location=["India", "Pune"], source="sms")
        datarecord.register(self.dbm, entity_type=["Reporter"], data=[("telephone_number", '1234', self.telephone_number_type),
                                                                      ("first_name","Test_reporter", self.first_name_type)], location=[],
                            source="sms")
        question1 = TextField(name="entity_question", question_code="ID", label="What is associated entity"
                              , language="eng", entity_question_flag=True)
        question2 = TextField(name="Name", question_code="NAME", label="Clinic Name",
                              defaultValue="some default value", language="eng")
        question3 = IntegerField(name="Arv stock", question_code="ARV", label="ARV Stock",
                                 range={"min": 15, "max": 120})
        question4 = SelectField(name="Color", question_code="COL", label="Color",
                                options=[("RED", 1), ("YELLOW", 2)])

        self.form_model = FormModel(self.dbm, entity_type_id=self.entity_type.id, name="aids", label="Aids form_model",
                                    form_code="CLINIC", type='survey', fields=[question1, question2, question3])
        self.form_model.add_field(question4)
        self.form_model__id = self.form_model.save()



    def tearDown(self):
        del self.dbm.database[self.form_model__id]
        _delete_db_and_remove_db_manager(self.dbm)
        pass

    def test_should_save_submitted_sms(self):
        #text = "CLINIC +ID %s +NAME CLINIC-MADA +ARV 50 +COL RED" % self.entity.id
        #s = SubmissionHandler(self.dbm)
        #
        #response = s.accept(Request("sms",text,"1234","5678"))
        #
        #self.assertTrue(response.success)
        #data = self.entity.values({"Name": "latest", "Arv stock": "latest", "Color": "latest"})
        #self.assertEquals(data["Name"],"CLINIC-MADA")
        #self.assertEquals(data["Arv stock"],50)
        #self.assertEquals(data["Color"],"RED")
        pass
