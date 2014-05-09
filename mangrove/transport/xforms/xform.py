from coverage.html import escape
from jinja2 import Environment, PackageLoader
from mangrove.datastore.entity import get_all_entities
from mangrove.form_model.field import field_attributes, SelectField, UniqueIdField
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
    field_attributes.UNIQUE_ID_FIELD: env.get_template('unique_id_field.xml'),
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

class UniqueIdUIField(UniqueIdField):
    def __init__(self, field, dbm):
        super(UniqueIdUIField, self).__init__(unique_id_type=field.unique_id_type, name=field.name, code=field.code, label=field.label, instruction=field.instruction, constraints=field.constraints)
        self.dbm = dbm

    @property
    def options(self):
        return [(entity.short_code, entity.data['name']['value']) for entity in
                    get_all_entities(self.dbm, [self.unique_id_type])]

def xform_for(dbm, form_id, reporter_id):
    questionnaire = FormModel.get(dbm, form_id)
    _escape_special_characters(questionnaire)
    ui_fields = []
    for field in questionnaire.fields:
        if isinstance(field, UniqueIdField):
            ui_fields.append(UniqueIdUIField(field,dbm))
        else:
            ui_fields.append(field)
    template = env.get_template('reporter_entity_form.xml')
    return template.render(questionnaire=questionnaire, fields=ui_fields, field_xmls=field_xmls, reporter_id=reporter_id,
                           field_types=field_types, default_template=env.get_template('text_field.xml'))


def _escape_special_characters(questionnaire):
    questionnaire.name = escape(questionnaire.name)
    for question in questionnaire.fields:
        question.set_label(escape(question.label))
        question.set_instruction(escape(question.instruction))
        if type(question) == SelectField:
            for option in question.options:
                option['text'] = escape(option['text'])



