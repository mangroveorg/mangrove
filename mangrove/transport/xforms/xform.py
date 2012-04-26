from jinja2 import Environment, PackageLoader

def list_all_forms(form_tuples, xform_base_url):
    env = Environment(loader=PackageLoader('mangrove.transport.xforms', 'templates'),trim_blocks=True)
    template = env.get_template('form_list.xml')
    return template.render(form_tuples=form_tuples, xform_base_url=xform_base_url)

