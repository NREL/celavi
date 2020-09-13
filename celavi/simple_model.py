from typing import Dict, List, Callable

import simpy
import pandas as pd

from .unique_identifier import UniqueIdentifier
from .states import StateTransition, NextState
from .inventory import Inventory


class Component:
    def __init__(
        self,
        context,
        kind: str,
        xlat: float,
        ylon: float,
        parent_turbine_id: int,
        year: int,
        lifespan_years: float,
    ):
        self.state = ""  # There is no state until beginning of life
        self.context = context
        self.id = UniqueIdentifier.unique_identifier()
        self.kind = kind
        self.xlat = xlat
        self.ylon: ylon
        self.parent_turbine_id = parent_turbine_id
        self.year = year
        self.lifespan_years = lifespan_years
        self.transitions_table = self.make_transitions_table()
        self.transition_list: List[str] = []

    def make_transitions_table(self) -> Dict[StateTransition, NextState]:
        """
        This is an expensive method to execute, so just call it once during
        instantiation of a component.
        """
        transitions_table = {
            StateTransition(state="use", transition="landfilling"): NextState(
                state="landfill",
                lifespan_min=1000,
                lifespan_max=1000,
                state_entry_function=self.landfill,
                state_exit_function=self.leave_use,
            ),
        }

        return transitions_table

    @staticmethod
    def landfill(context, component, timestep: int) -> None:
        """
        Landfills a component material by incrementing the material in the
        landfill.

        The landfill process is special because there is no corresponding
        leave_landfill method since component materials never leave the
        landfill.

        This is a static method so it can be called by an arbitrary function
        during a SimPy process. Since it is a static method, it is not
        attached to any instance of the Component class, so the component
        must be passed explicitly.

        Parameters
        ----------
        context: Context
            The context in which this component lives. There is no type
            in the method signature to prevent a circular dependency.

        component: Component
            The component which is being landfilled.
        """
        print(f"Landfill process component {component.id}, timestep={timestep}")
        context.landfill_component_inventory.increment_quantity(
            item_name=component.type, quantity=1, timestep=timestep,
        )

    @staticmethod
    def use(context, component, timestep: int) -> None:
        """
        Makes a material enter the use phases from another state.

        This is a static method so it can be called by an arbitrary function
        during a SimPy process. Since it is a static method, it is not
        attached to any instance of the Component class, so the component
        must be passed explicitly.

        Parameters
        ----------
        context: Context
            The context in which this component lives. There is no type
            in the method signature to prevent a circular dependency.

        component: Component
            The component which is being landfilled.
        """
        print(f"Use process component {component.id}, timestep={timestep}")
        context.use_component_inventory.increment_quantity(
            item_name=component.type, quantity=1, timestep=timestep,
        )

    @staticmethod
    def leave_use(context, component, timestep: int):
        """
        This method decrements the use inventory when a component material leaves use.

        This is a static method so it can be called by an arbitrary function
        during a SimPy process. Since it is a static method, it is not
        attached to any instance of the Component class, so the component
        must be passed explicitly.

        Parameters
        ----------
        context: Context
            The conext in which this component lives

        component: Component
            The component which is being taken out of use.
        """
        print(
            f"Leave use process component_material {component.id}, timestep={timestep}"
        )
        context.use_component_inventory.increment_quantity(
            item_name=component.type, quantity=-1, timestep=timestep,
        )

    def begin_life(self, env):
        begin_timestep = (
            self.year - self.context.min_year
        ) / self.context.years_per_timestep
        yield env.timeout(begin_timestep)
        print(
            f"yr: {self.year}, ts: {begin_timestep}. {self.kind} {self.id} beginning life."
        )
        self.state = "use"
        self.transition_list.append("using")
        env.process(self.eol_process(env))

    def eol_process(self, env):
        # while True:
        #     yield env.timeout(self.lifespan_years / self.context.years_per_timestep)
        #     year = self.context.timesteps_to_years(env.now)
        #     print(f"yr: {year}, ts: {env.now}. {self.kind} {self.id} ending use.")
        yield env.timeout(self.lifespan_years / self.context.years_per_timestep)
        year = self.context.timesteps_to_years(env.now)
        print(f"yr: {year}, ts: {env.now}. {self.kind} {self.id} ending use.")


class Context:
    def __init__(self):
        self.max_timesteps = 272
        self.min_year = 1980
        self.years_per_timestep = 0.25
        self.components: List[Component] = []
        self.env = simpy.Environment()

        self.landfill_component_inventory = Inventory(
            name="components landfill",
            possible_items=["nacelle", "blade", "tower", "foundation",],
            timesteps=self.max_timesteps,
            quantity_unit="unit",
            can_be_negative=False,
        )

        self.use_component_inventory = Inventory(
            name="components use",
            possible_items=["nacelle", "blade", "tower", "foundation",],
            timesteps=self.max_timesteps,
            quantity_unit="unit",
            can_be_negative=False,
        )

    def years_to_timesteps(self, year: float):
        return year / self.years_per_timestep

    def timesteps_to_years(self, timesteps: int):
        return self.years_per_timestep * timesteps + self.min_year

    def populate(self, df: pd.DataFrame, lifespan_fns: Dict[str, Callable[[], float]]):
        for _, row in df.iterrows():
            component = Component(
                kind=row["kind"],
                xlat=row["xlat"],
                ylon=row["ylon"],
                year=row["year"],
                context=self,
                parent_turbine_id=0,
                lifespan_years=lifespan_fns[row["kind"]](),
            )
            self.env.process(component.begin_life(self.env))
            self.components.append(component)

    def run(self):
        self.env.run(until=self.max_timesteps)
