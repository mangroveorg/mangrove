import unittest
from mock import Mock, patch
from mangrove.datastore.entity import Entity
from mangrove.errors.MangroveException import DataObjectNotFound
from mangrove.transport.work_flow import _generate_short_code


class TestWorkFlow(unittest.TestCase):
    def test_should_create_entity_short_codes(self):
        with patch("mangrove.transport.work_flow.get_entity_count_for_type") as current_count:
            with patch("mangrove.transport.work_flow.get_by_short_code_include_voided") as if_short_code_exists:
                current_count.return_value = 1
                if_short_code_exists.side_effect = DataObjectNotFound('entity','short_code','som2')
                code = _generate_short_code(Mock, 'some_type')
                self.assertEquals(code, 'som2')


    def test_should_create_entity_short_code_from_entity_type_name_having_spaces_in_first_three_characters(self):
        with patch("mangrove.transport.work_flow.get_entity_count_for_type") as current_count:
            with patch("mangrove.transport.work_flow.get_by_short_code_include_voided") as if_short_code_exists:
                current_count.return_value = 1
                if_short_code_exists.side_effect = DataObjectNotFound('entity','short_code','som2')
                code = _generate_short_code(Mock, 'so m')
                self.assertEquals(code, 'som2')

    def test_should_not_duplicate_entity_short_codes(self):
        side_effect_values = [Mock(spec=Entity), DataObjectNotFound('entity','short_code','som3')]

        def side_effect(*args):
            result = side_effect_values.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with patch("mangrove.transport.work_flow.get_entity_count_for_type") as current_count:
            with patch("mangrove.transport.work_flow.get_by_short_code_include_voided") as if_short_code_exists:
                current_count.return_value = 1
                if_short_code_exists.side_effect = side_effect
                code = _generate_short_code(Mock, 'so m')
                self.assertEquals(code, 'som3')



