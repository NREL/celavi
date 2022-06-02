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

The `cost uncertainty` dictionary (an element of the `circular_pathways` dictionary) structure can be adjusted based on the modeling requirements of a particular case study. The structure here can apply to cost models that depend linearly on time and can take on random or array-based uncertainty.

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
		cost uncertainty:       # Dictionary of probability distribution parameters for cost models.
			[process step]:     # Name of process step for the cost model. 
				uncertainty:    # random or array to implement uncertainty; leave blank for no uncertainty.
				c:              # c, loc, scale: Probability distribution parameter(s) for random uncertainty type; can be re-named depending on distribution. See https://docs.scipy.org/doc/scipy/reference/stats.html.
				loc: 
				scale: 
				m:              # m, b: Cost model parameter(s) for array uncertainty type; can be scalars or lists of equal length.
				b:
		path_split:             # Dictionary defining any process steps where the material stream splits, e.g. for material losses.
			[process step]:     # Name of process step where split occurs.
				fraction:       # Float or list of floats; fraction of material sent to facility_1 type
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

Scenario Flags
^^^^^^^^^^^^^^

The set of Boolean flags at the top of the scenario configuration file control much of the preprocessing done to set up a CELAVI simulation. Additional explanations for each flag are provided here.

* `clear_results`
	* When CELAVI is executed multiple times on the same machine, it will produce one or more sets of output files in the `results` directory (one set of results files is produced per model run). Set `clear_results` to True if you expect to be executing CELAVI more than once and do not want the results of each execution to be overwritten.
	* Results from the most recent CELAVI execution are always found in the `results` directory.
	* When `clear_results` is True, every CELAVI execution after the first one will produce an additional directory of results files, with "results-" and the current timestamp in the directory name. The contents of the new `results` directory is the output files from the *previous* CELAVI execution.
* `compute_locations`
	* This flag controls whether the facility location and type dataset is assembled from raw location files before supply chain routes are found or the simulation begins.
	* If you have already manually assembled the facility location and type dataset for your supply chain, then this flag can be set to False. However, if the facility information to be used in your supply chain is coming from a database such as the U.S. Wind Turbine Database or the Landfill Methane Outreach Program, then setting `compute_locations` to True will assemble the complete facility dataset.
* `run_routes`
	* When `run_routes` is True, then the facility locations and route pairs datasets will be used to identify pairs of facilities between which materials will be transported. The `Router` module is then used to calculate minimum-distance (on-road) routes between each facility pair.
	* Generating routes for a multi-state or national supply chain can be time consuming, depending on the number of facilities in a supply chain. If the underlying facility locations dataset is stable, then `run_routes` need be True only for one CELAVI execution. Future executions will use the same set of routes and there is no need to re-generate the routes dataset.
* `use_computed_routes`
	* The user can bypass the built-in Router module and supply a custom routes dataset by setting `use_computed_routes` to False. In this case, the filename with the custom routes dataset must also be provided in the Case Study configuration file.
	* If `run_routes` is True, then `use_computed_routes` should also generally be True, unless the user is comparing results from two different routes datasets.
* `initialize_costgraph`
	* The Cost Graph model is initialized from the facility locations dataset, the routes dataset, and several other datasets that define how facilities in the supply chain are interconnected.
	* While initializing the Cost Graph can be time consuming, it is recommended to keep `initialize_costgraph` set to True unless CELAVI is being executed with one model run per simulation and no changes in the input datasets or parameters are being made between executions.
	* When executing multiple runs per scenario, the Cost Graph model will only be initialized once, thus `initialize_costgraph` should be True in this case.
* `location_filtering`
	* This flag can be used in combination with the `states_included` list under the `scenario` dictionary to filter down large input datasets to include only certain U.S. states (region_id_2, in the input datasets). One set of (for example) national-scale data can then be defined and filtered as needed, rather than developing separate datasets.
	* If `location_filtering` is True but there are no states listed under `states_included`, then a warning is printed and no filtering is performed. If `location_filtering` is False, then no filtering is performed even if states are listed under `states_included`.
	* Both the processed facility locations dataset and the routes dataset are filtered with this flag.
* `distance_filtering`
	* When `distance_filtering` is True, the route pairs dataset is used to filter down the routes file and Cost Graph edges based on the `vkmt_max` column. This allows users to set a transportation distance limit, for instance for transportation to landfills, without having to manually remove unrealistically lengthy routes.
	* Some care should be taken in using `distance_filtering` and in setting the `vkmt_max` values. It's possible to filter out routes that must be included for the supply chain to be complete (e.g. routes to a power plant from a manufacturing facility), and in this case the filtering will produce an error during the CELAVI execution.
	* Any blank values in the `vkmt_max` column will be backfilled with a sufficiently large number that no routes will be filtered out, allowing for only routes between specific facility pairs to be filtered based on distance.
* `pickle_costgraph`
	* When True, the `pickle_costgraph` flag will save (pickle) a copy of the initialized Cost Graph model as a Python object that can be examine or used outside the CELAVI execution. This can be useful for multiple repeated CELAVI executions.
* `generate_step_costs`
	* The step costs dataset assigns processing cost methods (models) to every facility in the supply chain. Depending on how the processing costs vary with space and with facility, users may want to manually generate the step costs dataset or generate it automatically by setting `generate_step_costs` to True.
	* If this flag is True, the assumption is that processing costs *do not vary with facility location*, and more broadly that there is one (set of) processing cost methods per facility type. In the case that there are multiple processing cost methods for a single facility type - for instance, separate landfill tipping fee models by U.S. state or county - then `generate_step_costs` must be set to False and the step costs dataset generated manually.
* `use_fixed_lifetime`
	* Technology components remain "in use" for a period of time before entering the end-of-life phase. The time "in use" is the component lifetime, which for each component type can be modeled either as a fixed value or as random draws from a Weibull distribution. Both the fixed values and the Weibull parameters are defined by component type in the Scenario configuration file.
	* Set `use_fixed_lifetime` to True to use a fixed, deterministic lifetime for every technology component, or set to False to generate lifetimes from the Weibull distributions.
	* If `use_fixed_lifetime` is set to False, it is recommended that users also set the `seed` value under the `scenario` dictionary. This will generate stochastic results that are reproducible in repeated CELAVI executions.
* `use_lcia_shortcut`
	* Repeatedly performing LCIA calculations can lengthen CELAVI run time considerably. To speed up the calculations, `use_lcia_shortcut` can be set to True to use precomputed emission factors stored in a local file. If this file does not yet exist, then LCIA calculations are performed normally and the file is populated with emission factors as they are calculated.
	* When performing multiple model runs in a single CELAVI execution, it is strongly recommended to set `use_lcia_shortcut` to True to shorten the run time.
	* After changes to the scenario parameters or to the input datasets, it is recommended to delete the local emission factors file to avoid using incorrect factors.


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