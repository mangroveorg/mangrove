-----------------------
Core Datastore Overview
-----------------------

Introduction
------------
The high-level goal of the Mangrove datastore is to allow the free submission 
of data about a known set of *entities* and the quick and easy retrieval of 
data aggregated across time and hierarchy *without* requiring any upfront 
definition of schemas or entity structure. 

The key goals can be summarized as:

*   **Support Schema-less submission of arbitrary data**

    This is motivated by expected usage patterns where an organization will 
    frequently modify the data collected based on actual usage. By avoiding 
    requiring any a-priori definition of data-sets users are given full 
    flexibility to adjust data collected on-the-fly.
    
    for example, a health NGO operating rural clinics might begin by simply
    collecting a monthly report of how many patients where seen in that month. 
    As they get more sophisticated they may start collecting separate values for
    men, women, girls and boys. This transition should not require any datastore 
    restructuring.
    
*   **Support aggregation of data across time and hierarchy (geographic as special case)**

    Time-based aggregations include queries such as "Average number of patients seen in 2011" or
    more complex segmented time aggregations such as "Average number of patients seen each month in 2011"

    The key hierarchical aggregation is by geographic administrative boundaries. For example:
    "Total number of patients seen in 2011 for all clinics in San Francisco 
    (or California or United States)"

    Non-geographic arbitrary aggregation trees as supported as well. For example, aggregation by
    organization chart: "Patients seen at clinics managed by the Child Protection group"

*   **Provide data consistency on a field level via 'Data Dictionary'**
    
    To make it easy for users to aggregate data collect for a given entity via 
    unstructured data submissions, the core datastore will include a 'Data Dictionary' 
    where semantic-types are defined at stored. These types are then applied to submitted
    data fields allowing aggregation across different submissions and encouraging data 
    consistency.
    
    For example, our health NGO now wishes to  collecting data on each patient who receives an HIV 
    test so they submit data for each patient test in form (name, age-in-years, test-administered).
    
    Later they start recording patients who receive family-planning counseling and collect: 
    (name, age-in-years, counseling-program-attended)
    
    When they want to get the average age of patients who received HIV Tests or Family Planning Counseling
    the system can aggregate values of 'age-in-years' from both submissions even though the structure of 
    each submission is different.
    
    And later, when they want to start registering infants seen, they can define a more useful 'Age in Months'
    field (with values ranging from 0-60) and still run aggregations of the form 
    "Average age of patients seen" by multiplying any aggregated "Age in Years" values by 12 before averaging
    with "Age in Months" fields.
    
*   **Provide simple Python and RESTful APIs for accessing data and standard aggregation queries**

    The datastore is agnostic as to both the sources and consumers of data. These APIs will allow data sources
    ranging from SMS engines, to XForms clients and Web applications to submit data. 
    
    On the visualization and reporting side, charting, plotting, graphing, and geographic visualization 
    clients may access data series suitable for visualization pre-aggregated across time and hierarchy.
    
Core Structures
---------------

The logical architecture as envision has very few structures:

*   **Entity**

    An 'entity' is anything that users may want to report on. For example: a patient, a clinic, 
    a waterpoint, etc... Entities are *typed* (e.g. 'Clinic', 'Waterpoint') and *uniquely identified*  

    Entities contain *no data* beyond **UID** and **TYPE** 

    Entities must be *registered* in the system before data can be collected on them. 
    Registration is nothing more than the process of assigning a UID to the entity and does *not* 
    have to be a distinct user-action—the datastore can register an entity as part of the process of 
    recording the first submission of data on the entity.
     
*   **Data Record**

    Every time data is submitted to the datastore it is saved as an independent time-stamped data record.
    
    Each data record is associated with a single Entity. The set of data records for a given Entity 
    comprises all the values/data known about that Entity.
    
    For example, if a user submits a report that 10 patients were seen in May at Clinic1, and other user 
    submits a report that Clinic1 had stock of 20 bednets in May, the set of 
    information known about Clinic1 is that in May 10 patients were seen and 20 bednets are in stock.
     
*   **Fields and Values**
    
    Each data record contains an arbitrary set of field/value tuples with fields optionally
    typed from the Data Dictionary.
    
*   **Data Dictionary Types**
    
    These are definitions of types which can be associated with fields in a data record. Defined types
    maybe contain the following:
    
    * Type name
    * Base type (numeric, string, choice, geocode etc...)
    * User readable description
    * Validation constraints
    
Questions we want to ask the Data Store
---------------------------------------
Rather than set out specific technical proposals, or get caught in the argument
over what should be done in the DB vs. in application logic, here I try to 
categorize the different kinds of questions we want to be able to ask the data store. 

For the examples, assume the datastore is holding information for a NGO that operates health 
clinics throughout the United State.

Basic Retrieval
+++++++++++++++

**Question**
    Retrieve all the Entities of a specific type.
**Example**
    Show a list of all health clinics.

--------

**Question**
    Retrieve specific entity by a unique id.
**Example**
    Show health clinic with ID Clinic001:

--------

**Question**
    Retrieve specific entity by a semi-unique id. This may return a list if there are multiple matches.
**Example**
    Show health clinic with "Free Clinic" in its name.

State Queries
+++++++++++++

**Question**
    Retrieve an Entity (or set of Entities) with a specific set of values.
**Example**
    Show a list of all health clinics and include with each clinic:
    
    * Geographic location
    * Clinic Directors Name
    * Current stock of Cipro (an antibiotic)

--------
    
**Question** 
    Return an Entity (or set of Entities) with *all* the latest values associated with it.
**Example**
    Show the latest information for Clinic001. This should include the latest reported value of
    every field every reported on this clinic.
  
--------
      
**Question**
    Retrieve an Entity (or set of Entities) a set of values *as of a given date*
**Example**
    Show all the latest information on Clinic001 as of Jan 15, 2010

Time Aggregated Queries
+++++++++++++++++++++++

**Question**
    Retrieve an Entity (or set of Entities) with a specific set of values *aggregated* by 
    a function such as ``sum()`` or ``avg()`` over a given time range.
**Example**
    Show a list of all health clinics and include with each clinic:
    
    * Total number of patients seen in 2011

--------
        
**Question**
    Retrieve an Entity (or set of Entities) with a specific set of values *aggregated* by 
    a function such as ``sum()`` or ``avg()`` over a given time range with a given *periodicity*.
**Example**
    Show a list of all health clinics and include with each clinic:
    
    * Average number of patients seen each *month* for each month in 2011

    
Selection Queries
+++++++++++++++++
**Question**
    Retrieve all Entities which have a specific value.
**Example**
    Show all health clinics where "Population Served" > 1000
 
--------
       
**Question**
    Retrieve all Entities which have a specific *aggregated* value.
**Example**
    Show all health clinics where "Total Patients Seen" > 1000
 
--------
       
**Question**
    Retrieve all Entities which have a specific aggregated value over time.
**Example**
    Show all health clinics where "Total Patients Seen in 2011" > 1000
       

Hierarchy Aggregated Queries
++++++++++++++++++++++++++++
**Note**: These queries don't return entities, they return values aggregated by a 
hierarchy node (e.g. 'California' or 'San Francisco') which suggests that maybe 
Matt Berg is right and hierarchy nodes maybe should be consider 'Entities', or 
'Generated Entities'...

**Question**
    Retrieve a set of *Values* aggregated by a given *node* in a hierarchy.
**Example**
    From the set of all clinics in California show:
    
    * Total number of patients seen in 2011 (in California)
    * Average number of patients seen in 2011 (in California)

--------
        
**Question**
    Retrieve a set of *Values* aggregated by a given *level* in a hierarchy.
**Example**
    From each State in the United States show:
    
    * Total number of patients seen in clinics in that state 2011 
    * Average number of patients seen in clinics in that state in 2011
