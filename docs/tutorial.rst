-----------------------
Mangrove Tutorial
-----------------------

Introduction
------------
Follow are the main concepts in mangrove.

Entity Type:
---------------
create entity type::

     entity_type = ["HealthFacility", "Clinic"]
     # entity type is hierarchy. example "Education School" etc
     define_type(self.dbm, entity_type)

Entity:
---------------
create entity ::

     entity_type = ["HealthFacility", "Clinic"]
     # entity type is hierarchy. example "Education School" etc
     create_entity(self.dbm, entity_type=entity_type, short_code="1")

Data Record:
---------------
get datarecord::

     DataRecord.get(self.dbm,data_record_id)


Form Model:
---------------
Create a Form::

    default_ddtype = DataDictType(self.dbm, name='Default String Datadict Type', slug='string_default',
                                           primitive_type='string')
    default_ddtype.save()
    question1 = TextField(name="Q1", code="ID", label="What is the reporter ID?",
                                  language="eng", entity_question_flag=True, ddtype=default_ddtype)

    question2 = TextField(name="Q2", code="DATE", label="What month and year are you reporting for?",
                                      language="eng", entity_question_flag=False, ddtype=default_ddtype)

    question3 = TextField(name="Q3", code="NETS", label="How many mosquito nets did you distribute?",
                                      language="eng", entity_question_flag=False, ddtype=default_ddtype)

    form_model = FormModel(dbm, entity_type=["Reporter"], name="Mosquito Net Distribution Survey",
                                    label="Mosquito Net Distribution Survey",
                                    form_code="MNET",
                                    type='survey',
                                    fields=[question1, question2, question3])
    form_model.save()

Data Submission:
---------------
Submit data to the form directly
++++++++++++++++++++++++++++++++

::

    values = { "ID" : "rep45", "DATE" : "10.2010", "NETS" : "50" }
    form = get_form_model_by_code(dbm, "MNET")
    form_submission = form.submit(dbm, values, submission_id)

Submit data to the player
++++++++++++++++++++++++++++++++

::

    text = "MNET .ID rep45 .DATE 10.2010 .NETS 50"
    transport_info = TransportInfo(transport="sms", source="9923712345", destination="5678")
    sms_player = SMSPlayerV2(dbm,[])
    response = sms_player.add_survey_response(Request(transportInfo=transport_info, message=text))

    The player will also log the submission for you in Mangrove.

Load all submissions for the form::
++++++++++++++++++++++++++++++++
::


    get_submissions_made_for_form()

Aggregation:
---------------

Monthly Aggregate on all data records for a field per entity for the form code
++++++++++++++++++++++++++++++++

::

    values = aggregate_for_time_period(
        self.manager,
        form_code='CL1',
        aggregates=[Sum("patients"), Min('meds'), Max('beds'),Latest("director")],
        period=Month(2, 2010)
        )

    Returns one row per entity, with the aggregated values for each
    field.
    {"<entity_id>": {"patients": 10, 'meds': 20, 'beds': 300 , 'director': "Dr. A"}}


Weekly Aggregate on all data records for a field per entity for the form code
++++++++++++++++++++++++++++++++

::

    values = aggregate_for_time_period(
        self.manager,
        form_code='CL1',
        aggregates=[Sum("patients"), Min('meds'), Max('beds'),Latest("director")],
        period=Week(52, 2009)
        )

    52 is the weeknumber and 2009 is the year.
    Returns one row per entity, with the aggregated values for each field.
    {"<entity_id>": {"patients": 10, 'meds': 20, 'beds': 300 , 'director': "Dr. A"}}


Yearly Aggregate on all data records for a field per entity for the form code
++++++++++++++++++++++++++++++++

::

    values = aggregate_for_time_period(
        self.manager,
        form_code='CL1',
        aggregates=[Sum("patients"), Min('meds'), Max('beds'),Latest("director")],
        period=Year(2010)
        )

    2010 is the year.
    Returns one row per entity, with the aggregated values for each field.
    {"<entity_id>": {"patients": 10, 'meds': 20, 'beds': 300 , 'director': "Dr. A"}}
