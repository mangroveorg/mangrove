# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime
from pytz import UTC
from mangrove.datastore.entity import void_entity
from mangrove.datastore.entity_type import define_type
from mangrove.datastore.datadict import get_or_create_data_dict, DataDictType
from mangrove.contrib.registration import create_default_reg_form_model
from mangrove.utils.test_utils.mangrove_test_case import MangroveTestCase
from mangrove.datastore.entity import create_entity
from mangrove.form_model.form_model import REPORTER

class TestMobileNumberMandatoryValidationsForReporterRegistrationValidatorIntegrationTest(MangroveTestCase):
    def setUp(self):
        MangroveTestCase.setUp(self)
        define_type(self.manager, [REPORTER])
        self.reg_form = create_default_reg_form_model(self.manager)
        self.geo_code_type = DataDictType(self.manager, name='GeoCode Type', slug='geo_code', primitive_type='geocode')

    def test_should_return_error_dict_if_mobile_number_field_missing(self):
        values = dict(t='reporter')
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertIn('m', errors)

    def test_should_return_error_dict_if_mobile_number_allready_exist(self):
        values = dict(t='reporter', m='123', s='rep_test1', l='test_location', g='1 1')
        reporter1 = create_entity(self.manager, [REPORTER], 'rep_test1')
        reporter1.add_data(data=[("mobile_number", "123", self.geo_code_type)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='reg'))
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertIn('m', errors)

    def test_should_not_return_error_dict_if_reporter_with_mobile_number_deleted(self):
        values = dict(t='reporter', m='123', s='rep_test2', l='test_location', g='1 1', n='Test Reporter')
        reporter1 = create_entity(self.manager, [REPORTER], 'rep_test1')
        reporter1.add_data(data=[("mobile_number", "123", self.geo_code_type)],
            event_time=datetime.datetime(2010, 02, 01, tzinfo=UTC),
            submission=dict(submission_id='1', form_code='reg'))
        void_entity(self.manager, [REPORTER], 'rep_test1')
        cleaned_data, errors = self.reg_form.validate_submission(values)
        self.assertNotIn('m', errors)
