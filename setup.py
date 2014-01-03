from setuptools import find_packages
from distutils.core import setup
REQUIREMENTS = [i.strip() for i in open("requirements.pip").readlines()]
setup(name='mangrove',
      version='1.0',
      description='The Mangrove package',
      author='ThoughtWorks',
      author_email='mangroveorg@googlegroups.com',
      url='https://github.com/mangroveorg/mangrove/',
      packages=find_packages(),
      package_data={'mangrove.transport.xforms.templates': ['./*.xml'], "mangrove.bootstrap.views":["*.js"]},
      install_requires=REQUIREMENTS)