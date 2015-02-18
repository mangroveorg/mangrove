import os
from unittest import TestCase

from mock import Mock, patch

from mangrove.datastore.database import DatabaseManager
from mangrove.datastore.entity import Entity
from mangrove.form_model.field_builder import QuestionBuilder
from mangrove.form_model.project import Project


class TestXformFormModel(TestCase):
    def setUp(self):
        self.dbm = Mock(spec=DatabaseManager)

        questions = [
            {'uniqueIdType': u'clinic', 'code': u'my_unique', 'instruction': 'Answer must be a Identification Number',
             'name': u'mu_uni', 'parent_field_code': None, 'title': u'mu_uni', 'is_entity_question': True,
             'type': 'unique_id', 'required': False},
            {'code': u'my_group', 'instruction': 'No answer required', 'name': u'my_group', 'parent_field_code': None,
             'title': u'my_group', 'fields': [
                {'code': u'grouprepeat', 'instruction': 'No answer required', 'name': u'grouprepeat',
                 'parent_field_code': u'my_group', 'title': u'grouprepeat', 'fields': [
                    {'uniqueIdType': u'clinic', 'code': u'unique_in_grouprepeat',
                     'instruction': 'Answer must be a Identification Number', 'name': u'unique_in_grouprepeat',
                     'parent_field_code': u'grouprepeat', 'title': u'unique_in_grouprepeat', 'is_entity_question': True,
                     'type': 'unique_id', 'required': False}], 'is_entity_question': False, 'type': 'field_set',
                 'fieldset_type': 'repeat', 'required': False}], 'is_entity_question': False, 'type': 'field_set',
             'fieldset_type': 'group', 'required': False},
            {'code': u'repeat_out', 'instruction': 'No answer required', 'name': u'repeat_out',
             'parent_field_code': None, 'title': u'repeat_out', 'fields': [
                {'uniqueIdType': u'clinic', 'code': u'unique_in_repeat',
                 'instruction': 'Answer must be a Identification Number', 'name': u'unique_in_repeat',
                 'parent_field_code': u'repeat_out', 'title': u'unique_in_repeat', 'is_entity_question': True,
                 'type': 'unique_id', 'required': False}], 'is_entity_question': False, 'type': 'field_set',
             'fieldset_type': 'repeat', 'required': False},
            {'code': u'myrepeat', 'instruction': 'No answer required', 'name': u'myrepeat', 'parent_field_code': None,
             'title': u'myrepeat', 'fields': [
                {'code': u'repeat_group', 'instruction': 'No answer required', 'name': u'repeat_group',
                 'parent_field_code': u'myrepeat', 'title': u'repeat_group', 'fields': [
                    {'uniqueIdType': u'clinic', 'code': u'unique_in_repeatgroup',
                     'instruction': 'Answer must be a Identification Number', 'name': u'unique_in_repeatgroup',
                     'parent_field_code': u'repeat_group', 'title': u'unique_in_repeatgroup',
                     'is_entity_question': True, 'type': 'unique_id', 'required': False}], 'is_entity_question': False,
                 'type': 'field_set', 'fieldset_type': 'group', 'required': False}], 'is_entity_question': False,
             'type': 'field_set', 'fieldset_type': 'repeat', 'required': False},
            {'code': u'group_out', 'instruction': 'No answer required', 'name': u'group_out', 'parent_field_code': None,
             'title': u'group_out', 'fields': [{'uniqueIdType': u'clinic', 'code': u'unique_in_group',
                                                'instruction': 'Answer must be a Identification Number',
                                                'name': u'unique_in_group', 'parent_field_code': u'group_out',
                                                'title': u'unique_in_group', 'is_entity_question': True,
                                                'type': 'unique_id', 'required': False}], 'is_entity_question': False,
             'type': 'field_set', 'fieldset_type': 'group', 'required': False},
            {'code': u'parent_group', 'instruction': 'No answer required', 'name': u'parent_group',
             'parent_field_code': None, 'title': u'parent_group', 'fields': [
                {'code': u'groupgroup', 'instruction': 'No answer required', 'name': u'groupgroup',
                 'parent_field_code': u'parent_group', 'title': u'groupgroup', 'fields': [
                    {'uniqueIdType': u'clinic', 'code': u'unique_in_groupgroup',
                     'instruction': 'Answer must be a Identification Number', 'name': u'unique_in_groupgroup',
                     'parent_field_code': u'groupgroup', 'title': u'unique_in_groupgroup', 'is_entity_question': True,
                     'type': 'unique_id', 'required': False}], 'is_entity_question': False, 'type': 'field_set',
                 'fieldset_type': 'group', 'required': False}], 'is_entity_question': False, 'type': 'field_set',
             'fieldset_type': 'group', 'required': False}]

        fields = self._generate_fields_by_question_set(questions)
        self.dbm = Mock(spec=DatabaseManager)
        self.questionnaire = Project(self.dbm, name='xform_test',
                                     fields=fields, form_code='001',
                                     devices=[u'sms', u'web', u'smartPhone'])


    def test_xform_with_unique_ids_substituted(self):
        self.questionnaire.xform = open(
            os.path.join(os.path.dirname(__file__), "xform_with_unique_id_at_all_levels.xml"), 'r').read()
        entity1 = Entity(self.dbm, short_code="shortCode1", entity_type="clinic")
        entity1._doc.data['name'] = {'value': 'nameOfEntity1'}
        entity2 = Entity(self.dbm, short_code="shortCode2", entity_type="clinic")
        entity2._doc.data['name'] = {'value': 'nameOfEntity2'}
        entities = [entity1, entity2]
        with patch('mangrove.form_model.field.get_all_entities') as get_entities:
            get_entities.return_value = entities
            actual_xform = self.questionnaire.xform_with_unique_ids_substituted()
            expected_xform = open(os.path.join(os.path.dirname(__file__), "xform_with_choices_substituted.xml"), 'r').read()
            self.assertEqual(actual_xform, expected_xform)

    def _generate_fields_by_question_set(self, question_set):
        new_fields = []
        question_builder = QuestionBuilder()
        for question in question_set:
            question_code = question['code']
            field = question_builder.create_question(question, question_code)
            new_fields.append(field)
        return new_fields