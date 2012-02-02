Setting Up the development environment
======================================

* Create a folder "mangrove" which will have the following::

    $ CLONE mangrove, datawinners, shape files from github (https://github.com/mangroveorg/) into the folder which we have created
      All the three repositories should be at the same directory level in the folder we created.

* sudo apt-get install gdal-bin python-psycopg2 python-setuptools

* Setup virtual environment::

    $ (http://blog.devinterface.com/2010/08/how-to-create-multiple-django-environments-using-virtualenv/)

Install pip

* DataBase Requirements::

	$ Intsall Postgres (For Linux - apt-get install postgresql-8.4)
	$ Intsall Postgis  (For Linux - apt-get install postgresql-8.4-postgis)
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

   $ sudo apt-get install libgeos-c1 libpq-dev

* https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#spatial-database

* From your user exceute following commands to create postgis template::

 	$ wget https://docs.djangoproject.com/en/dev/_downloads/create_template_postgis-debian.sh
   	$ chmod 755 create_template_postgis-debian.sh
   	$ run ./create_template_postgis-debian.sh

* Create geodjango db from the postgis template::

	$ createdb -T template_postgis geodjango

* In Mangrove module (pip install -r requirements.pip)

* In DataWinners module (pip install -r requirements.pip)

* In Mangrove module (python setup.py develop)

* In DataWinners module (python manage.py syncdb migrate recreatedb)

* In DataWinners module (python manage.py loadshapes)

* In DataWinners module (django-admin.py compilemessages)




(For future purposes, ignore this currently) Setting Up the development environment using Chef
=================================================
In order to get your machine setup to start contributing to mangrove - this is what you need to do:

* Install chef client
* Clone the chef repository from mangrove
* Run chef solo

Details
-------

We are detailing out the above steps for Ubuntu 10.10. For any other OS - please look through the chef documentation given here_

* Install ruby::

    $ sudo apt-get install ruby-full

* Install rubygems::

    $ cd /tmp
    $ wget http://rubyforge.org/frs/download.php/70696/rubygems-1.3.7.tgz
    $ tar zxf rubygems-1.3.7.tgz
    $ cd rubygems-1.3.7
    $ sudo ruby setup.rb

    You can verify your installation was successful with

    $ gem -v
    1.3.7

* Install chef client::

    $ sudo gem install chef

    You can verify your installation was successful with

    $ chef-client -v
    Chef: 0.9.0

* Install git::

    $sudo apt-get install git

* Clone the chef repository::

    $git://github.com/mangroveorg/chef-repo.git

* Make sure your system is updated and upgraded before you run the chef script::

    $sudo apt-get update
    $sudo apt-get upgrade

* Create a user mangrover and give him sudo rights::

    $useradd mangrover
    $passwd mangrover
    $sudo usermod -aG sudo mangrover

* Run chef solo(as mangrover)::

    $cd chef-repo
    $sudo chef-solo -c chef-solo/solo.rb -j chef-solo/node.json


.. _here: http://help.opscode.com/kb/start/1-system-requirements-dependencies



