Discrete Event Simulation
=========================

The discrete event simulation (DES) consists of:

* A **Context** instance which stores supply-chain-level information and methods
* Many **Component** instances that transition through the supply chain during the simulation
* A **Facility Inventory** for every facility in the supply chain: this inventory records material flows.
* A **Transportation Tracker** for every facility in the supply chain with *inbound* material flows.

Context
-------

.. automodule:: celavi.des
    :members:
	

Component
---------

A technology component is the basic unit of a CELAVI simulation. A component has one or more constituent materials that are also tracked.

.. automodule:: celavi.component
    :members:


Facility Inventory
------------------

.. automodule:: celavi.inventory
    :members:

Critical Instance Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^
These variables are passed to other classes and methods within CELAVI.

self.component_materials: Dict[str, float]
	The cumulative amount of component materials over the entire
	lifetime of the simulation.

self.component_materials_deposits: List[Dict[str, float]]
	The history of the deposits from this inventory. These are
	instantaneous, not cumulative, values.

Transportation Tracker
----------------------

.. automodule:: celavi.transportation_tracker
    :members:
