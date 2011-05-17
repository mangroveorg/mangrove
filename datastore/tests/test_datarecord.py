# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import unittest
from mangrove.datastore.database import _delete_db_and_remove_db_manager, get_db_manager
from mangrove.datastore.entity import Entity
import mangrove.datastore.datarecord as datarecord
from mangrove.datastore.datadict import DataDictType


class TestDataRecord(unittest.TestCase):

    def setUp(self):
        self.dbm = get_db_manager(database='mangrove-test')

    def tearDown(self):
        _delete_db_and_remove_db_manager(self.dbm)

    def test_should_be_able_to_submit_datarecord_on_entity(self):
        e = Entity(self.dbm, entity_type="clinic", location=["India", "MH", "Pune"])
        uuid = e.save()
        name_type = DataDictType(self.dbm, name='First name', slug='first_Name', primitive_type='string')
        name_type.save()
        submission_ids = datarecord.submit(self.dbm, entity_id=uuid, data=[('first_Name', "Jeff", name_type)], source="web")
        assert submission_ids[0]
        assert submission_ids[1]

    def test_should_be_able_to_submit_datarecord_on_entity_2(self):
        name_type = DataDictType(self.dbm, name='First name', slug='first_Name', primitive_type='string')
        name_type.save()
        entity = datarecord.register(self.dbm, entity_type="HNI.Reporter", data=[('first_Name', "Jeff", name_type)],
                                     location=["India", "Pune"], source="web")
        assert entity
        current_values = entity.values({"first_Name": "latest"})
        self.assertEquals("Jeff", current_values["first_Name"])

