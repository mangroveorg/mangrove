# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import Entity
import mangrove.datastore.datarecord as datarecord

class TestDataRecord(unittest.TestCase):

    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_be_able_to_submit_datarecord_on_entity(self):
        e = Entity(self.dbm, entity_type="clinic", location=["India","MH","Pune"])
        uuid = e.save()
        submission_ids = datarecord.submit(self.dbm, entity_id=uuid, data=[("First_Name", "Jeff",)], source="web")
        assert submission_ids[0]
        assert submission_ids[1]


    def test_should_be_able_to_submit_datarecord_on_entity(self):
        entity = datarecord.register(self.dbm,entity_type = "HNI.Reporter", data=[("First_Name", "Jeff",)],
                                     location= ["India", "Pune"], source="web")
        assert entity
        current_values = entity.values({"First_Name": "latest"})
        self.assertEquals("Jeff", current_values["First_Name"])
