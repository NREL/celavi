Data Preprocessing
==================

Classes documented here deal with processing raw information into CELAVI-ready input datasets. Depending on the data source used, methods within the Compute Locations class may need to be edited or new methods added, to work with the different formats of the raw information.

Data Manager
------------

The `Data` class and its child classes define specific data formats (column names) and data types for the CELAVI input datasets. Backfilling can also be performed, or not, for each dataset type.

.. automodule:: celavi.data_manager
    :members:

Compute Locations
-----------------

Methods in this class perform merging and filtering operations to generate one dataset of all supply chain facility locations and types, and a second dataset of technology unit installations over time.

.. automodule:: celavi.compute_locations
    :members:
	

Data Filtering
--------------

The Data Filtering methods produce subsets of the facility locations, technology unit installation, and routes datasets (all outputs of preprocessing methods documented here) by U.S. state (region_id_2) and/or by the distance between facility pairs.

.. automodule:: celavi.data_filtering
    :members:


Router
------

Router methods implement the Djikstra minimum-distance algorithm to find on-road transportation routes between supply chain facility pairs.

.. automodule:: celavi.routing
    :members:
