Setting Up the POSTGIST and importing location data
======================================

In order to get postgis configured and import location data - this is what you need to do:

* Install Spatial Database PostgreSQL 8.4 (with PostGIS 1.5),
* Install Geospatial Libraries¶
* Create Spatial Database Template for PostGIS
* Create spatial database using the template
* Import the shape files in the spatial database


Details
-------

* Install Spatial Database PostgreSQL (with PostGIS) and Geospatial Libraries ::

    $ sudo apt-get install postgresql
    $ sudo apt-get install binutils gdal-bin postgresql-8.4-postgis \
     postgresql-server-dev-8.4 python-psycopg2 python-setuptools

    for details visit the url https://help.ubuntu.com/community/PostgreSQL

* Create Spatial Database Template for PostGIS::

    follow the instructions from the url: https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#spatialdb-template
    use Debian/Ubuntu 	create_template_postgis-debian.sh


* Create spatial database using the template::

    follow the instructions from the url: https://docs.djangoproject.com/en/dev/ref/contrib/gis/tutorial/#setting-up
    $ createdb -T template_postgis geodjango

* Import the shape files in the spatial database::

    Clone the git@github.com:mangroveorg/shape_files.git to a folder which is at the same level as the mangrove repository.
    E.g. /home/user/code/mangrove and /home/user/code/shape_files
    run python manage.py loadshapes

