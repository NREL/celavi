Python Life Cycle Inventory Analysis
====================================

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

.. autofunction:: solver_optimization

.. autofunction:: runner

.. autofunction:: model_celavi_lci_insitu


Concrete Inventory Editor
-------------------------

.. currentmodule:: concrete_life_cycle_inventory_editor

.. autofunction:: concrete_life_cycle_inventory_updater


Background Inventory Optimization
---------------------------------

.. currentmodule:: pylca_opt_background

.. autofunction:: model_celavi_lci_background

`model_celavi_lci_background` has functions defined within it that are not accessible to the autodoc.

Foreground Inventory Optimization
---------------------------------

.. currentmodule:: pylca_opt_foreground

.. autofunction:: preprocessing

.. autofunction:: solver_optimization

.. autofunction:: electricity_corrector_before20

.. autofunction:: runner

.. autofunction: model_celavi_lci


Background Emissions Postprocessing
-----------------------------------

.. currentmodule:: pylca_celavi_background_postprocess

.. autofunction:: postprocessing

.. autofunction:: impact_calculations