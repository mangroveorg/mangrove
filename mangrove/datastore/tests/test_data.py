
import datetime
from pytz import UTC
from mangrove.datastore.entity import Entity, create_entity, get_by_short_code
from mangrove.datastore.entity_type import define_type
from mangrove.errors.MangroveException import FormModelDoesNotExistsException
from mangrove.form_model.field import TextField, IntegerField, SelectField
from mangrove.form_model.form_model import FormModel, get_form_model_by_code
from mangrove.utils.test_utils.database_utils import safe_define_type, uniq, delete_and_create_entity_instance


class TestData(object):
    def __init__(self, manager):
        self.manager = manager
        self.setup()

    def setup(self):
    #        Two forms with data for two months with monthly frequency
        self.ENTITY_TYPE = ["health_facility", "clinic"]
        self.entity_type_string = "health_facility.clinic"
        self.create_clinic_type(self.ENTITY_TYPE)
        self._create_form_model("CL2")
        self._create_form_model("CL1")

        self.entity1, id1 = delete_and_create_entity_instance(self.manager, self.ENTITY_TYPE, ['India', 'MH', 'Pune'],
                                                              "1")

        self._add_data_for_form_1_entity_1(self.entity1)

        self._add_data_for_form_2_entity_1(self.entity1)

        self.entity2, id2 = delete_and_create_entity_instance(self.manager, self.ENTITY_TYPE,
                                                              ['India', 'Karnataka', 'Bangalore'], "2")

        self._add_data_for_form_1_entity_2(self.entity2)
        self._add_data_form_2_entity_2(self.entity2)

        self.entity3, id3 = delete_and_create_entity_instance(self.manager, self.ENTITY_TYPE, ['India', 'MH', 'Mumbai'],
                                                              "3")
        self.entity3.add_data(data=[("beds", 200), ("meds", 50),
                                    ("director", "Dr. C"),
                                    ("patients", 12)],
                              event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
                              submission=dict(submission_id='5', form_code='CL1'))


    def create_clinic_type(self, entity_type):
        self.entity_type = entity_type
        safe_define_type(self.manager, entity_type)

    def create_water_point_entity(self):
        water_point_type = ["waterpoint"]
        safe_define_type(self.manager, water_point_type)
        create_entity(self.manager, entity_type=water_point_type, short_code=uniq("4"))

    def _create_form_model(self, form_code):
        try:
            form = get_form_model_by_code(self.manager, form_code)
            if form:
                form.delete()
        except FormModelDoesNotExistsException:
            pass
        question1 = TextField(name="entity_question", code="ID", label="What is associated entity",
                              entity_question_flag=True)
        question2 = TextField(name="question1_Name", code="Q1", label="What is your name",
                              defaultValue="some default value")
        question3 = IntegerField(name="Father's age", code="Q2", label="What is your Father's Age")
        question4 = SelectField(name="Color", code="Q3", label="What is your favourite color",
                                options=[("RED", 'a'), ("YELLOW", 'b')])

        self.form_model = FormModel(self.manager, entity_type=self.entity_type, name="aids", label="Aids form_model",
                                    form_code=form_code, type='survey', fields=[
                question1, question2, question3, question4])
        self.form_model__id = self.form_model.save()

    def _add_data_for_form_1_entity_1(self, e):
        e.add_data(data=[("name", 'clinic1'), ("beds", 300),
                         ("meds", 20),
                         ("director", "Dr. A"),
                         ("patients", 10), ],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='1', form_code='CL1'))
        e.add_data(data=[("name", 'clinic1'), ("beds", 500),
                         ("meds", 50),
                         ("patients", 20)],
                   event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL1'))
        e.add_data(data=[("name", 'clinic1'), ("beds", 300),
                         ("doctors", 20),
                         ("director", "Dr. A1"),
                         ("patients", 10)],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='1', form_code='CL1'))
        e.add_data(data=[("name", 'clinic1'), ("beds", 200),
                         ("meds", 10),
                         ("patients", 20),
                         ("director", "Dr. A2")],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL1'))

    def _add_data_for_form_2_entity_1(self, e):
        e.add_data(data=[("beds", 200), ("meds", 20),
                         ("patients", 45)],
                   event_time=datetime.datetime(2011, 04, 01, tzinfo=UTC),
                   submission=dict(submission_id='2', form_code='CL2'))

    def _add_data_for_month_aggregate_latest(self, form_code):
        self._create_form_model(form_code)
        e, id = delete_and_create_entity_instance(self.manager, self.ENTITY_TYPE, ['India', 'MH', 'Pune'], "6")
        e.add_data(data=[("icu", 600), ("meds", 250),
                         ("director", "Dr. A"),
                         ("patients", 5)],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code=form_code))
        e.add_data(data=[("icu", 300), ("meds", 400),
                         ("director", "Dr. B2"),
                         ("patients", 20)],
                   event_time=datetime.datetime(2010, 02, 9, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code=form_code))
        e.add_data(data=[("icu", 300), ("meds", 400),
                         ("director", "Dr. B2"),
                         ("patients", 20)],
                   event_time=datetime.datetime(2010, 03, 1, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code=form_code))
        e2, id = delete_and_create_entity_instance(self.manager, self.ENTITY_TYPE, ['India', 'MH', 'Pune'], "7")
        e2.add_data(data=[("icu", 630), ("meds", 250),
                          ("director", "Dr. C"),
                          ("patients", 7)],
                    event_time=datetime.datetime(2010, 02, 12, tzinfo=UTC),
                    submission=dict(submission_id='3', form_code=form_code))



    def _add_data_for_month_aggregate(self, form_code):
        self._create_form_model(form_code)
        e, id = delete_and_create_entity_instance(self.manager, self.ENTITY_TYPE, ['India', 'MH', 'Pune'], "6")
        e.add_data(data=[("icu", 600), ("meds", 250),
                         ("director", "Dr. A"),
                         ("patients", 5)],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code=form_code))
        e.add_data(data=[("icu", 300), ("meds", 400),
                         ("director", "Dr. B2"),
                         ("patients", 20)],
                   event_time=datetime.datetime(2010, 02, 9, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code=form_code))
        e.add_data(data=[("icu", 300), ("meds", 400),
                         ("director", "Dr. B2"),
                         ("patients", 20)],
                   event_time=datetime.datetime(2010, 03, 1, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code=form_code))
        e2, id = delete_and_create_entity_instance(self.manager, self.ENTITY_TYPE, ['India', 'MH', 'Pune'], "7")
        e2.add_data(data=[("icu", 630), ("meds", 250),
                          ("director", "Dr. C"),
                          ("patients", 7)],
                    event_time=datetime.datetime(2010, 02, 12, tzinfo=UTC),
                    submission=dict(submission_id='3', form_code=form_code))

    def _add_data_for_grand_total(self, form_code):
        self._create_form_model(form_code)
        e, id = delete_and_create_entity_instance(self.manager, self.ENTITY_TYPE, ['India', 'MH', 'Pune'], "6")
        e.add_data(data=[("icu", 600), ("meds", 250),
                         ("director", "Dr. A"),
                         ("patients", 5)],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code=form_code))
        e.add_data(data=[("icu", 300), ("meds", 400),
                         ("director", "Dr. B2"),
                         ("patients", 20)],
                   event_time=datetime.datetime(2010, 12, 01, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code=form_code))
        e.add_data(data=[("icu", 200), ("meds", 50),
                         ("director", "Dr. A"),
                         ("patients", 5)],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code=form_code))
        e.add_data(data=[("icu", 200), ("meds", 50),
                         ("director", "Dr. C"),
                         ("patients", 12)],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code=form_code))

        e.add_data(data=[("icu", 200), ("meds", 50),
                         ("director", "Dr. C"),
                         ("patients", 12)],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='agg1'))
        e2, id = delete_and_create_entity_instance(self.manager, self.ENTITY_TYPE, ['India', 'MH', 'Pune'], "7")
        e2.add_data(data=[("icu", 630), ("meds", 250),
                          ("director", "Dr. C"),
                          ("patients", 7)],
                    event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                    submission=dict(submission_id='3', form_code=form_code))


    def _add_data_for_form_1_entity_2(self, e):
        e.add_data(data=[("beds", 100), ("meds", 250),
                         ("director", "Dr. B1"),
                         ("patients", 50)],
                   event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL1'))
        e.add_data(data=[("beds", 200), ("meds", 400),
                         ("director", "Dr. B2"),
                         ("patients", 20)],
                   event_time=datetime.datetime(2010, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code='CL1'))
        e.add_data(data=[("beds", 150), ("meds", 50),
                         ("director", "Dr. B1"),
                         ("patients", 50)],
                   event_time=datetime.datetime(2011, 02, 01, tzinfo=UTC),
                   submission=dict(submission_id='3', form_code='CL1'))

    def _add_data_form_2_entity_2(self, e):
        e.add_data(data=[("beds", 270), ("doctors", 40),
                         ("director", "Dr. B2"),
                         ("patients", 20)],
                   event_time=datetime.datetime(2011, 03, 01, tzinfo=UTC),
                   submission=dict(submission_id='4', form_code='CL2'))

    def add_weekly_data_for_entity1(self):
        self.entity1.add_data(data=[("beds", 100), ("meds", 250),
                                    ("director", "Dr. B1"),
                                    ("patients", 50)],
                              event_time=datetime.datetime(2009, 12, 23, tzinfo=UTC),
                              submission=dict(submission_id='3', form_code='CL1'))
        self.entity1.add_data(data=[("beds", 200), ("meds", 400),
                                    ("director", "Dr. B2"),
                                    ("patients", 20)],
                              event_time=datetime.datetime(2009, 12, 24, tzinfo=UTC),
                              submission=dict(submission_id='4', form_code='CL1'))
        self.entity1.add_data(data=[("beds", 150), ("meds", 50),
                                    ("director", "Dr. B1"),
                                    ("patients", 70)],
                              event_time=datetime.datetime(2009, 12, 27, tzinfo=UTC),
                              submission=dict(submission_id='3', form_code='CL1'))


