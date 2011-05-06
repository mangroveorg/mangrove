# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import couchdb.json
from ..utils.json_codecs import decode_json, encode_json
couchdb.json.use(encode=encode_json, decode=decode_json)
