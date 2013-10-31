# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
class ValidatorTypes(object):
    MANDATORY = 'mandatory'
    #todo Error class is oly being used in datasender for as of now
    MANDATORY_FIELD_FOR_REPORTER = 'mandatory_field_for_reporter'
    MOBILE_NUMBER_MANDATORY_FOR_REPORTER = 'mobile_number_mandatory_for_reporter'
    EMAIL_FIELD_VALIDATOR_FOR_REPORTER = 'email_field_validator_for_reporter'
    At_Least_One_Location_Field_Must_Be_Answered = 'at_least_one_location_field_must_be_answered_validator'
    ENTITY_SHOULD_EXIST = 'entity_should_exist_validator'