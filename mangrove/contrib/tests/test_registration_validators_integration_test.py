# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
import unittest
from pytz import UTC
from mangrove.datastore.entity import void_entity
from mangrove.datastore.datadict import DataDictType
from mangrove.contrib.registration import GLOBAL_REGISTRATION_FORM_CODE
from mangrove.utils.test_utils.database_utils import create_dbmanager_for_ut, delete_and_create_form_model, safe_define_type, ut_reporter_id, safe_delete_reporter_by_phone
from mangrove.datastore.entity import create_entity
from mangrove.form_model.form_model import REPORTER




class TestMobileNumberMandatoryValidationsForReporterRegistrationValidatorIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_dbmanager_for_ut(cls)
        safe_define_type(cls.manager, [REPORTER])
        cls.reg_form = delete_and_create_form_model(cls.manager, GLOBAL_REGISTRATION_FORM_CODE)
        cls.geo_code_type = DataDictType(cls.manager, name='GeoCode Type', slug='geo_code', primitive_type='geocode')

    def test_should_return_error_dict_if_mobile_number_field_missing(self):
        values = dict(t='reporter')
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertIn('m', errors)

    def test_should_allow_the_same_mobile_number_while_editing_a_reporter_details(self):
        reporter_id = ut_reporter_id()
        mobile_number = "99992"
        safe_delete_reporter_by_phone(self.manager, mobile_number)
        reporter1 = create_entity(self.manager, [REPORTER], reporter_id)
        reporter1.add_data(data=[("mobile_number", ("%s" % mobile_number), self.geo_code_type)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='reg'))
        values = dict(t='reporter', m=('%s' % mobile_number), s=reporter_id, l='test_location', g='1 1')
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertNotIn('m', errors)


    def test_should_return_error_dict_if_mobile_number_already_exists_for_a_different_reporter(self):
        reporter1 = create_entity(self.manager, [REPORTER], ut_reporter_id())
        reporter1.add_data(data=[("mobile_number", "123", self.geo_code_type)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='reg'))
        values = dict(t='reporter', m='123', s='rep_test2', l='test_location', g='1 1')
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertIn('m', errors)

    def test_should_not_return_error_dict_if_reporter_with_mobile_number_deleted(self):
        values = dict(t='reporter', m='99991', s='rep_test2', l='test_location', g='1 1', n='Test Reporter')
        id = ut_reporter_id()
        reporter1 = create_entity(self.manager, [REPORTER], id)
        reporter1.add_data(data=[("mobile_number", "99991", self.geo_code_type)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='reg'))
        void_entity(self.manager, [REPORTER], id)
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertNotIn('m', errors)

    def test_should_return_error_if_mobile_number_comes_in_epsilon_format_from_excel_file(self):
        reporter1 = create_entity(self.manager, [REPORTER], ut_reporter_id())
        reporter1.add_data(data=[("mobile_number", "266123321435", self.geo_code_type)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='reg'))
        values = dict(t='reporter', m='2.66123321435e+11', s='rep_test2', l='test_location', g='1 1', n='Test Reporter')
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertTrue('m' in errors)

    def test_should_return_error_if_mobile_number_has_hyphens_from_excel_file(self):
        reporter1 = create_entity(self.manager, [REPORTER], ut_reporter_id())
        reporter1.add_data(data=[("mobile_number", "266123321435", self.geo_code_type)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='reg'))
        values = dict(t='reporter', m='266-123321435', s='rep_test2', l='test_location', g='1 1', n='Test Reporter')
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertTrue('m' in errors)

    def test_should_return_error_if_mobile_number_comes_as_floating_point_number_from_excel_file(self):
        reporter1 = create_entity(self.manager, [REPORTER], ut_reporter_id())
        reporter1.add_data(data=[("mobile_number", "266123321435", self.geo_code_type)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='reg'))
        values = dict(t='reporter', m='266123321435.0', s='rep_test2', l='test_location', g='1 1', n='Test Reporter')
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertTrue('m' in errors)

if __name__ == '__main__':
    unittest.main()
