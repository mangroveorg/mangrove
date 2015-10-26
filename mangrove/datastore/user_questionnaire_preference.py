from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import UserQuestionnairePreferenceDocument
from mangrove.form_model.form_model import get_form_model_fields_by_entity_type
import re
from collections import OrderedDict

'''
    Visibility rules are applied from top to bottom.
    First match takes precedence.
'''
VISIBILITY_RULES = {
    "datasender.mobile_number": False,
    "datasender.email": False,
    "datasender.location": False,
    "datasender.geo_code":False,
    ".*_details\.q2": True,
    ".*_details\.q6": True,
    ".*_details\..*": False,
}


def get_analysis_field_preferences(manager, user_id, project, display_messages):
    '''
    Provides hierrachial view of user preferences, questionnaire fields
    with sub questionnaires. It combines the preferences stored in db with display information.
    Useful for merging user specific preference data with questionnaire specific display info.
    '''
    preferences = []
    user_questionnaire_preference = get_user_questionnaire_preference(manager, user_id, project.id)
    preferences = [_convert_field_to_preference(manager, field, user_questionnaire_preference, project.id) for field in
                   project.form_fields]
    preferences.insert(0, {
        "data": "date",
        "title": display_messages('Submission Date'),
        "visibility": detect_visibility(user_questionnaire_preference, 'date')
    })
    preferences.insert(1, _get_datasender_preferences(user_questionnaire_preference, display_messages))
    return preferences


preference_dict = {'analysis': get_analysis_field_preferences}

def get_preferences(manager, user_id, project, submission_type):
    get_preference_method = preference_dict.get(submission_type)
    if get_preference_method:
        return get_preference_method(manager, user_id, project)
    return None

def save_analysis_field_preferences(manager, user_id, project, preferences):
    user_questionnaire_preference = get_user_questionnaire_preference(manager, user_id, project.id)
    if user_questionnaire_preference is None:
        user_questionnaire_preference = UserQuestionnairePreference(manager, user_id, project.id)
    user_questionnaire_preference.analysis_fields = preferences
    user_questionnaire_preference.save()


def get_user_questionnaire_preference(manager, user_id, project_id):
    rows = manager.load_all_rows_in_view('user_questionnaire_preference', key=[user_id, project_id])
    user_questionnaire_preference = None
    if len(rows):
        user_questionnaire_preference = UserQuestionnairePreference.new_from_doc(manager,
                                                                                 UserQuestionnairePreferenceDocument.wrap(
                                                                                     rows[0]['value']))
    return user_questionnaire_preference


def _convert_field_to_preference(manager, field, preferences, project_id, key=None):
    data = project_id + '_' + field.get('code') if not key else key + '.' + field.get('code')
    analysis_field_preference = {
        "data": data,
        "title": field.get('label'),
        "visibility": detect_visibility(preferences, data)
    }

    if field.get('type') in ['unique_id']:
        key = data + "_details"
        id_number_fields = get_form_model_fields_by_entity_type(manager, [field.get('unique_id_type')])
        analysis_field_preference["children"] = [_convert_field_to_preference(
            manager, child_field,
            preferences,
            project_id, key)
                                                 for child_field in id_number_fields]

    return analysis_field_preference


def detect_visibility(preferences, data):
    if preferences is None:
        for key in VISIBILITY_RULES:
            if re.match(key, data):
                return VISIBILITY_RULES.get(key)
        return True

    visibility = preferences.analysis_fields.get(data, False)
    visibility_flag = visibility[0] if isinstance(visibility, list) else visibility
    return visibility_flag


def _get_datasender_preferences(preferences, display_messages):
    data = "datasender"
    analysis_field_preference = {
        "data": data,
        "title": display_messages("Data Sender"),
        "visibility": detect_visibility(preferences, data)
    }
    children = []
    datasender_columns = OrderedDict()
    datasender_columns['datasender.name'] = display_messages('Data Sender Name')
    datasender_columns['datasender.id'] = display_messages('Data Sender ID Number')
    datasender_columns['datasender.mobile_number'] = display_messages('Data Sender Mobile Number')
    datasender_columns['datasender.email'] = display_messages('Data Sender Email')
    datasender_columns['datasender.location'] = display_messages('Data Sender Location')
    datasender_columns['datasender.geo_code'] = display_messages('Data Sender GPS Coordinates')

    for column_id, column_title in datasender_columns.iteritems():
        children.append({
            "data": column_id,
            "title": column_title,
            "visibility": detect_visibility(preferences, column_id)
        })
    analysis_field_preference["children"] = children
    return analysis_field_preference


class UserQuestionnairePreference(DataObject):
    __document_class__ = UserQuestionnairePreferenceDocument

    def __init__(self, dbm, user_id=None, project_id=None, **kwargs):
        super(UserQuestionnairePreference, self).__init__(dbm)
        doc = UserQuestionnairePreferenceDocument()
        doc.user_id = user_id
        doc.project_id = project_id
        DataObject._set_document(self, doc)

    @property
    def analysis_fields(self):
        return self._doc.analysis_fields

    @analysis_fields.setter
    def analysis_fields(self, value):
        self._doc.analysis_fields = value

    def show_fields(self, fields):
        self._change_visibility(fields, True)

    def hide_fields(self, fields):
        self._change_visibility(fields, False)

    def _change_visibility(self, fields, visibility, preference='analysis_fields'):
        if not isinstance(fields, list):
            fields = [fields]
        for field in getattr(self, preference):
            if field.get('id') in fields:
                field['visibility'] = visibility
