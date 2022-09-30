Python Life Cycle Inventory Analysis
====================================
The PyLCIA module links to the DES material model through the DES interface code. The DES interface preprocesses the incoming materials dataframe and prepares it for the LCA calculations. The interface calls on five main subcomponents of the pyLCIA module. 
It calls the concrete life cycle inventory updater to check for glass fiber materials in the incoming stream. If yes, it creates a modified cement coprocessing inventory based on the amount of glass fiber present in the incoming stream. This modified inventory is then used for LCA calculations. 
It calls the insitu_emission module to calculation insitu emissions. The foreground system for the study has direct emissions. To calculation those emissions, these systems are required to be scaled up based on their usage and then direct emissions derived using the scaling variables. These calculations are done using a modified LCA approach using a static inventory with just just product flows. 
It calls the pylca_opt_foreground module to calculate the first set of LCA calculations only for the foreground activities. All input flows to the foreground system from the background life cycle inventory are derived based on the scale up or scale down of these processes. This module also preprocesses the inventory and allows replacement of electricity production with dynamic grid mixes from electricity capacity expansion models. 
It call the pylca_opt_background module to perform the major LCA calculations of the background inventory. The final demand to the background LCI is obtained from the pylca_opt_foreground module. This module calculates the complete cradle to gate life cycle emissions for the foreground processes. 
The final module used by PyLCIA is the pylca_celavi_background_postprocess which has two main functions. It combines background and foreground emissions to complete our system boundary for the life cyle analysis. Finally, it converts emissions to impact factors and prepares the results to be sent to DES for final processing and visualization. 


ReEDS Data Importer
-------------------

.. automodule:: celavi.reeds_importer
    :members:

Discrete Event Simulation Interface
-----------------------------------

.. currentmodule:: des_interface
.. autoclass:: PylcaCelavi
	:members:

Insitu Emission Calculations
----------------------------

.. currentmodule:: insitu_emission


.. autofunction:: preprocessing

.. autofunction:: solver

.. autofunction:: electricity_corrector_before20

.. autofunction:: runner_insitu

.. autofunction:: model_celavi_lci_insitu


Concrete Inventory Editor
-------------------------

.. currentmodule:: concrete_life_cycle_inventory_editor

.. autofunction:: concrete_life_cycle_inventory_updater


Background Inventory Optimization
---------------------------------

.. currentmodule:: pylca_opt_background

.. autofunction:: model_celavi_lci_background

Please note: `model_celavi_lci_background` has functions defined within it that are not accessible to the autodoc.

Foreground Inventory Optimization
---------------------------------

.. currentmodule:: pylca_opt_foreground

.. autofunction:: preprocessing

.. autofunction:: solver

.. autofunction:: electricity_corrector_before20

.. autofunction:: lca_runner_foreground

.. autofunction: model_celavi_lci


Background Emissions Postprocessing
-----------------------------------

.. currentmodule:: pylca_celavi_background_postprocess

.. autofunction:: postprocessing

.. autofunction:: impact_calculations
