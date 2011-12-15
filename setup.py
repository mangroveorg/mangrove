from distutils.core import setup

setup(name='mangrove',
      version='1.0',
      description='The Mangrove package',
      author='ThoughtWorks',
      author_email='mangroveorg@googlegroups.com',
      url='https://github.com/mangroveorg/mangrove/',
      packages=['mangrove', 'mangrove.datastore', 'mangrove.errors', 'mangrove.form_model', 'mangrove.georegistry', 'mangrove.transport', 'mangrove.utils'],
      requires=["nose", "CouchDB", "coverage", "simplejson", "mock", "iso8601", "pytz", "xlwt"])
