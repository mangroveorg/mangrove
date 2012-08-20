# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


def slugify(text, delim=u'_'):
    u"""'Generates an ASCII-only slug.''"""
    import re
    from unicodedata import normalize

    _punct_re = re.compile(r'[\t :;!"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))

def find_index_represented(response):
    assert len(response) <= 2
    index = ord(response[len(response) - 1]) - ord('a')
    if len(response) == 2:
        index = index + int(response[0])*26
    return index