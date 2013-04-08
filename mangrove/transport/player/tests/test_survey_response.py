from unittest import TestCase
from mock import Mock
from mangrove.transport.contract.survey_response import SurveyResponse, SurveyResponseDifference
from mangrove.transport.contract.transport_info import TransportInfo

class TestSurveyResponse(TestCase):
    def test_answer_differences_between_two_survey_response(self):
        new_survey_response = SurveyResponse(Mock(), values={'q1': 'ans1', 'q2': 'ans2', 'q3': 'ans3'},
            transport_info=TransportInfo('web', 'web', 'web'))
        new_survey_response._doc.status = True
        old_survey_response = SurveyResponse(Mock(), values={'q1': 'ans5', 'q2': 'ans6', 'q3': 'ans3'},
            transport_info=TransportInfo('web', 'web', 'web'))
        old_survey_response._doc.status = True
        result_diff = new_survey_response.differs_from(old_survey_response)
        expected_result_diff = SurveyResponseDifference(old_survey_response.created, False)
        expected_result_diff.changed_answers = {'q1': {'old': 'ans5', 'new': 'ans1'},
                                                'q2': {'old': 'ans6', 'new': 'ans2'}}
        self.assertEquals(expected_result_diff,result_diff)

    def test_status_differences_between_two_survey_response(self):
        old_survey_response = SurveyResponse(Mock(), values={'q1': 'ans5', 'q2': 'ans6', 'q3': 'ans3'},
            transport_info=TransportInfo('web', 'web', 'web'))
        new_survey_response = SurveyResponse(Mock(), values={'q1': 'ans1', 'q2': 'ans2', 'q3': 'ans3'},
            transport_info=TransportInfo('web', 'web', 'web'))
        new_survey_response._doc.status = True
        result_diff = new_survey_response.differs_from(old_survey_response)
        expected_result_diff = SurveyResponseDifference(old_survey_response.created, True)
        expected_result_diff.changed_answers = {'q1': {'old': 'ans5', 'new': 'ans1'},
                                                'q2': {'old': 'ans6', 'new': 'ans2'}}
        self.assertEqual(expected_result_diff,result_diff)

    def test_difference_between_two_survey_response_with_added_question_in_new_questionnaire(self):
        old_survey_response = SurveyResponse(Mock(), values={'q1': 'ans5', 'q2': 'ans6'},
            transport_info=TransportInfo('web', 'web', 'web'))
        new_survey_response = SurveyResponse(Mock(), values={'q1': 'ans1', 'q2': 'ans2', 'q3': 'ans3'},
            transport_info=TransportInfo('web', 'web', 'web'))
        new_survey_response._doc.status = True
        result_diff = new_survey_response.differs_from(old_survey_response)
        expected_result_diff = SurveyResponseDifference(old_survey_response.created, True)
        expected_result_diff.changed_answers = {'q1': {'old': 'ans5', 'new': 'ans1'},
                                                'q2': {'old': 'ans6', 'new': 'ans2'},
                                                'q3': {'old': '', 'new': 'ans3'}}
        self.assertEqual(expected_result_diff,result_diff)

    def test_difference_between_two_survey_response_with_with_deleted_question_in_new_questionnaire(self):
        old_survey_response = SurveyResponse(Mock(), values={'q1': 'ans5', 'q2': 'ans6','q3' : 'ans3'},
            transport_info=TransportInfo('web', 'web', 'web'))
        new_survey_response = SurveyResponse(Mock(), values={'q1': 'ans1', 'q2': 'ans2'},
            transport_info=TransportInfo('web', 'web', 'web'))
        new_survey_response._doc.status = True
        result_diff = new_survey_response.differs_from(old_survey_response)
        expected_result_diff = SurveyResponseDifference(old_survey_response.created, True)
        expected_result_diff.changed_answers = {'q1': {'old': 'ans5', 'new': 'ans1'},
                                                'q2': {'old': 'ans6', 'new': 'ans2'}}
        self.assertEqual(expected_result_diff,result_diff)

    def test_deep_copy(self):
        original = SurveyResponse(Mock(), values={'q1': 'ans5', 'q2': 'ans6', 'q3': 'ans3'},
            transport_info=TransportInfo('web', 'web', 'web'))
        duplicate = original.copy()
        original.values['q1'] = 2
        original.values['q2'] = 2
        original.values['q3'] = 2
        self.assertNotEqual(original.values['q1'], duplicate.values['q1'])
        self.assertNotEqual(original.values['q2'], duplicate.values['q2'])
        self.assertNotEqual(original.values['q3'], duplicate.values['q3'])