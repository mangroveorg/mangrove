# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from  mangrove import initializer
from mangrove.datastore.database import get_db_manager, remove_db_manager
from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.entity import define_type, create_entity
from mangrove.form_model.field import SelectField, IntegerField, TextField
from mangrove.form_model.form_model import FormModel, NAME_FIELD, MOBILE_NUMBER_FIELD
from mangrove.form_model.validation import NumericConstraint, TextConstraint
from mangrove.datastore.report_generator import get_data_by_form_code
from mangrove.transport.submissions import SubmissionHandler, Request

class TestReportForFormCode(unittest.TestCase):
    
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        initializer.run(self.dbm)
        define_type(self.dbm, ["dog"])
        entity_type = ["HealthFacility", "Clinic"]
        define_type(self.dbm, entity_type)
        name_type = DataDictType(self.dbm, name='Name', slug='name', primitive_type='string')
        telephone_number_type = DataDictType(self.dbm, name='telephone_number', slug='telephone_number',
                                                  primitive_type='string')
        entity_id_type = DataDictType(self.dbm, name='Entity Id Type', slug='entity_id', primitive_type='string')
        stock_type = DataDictType(self.dbm, name='Stock Type', slug='stock', primitive_type='integer')
        color_type = DataDictType(self.dbm, name='Color Type', slug='color', primitive_type='string')
        name_type.save()
        telephone_number_type.save()
        stock_type.save()
        color_type.save()

        create_entity(self.dbm, entity_type=["HealthFacility", "Clinic"],
                                    location=["India", "Pune"], aggregation_paths=None, short_code="CLI1",
                                    )
        create_entity(self.dbm, entity_type=["HealthFacility", "Clinic"],
                                    location=["India", "Pune"], aggregation_paths=None, short_code="CLI2",
                                    )
        create_entity(self.dbm, entity_type=["HealthFacility", "Clinic"],
                                    location=["India", "Pune"], aggregation_paths=None, short_code="CLI3",
                                    )
        reporter = create_entity(self.dbm, entity_type=["Reporter"],
                                 location=["India", "Pune"], aggregation_paths=None, short_code="REP1",
                                 )

        reporter.add_data(data=[(MOBILE_NUMBER_FIELD, '1234', telephone_number_type),
                                (NAME_FIELD, "Test_reporter", name_type)], submission = dict(submission_id="2"))

        question1 = TextField(name="entity_question", code="EID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=entity_id_type)
        question2 = TextField(name="Name", code="NAME", label="Clinic Name",
                              defaultValue="some default value", language="eng", length=TextConstraint(4, 15),
                              ddtype=name_type)
        question3 = IntegerField(name="Arv stock", code="ARV", label="ARV Stock",
                                 range=NumericConstraint(min=15, max=120), ddtype=stock_type)
        question4 = SelectField(name="Color", code="COL", label="Color",
                                options=[("RED", 1), ("YELLOW", 2)], ddtype=color_type)

        form_model = FormModel(self.dbm, entity_type=entity_type, name="aids", label="Aids form_model",
                                    form_code="CLINIC", type='survey', fields=[question1, question2, question3])
        form_model.add_field(question4)
        form_model.save()

    def tearDown(self):
        remove_db_manager(self.dbm)
        if self.dbm.database_name in self.dbm.server:
            del self.dbm.server[self.dbm.database_name]


    def test_should_get_latest_value_for_a_form_code(self):
        s = SubmissionHandler(self.dbm)

        text1 = "CLINIC +EID CLI1 +name CLINIC-MADA +ARV 50 +COL a"
        text2 = "CLINIC +EID CLI3 +name CLINIC-MADA +ARV 20 +COL a"
        text3 = "CLINIC +EID CLI1 +name CLINIC-MADA +ARV 60 +COL a"
        text4 = "CLINIC +EID CLI2 +name CLINIC-MADA +ARV 90 +COL a"
        text5 = "CLINIC +EID CLI1 +name CLINIC-MADA +ARV 30 +COL a"
        text6 = "CLINIC +EID CLI3 +name CLINIC-MADA +ARV 40 +COL a"
        text7 = "CLINIC +EID CLI2 +name CLINIC-MADA +ARV 50 +COL a"

        s.accept(Request("sms", text1, "1234", "5678"))
        s.accept(Request("sms", text2, "1234", "5678"))
        s.accept(Request("sms", text3, "1234", "5678"))
        s.accept(Request("sms", text4, "1234", "5678"))
        s.accept(Request("sms", text5, "1234", "5678"))
        s.accept(Request("sms", text6, "1234", "5678"))
        s.accept(Request("sms", text7, "1234", "5678"))

        data = get_data_by_form_code(self.dbm, "CLINIC")
        self.assertEquals(3, len(data))
        self.assertEquals(data[0]["short_code"], "CLI1")
        self.assertEquals(data[1]["short_code"], "CLI2")
        self.assertEquals(data[2]["short_code"], "CLI3")

        self.assertEquals(data[0]["Arv stock"], 30)
        self.assertEquals(data[1]["Arv stock"], 50)
        self.assertEquals(data[2]["Arv stock"], 40)


