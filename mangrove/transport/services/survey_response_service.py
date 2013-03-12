from transport.submissions import Submission

def create_survey_response(manager):
    pass


class SurveyResponseRequest(object):

    def __init__(self, id):
        self.id = id

    def id(self):
        return self.id

    def values(self):
        return self.values