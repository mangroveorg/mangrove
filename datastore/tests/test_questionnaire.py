import unittest
import uuid
from mangrove.datastore.database import get_db_manager, _delete_db_and_remove_db_manager
from mangrove.datastore.questionnaire import get, submit
from mangrove.datastore.questionnaire import Questionnaire

class TestQuestionnaire(unittest.TestCase):
    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')
        self.entity_id = uuid.uuid4().get_hex()
        question1 = {"field_name": "Name", "type": "Name", "text": "What is your name","description": "Provide your first name"}
        question2 = {"field_name": "Age", "type": "Age", "text": "What is your Age","description": "Provide your Age"}
        self.e = Questionnaire(self.dbm, entity_id =self.entity_id,name="aids", description="Aids Questionnaire",short_id="1",questions=[
                question1,question2])
        self.questionnaire__id = self.e.save()

    def tearDown(self):
        pass    
#        del self.dbm.database[self.questionnaire__id]
#        _delete_db_and_remove_db_manager(self.dbm)

    def test_create_questionnaire(self):
        self.assertTrue(self.questionnaire__id)

    def test_get_questionnaire(self):
        e = get(self.dbm, self.questionnaire__id)
        self.assertTrue(e.id)
        self.assertTrue(e.type_string == "Questionnaire")

    def test_should_add_name_of_questionnaire(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(saved.name == "aids")

    def test_should_add_description(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(saved.description == "Aids Questionnaire")

    def test_should_add_short_ids(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(saved.short_id == "1")

    def test_should_add_entity_id(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(saved.entity_id == self.entity_id)

    def test_should_add_questions(self):
        saved = get(self.dbm, self.questionnaire__id)
        self.assertTrue(len(saved.questions) == 2)
        self.assertTrue(saved.questions[0].get("field_name") == "Name")
        self.assertTrue(saved.questions[1].get("field_name") == "Age")


    def test_should_submission(self):
        is_success=submit(self.e,[{"Q1":"Ans1","Q2":"Ans2"}],"SMS")
        self.assertTrue(is_success)
