

import couchdb.json
from mangrove.utils.json_codecs import decode_json, encode_json

couchdb.json.use(encode=encode_json, decode=decode_json)
