Developer Practices
===================

* We are using Git_ as the Source Control Manager (SCM)
* We are using GitFlow_ for better version control and branching
* Our Documentation style is restructuredtext_ (RST)
    - We can try out RST text with the online tool reSTrenderer_
* Our python coding style guide is PEP8_
 	
	- 4 spaces per indentation level
 	- Soft tabs (indentation is with spaces only)
* We have a continuous integration server set up using jenkins_. It can be viewed on http://178.79.163.33:8080/
* We have detailed test reports and code coverage for every build
* We are using nose_ tests to write unit tests. You are requested to maintain the unit test suit for every code you check in. Please make sure that the test coverage for code is high :)   
* Our functional tests are written in WebDriver_ (Selenium 2.0b2)
* We are using fabric_ for automatic deployment
* We use virtualenv_ and pip_ to set up our python environment


Other important links
---------------------
* Our transport layer is managed by VUMI_
* `Django 1.3`_ is our web framework

.. _Django 1.3: http://www.djangoproject.com
.. _VUMI: https://github.com/praekelt/vumi 
.. _Git: http://git-scm.com/
.. _GitFlow: https://github.com/nvie/gitflow
.. _restructuredtext: http://docutils.sourceforge.net/rst.html
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _jenkins: http://jenkins-ci.org/
.. _nose: http://ivory.idyll.org/articles/nose-intro.html
.. _WebDriver: http://code.google.com/p/selenium/wiki/GettingStarted
.. _fabric: http://docs.fabfile.org/0.9.4/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _pip: http://pypi.python.org/pypi/pip
.. _reSTrenderer: http://www.tele3.cz/jbar/rest/rest.html
