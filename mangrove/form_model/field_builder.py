from mangrove.form_model.field import IntegerField, TextField, DateField, SelectField, GeoCodeField, \
    TelephoneNumberField, HierarchyField, UniqueIdField, ShortCodeField, FieldSet, PhotoField, VideoField, AudioField, \
    TimeField, DateTimeField
from mangrove.form_model.form_model import LOCATION_TYPE_FIELD_NAME
from mangrove.form_model.validation import NumericRangeConstraint, TextLengthConstraint, RegexConstraint
from mangrove.utils.types import is_empty


class QuestionBuilder(object):
    type_media_dict = {'photo': PhotoField, 'video': VideoField, 'audio': AudioField}

    def create_question(self, post_dict, code):
        if post_dict["type"] == "text":
            return self._create_text_question(post_dict, code)
        if post_dict["type"] == "time":
            return self._create_time_question(post_dict, code)
        if post_dict["type"] == "datetime":
            return self._create_date_time_question(post_dict, code)
        if post_dict["type"] == "integer":
            return self._create_integer_question(post_dict, code)
        if post_dict["type"] == "geocode":
            return self._create_geo_code_question(post_dict, code)
        if post_dict["type"] == "select":
            return self._create_select_question(post_dict, False, code)
        if post_dict["type"] == "date":
            return self._create_date_question(post_dict, code)
        if post_dict["type"] == "select1":
            return self._create_select_question(post_dict, True, code)
        if post_dict["type"] == "telephone_number":
            return self._create_telephone_number_question(post_dict, code)
        if post_dict["type"] == "list":
            return self._create_location_question(post_dict, code)
        if post_dict["type"] == "unique_id":
            return self._create_unique_id_question(post_dict, code)
        if post_dict["type"] == "short_code":
            return self._create_short_code_field(post_dict, code)
        if post_dict["type"] == "field_set":
            return self._create_field_set_question(post_dict, code)
        if post_dict["type"] == "photo" or post_dict["type"] == "video" or post_dict["type"] == "audio":
            return self._create_media_question(post_dict, code)

    def _create_field_set_question(self, post_dict, code):

        fields = post_dict.get("fields")
        sub_form_fields = [self.create_question(f, f['code']) for i, f in enumerate(fields)]
        return FieldSet(name=self._get_name(post_dict), code=code, label=post_dict["title"],
                        instruction=post_dict.get("instruction"), required=post_dict.get("required"),
                        field_set=sub_form_fields,
                        fieldset_type=post_dict.get("fieldset_type"),
                        parent_field_code=post_dict.get('parent_field_code'),
                        hint=post_dict.get('hint'),
                        constraint_message=post_dict.get('constraint_message'),
                        appearance=post_dict.get('appearance'),
                        default=post_dict.get('default'))


    def _get_name(self, post_dict):
        name = post_dict.get("name")
        return name if name else post_dict["title"]

    def _add_text_length_constraint(self, post_dict):
        max_length_from_post = post_dict.get("max_length")
        min_length_from_post = post_dict.get("min_length")
        max_length = max_length_from_post if not is_empty(max_length_from_post) else None
        min_length = min_length_from_post if not is_empty(min_length_from_post) else None
        constraints = []
        if not (max_length is None and min_length is None):
            constraints.append(TextLengthConstraint(min=min_length, max=max_length))
        return constraints

    def _create_text_question(self, post_dict, code):
        constraints = self._add_text_length_constraint(post_dict)
        return TextField(name=self._get_name(post_dict),
                         code=code,
                         label=post_dict["title"],
                         constraints=constraints,
                         instruction=post_dict.get("instruction"),
                         required=post_dict.get("required"),
                         parent_field_code=post_dict.get('parent_field_code'),
                         is_calculated=post_dict.get('is_calculated'),
                         hint=post_dict.get('hint'),
                         constraint_message=post_dict.get('constraint_message'),
                         appearance=post_dict.get('appearance'),
                         default=post_dict.get('default'))

    def _create_time_question(self, post_dict, code):
        return TimeField(name=self._get_name(post_dict),
                         code=code,
                         label=post_dict["title"],
                         instruction=post_dict.get("instruction"),
                         required=post_dict.get("required"),
                         parent_field_code=post_dict.get('parent_field_code'),
                         hint=post_dict.get('hint'),
                        constraint_message=post_dict.get('constraint_message'),
                        appearance=post_dict.get('appearance'),
                         default=post_dict.get('default'))

    def _create_date_time_question(self, post_dict, code):
        return DateTimeField(name=self._get_name(post_dict),
                             code=code,
                             label=post_dict["title"],
                             instruction=post_dict.get("instruction"),
                             required=post_dict.get("required"),
                             parent_field_code=post_dict.get('parent_field_code'),
                             hint=post_dict.get('hint'),
                             constraint_message=post_dict.get('constraint_message'),
                             appearance=post_dict.get('appearance'),
                             default=post_dict.get('default'))

    def _create_integer_question(self, post_dict, code):
        max_range_from_post = post_dict.get("range_max")
        min_range_from_post = post_dict.get("range_min")
        max_range = max_range_from_post if not is_empty(max_range_from_post) else None
        min_range = min_range_from_post if not is_empty(min_range_from_post) else None
        range = NumericRangeConstraint(min=min_range, max=max_range)
        return IntegerField(name=self._get_name(post_dict), code=code, label=post_dict["title"],
                            constraints=[range], instruction=post_dict.get("instruction"),
                            required=post_dict.get("required"), parent_field_code=post_dict.get('parent_field_code'),
                            hint=post_dict.get('hint'), constraint_message=post_dict.get('constraint_message'),
                            appearance=post_dict.get('appearance'),
                            default=post_dict.get('default'))


    def _create_date_question(self, post_dict, code):
        return DateField(name=self._get_name(post_dict), code=code, label=post_dict["title"],
                         date_format=post_dict.get('date_format'),
                         instruction=post_dict.get("instruction"),
                         required=post_dict.get("required"), parent_field_code=post_dict.get('parent_field_code'),
                         hint=post_dict.get('hint'), constraint_message=post_dict.get('constraint_message'),
                         appearance=post_dict.get('appearance'),
                         default=post_dict.get('default'))


    def _create_geo_code_question(self, post_dict, code):
        return GeoCodeField(name=self._get_name(post_dict), code=code, label=post_dict["title"],
                            instruction=post_dict.get("instruction"), required=post_dict.get("required"),
                            parent_field_code=post_dict.get('parent_field_code'),
                            hint=post_dict.get('hint'), constraint_message=post_dict.get('constraint_message'),
                            appearance=post_dict.get('appearance'),
                            default=post_dict.get('default'))


    def _create_select_question(self, post_dict, single_select_flag, code):
        options = [(choice['value'].get("text"), choice['value'].get("val").lower()) for choice in post_dict["choices"]]
        return SelectField(name=self._get_name(post_dict), code=code, label=post_dict["title"],
                           options=options, single_select_flag=single_select_flag,
                           instruction=post_dict.get("instruction"), required=post_dict.get("required"),
                           parent_field_code=post_dict.get('parent_field_code'), has_other=post_dict.get('has_other'),
                           hint=post_dict.get('hint'), constraint_message=post_dict.get('constraint_message'),
                           appearance=post_dict.get('appearance'),
                           default=post_dict.get('default'))


    def _create_telephone_number_question(self, post_dict, code):
        return TelephoneNumberField(name=self._get_name(post_dict), code=code,
                                    label=post_dict["title"],
                                    instruction=post_dict.get("instruction"), constraints=(
                self._create_constraints_for_mobile_number()), required=post_dict.get("required"),
                                    parent_field_code=post_dict.get('parent_field_code'),
                                    hint=post_dict.get('hint'), constraint_message=post_dict.get('constraint_message'),
                                    appearance=post_dict.get('appearance'),
                                    default=post_dict.get('default'))

    def _create_constraints_for_mobile_number(s_create_short_code_fieldelf):
        mobile_number_length = TextLengthConstraint(max=15)
        mobile_number_pattern = RegexConstraint(reg='^[0-9]+$')
        mobile_constraints = [mobile_number_length, mobile_number_pattern]
        return mobile_constraints

    def _create_location_question(self, post_dict, code):
        return HierarchyField(name=LOCATION_TYPE_FIELD_NAME, code=code,
                              label=post_dict["title"], instruction=post_dict.get("instruction"),
                              parent_field_code=post_dict.get('parent_field_code'),
                              hint=post_dict.get('hint'),
                              constraint_message=post_dict.get('constraint_message'),
                              appearance=post_dict.get('appearance'),
                              default=post_dict.get('default'))

    def _create_media_question(self, post_dict, code):
        media_class = self.type_media_dict[post_dict['type']]
        return media_class(name=self._get_name(post_dict), code=code,
                           label=post_dict["title"], instruction=post_dict.get("instruction"),
                           required=post_dict.get("required"), parent_field_code=post_dict.get('parent_field_code'),
                           hint=post_dict.get('hint'),
                           constraint_message=post_dict.get('constraint_message'),
                           appearance=post_dict.get('appearance'),
                           default=post_dict.get('default'))


    def _get_unique_id_type(self, post_dict):
        return post_dict["uniqueIdType"].strip().lower()

    def _create_unique_id_question(self, post_dict, code):
        return UniqueIdField(unique_id_type=self._get_unique_id_type(post_dict), name=self._get_name(post_dict),
                             code=code,
                             label=post_dict["title"],
                             instruction=post_dict.get("instruction"),
                             parent_field_code=post_dict.get('parent_field_code'),
                             hint=post_dict.get('hint'), constraint_message=post_dict.get('constraint_message'),
                             appearance=post_dict.get('appearance'),
                             default=post_dict.get('default'))

    def _create_short_code_field(self, post_dict, code):
        return ShortCodeField(name=self._get_name(post_dict), code=code,
                              label=post_dict["title"],
                              instruction=post_dict.get("instruction"),
                              parent_field_code=post_dict.get('parent_field_code'),
                              hint=post_dict.get('hint'), constraint_message=post_dict.get('constraint_message'),
                              appearance=post_dict.get('appearance'),
                              default=post_dict.get('default'))
