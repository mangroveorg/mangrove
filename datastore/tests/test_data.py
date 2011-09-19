# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
from pytz import UTC
from mangrove.datastore.datadict import DataDictType
from mangrove.datastore.entity import Entity
from mangrove.datastore.entity_type import define_type
from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel


class TestData(object):
    def __init__(self,manager):
        self.manager=manager
        self.setup()
        
    def setup(self):
#        Two forms with data for two months with monthly frequency
        ENTITY_TYPE = ["Health_Facility", "Clinic"]
        self.create_clinic_type(ENTITY_TYPE)
        self._create_form_model("CL2")
        self._create_form_model("CL1")
        self.dd_types = self.create_datadict_types()
        self.entity1, id1 = self.create_entity_instance(ENTITY_TYPE, ['India', 'MH', 'Pune'],"1")

        self._add_data_for_form_1_entity_1(self.entity1)

        self._add_data_for_form_2_entity_1(self.entity1)

        self.entity2, id2 = self.create_entity_instance(ENTITY_TYPE, ['India', 'Karnataka', 'Bangalore'],"2")

        self._add_data_for_form_1_entity_2( self.entity2)
        self._add_data_form_2_entity_2( self.entity2)

        self.entity3, id3 = self.create_entity_instance(ENTITY_TYPE, ['India', 'MH', 'Mumbai'],"3")
        self.entity3.add_data(data=[("beds", 200, self.dd_types['beds']), ("meds", 50, self.dd_types['meds']),
            ("director", "Dr. C", self.dd_types['director']), ("patients", 12, self.dd_types['patients'])],
                   event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='5', form_code='CL1'))


    def create_entity_instance(self, ENTITY_TYPE, location,short_code):
        e = Entity(self.manager, entity_type=ENTITY_TYPE, location=location,short_code=short_code)
        id1 = e.save()
        return e, id1

    def create_clinic_type(self, entity_type):
        self.entity_type = entity_type
        define_type(self.manager, entity_type)


    def _create_form_model(self, form_code):
        self.default_ddtype = DataDictType(self.manager, name='Default String Datadict Type', slug='string_default',
                                           primitive_type='string')
        self.default_ddtype.save()
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
                              language="eng", entity_question_flag=True, ddtype=self.default_ddtype)
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
                              defaultValue="some default value", language="eng",
                              ddtype=self.default_ddtype)
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age",
                                 ddtype=self.default_ddtype)
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
                                options=[("RED", 1), ("YELLOW", 2)], ddtype=self.default_ddtype)

        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code=form_code, type='survey', fields=[
                question1, question2, question3, question4])
        self.form_model__id = self.form_model.save()

    def create_datadict_types(self):
        dd_types = {
            'beds': DataDictType(self.manager, name='beds', slug='beds', primitive_type='number'),
            'meds': DataDictType(self.manager, name='meds', slug='meds', primitive_type='number'),
            'patients': DataDictType(self.manager, name='patients', slug='patients', primitive_type='number'),
            'doctors': DataDictType(self.manager, name='doctors', slug='doctors', primitive_type='number'),
            'director': DataDictType(self.manager, name='director', slug='director', primitive_type='string')
        }
        for label, dd_type in dd_types.items():
            dd_type.save()
        return dd_types
    
    def _add_data_for_form_1_entity_1(self,  e):
        e.add_data(data=[("beds", 300, self.dd_types['beds']), ("meds", 20, self.dd_types['meds']),
                ("director", "Dr. A", self.dd_types['director']), ("patients", 10, self.dd_types['patients'])],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='1', form_code='CL1'))
        e.add_data(data=[("beds", 500, self.dd_types['beds']), ("meds", 50, self.dd_types['meds']),
                ("patients", 20, self.dd_types['patients'])],
                   event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL1'))
        e.add_data(data=[("beds", 300, self.dd_types['beds']), ("doctors", 20, self.dd_types['doctors']),
                ("director", "Dr. A1", self.dd_types['director']), ("patients", 10, self.dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='1', form_code='CL1'))
        e.add_data(data=[("beds", 200, self.dd_types['beds']), ("meds", 10, self.dd_types['meds']),
                ("patients", 20, self.dd_types['patients']), ("director", "Dr. A2", self.dd_types['director'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL1'))

    def _add_data_for_form_2_entity_1(self, e):
        e.add_data(data=[("beds", 200, self.dd_types['beds']), ("meds", 20, self.dd_types['meds']),
                ("patients", 45, self.dd_types['patients'])],
                   event_time=datetime.datetime(2011, 04, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL2'))

    def _add_data_for_form_1_entity_2(self,  e):
        e.add_data(data=[("beds", 100, self.dd_types['beds']), ("meds", 250, self.dd_types['meds']),
                ("director", "Dr. B1", self.dd_types['director']), ("patients", 50, self.dd_types['patients'])],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL1'))
        e.add_data(data=[("beds", 200, self.dd_types['beds']), ("meds", 400, self.dd_types['meds']),
                ("director", "Dr. B2", self.dd_types['director']), ("patients", 20, self.dd_types['patients'])],
                   event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code='CL1'))
        e.add_data(data=[("beds", 150, self.dd_types['beds']), ("meds", 50, self.dd_types['meds']),
                ("director", "Dr. B1", self.dd_types['director']), ("patients", 50, self.dd_types['patients'])],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL1'))

    def _add_data_form_2_entity_2(self, e):
        e.add_data(data=[("beds", 270, self.dd_types['beds']), ("doctors", 40, self.dd_types['doctors']),
                ("director", "Dr. B2", self.dd_types['director']), ("patients", 20, self.dd_types['patients'])],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code='CL2'))

    def add_weekly_data_for_entity1(self):
        self.entity1.add_data(data=[("beds", 100, self.dd_types['beds']), ("meds", 250, self.dd_types['meds']),
                ("director", "Dr. B1", self.dd_types['director']), ("patients", 50, self.dd_types['patients'])],
                   event_time=datetime.datetime(2009, 12, 23, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL1'))
        self.entity1.add_data(data=[("beds", 200, self.dd_types['beds']), ("meds", 400, self.dd_types['meds']),
                ("director", "Dr. B2", self.dd_types['director']), ("patients", 20, self.dd_types['patients'])],
                   event_time=datetime.datetime(2009, 12, 24, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code='CL1'))
        self.entity1.add_data(data=[("beds", 150, self.dd_types['beds']), ("meds", 50, self.dd_types['meds']),
                ("director", "Dr. B1", self.dd_types['director']), ("patients", 70, self.dd_types['patients'])],
                   event_time=datetime.datetime(2009, 12, 27, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL1'))
