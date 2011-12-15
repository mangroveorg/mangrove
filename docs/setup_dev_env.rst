Setting Up the development environment
======================================
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
