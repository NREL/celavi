Cost Graph
==========

The Cost Graph is a directed network-based representation of the supply chain superstructure. It is used to store information about the supply chain such as costs and distances. During simulation, the Cost Graph is queried by the DES to calculate pathway characteristics and determine the preferred end-of-life pathway for technology components.

.. automodule:: celavi.costgraph
    :members:

Cost Methods
------------

Cost Methods are user-defined functions for calculating process costs.

.. automodule:: celavi.costmethods
    :members:

Wind Blade `path_dict` Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Because the `circular_pathways` and in particular the `cost uncertainty` dictionaries can vary in structure, here we include the complete dictionary for the wind blade case study. This version of the dictionary is for a single model run that does not include uncertainty. Quantities that may take on array-based uncertainty are indicated with comments.

.. code-block:: yaml

	circular_pathways:
		sc_begin: manufacturing
		sc_end: 
		- landfilling
		- cement co-processing
		- next use
		learning:
			coarse grinding:
				component : blade
				initial cumul: 1.0
				cumul: 
				learn rate: -0.05        # Define a list for array-based uncertainty.
				steps:
				- coarse grinding
				- coarse grinding onsite
			fine grinding:
				component : blade
				initial cumul: 1.0
				cumul:
				learn rate: -0.05        # Define a list for array-based uncertainty.
				steps:
				- fine grinding
		cost uncertainty:
			landfilling:
				uncertainty:
				c: 0.5
				loc: 0.8
				scale: 0.4
				m: 1.5921                # Define a list for array-based uncertainty.
				b: 59.23                 # Define a list for array-based uncertainty.
			rotor teardown:
				uncertainty:
				c: 0.5
				loc: 0.8
				scale: 0.4
				m: 1467.08               # Define a list for array-based uncertainty.
				b: 29626.0               # Define a list for array-based uncertainty.
			segmenting:
				uncertainty:
				c: 0.5
				loc: 0.8
				scale: 0.4
				b: 27.56                 # Define a list for array-based uncertainty.
			coarse grinding onsite:
				uncertainty:
				actual cost:
					c: 0.5
					loc: 0.8
					scale: 0.4
				initial cost: 106        # Define a list for array-based uncertainty.
			coarse grinding:
				uncertainty:
				actual cost:
					c: 0.5
					loc: 0.8
					scale: 0.4
				initial cost: 106        # Define a list for array-based uncertainty.
			fine grinding:
				uncertainty:
				actual cost:
					c: 0.5
					loc: 0.8
					scale: 0.4
				initial cost: 143       # Define a list for array-based uncertainty.
				revenue:     
					c: 0.5
					loc: 0.8
					scale: 0.4
					b: 273              # Define a list for array-based uncertainty.
			coprocessing:
				uncertainty:
				c: 0.5
				loc: 0.8
				scale: 0.4
				b: 10.37                # Define a list for array-based uncertainty.
			segment transpo:
				uncertainty:
				c: 0.5
				loc: 0.8
				scale: 0.4
				cost 1: 4.35 # Before 2001; 2002-2003; Define a list for array-based uncertainty.
				cost 2: 8.70 # 2001-2002; 2003-2019; Define a list for array-based uncertainty.
				cost 3: 13.05 # 2019-2031; Define a list for array-based uncertainty.
				cost 4: 17.40 # 2031-2044; Define a list for array-based uncertainty.
				cost 5: 21.75 # 2044-2050; Define a list for array-based uncertainty.
			shred transpo:
				uncertainty:
				c: 0.5
				loc: 0.8
				scale: 0.4
				m: 0.0011221            # Define a list for array-based uncertainty.
				b: 0.0739               # Define a list for array-based uncertainty.
			manufacturing:
				uncertainty:
				c: 0.5
				loc: 0.8
				scale: 0.4
				b: 11440.0               # Define a list for array-based uncertainty.
		path_split: 
			fine grinding:
				fraction: 0.3            # Define a list for array-based uncertainty.
				facility_1: landfilling
				facility_2: next use  
			pass:
				next use
		permanent_lifespan_facility: 
		- landfilling
		- cement co-processing
		- next use
		vkmt : 
		component mass : 
		year : 