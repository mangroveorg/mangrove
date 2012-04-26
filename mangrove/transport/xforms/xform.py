from jinja2 import Environment, PackageLoader
from mangrove.form_model.form_model import FormModel
from mangrove.transport.xforms.xml_dict_conversion import xml_to_dict

env = Environment(loader=PackageLoader('mangrove.transport.xforms', 'templates'),trim_blocks=True)

def list_all_forms(form_tuples, xform_base_url):
    template = env.get_template('form_list.xml')
    return template.render(form_tuples=form_tuples, xform_base_url=xform_base_url)

def xform_for(dbm, form_id) :
    questionnaire = FormModel.get(dbm, form_id)
    template = env.get_template('form.xml')
    return template.render(questionnaire=questionnaire)

def get_submission_data_from_xml_file(request):
    submission_data = request.FILES.get("xml_submission_file").read()
    submission_data_dict = xml_to_dict(submission_data)
    for key in submission_data_dict.keys() :
        submission_data_dict[key] = ",".join(submission_data_dict[key])
    return submission_data_dict


