**********************************
Data Dictionary Concept and usages
**********************************

The data dictionary is an stand alone service that hosts data type definitions in order to allow user to share them.

This project is part of the `mangrove <https://github.com/mangroveorg/mangrove>`_ project.

It provides
===========

- A simple format to define any kind of data by providing a basic type, tags and contraints.
- An unique ID to refence a definition in external services.
- HTTP API to get the definition from external service.
- A python wrapper around the HTTP API than provide contraints checking and type casting.
- A replication system to synchronize several data dictionaries together.
- A versioning system ensuring that updating definitions doesn't break others references.

Use cases
==========

- You share common types among several systems and keep them up to date and in sync.
- You expect the user to define data himself.
- You store data in a schemaless data base and want to attach a type, a meaning or constraints to it.


What it's not
==============

- An semantic data base. No complexe defintion nor RDF/SPARQL magic in there.
- A user interface to let the user enter data types. You have to provide it.
- A bullet proof solution for anything. This is work in progress and design to solve a very specific problem, 
  not a standard or anything to solve anybody's data type problems.


The data dictionary in the Mangrove project
============================================

We need to store data in a schemaless database.

The data is going to be defined by the user and organisations will want to share their definations.

The data is going to be inputs from field agents about any subjects they are studying so the system cannot know in advance the data type. 
For example some NGO would be studying school results in India and other would be studying school attentance in Africa. They all would want data defination for school and students.
The data dictionary is designed to hold this defination so that it is reusable across orgnanisation.



  


Current implementation
=======================

- CouchDB database
- couchdb-python
