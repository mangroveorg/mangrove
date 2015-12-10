
#TODO: Please Read Readme.rst of errors before defining any new exception


class MangroveException(Exception):
    def __init__(self, message, data=None):
        assert data is None or type(data) is tuple
        self.message = message
        self.data = data

    def __str__(self):
        return self.message


class DataObjectAlreadyExists(MangroveException):
    def __init__(self, dataobject_name, param, value, existing_name=''):
        error_message = u"%s with %s = %s already exists." % (dataobject_name, param, value)
        MangroveException.__init__(self, error_message, (param, value, dataobject_name, existing_name))

class EmptyRowException(MangroveException):
    def __init__(self):
        error_message = u"The row is empty"
        MangroveException.__init__(self, message=error_message)


class DataObjectNotFound(MangroveException):
    def __init__(self, dataobject_name, param, value):
        error_message = u"%s with %s = %s not found." % (dataobject_name, param, value)
        MangroveException.__init__(self, error_message, (dataobject_name, param, value))


class EntityTypeAlreadyDefined(MangroveException):
    pass


class FormModelDoesNotExistsException(MangroveException):
    def __init__(self, questionnaire_code):
        error_message = u"The questionnaire with code %s does not exist." % questionnaire_code if questionnaire_code else "The questionnaire does not exist."
        MangroveException.__init__(self, error_message, (questionnaire_code, ))


class ProjectPollCodeDoesNotExistsException(MangroveException):
    def __init__(self, questionnaire_code):
        error_message = u"The questionnaire with code %s does not exist." % questionnaire_code if questionnaire_code else "The questionnaire does not exist."
        MangroveException.__init__(self, error_message, (questionnaire_code, ))


class FieldDoesNotExistsException(MangroveException):
    def __init__(self, field_code):
        MangroveException.__init__(self, u"The field with code %s does not exist." % field_code, (field_code, ))


class EntityQuestionCodeNotSubmitted(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, u"The submission does not contain entity question code.")


class EntityTypeCodeNotSubmitted(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, u"The submission does not contain entity type code.")


class EntityQuestionAlreadyExistsException(MangroveException):
    pass


class QuestionAlreadyExistsException(MangroveException):
    pass


class QuestionnaireAlreadyExistsException(MangroveException):
    pass


class QuestionCodeAlreadyExistsException(MangroveException):
    pass


class NoQuestionsSubmittedException(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, u"The submission contains no valid questions.")


class NumberNotRegisteredException(MangroveException):
    def __init__(self, from_number):
        MangroveException.__init__(self, (u"Sorry, this number %s is not registered with us.") % (from_number,),
            (from_number,))


class MultipleReportersForANumberException(MangroveException):
    def __init__(self, from_number):
        MangroveException.__init__(self,
                                   (u"Sorry, the telephone number %s has already been registered.") % (from_number,),
            (from_number,))


class MultipleSubmissionsForSameCodeException(MangroveException):
    def __init__(self, field_code):
        MangroveException.__init__(self, (u"Multiple responses for question code %s") % (field_code, ), (field_code,))

class MobileNumberMandatoryException(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, "Answer for question 'Mobile Number' is required")



class EntityTypeDoesNotExistsException(MangroveException):
    def __init__(self, entity_type):
        entity_type_full_name = ".".join(entity_type)
        entity_type_short_name = entity_type[-1]
        MangroveException.__init__(self,
                                   (u"Entity type %s doesnt exist.") % (entity_type_full_name,),
            (entity_type_short_name,))


class InvalidAnswerSubmissionException(MangroveException):
    def __init__(self, message, code, data=None):
        final_data = [code]
        if data is not None:
            data = [a for a in data]
            final_data.extend(data)
        data = tuple(final_data)
        MangroveException.__init__(self, message, data)


class AnswerTooBigException(InvalidAnswerSubmissionException):
    def __init__(self, code, answer):
        InvalidAnswerSubmissionException.__init__(self,
                                                  (u"Answer %s for question %s is greater than allowed.") % (
                                                      answer, code,), code, (answer,))


class AnswerTooSmallException(InvalidAnswerSubmissionException):
    def __init__(self, code, answer):
        InvalidAnswerSubmissionException.__init__(self,
                                                  (u"Answer %s for question %s is smaller than allowed.") % (
                                                      answer, code), code, (answer,))


class AnswerTooLongException(InvalidAnswerSubmissionException):
    def __init__(self, code, answer, max_length):
        InvalidAnswerSubmissionException.__init__(self,
                                                  (u"Answer %s for question %s is longer than allowed.") % (
                                                      answer, code), code, (answer,))


class AnswerTooShortException(InvalidAnswerSubmissionException):
    def __init__(self, code, answer, min_length):
        InvalidAnswerSubmissionException.__init__(self,
                                                  (u"Answer %s for question %s is shorter than allowed.") % (
                                                      answer, code), code, (answer,))


class AnswerHasTooManyValuesException(InvalidAnswerSubmissionException):
    def __init__(self, code, answer):
        InvalidAnswerSubmissionException.__init__(self,
                                                  (u"Answer %s for question %s contains more than one value.") % (
                                                      answer, code,), code, (answer,))


class AnswerHasNoValuesException(InvalidAnswerSubmissionException):
    def __init__(self, code, answer):
        InvalidAnswerSubmissionException.__init__(self,
                                                  (u"Answer %s for question %s has no value.") % (
                                                      answer, code,), code, (answer,))


class AnswerNotInListException(InvalidAnswerSubmissionException):
    def __init__(self, code, answer):
        InvalidAnswerSubmissionException.__init__(self,
                                                  (
                                                      u"Answer %s for question %s is not present in the allowed options.") % (
                                                      answer, code,), code, (answer,))


class AnswerWrongType(InvalidAnswerSubmissionException):
    def __init__(self, code, answer):
        InvalidAnswerSubmissionException.__init__(self,
                                                  (u"Answer %s for question %s is of the wrong type.") % (answer, code,)
                                                  , code, (answer,))


class IncorrectDate(InvalidAnswerSubmissionException):
    def __init__(self, code, answer, date_format):
        InvalidAnswerSubmissionException.__init__(self,
                                                  (
                                                      u'Answer %s for question %s is invalid. Expected date in %s format') %
                                                  (answer, code, date_format), code, (answer, date_format))


class NoDocumentError(MangroveException):
    pass


class UnknownOrganization(MangroveException):
    def __init__(self, tel_number):
        MangroveException.__init__(self, (u'No organization found for telephone number %s') %
                                         (tel_number,), (tel_number,))


class ShortCodeAlreadyInUseException(MangroveException):
    def __init__(self, short_code):
        MangroveException.__init__(self, (u'The ID %s is already in use. Please specify another') %
                                         (short_code,), (short_code,))


class ShortCodeTooLongException(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, u"The short code is longer than 12 characters")


class LatitudeNotFloat(MangroveException):
    def __init__(self, lat):
        MangroveException.__init__(self, (u'Answer must be in the following format: xx.xxxx yy.yyyy Example: -18.1324 27.6547'), data=(lat,))


class LongitudeNotFloat(MangroveException):
    def __init__(self, long):
        MangroveException.__init__(self, (u'Answer must be in the following format: xx.xxxx yy.yyyy Example: -18.1324 27.6547'), data=(long,))


class LongitudeNotInRange(MangroveException):
    def __init__(self, long):
        MangroveException.__init__(self, (u'Invalid GPS value.'), data=(long,))


class LatitudeNotInRange(MangroveException):
    def __init__(self, lat):
        MangroveException.__init__(self, (u'Invalid GPS value.'), (lat,))


class GeoCodeFormatException(MangroveException):
    def __init__(self, data):
        MangroveException.__init__(self,
                                   u"Incorrect GPS format. The GPS coordinates must be in the following format: xx.xxxx,yy.yyyy. Example -18.8665,47.5315"
                                   , (data,))


class FailedToSaveDataObject(MangroveException):
    def __init__(self, data):
        MangroveException.__init__(self, u"Root Exception: %s" % data)


class SMSParserInvalidFormatException(MangroveException):
    def __init__(self, data):
        MangroveException.__init__(self, u"Could not parse, invalid format: %s" % data, (data,))
        
class SMSParserWrongNumberOfAnswersException(MangroveException):
    def __init__(self, form_code):
        MangroveException.__init__(self, u"Could not parse, Wrong number of answers submitted.", (form_code, ))

class CSVParserInvalidHeaderFormatException(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, u"Could not parse header, invalid format.")


class XlsParserInvalidHeaderFormatException(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, u"Could not parse header, invalid format.")


class AggregationNotSupportedForTypeException(MangroveException):
    def __init__(self, field, aggregation):
        error_message = "%s for %s is not supported" % (aggregation, field)
        MangroveException.__init__(self, error_message, (aggregation, field))


class SubmissionParseException(MangroveException):
    def __init__(self, form_code, message):
        MangroveException.__init__(self, message, (form_code,))


class MobileNumberMissing(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, "Mobile number is missing", ('reg',))


class RegexMismatchException(MangroveException):
    def __init__(self, pattern):
        MangroveException.__init__(self, "Invalid Mobile Number.")

class ShortCodeRegexMismatchException(MangroveException):
    def __init__(self, pattern):
        MangroveException.__init__(self, "Invalid Short Code. Only letters and numbers are valid.")

class ConstraintTypeUnknownException(MangroveException):
    def __init__(self, name):
        MangroveException.__init__(self, "Unknown constraint type: %s" % (name,))

class RequiredFieldNotPresentException(MangroveException):
    def __init__(self, code):
        MangroveException.__init__(self, "Mandatory Field with code: %s is not present" % (code,))

class LocationFieldNotPresentException(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, "Please fill out atleast one location field")

class AccountExpiredException(MangroveException):
    def __init__(self, message = "Trial account has been expired!"):
        MangroveException.__init__(self, message)

class DeleteRequestParserInvalidFormatException(MangroveException):
    def __init__(self, data):
        MangroveException.__init__(self, u"Could not parse, invalid format: %s" % data, (data,))

class DeleteRequestParserWrongNumberOfAnswersException(MangroveException):
    def __init__(self, message):
        MangroveException.__init__(self, u"Could not parse, Wrong number of answers submitted.", (message, ))

        
class ExceedSubmissionLimitException(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, u"You have reached your limit of 1000 free Submissions. Upgrade to a monthly subscription to continue sending in Submissions.")


class ExceedSMSLimitException(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, u"You have reached your 50 SMS Submission limit. Please upgrade to a monthly subscription to continue sending in SMS Submissions to your Questionnaires.")

class DatasenderIsNotLinkedException(MangroveException):
    def __init__(self, dsname, dsid):
        MangroveException.__init__(self, u"Error. You are not authorized to submit data for this Questionnaire. Please contact your supervisor.", (dsname, dsid))

class CodeSheetMissingException(Exception):
    def __str__(self):
        return self.message