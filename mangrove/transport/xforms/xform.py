from jinja2 import Environment, PackageLoader
from mangrove.form_model.field import field_attributes
from mangrove.form_model.form_model import FormModel

env = Environment(loader=PackageLoader('mangrove.transport.xforms'),trim_blocks=True)
field_xmls = {field_attributes.TEXT_FIELD : env.get_template('text_field.xml')}

def list_all_forms(form_tuples, xform_base_url):
    template = env.get_template('form_list.xml')
    return template.render(form_tuples=form_tuples, xform_base_url=xform_base_url)

def xform_for(dbm, form_id) :
    questionnaire = FormModel.get(dbm, form_id)
    template = env.get_template('form.xml')
    return template.render(questionnaire=questionnaire, field_xmls=field_xmls)

