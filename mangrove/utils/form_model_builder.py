from mangrove.datastore.entity_type import entity_type_already_defined, define_type
from mangrove.form_model.form_model import FormModel

class FormModelBuilder(object):
    def __init__(self, manager, entity_type, form_code='form_code', type="form_model_type"):
        self._manager = manager
        self._type = type
        self._form_code = form_code
        self._entity_type = entity_type
        self._label, self._name = 'form_model_label', 'form_model_name'
        self._fields = []
        self._is_reg = False

    def name(self, name):
        self._name = name
        return self

    def label(self, label):
        self._label = label
        return self

    def add_field(self, field):
        self._fields.append(field)
        return self

    def add_fields(self, *fields):
        self._fields.extend(fields)
        return self

    def is_registration_model(self, _is_reg):
        self._is_reg = _is_reg
        return self

    def build(self):
        if not entity_type_already_defined(self._manager, self._entity_type):
            define_type(self._manager, self._entity_type)

        self.form_model = FormModel(self._manager, name=self._name, label=self._label,
            form_code=self._form_code, type=self._type, fields=self._fields, is_registration_model=self._is_reg)
        form_model_id = self.form_model.save()
        return FormModel.get(self._manager, form_model_id)