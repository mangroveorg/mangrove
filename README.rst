Copyright and license
---------------------

Copyright 2014 ThoughtWorks

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Setting Up the development environment
======================================

* Create a folder "mangrove" which will have the following::

    $ CLONE mangrove, datawinners, shape files from github (https://github.com/mangroveorg/) into the folder which we have created
      All the three repositories should be at the same directory level in the folder we created.

* sudo apt-get install gdal-bin python-psycopg2 python-setuptools

* Setup virtual environment::

    $ (http://blog.devinterface.com/2010/08/how-to-create-multiple-django-environments-using-virtualenv/)

* Install pip

* DataBase Requirements::

	$ Intsall Postgres (For Linux - apt-get install postgresql-8.4)
	$ Intsall Postgis  (For Linux - apt-get install postgresql-8.4-postgis)
		NOTE: If unable to install (specially for Ubuntu 11.10 users) you can perform the following:
			$ sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
			$ update repository
			$ apt-get install postgresql-8.4-postgis
	$ Install CouchDb  (For Linux - apt-get install couchdb)

* Install python-dev if already not installed

* See if gcc is installed on the system::

   $ type dpkg -i gcc
   $ if not install gcc with the command sudo apt-get install gcc

* See if make is install on the system::

   $ type dpkg -i make
   $ if not, install make with the command sudo apt-get install make

* See if g++ is install on the system::

   $ type dpkg -i g++
   $ if not, install g++ with the command sudo apt-get install g++

* Install GEOS, PROJ.4 & GDAL::

   $ sudo apt-get install libgeos-c1 libpq-dev libxml2-dev libxslt1-dev

* https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#spatial-database

* From your user exceute following commands to create postgis template::

 	$ wget https://docs.djangoproject.com/en/dev/_downloads/create_template_postgis-debian.sh
   	$ chmod 755 create_template_postgis-debian.sh
   	$ run ./create_template_postgis-debian.sh

* Create geodjango db from the postgis template::

	$ createdb -T template_postgis geodjango

* In Mangrove module::

    $ pip install -r requirements.pip
    $ python setup.py develop

* In DataWinners module::

    $ pip install -r requirements.pip
    $ python manage.py syncdb migrate recreatedb
    $ python manage.py loadshapes
    $ django-admin.py compilemessages
    $ python manage.py runserver


