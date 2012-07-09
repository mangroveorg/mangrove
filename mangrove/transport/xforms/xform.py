from coverage.html import escape
from jinja2 import Environment, PackageLoader
from mangrove.datastore.entity import get_all_entities
from mangrove.form_model.field import field_attributes, SelectField
from mangrove.form_model.form_model import FormModel

env = Environment(loader=PackageLoader('mangrove.transport.xforms'), trim_blocks=True)
date_appearance = {
    'mm.yyyy': 'month-year',
    'yyyy': 'year'
}

field_xmls = {
    field_attributes.DATE_FIELD: env.get_template(name='date_field.xml', globals={'date_appearance': date_appearance}),
    field_attributes.SELECT_FIELD: env.get_template('select_field.xml'),
    field_attributes.MULTISELECT_FIELD: env.get_template('select_field.xml'),
    field_attributes.LOCATION_FIELD: env.get_template('geo_code_field.xml'),
    }

field_types = {
    field_attributes.LOCATION_FIELD: 'geopoint',
    field_attributes.TEXT_FIELD: 'string',
    field_attributes.INTEGER_FIELD: 'decimal',
    }

def list_all_forms(form_tuples, xform_base_url):
    template = env.get_template('form_list.xml')
    form_tuples = [(escape(form_name), form_id) for form_name, form_id in form_tuples]
    return template.render(form_tuples=form_tuples, xform_base_url=xform_base_url)


def xform_for(dbm, form_id, reporter_id):
    questionnaire = FormModel.get(dbm, form_id)
    _escape_special_characters(questionnaire)
    if questionnaire.entity_defaults_to_reporter():
        template = env.get_template('reporter_entity_form.xml')
        return template.render(questionnaire=questionnaire, field_xmls=field_xmls, field_types=field_types,
            reporter_id=reporter_id,
            default_template=env.get_template('text_field.xml'))
    else:
        template = env.get_template('entity_form.xml')
        entities = [(entity.short_code, entity.data['name']['value']) for entity in
                                                                      get_all_entities(dbm, questionnaire.entity_type)]
        return template.render(questionnaire=questionnaire, field_xmls=field_xmls, field_types=field_types,
            entities=entities, default_template=env.get_template('text_field.xml'),
            entity_field=questionnaire.entity_question)


def _escape_special_characters(questionnaire):
    questionnaire.name = escape(questionnaire.name)
    active_language = questionnaire.activeLanguages[0]
    for question in questionnaire.fields:
        question.set_name(escape(question.name))
        question.set_instruction(escape(question.instruction))
        if type(question) == SelectField:
            for option in question.options:
                option['text'][active_language] = escape(option['text'][active_language])



