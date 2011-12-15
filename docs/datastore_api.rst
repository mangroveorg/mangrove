====
APIs
====

To get a quick idea of the current state of the mangrove.datastore
API, we have included the API for all the files in
mangrove/datastore/.

Here's what's in mangrove.datastore:

.. automodule:: mangrove.datastore
    :members:

---------------
aggregationtree
---------------
.. automodule:: mangrove.datastore.aggregationtree
    :members:

------
config
------
.. automodule:: mangrove.datastore.config
    :members:

--------
database
--------
.. automodule:: mangrove.datastore.database
    :members:

--------
datadict
--------
.. automodule:: mangrove.datastore.datadict
    :members:

----
data
----
.. automodule:: mangrove.datastore.data
    :members:

----------
datarecord
----------
.. automodule:: mangrove.datastore.datarecord
    :members:

---------
documents
---------
.. automodule:: mangrove.datastore.documents
    :members:

------
entity
------
.. automodule:: mangrove.datastore.entity
    :members:

-----------
initializer
-----------
This module tries to import validate.py, but I can't get it to work on
my machine.

.. .. automodule:: mangrove.datastore.initializer
..     :members:


--------
reporter
--------
This module tries to import validate.py, but I can't get it to work on
my machine.

.. .. automodule:: mangrove.datastore.reporter
..     :members:

--------
settings
--------
.. automodule:: mangrove.datastore.settings
    :members:

============================
Datastore document structure
============================

Entities::

    Reporter
    {
       "_id": "a676766fe45440f48ff4e9a0ce58b329",
       "_rev": "1-f83b88a382c14b5ade660710adde0d9e",
       "name": "reporter1",
       "entity_type": "reporter",
       "last_updated_on": null,
       "created_on": "2011-03-24T07:32:15Z",
       "aggregation_trees": {
           "org_chart": [
               "Country Manager",
               "Field Manager",
               "Field Agent"
           ]
       },
       "attributes": {
           "age": 25,
           "entity_type": "reporter"
       },
       "document_type": "Entity"
    }
    
    Clinic
    {
       "_id": "961cefb2a0324878bed06ab736e5dc09",
       "_rev": "1-c4d02559a13e7698437aae58f35e8440",
       "name": "Clinic 1",
       "entity_type": "clinic",
       "last_updated_on": null,
       "created_on": "2011-03-24T07:32:15Z",
       "aggregation_trees": {
           "location": [
               "India",
               "Maharashtra",
               "Pune"
           ]
       },
       "attributes": {
           "entity_type": "clinic"
       },
       "document_type": "Entity"
    }
    
Data Records::

    Data Record
    {
       "_id": "e4d5cb3e76ca40a78088c7bfe5d0cf03",
       "_rev": "1-7ca2ee8ad10a444eb6f3a8bad19ff957",
       "reporter_backing_field": {
           "_id": "a676766fe45440f48ff4e9a0ce58b329",
           "name": "reporter1",
           "entity_type": "reporter",
           "_rev": "1-f83b88a382c14b5ade660710adde0d9e",
           "last_updated_on": null,
           "created_on": "2011-03-24T07:32:15Z",
           "aggregation_trees": {
               "org_chart": [
                   "Country Manager",
                   "Field Manager",
                   "Field Agent"
               ]
           },
           "attributes": {
               "age": 25,
               "entity_type": "reporter"
           },
           "document_type": "Entity"
       },
       "last_updated_on": null,
       "source": {
           "report": "hn1.2424",
           "phone": "1234"
       },
       "created_on": "2011-03-24T07:32:15Z",
       "attributes": {
           "beds": "100",
           "event_time": "2011-02-01 00:00:00",
           "arv": "200"
       },
       "document_type": "DataRecord",
       "entity_backing_field": {
           "_id": "880552a483594ca9af07508e379f4520",
           "name": "Clinic 2",
           "entity_type": "clinic",
           "_rev": "1-99c4e6ebd76bba417dcd034f935d7483",
           "last_updated_on": null,
           "created_on": "2011-03-24T07:32:15Z",
           "aggregation_trees": {
               "location": [
                   "India",
                   "Karnataka",
                   "Bangalore"
               ]
           },
           "attributes": {
               "entity_type": "clinic"
           },
           "document_type": "Entity"
       }
    }
