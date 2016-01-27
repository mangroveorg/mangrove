from mangrove.datastore.database import DataObject
from mangrove.datastore.documents import UserQuestionnairePreferenceDocument
from mangrove.form_model.form_model import get_form_model_by_entity_type
import re
from collections import OrderedDict

'''
    Visibility rules are applied from top to bottom.
    First match takes precedence.
    Order of these rules are important
'''
VISIBILITY_RULES = OrderedDict()
VISIBILITY_RULES["datasender.mobile_number"] = False
VISIBILITY_RULES["datasender.email"] = False
VISIBILITY_RULES["datasender.location"] = False
VISIBILITY_RULES["datasender.geo_code"] = False
VISIBILITY_RULES[".*_details$"] = False
VISIBILITY_RULES["[\w-]*_details\.q2$"] = True
VISIBILITY_RULES["[\w-]*_details\.q6$"] = True
VISIBILITY_RULES["[\w-]*_details\.q6$"] = True
VISIBILITY_RULES[".*_details\..*"] = False
VISIBILITY_RULES["datasender$"] = False


def get_analysis_field_preferences(manager, user_id, project, display_messages):
    '''
    Provides hierrachial view of user preferences, questionnaire fields
    with sub questionnaires. It combines the preferences stored in db with display information.
    Useful for merging user specific preference data with questionnaire specific display info.
    '''
    preferences = []
    user_questionnaire_preference = get_user_questionnaire_preference(manager, user_id, project.id)
    preferences = [_convert_field_to_preference(manager, field, user_questionnaire_preference, project.id, parent_field_types=[]) for field in
                   project.fields]
    preferences.insert(0, {
        "data": "date",
        "title": display_messages('Submission Date'),
        "visibility": detect_visibility(user_questionnaire_preference, 'date')
    })
    preferences.insert(1, _get_datasender_preferences(user_questionnaire_preference, display_messages))
    return preferences


preference_dict = {'analysis': get_analysis_field_preferences}

def get_preferences(manager, user_id, project, submission_type, *args):
    get_preference_method = preference_dict.get(submission_type)
    if get_preference_method:
        return get_preference_method(manager, user_id, project, *args)
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


def _convert_field_to_preference(manager, field, preferences, project_id, key=None, is_group_child=False, parent_field_types=[]):
    if is_group_child:
        key = key+'-'+field.code
    elif key:
        key = key + '.' + field.code

    data = project_id + '_' + field.code if not key else key
    if field.type in ['unique_id']:
        data += '_details'
    
    analysis_field_preference = {
        "data": data,
        "title": field.label,
        "visibility": detect_visibility(preferences, data)
    }

    if field.type in ['unique_id']:
        if field.unique_id_type in parent_field_types:
            return None #Prevent cyclic Linked ID Nr
        parent_field_types.append(field.unique_id_type)
        id_number_fields = get_form_model_by_entity_type(manager, [field.unique_id_type]).fields
        analysis_field_preference["children"] = [_convert_field_to_preference(
            manager, child_field,
            preferences,
            project_id, data, parent_field_types=parent_field_types)
                                                 for child_field in id_number_fields]

    if field.is_group():
        analysis_field_preference["children"] = [_convert_field_to_preference(
            manager, child_field,
            preferences,
            project_id, data, is_group_child=True) for child_field in field.fields]

    if analysis_field_preference.get("children"):
        analysis_field_preference["children"] = [child for child in analysis_field_preference["children"] if child is not None]
    
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
    datasender_columns['datasender.id'] = display_messages('Data Sender Id')
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
