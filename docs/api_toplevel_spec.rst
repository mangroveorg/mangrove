API SPEC EXAMPLES
=================

Top Level Format:
-----------------

Each API response shall have a dictonaty with 4 items.  When responding via HTTP
the status filed shall match the HTTP response status code.

============    ============    ===============================================================
FIELD           TYPE            DESCRIPTION
============    ============    ===============================================================
status          int             HTTP status 2xx, 3xx, 4xx, 5xx
message         str             A string containing a message about the response
num_results     int             The number of results <=0
results         list            A list of results of length num_results. If 0, then empty list
============    ============    ===============================================================


An example of an Error response in JSON.
::
    {
    status:         401,
    message:        "Not Authorized",
    num_results:    0,
    results:        ()
    }

An example of an successful created response in JSON.
::
    {
    status:         201,
    message:        "Data Record Created",
    num_results:    1,
    results:        (
                    '_id':    'ee7c7583-1afe-4985-a1ea-69fd4764552b',
                    'field1': 'foo',
                    'field2': 'bar',
                    )
    }
    
An example of an successful search response in JSON.
::
    {
    status:         200,
    message:        "Search results successful",
    num_results:    2,
    results:        (
                        {
                        '_id':    'ee7c7583-1afe-4985-a1ea-69fd4764552b',
                        'field1': 'foo',
                        'field2': 'bar'
                        },
                        
                        {
                        '_id':    '4d4eb8de-3955-412c-a078-3e846182380b',
                        'field':  'milli',
                        'field2': 'vanilli'
                        },
                    )
    }