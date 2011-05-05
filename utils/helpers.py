# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

def slugify(text, delim=u'_'):
    '''Generates an ASCII-only slug.'''
    import re
    from unicodedata import normalize

    _punct_re = re.compile(r'[\t :;!"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))
