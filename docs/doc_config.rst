Configuration Files
===================

The Case Study config file only needs to be created once per supply chain or per case study.

Several versions of the Scenario config file can be created per case study to explore the impacts of different cost and other scenarios.

Case Study Config Template
--------------------------

.. code-block:: yaml

	model_run:
		start_year:          # Integer; Calendar year
		end_year:            # Integer; Calendar year
		timesteps_per_year:  # Integer; Units = timesteps
		min_lifespan:        # Integer; Units = timesteps
		lcia_update:         # Integer; Units = timesteps
		cg_update:           # Integer; Units = timesteps
		cg_verbose:          # Integer <= 2
		save_cg_csv:         # Boolean

	directories:
		# The required directories should all exist in the same directory where the config files are located.
		quality_checks:          # Not required
		inputs_to_preprocessing: # Required
		inputs_optional:         # Not required
		inputs:                  # Required
		generated:               # Required; Empty
		results:                 # Required; Empty

	files:
		# All file names must include the extension, which is ".csv" unless otherwise noted.
		
		# Information used for internal data checks.
		quality_checks:
			quality_check: data-quality-checks.csv

		# Datasets that are preprocessed and/or used to generate input datasets.
		inputs_to_preprocessing:
			transportation_graph: 
			node_locs: 
			power_plant_locs: 
			landfill_locs: 
			other_facility_locs: 
			capacity_projection: # This parameter should remain blank - it will be filled in with a value from the Scenario config file.
		
		# Datasets that can be provided as alternatives to programmatically generated datasets.
		inputs_optional:
			step_costs_custom: # An alternative to the generated step_costs file
			routes_custom:     # An alternative to the generated routes_computed file
			stock_filename:    # .p

		# Input datasets that do not require preprocessing
		inputs:
			lookup_facility_type: 
			lookup_step_costs: 
			lookup_steps: 
			lookup_transpo_cost_methods: 
			lookup_step_cost_methods: 
			fac_edges: 
			transpo_edges: 
			route_pairs: 
			component_material_mass: 
			static_lci: 
			uslci: # .p
			lci_activity_locations: 
			emissions_lci: 
			traci_lci: 
			state_reeds_grid_mix: 
			national_reeds_grid_mix: 

		# Datasets and files generated internally as data storage and/or used for debugging.
		generated:
			costgraph_pickle: # .obj
			costgraph_csv: 
			step_costs: 
			locs: 
			technology_data: 
			routes_computed: 
			intermediate_demand: 
			lcia_to_des: 
			lcia_shortcut_db: 
			state_electricity_lci: 
			national_electricity_lci: 
		
		# Human-readable results files for diagnostic visualization and further analysis
		results:
			pathway_criterion_history: 
			component_counts_plot: # .png
			material_mass_plot: # .png
			count_cumulative_histories: 
			mass_cumulative_histories: 
			lcia_facility_results: 
			lcia_transpo_results: 

Scenario Config Template
------------------------

.. code-block:: yaml

	flags:
		# Each parameter here should be a Boolean (True/False)
		clear_results         :    # Move existing results files to a sub-directory to avoid overwriting.
		compute_locations     :    # Compute locations from raw input files (e.g., LMOP, US Wind Turbine Database).
		run_routes            :    # Compute routing distances between connected facilities.
		use_computed_routes   :    # Read in a pre-assembled routes file instead of generating a new one.
		initialize_costgraph  :    # Initialize Cost Graph from input data.
		location_filtering    :    # Filter facility locations based on states_included parameter.
		distance_filtering    :    # Filter computed routes and Cost Graph edges based on max distances in route_pairs file.
		pickle_costgraph      :    # Save the Cost Graph instance as a pickle file.
		generate_step_costs   :    # Programmatically generate step_costs file; set to False if supply chain costs for a facility type vary regionally.
		use_fixed_lifetime    :    # Use fixed technology component lifetime instead of drawing from Weibull distribution.
		use_lcia_shortcut     :    # Use precomputed LCI file where possible to speed up LCIA calculations.
	
	scenario:
		capacity_projection:     # Name of file with scenario-specific capacity projection data.
		states_included:         # List of U.S. states to optionally filter facility locations.
		seed:                    # Random number generator seed
		electricity_mix_level :  # Specify disaggregation for electricity grid mix data: "state" or "national"
		runs:                    # Number of model runs within this scenario to execute.

	circular_pathways:
		sc_begin:               # Facility type where the supply chain "begins". Typically manufacturing or resource extraction.
		sc_end:                 # List of facility types where the supply chain "ends".
		learning:               # Dictionary of parameters for industrial learning-by-doing parameters.
			[facility type]:    # Facility type to which this learning cost model applies.
				component :     # String; component type(s).
				initial cumul:  # Initial cumulative production for this technology.
				cumul:          # Leave blank: this value is filled in and updated during simulation.
				initial cost:   # Processing cost (USD/mass) at the beginning of the model run.
				revenue:        # Revenue (USD/mass) from this processing step (may be zero).
				learn rate:     # Rate at which industrial learning-by-doing reduces costs. Must be negative.
				steps:          # List of processing steps where this cost model is applied.
		cost_uncertainty:       # Dictionary of probability distribution parameters for cost models.
			[process step]:     # Name of process step for the cost model. 
				uncertainty:    # Boolean (True/False): whether to implement uncertainty for this process step.
				c:              # c, loc, scale: Probability distribution parameter(s); can be re-named depending on distribution. See https://docs.scipy.org/doc/scipy/reference/stats.html.
				loc: 
				scale: 
		path_split:             # Dictionary defining any process steps where the material stream splits, e.g. for material losses.
			[process step]:     # Name of process step where split occurs.
				fraction: 0.3   # Float; fraction of material sent to facility_1 type
				facility_1:     # Downstream facility type where fraction of material is sent.
				facility_2:     # Downstream facility type where 1 - fraction of material is sent.
			pass:               # Facility type(s) to ignore in DES because material was sent there during the split.
		permanent_lifespan_facility:  # Facility type(s) where material accumulates (e.g. landfills).
		vkmt :                        # Leave blank: this value is updated during simulation.
		component mass :              # Leave blank: this value is updated during simulation.
		year :                        # Leave blank: this value is updated during simulation.
		

	technology_components:         # Dictionary of information about the composition of a technology unit.
		circular_components:       # List of technology components involved in the circular supply chain.
		component_list:            # Dictionary of all technology components and the number of components in each unit.
		component_materials:       # Dictionary listing the constituent materials in each component.
		component_fixed_lifetimes: # Dictionary with fixed lifetimes (years) of each component.
		component_weibull_params:  # Dictionary with Weibull distribution parameters (L, K) of each component lifetime.
		substitution_rates:        # Dictionary of materials substituted by circular components/materials and the substitution rates (kg/kg).


Case Study Config Example
-------------------------

.. code-block:: yaml

	model_run:
		start_year: 2000
		end_year: 2050
		timesteps_per_year: 12
		min_lifespan: 120 # timesteps
		lcia_update: 12 # timesteps
		cg_update: 12 #timesteps
		cg_verbose: 1
		save_cg_csv: True

	directories:
		quality_checks: quality_checks/
		inputs_to_preprocessing: inputs_to_preprocessing/
		inputs_optional: inputs_optional/
		inputs: inputs/
		generated: generated/
		results: results/

	files:
		# Files used for input dataset validation
		quality_checks:
			quality_check: data-quality-checks.csv

		# Files that must be processed to create CELAVI input files
		inputs_to_preprocessing:
			transportation_graph: transportation_graph.csv
			node_locs: node_locations.csv
			power_plant_locs: uswtdb_v4_1_20210721.csv
			landfill_locs: landfilllmopdata.csv
			other_facility_locs: other_facility_locations_all_us.csv
			capacity_projection: #leave this blank
		
		# Inputs that are alternatives to programmatically generated inputs
		inputs_optional:
			step_costs_custom: step_costs_custom.csv # an alternative to the generated step_costs file
			routes_custom: routes.csv # an alternative to the generated routes_computed file
			stock_filename: stock_filename.p

		# Files used directly as CELAVI inputs
		inputs:
			lookup_facility_type: facility_type.csv
			lookup_step_costs: step_costs_default.csv
			lookup_steps: step.csv
			lookup_transpo_cost_methods: transpo_cost_method.csv
			lookup_step_cost_methods: step_cost_method.csv
			fac_edges: fac_edges.csv
			transpo_edges: transpo_edges.csv
			route_pairs: route_pairs.csv
			component_material_mass: avgmass.csv
			static_lci: foreground_process_inventory.csv
			uslci: usnrellci_processesv2017_loc_debugged.p
			lci_activity_locations: location.csv
			emissions_lci: emissions_inventory.csv
			traci_lci: traci21.csv
			state_reeds_grid_mix: state_dynamic_grid_mix.csv
			national_reeds_grid_mix: national_dynamic_grid_mix.csv

		# Files written during CELAVI runs intended only for internal or debugging use
		generated:
			costgraph_pickle: netw.obj
			costgraph_csv: netw.csv
			step_costs: step_costs.csv
			locs: locations_computed.csv
			technology_data: number_of_technology_units.csv
			routes_computed: routes_computed.csv
			intermediate_demand: intermediate_demand.csv
			lcia_to_des: final_lcia_results_to_des.csv
			lcia_shortcut_db: lca_db.csv
			state_electricity_lci: state_level_grid_mix.csv
			national_electricity_lci: national_level_grid_mix.csv
		
		# Human-readable results files for visualization and further analysis
		results:
			pathway_criterion_history: pathway_criterion_history.csv
			component_counts_plot: component_counts.png
			material_mass_plot: material_mass.png
			count_cumulative_histories: count_cumulative_histories.csv
			mass_cumulative_histories: mass_cumulative_histories.csv
			lcia_facility_results: lcia_locations_join.csv
			lcia_transpo_results: lcia_transportation.csv		


Scenario Config Example
------------------------

.. code-block:: yaml

	flags:
		clear_results         : True # If results files already exist, move them to a sub-directory to avoid overwriting
		compute_locations     : True  # if compute_locations is enabled (True), compute locations from raw input files (e.g., LMOP, US Wind Turbine Database)
		run_routes            : True  # if run_routes is enabled (True), compute routing distances between all input locations
		use_computed_routes   : True  # if use_computed_routes is enabled, read in a pre-assembled routes file instead of generating a new one
		initialize_costgraph  : True  # create cost graph fresh or use an imported version
		location_filtering    : True  # If true, dataset will be filtered to the states below
		distance_filtering    : False # if true, filter computed routes based on max distances in route_pairs file
		pickle_costgraph      : True  # save the newly initialized costgraph as a pickle file
		generate_step_costs   : True # set to False if supply chain costs for a facility type vary regionally
		use_fixed_lifetime    : False # set to False to use Weibull distribution for lifetimes
		use_lcia_shortcut     : False # set to False to re-generate the lca_db file
	
	scenario:
		capacity_projection: StScen20A_MidCase_annual_state.csv
		states_included:
		- IA
		- MO
		seed: 13
		electricity_mix_level : state
		runs: 3

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
				initial cost: 121.28
				revenue: 0
				learn rate: -0.05
				steps:
				- coarse grinding
				- coarse grinding onsite
			fine grinding:
				component : blade
				initial cumul: 1.0
				cumul: 
				initial cost: 100.38
				revenue: 242.56
				learn rate: -0.05
				steps:
				- fine grinding
		cost_uncertainty:
			landfilling:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			rotor_teardown:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			segmenting:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			coarse_grinding_onsite:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			coarse_grinding:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			fine_grinding:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			fine_grinding_revenue:
				c: 0.5
				loc: 0.8
				scale: 0.4
			coprocessing:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			segment_transpo:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			shred_transpo:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			manufacturing:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
			blade_transpo:
				uncertainty: True
				c: 0.5
				loc: 0.8
				scale: 0.4
		path_split:
			fine grinding:
				fraction: 0.3
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
		

	technology_components:
		circular_components:
		- blade
		component_list:
			nacelle : 1
			blade : 3
			tower : 1
			foundation : 1
		component_materials:
			nacelle : 
			- steel
			blade : 
			- glass fiber
			- epoxy
			tower : 
			- steel
			foundation : 
			- concrete
		component_fixed_lifetimes: # Years
			nacelle : 30
			blade : 20
			foundation : 50
			tower : 50
		component_weibull_params: #L, K
			nacelle : 
			blade : 
				L : 240
				K : 2.2
			foundation : 
			tower :
		substitution_rates:
			sand: 0.15
			coal: 0.30