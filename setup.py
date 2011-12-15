from setuptools import find_packages
from distutils.core import setup

setup(name='mangrove',
      version='1.0',
      description='The Mangrove package',
      author='ThoughtWorks',
      author_email='mangroveorg@googlegroups.com',
      url='https://github.com/mangroveorg/mangrove/',
      packages=find_packages(),
      requires=["nose (==1.0.0)", "CouchDB (==0.8)", "coverage (==3.4)", "simplejson", "mock", "iso8601", "pytz", "xlwt"])
