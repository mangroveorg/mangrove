------------------------------------
Setting up the 'DataWinners' Web App
------------------------------------


* Pre-requisites:

	1. Install python 2.7
		``apt-get install python2.7``
	2. Install couchdb
		``apt-get install couchdb``
	3. Install python2.7-dev
		``apt-get install python2.7-dev``
	4. Install subversion (SVN)
		``apt-get install subversion``
	5. Install virtualenv
		``apt-get install virtualenv``
	6. Install python-setuptools
		``apt-get install python-setuptools``


* Environment Setup:

	1. Create virtual environment 
		``virtualenv --no-site-packages --python=python2.7 <foldername>``
	2. Go inside folder <foldername>
		``cd <foldername>``
	3. Clone git repository
		``git clone https://github.com/mangroveorg/mangrove.git``
	4. Go to mangrove folder
		``cd mangrove``
	5. Switch to develop branch
		``git checkout develop``
	6. Check the status
		``git status``
	7. Go out of folder <foldername>
		``cd ../..``
	8. Run requirement.pip file
		``pip install -E <foldername> -r <foldername>/mangrove/requirements.pip``


* Execute Environment:

	1. Activate virtual environment
		``source <foldername>/bin/activate``
	2. Run server
		``python <foldername>/mangrove/src/web/manage.py runserver``


* Access URLs:

	1. Website URL: http://localhost:8000/login
	2. Couchdb URL: http://localhost:5984/_utils
