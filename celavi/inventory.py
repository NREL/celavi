from typing import Dict, List
import numpy as np
import pandas as pd


class FacilityInventory:
    def __init__(
        self,
        facility_id: int,
        facility_type: str,
        step: str,
        possible_items: List[str],
        timesteps: int,
        quantity_unit: str = "tonne",
        can_be_negative: bool = False,
    ):
        """
        The inventory class holds an inventory of materials and quantities
        for a landfill, virgin material extraction, or recycled material
        availability

        Parameters
        ----------
        facility_id: int
            The id of the facility in the locations table

        facility_type: str
            The type of the facility from the locations table.

        step: str
            The step that is held by this inventory.

        quantity_unit: str
            The unit in which the quantity is recorded.

        possible_items: List[str]
            A list of strings (e.g., "Nacelle Aluminum") that represent all
            possible component materials that may be stored in this inventory

        timesteps: int
            The number of discrete timesteps in the simulation that this
            inventory will hold.

        can_be_negative: bool
            True if the quantity in this inventory can be negative. If False,
            the quantity must always be positive.

        Other instance variables
        ------------------------
        self.component_materials: Dict[str, float]
            The cumulative amount of component materials over the entire
            lifetime of the simulation.

        self.component_materials_deposits: List[Dict[str, float]]
            The history of the deposits and withdrawals from this
            inventory. These are instantaneous, not cumulative, values.
        """
        self.step = step
        self.facility_id = facility_id
        self.facility_type = facility_type
        self.can_be_negative = can_be_negative
        self.quantity_unit = quantity_unit
        self.component_materials: Dict[str, float] = {}
        for possible_item in possible_items:
            self.component_materials[possible_item] = 0.0

        # Populate the deposit and withdrawal history with copies of the
        # initialized dictionary from above that has all values set to 0.0
        self.transactions: List[Dict[str, float]] = []
        for _ in range(int(timesteps)):
            self.transactions.append(self.component_materials.copy())

        # Populate the deposit-only history with copies of the
        # initialized dictionary from above that has all values set to 0.0
        self.input_transactions: List[Dict[str, float]] = []
        for _ in range(int(timesteps)):
            self.input_transactions.append(self.component_materials.copy())

    def increment_quantity(
        self, item_name: str, quantity: float, timestep: int
    ) -> float:
        """
        Changes the material quantity in this inventory.

        For virgin material extractions, the quantity should be negative
        to indicate a withdrawal.

        For landfill additions, the quantity should be positive to
        indicate a deposit of material.

        For recycling, the quantity can either be positive or negative,
        depending on if there is an increase in supply or a decrease in
        supply through consumption.

        Parameters
        ----------
        item_name: str
            The material being deposited or withdrawn

        quantity: int
            The quantity of the material, either positive or negative.

        timestep: int
            The timestep of this deposit or withdrawal or deposit
            (depending on the sign the quantity)

        Returns
        -------
        int
            The new quantity of the material.
        """
        # Place this transaction in the history
        timestep = int(timestep)
        self.transactions[timestep][item_name] += quantity

        # Only if the quantity is an input, attach the transaction to the
        # input transactions table
        if quantity > 0:
            self.input_transactions[timestep][item_name] += quantity

        # Now increment the inventory
        self.component_materials[item_name] += quantity

        if (
            round(self.component_materials[item_name], 2) < 0
            and not self.can_be_negative
        ):
            raise ValueError(
                f"Inventory {self.name} cannot go negative. {self.component_materials[item_name]}"
            )

        # Return the new level
        return self.component_materials[item_name]

    @property
    def cumulative_history(self) -> pd.DataFrame:
        """
        Calculate the cumulative level of a facility inventory over all its
        transactions.

        Returns
        -------
        pd.DataFrame
            The cumulative history of all the transactions of the component
            materials.
        """
        component_materials_history_df = pd.DataFrame(self.transactions)
        cumulative_history = pd.DataFrame()
        for column in component_materials_history_df.columns:
            cumulative_history[column] = np.cumsum(
                component_materials_history_df[column].values
            )
        return cumulative_history

    @property
    def cumulative_input_history(self) -> pd.DataFrame:
        """
        Calculate the cumulative input quantities of a facility inventory over
        all its input transactions.

        Returns
        -------
        pd.DataFrame
            The cumulative history of all the transactions of the component
            materials.
        """
        component_materials_history_df = pd.DataFrame(self.input_transactions)
        cumulative_history = pd.DataFrame()
        for column in component_materials_history_df.columns:
            cumulative_history[column] = np.cumsum(
                component_materials_history_df[column].values
            )
        return cumulative_history

    @property
    def transaction_history(self) -> pd.DataFrame:
        """
        Because this method instantiates a DataFrame, it should be called
        sparingly, as this is a resource consuming procedure.

        Returns
        -------
        pd.DataFrame
            The history of transactions in dataframe form.
        """
        transactions_df = pd.DataFrame(self.transactions)
        return transactions_df

    @property
    def input_transaction_history(self) -> pd.DataFrame:
        """

        Returns
        -------

        """
        input_transactions_df = pd.DataFrame(self.input_transactions)
        return input_transactions_df
