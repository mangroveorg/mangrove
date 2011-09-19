# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

def get_entity_count_for_type(dbm, entity_type):
    rows = dbm.view.by_short_codes(descending=True,
                                     startkey=[[entity_type], {}], endkey=[[entity_type]], group_level=1)
    return rows[0][u"value"] if len(rows) else 0
