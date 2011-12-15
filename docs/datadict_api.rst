*********************
Data Dictionary Expected API
*********************


How it is stored in nosql database.
===================================
In the mangrove system, this is termed as data dict storage::

	{
		"_id": """,
		"primitive type": "int",
		"name": "Malaria pills stock",
		"description": "Description of this drug and the stock itself.",
		"version": "2010-10-10 07:06:45.45646",
		"tags": [
			"health",
			"medicine",
			"drug",
			"malaria", 
			"pill"
		   ],
		"constraints": {
			"gt": "0",
			"lt": "10"
		   },
	}



How it is refereneced in external service.
==========================================

In Mangrove system, the data is stored in datastore. Each data instance holds a reference to its type.:: 


	type {
		"uuid" : "b4cd35d9f04887da905c051b894568",
		"version" : "2010-10-10 07:06:45.45646"
	}



Python wrapper API
===================

For querying the data dict, you can use a Python restful wrapper that provides filtering, type casting and constraint validations.

For example:
 
In settings.py::

	DATABASE_NAME = 'datadict'
	SERVER_ADDRESS = 'http://localhost'
	SERVER_PORT = '5984'

Create a data type::

       dt = DataType(name="test", contraints={'gt':4}, tags=['foo', 'bar'], 
                     type="int", description="Super dupper type")        
       dt.save()

or:: 
       
	DataType.create(name="test", contraints={'gt':4}, tags=['foo', 'bar'], 
                     type="int", description="Super a type")

Searching for datatype with tags::

	DataType.with_tags('foo', 'bar')


Getting datatype::

	dt = DataType.get(id, version)

validating data::

	try:
		dt.validate(value)
	except dt.ValidationError as e:
		for error in e.errors:
			print error

casting data::

	dt.to_python(value)
	dt.to_json(value)
	dt.to_xform(value)


