# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import unittest
import uuid
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.entity import Entity
from mangrove.datastore.question import Question, QuestionBuilder
from mangrove.datastore.questionnaire import get, submit
from mangrove.datastore.questionnaire import Questionnaire

class TestQuestionnaire(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        self.entity_id = uuid.uuid4().get_hex()
        e = Entity(self.dbm, entity_type="clinic", location=["India","MH","Pune"])
        self.entity_uuid = e.save()
        question1 = QuestionBuilder(name="question1_Name", type="text", sms_code="Q1", label="What is your name",
                            defaultValue="some default value",language="eng").to_json()
        question2 = QuestionBuilder(name= "Father's age", type= "integer", sms_code="Q2",label= "What is your Father's Age",range= {"min": 15,"max": 120}).to_json()
        question3 = QuestionBuilder(name= "Color", type= "select1", sms_code="Q3",label= "What is your favourite color",options= [("RED",1),("YELLOW",2)]).to_json()



        self.questionare = Questionnaire(self.dbm, entity_id =self.entity_uuid,name="aids", label="Aids Questionnaire",questionnaire_code="1",type='survey',questions=[
                question1,question2,question3])
        self.questionnaire__id = self.questionare.save()

    def tearDown(self):
        del self.dbm.database[self.questionnaire__id]
        _delete_db_and_remove_db_manager(self.dbm)
        pass

    def test_create_questionnaire(self):
        self.assertTrue(self.questionnaire__id)

    def test_get_questionnaire(self):
        e = get(self.dbm, self.questionnaire__id)
        self.assertTrue(e.id)
        self.assertTrue(e.type == "survey")

    def test_should_add_name_of_questionnaire(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(saved.name == "aids")

    def test_should_add_label(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(saved.label == "Aids Questionnaire")

    def test_should_add_short_ids(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(saved.questionnaire_code == "1")

    def test_should_add_entity_id(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(saved.entity_id == self.entity_uuid)

    def test_should_add_questions(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(len(saved.questions) == 3)
        self.assertTrue(saved.questions[0].get("name") == "question1_Name")
        self.assertTrue(saved.questions[1].get("name") == "Father's age")

    def test_should_add_integer_question_with_constraints(self):
        integer_question = get(self.dbm, self.questionnaire__id).questions[1]
        range_constraint = integer_question.get("range")
#        self.assertTrue(range_constraint)
        self.assertTrue(integer_question.get("name") == "Father's age")
        self.assertTrue(range_constraint.get("min"),15)
        self.assertTrue(range_constraint.get("max"),120)

    def test_should_add_select1_question(self):
        select_question = get(self.dbm, self.questionnaire__id).questions[2]
        option_constraint = select_question.get("options")

        self.assertEquals(len(option_constraint),2)
        self.assertEquals(option_constraint[0].get("val"),1)

    def test_should_add_english_as_default_langauge(self):
        activeLangauges = self.questionare.activeLanguages
        self.assertTrue("eng" in activeLangauges)


    def test_should_submission(self):
        data_record_id=submit(self.dbm,self.questionare.questionnaire_code ,self.questionare.entity_id,{"Q1":"Ans1","Q2":"Ans2"},"SMS")
        self.assertTrue(data_record_id)
