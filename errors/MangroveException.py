# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
#TODO: Please Read Readme.rst of errors beafore defining any new exception

class MangroveException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class EntityTypeAlreadyDefined(MangroveException):
    pass

class FormModelDoesNotExistsException(MangroveException):
    def __init__(self,questionnaire_code):
        MangroveException.__init__(self,"The questionnaire with code %s does not exists"%questionnaire_code)

class FieldDoesNotExistsException(MangroveException):
    def __init__(self,field_code):
        MangroveException.__init__(self,"The field with code %s does not exists"%field_code)

class EntityQuestionCodeNotSubmitted(MangroveException):
    def __init__(self):
        MangroveException.__init__(self,"The submission does not contain entity question code")

class EntityQuestionAlreadyExistsException(MangroveException):
    pass

class QuestionCodeAlreadyExistsException(MangroveException):
    pass

class NumberNotRegisteredException(MangroveException):
    pass