# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from unittest.case import TestCase
from mock import Mock, patch
from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.transport.player.player import Request, TransportInfo, Player
from mangrove.transport.submissions import SubmissionHandler


class TestSMSPlayer(TestCase):

    def setUp(self):
        self.loc_tree = Mock()
        self.loc_tree.get_hierarchy_path.return_value = ['hierarchy']
        self.dbm = Mock(spec=DatabaseManager)
        self.submission_handler_mock = Mock(spec=SubmissionHandler)
        self.player = Player(self.dbm, self.submission_handler_mock, self.loc_tree)


    def test_should_not_resolve_location_hierarchy_if_hierarchy_already_passed_in(self):
        values = dict(l='a,b,c',t='clinic')
        self.player._get_location_data(values=values)
        self.assertEqual(['c', 'b', 'a'],values['l'])

    def test_should_resolve_location_hierarchy_if_hierarchy_not_passed_in(self):
        values = dict(l='no_hierarchy',t='clinic')
        self.player._get_location_data(values=values)
        self.assertEqual(['hierarchy'],values['l'])
