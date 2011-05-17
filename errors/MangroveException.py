# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
#TODO: Please Read Readme.rst of errors before defining any new exception


class MangroveException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class DataObjectAlreadyExists(MangroveException):
    def __init__(self, dataobject_name, param, value):
        error_message = "%s with %s = %s already exists." % (dataobject_name, param, value)
        MangroveException.__init__(self, error_message)


class DataObjectNotFound(MangroveException):
    def __init__(self, dataobject_name, param, value):
        error_message = "%s with %s = %s not found." % (dataobject_name, param, value)
        MangroveException.__init__(self, error_message)


class EntityTypeAlreadyDefined(MangroveException):
    pass


class FormModelDoesNotExistsException(MangroveException):
    def __init__(self, questionnaire_code):
        error_message = "The questionnaire with code %s does not exist." % questionnaire_code if questionnaire_code else "The questionnaire does not exist."
        MangroveException.__init__(self, error_message)


class FieldDoesNotExistsException(MangroveException):
    def __init__(self, field_code):
        MangroveException.__init__(self, "The field with code %s does not exist." % field_code)


class EntityQuestionCodeNotSubmitted(MangroveException):
    def __init__(self):
        MangroveException.__init__(self, "The submission does not contain entity question code.")


class EntityQuestionAlreadyExistsException(MangroveException):
    pass


class QuestionCodeAlreadyExistsException(MangroveException):
    pass


class NumberNotRegisteredException(MangroveException):
    def __init__(self, from_number):
        MangroveException.__init__(self, ("Sorry, this number %s is not registered with us.") % (from_number,))


class MultipleReportersForANumberException(MangroveException):
    def __init__(self, from_number):
        MangroveException.__init__(self, ("Sorry, more than one reporter found for %s.") % (from_number,))


class EntityInstanceDoesNotExistsException(MangroveException):
    pass


class AnswerTooBigException(MangroveException):
    def __init__(self, question_code, answer):
        MangroveException.__init__(self,
                                   ("Answer %s for question %s is greater than allowed.") % (answer, question_code,))


class AnswerTooSmallException(MangroveException):
    def __init__(self, question_code, answer):
        MangroveException.__init__(self,
                                   ("Answer %s for question %s is smaller than allowed.") % (answer, question_code,))


class AnswerTooLongException(MangroveException):
    def __init__(self, question_code, answer):
        MangroveException.__init__(self,
                                   ("Answer %s for question %s is longer than allowed.") % (answer, question_code,))


class AnswerTooShortException(MangroveException):
    def __init__(self, question_code, answer):
        MangroveException.__init__(self,
                                   ("Answer %s for question %s is shorter than allowed.") % (answer, question_code,))


class AnswerHasTooManyValuesException(MangroveException):
    def __init__(self, question_code, answer):
        MangroveException.__init__(self,
                                   ("Answer %s for question %s contains more than one value.") % (
                                   answer, question_code,))


class AnswerHasNoValuesException(MangroveException):
    def __init__(self, question_code, answer):
        MangroveException.__init__(self,
                                   ("Answer %s for question %s contains more than one value.") % (
                                   answer, question_code,))


class AnswerNotInListException(MangroveException):
    def __init__(self, question_code, answer):
        MangroveException.__init__(self,
                                   ("Answer %s for question %s is not present in the allowed options.") % (
                                   answer, question_code,))


class AnswerWrongType(MangroveException):
    def __init__(self, question_code):
        MangroveException.__init__(self, ("Answer to question %s is of wrong type.") % (question_code,))


class IncorrectDate(MangroveException):
    def __init__(self, question_code, answer, date_format):
        MangroveException.__init__(self, ('Answer to question %s is invalid: %s, expected date in %s format') %
                                         (question_code, answer, date_format))


class NoDocumentError(MangroveException):
    pass
