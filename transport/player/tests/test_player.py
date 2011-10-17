# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock
from mangrove.datastore.database import DatabaseManager
from mangrove.transport.player.player import   Player


class TestSMSPlayer(TestCase):
    def setUp(self):
        self.loc_tree = Mock()
        self.loc_tree.get_hierarchy_path.return_value = ['hierarchy']
        self.dbm = Mock(spec=DatabaseManager)
        self.submission_handler_mock = Mock()
        self.player = Player(self.dbm, self.loc_tree)


    def test_should_not_resolve_location_hierarchy_if_hierarchy_already_passed_in(self):
        values = dict(l='a,b,c', t='clinic')
        self.player._set_location_data(values=values)
        self.assertEqual(['c', 'b', 'a'], values['l'])

    def test_should_resolve_location_hierarchy_if_hierarchy_not_passed_in(self):
        values = dict(l='no_hierarchy', t='clinic')
        self.player._set_location_data(values=values)
        self.assertEqual(['no_hierarchy'], values['l'])
