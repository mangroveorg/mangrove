class Error(object):
    def __init__(self, field_name, error_code, value=None):
        self.field_name = field_name
        self.code = error_code
        self.value = value