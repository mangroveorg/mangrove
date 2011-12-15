Querying couch by hierarchy and time
====================================

The Problem : 
-------------
Doing aggregation by hierarchy and time in couchdb.
For example : 

Our aim is to be able to give results for the following types of queries:

1)Total population in Country/State/City wise for all months.
2)Monthly population country/state/city wise. For example Total Population in the state of Maharashtra in March.

The Data:
---------
The population would be stored as couchdb document in the following format. (It is simplified for the purpose of the illustration)
The basic document structure is as follows:: 

    {
        "_id": "Entity name",
        "path": [
                "India",
                "MH",
                "Pune"
                ],
        "population": 20,
        "month": "feb"
    }

MH - Maharashtra is a state
Pune is a city

We have written a map-reduce function to aggregate data by multilevel location hierarchy and time.
The "path" field indicates the location hierarchy tree for the entity. Month is the time value. It will be a proper date - we have taken month for the purpose of the spike.

The Map-Reduce:
---------------
The map function is as follows::
 
    function(doc){
            for (i in doc.path){
                emit([i,doc.path[i],doc.month], doc.population);
            }
    }

The reduce function is _sum

The Output:
-----------

The sample output will be as follows:(when reduced to level 2 in couchdb)::
    
    {
        ["2", "Pune", 7]    : 150
        ["2", "Pune", 3]	: 80
        ["2", "Pune", 2]	: 100
        ["1", "TN", 2]      : 120
        ["1", "MH", 7]	    : 150
        ["1", "MH", 2]      : 100
        ["0", "India", 7]	: 150
        ["0", "India", 2]	: 220
    }

TN-TamilNadu is a state
It gives month-wise aggregates.(The third key is the month 7-July,2-Feb etc. The second key is the label for the state)

At level 1 - it gives totals for all months::

    {
        ["2", "Pune"]	    : 330
        ["1", "TN"]	        : 320
        ["1", "MH"]	        : 330
        ["0", "India"]	    : 650
    }
