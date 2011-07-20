# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

SHORT_CODE = "short_code"

def create_formatted_data(rows):
    final_data = []
    for key, value in rows:
        if value[SHORT_CODE] not in [f.get(SHORT_CODE) for f in final_data]:
            final_data.append({SHORT_CODE: value[SHORT_CODE]})
        data = [data for data in final_data if data[SHORT_CODE] == value[SHORT_CODE]][0]
        column_name = key[len(key) - 1:][0]
        data[column_name] = value.get("value")
    return final_data


def get_data_by_form_code(dbm, form_code):
    rows = _load_all_data_by_form_code_for(form_code=form_code, using_dbm=dbm)
    return create_formatted_data(rows)


def _load_all_data_by_form_code_for(form_code, using_dbm):
    view_name = "data_by_form"
    rows = using_dbm.load_all_rows_in_view(view_name, startkey=[form_code, ], endkey=[form_code, {}], group_level=3,
                                           desc=False)
    return [(row.key, row.value) for row in rows]