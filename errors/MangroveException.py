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
