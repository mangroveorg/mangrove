# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock
from form_model.field import HierarchyField
from mangrove.form_model.form_model import FormModel
from mangrove.datastore.database import DatabaseManager
from mangrove.transport.player.player import   Player
from mangrove.transport.facade import RegistrationWorkFlow

def get_location_hierarchy(foo):
    return ["no_hierarchy"]

class TestBasePlayer(TestCase):
    def setUp(self):
        loc_tree = Mock()
        loc_tree.get_hierarchy_path.return_value = ['hierarchy']
        dbm = Mock(spec=DatabaseManager)
        form_model = Mock(spec=FormModel)
        location_field = Mock(spec=HierarchyField)
        form_model.get_field_by_name.return_value= location_field
        location_field.code='l'
        self.registration_workflow = RegistrationWorkFlow(dbm, form_model, loc_tree, get_location_hierarchy)

    def test_should_not_resolve_location_hierarchy_if_hierarchy_already_passed_in(self):
        values = dict(l='a,b,c', t='clinic')
        self.registration_workflow._set_location_data(values=values)
        self.assertEqual(['c', 'b', 'a'], values['l'])

    def test_should_resolve_location_hierarchy_if_hierarchy_not_passed_in(self):
        values = dict(l='no_hierarchy', t='clinic')
        self.registration_workflow._set_location_data(values=values)
        self.assertEqual(['no_hierarchy'], values['l'])
