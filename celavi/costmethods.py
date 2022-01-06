# TODO: Add a short module docstring above the code to:
#  1) provide authors, date of creation
#  2) give a high level description (2-3 lines) of what the module does
#  3) write any other relevant information

import pandas as pd
import numpy as np
import warnings


class CostMethods:
    """

    """

    def __init__(self,
                 step_costs_file: str = '../celavi-data/inputs/step_costs.csv',
                 transpo_edges_file: str = '../celavi-data/inputs/transpo_edges.csv'):
        """

        Parameters
        ----------
        step_costs_file
            file listing processing steps and cost calculation methods by
            facility type
        transpo_edges_file
            file listing inter-facility edges and transpo cost calculation
            methods

        Returns
        -------
        None
        """
        # TODO: it seems that the two variables below are not used anywhere
        #  (whenever the data from those two csv files are needed (e.g., in
        #  the costgraph module) they are directly read into Pandas DataFrames
        #  using the file locations provided in the config file. Consider
        #  removing the two lines below and the few lines above.
        self.step_costs = pd.read_csv(step_costs_file)
        self.transpo_edges = pd.read_csv(transpo_edges_file)


    @staticmethod
    def zero_method(path_dict):
        """
        Cost method that returns a cost of zero under all circumstances.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
        float
            Use this method for any processing step or transportation edge with
            no associated cost
        """
        return 0.0


    @staticmethod
    def landfilling(path_dict):
        """
        Tipping fee model based on national average tipping fees and year-over-
        year percent increase of 3.5%.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
        _fee
            Landfill tipping fee in USD/metric ton
        """
        _year = path_dict['year']
        _fee = 8.0E-30 * np.exp(0.0352 * _year)
        return _fee


    @staticmethod
    def rotor_teardown(path_dict):
        """
        Cost (USD/metric ton) of removing one metric ton of blade from the
        turbine. The cost of removing a single blade is calculated as one-third
        the rotor teardown cost, and this cost is divided by blade mass to
        calculate rotor teardown per metric ton of blade material.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
        _cost
            Cost in USD per metric ton of removing a blade from an
            in-use turbine. Equivalent to 1/3 the rotor teardown cost divided
            by the blade mass.
        """

        _year = path_dict['year']
        _mass = path_dict['component mass']
        _cost = 42.6066109 * _year ** 2 - 170135.7518957 * _year +\
                169851728.663209
        return _cost / _mass


    @staticmethod
    def segmenting(path_dict):
        """
        Cost method for blade segmenting into 30m sections performed on-site at
        the wind power plant.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Cost (USD/metric ton) of cutting a turbine blade into 30-m segments
        """
        # TODO: Input parameters should be used instead of magic numbers or
        #  at least those numbers should be stored in variables.
        #  Those variables could have default values set up in the init method
        #  of the CostMethods class (this way they may not be modified by users
        #  but the code is better organized).
        return 27.56


    # TODO: Consider having one general method that would compute learning by
    #  doing based on 4 inputs: cumul_initial, cumul, learning_rate, and
    #  init_cost. And  based on three steps i) determine cumul_blade,
    #  ii) compute learning, iii) update costs. The general method could then
    #  be called in the coarse_grinding_onsite, coarse_grinding, and
    #  fine_grinding methods with different inputs.
    @staticmethod
    def coarse_grinding_onsite(path_dict):
        """
        Cost method for coarsely grinding turbine blades onsite at a wind
        power plant. This calculation uses industrial learning-by-doing
        to gradually reduce costs over time.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Current cost of coarse grinding one metric ton of segmented blade
            material onsite at a wind power plant.
        """
        _dict = path_dict['learning']['coarse grinding']

        # If the "cumul" value is None, then there has been no processing
        # through coarse grinding and the initial cumul value from the config
        # file is used

        if _dict['cumul'] is not None:
            coarsegrind_cumul = max(
                1,
                _dict['cumul']
            )
        else:
            coarsegrind_cumul = _dict['initial cumul']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        coarsegrind_learning = coarsegrind_cumul ** _dict['learn rate']

        return _dict['initial cost'] * coarsegrind_learning


    @staticmethod
    def coarse_grinding(path_dict):
        """
        Cost method for coarsely grinding turbine blades at a mechanical
        recycling facility. This calculation uses industrial learning-by-doing
        to gradually reduce costs over time.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Current cost of coarse grinding one metric ton of segmented blade
            material in a mechanical recycling facility.
        """
        _dict = path_dict['learning']['coarse grinding']

        # If the "cumul" value is None, then there has been no processing
        # through coarse grinding and the initial cumul value from the config
        # file is used

        if _dict['cumul'] is not None:
            coarsegrind_cumul = max(
                1,
                _dict['cumul']
            )
        else:
            coarsegrind_cumul = _dict['initial cumul']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        coarsegrind_learning = coarsegrind_cumul ** _dict['learn rate']

        return _dict['initial cost'] * coarsegrind_learning


    @staticmethod
    def fine_grinding(path_dict):
        """
        Cost method for finely grinding turbine blades at a mechanical
        recycling facility. This calculation uses industrial learning-by-doing
        to gradually reduce costs over time.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Net cost (process cost plus landfilling cost minus revenue) of fine
            grinding one metric ton of blade material at a mechanical recycling
            facility and disposing of material losses in a landfill.
        """
        _dict = path_dict['learning']['fine grinding']
        _loss = path_dict['path_split']['fine grinding']['fraction']

        # If the "cumul" value is None, then there has been no processing
        # through fine grinding and the initial cumul value from the config
        # file is used
        if _dict['cumul'] is not None:
            _finegrind_cumul = max(
                1,
                _dict['cumul']
            )
        else:
            _finegrind_cumul = _dict['initial cumul']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        _finegrind_learning = _finegrind_cumul ** _dict['learn rate']

        # calculate process cost based on total input mass (no material loss
        # yet) (USD/metric ton)
        _cost = _dict['initial cost'] * _finegrind_learning

        # calculate revenue based on total output mass accounting for material
        # loss (USD/metric ton)
        _revenue = (1 - _loss) * _dict['revenue']

        # calculate additional cost of landfilling the lost material
        # (USD/metric ton)
        # see the landfilling method - this cost model is identical
        _landfill = _loss * 3.0E-29 * np.exp(0.0344 * path_dict['year'])

        # returns processing cost, reduced by learning, minus revenue which
        # stays constant over time (USD/metric ton)
        return _cost + _landfill - _revenue



    @staticmethod
    def coprocessing(path_dict):
        """
        Cost method that calculates revenue from sale of coarsely-ground blade
        material to cement co-processing plant.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Revenue (USD/metric ton) from selling 1 metric ton of ground blade
             to cement co-processing plant
        """
        # TODO: Input parameters should be used instead of magic numbers or
        #  at least those numbers should be stored in variables.
        #  Those variables could have default values set up in the init method
        #  of the CostMethods class (this way they may not be modified by users
        #  but the code is better organized).
        return -10.37


    @staticmethod
    def segment_transpo(path_dict):
        """
        Calculate segment transportation cost in USD/metric ton

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Cost of transporting one segmented blade one kilometer. Units:
            USD/blade
        """
        _vkmt = path_dict['vkmt']
        _mass = path_dict['component mass']
        _year = path_dict['year']

        if _vkmt is None or _mass is None:
            return 0.0
        else:
            if _year < 2001.0 or 2002.0 <= _year < 2003.0:
                _cost = 4.35
            elif 2001.0 <= _year < 2002.0 or 2003.0 <= _year < 2019.0:
                _cost = 8.70
            elif 2019.0 <= _year < 2031.0:
                _cost = 13.05
            elif 2031.0 <= _year < 2044.0:
                _cost = 17.40
            elif 2044.0 <= _year <= 2050.0:
                _cost = 21.75
            else:
                warnings.warn(
                    'Year out of range for segment transport; setting cost = 17.40')
                _cost = 17.40

            return _cost * _vkmt / _mass


    # TODO: Consider having one general method that would compute transport
    #  costs based on 3 inputs: modifier, distance (_vkmt), and costs (0.08).
    #  And  based on the current code with "return costs * modifier * _vkmt"
    #  The general method could then be called in the shred_transpo,
    #  finegrind_shred_transpo, and finegrind_loss_transpo, and methods with
    #  different inputs.
    @staticmethod
    def shred_transpo(path_dict):
        """
        Cost method for calculating shredded blade transportation costs (truck)
        in USD/metric ton.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Cost of transporting 1 metric ton of shredded blade material by
            one kilometer. Units: USD/metric ton.
        """
        _vkmt = path_dict['vkmt']
        if _vkmt is None:
            return 0.0
        else:
            return 0.08 * _vkmt


    @staticmethod
    def finegrind_shred_transpo(path_dict):
        """
        Cost method for calculating lost material transportation costs (truck)
        in USD/metric ton by accounting for the fraction of material lost from
        the fine grinding step.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Cost of transporting material loss metric ton of shredded blade
            material by one kilometer. Units: USD/metric ton.
        """
        _vkmt = path_dict['vkmt']
        _loss = path_dict['path_split']['fine grinding']['fraction']
        if np.isnan(_vkmt):
            return 0.0
        else:
            return 0.08 * (1 - _loss) * _vkmt

    @staticmethod
    def finegrind_loss_transpo(path_dict):
        """

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------

        """
        _vkmt = path_dict['vkmt']
        _loss = path_dict['path_split']['fine grinding']['fraction']
        if np.isnan(_vkmt):
            return 0.0
        else:
            return 0.08 * _loss * _vkmt


    @staticmethod
    def manufacturing(path_dict):
        """
        Cost method for calculating blade manufacturing costs in USD/metric
        ton. Data sourced from Murray et al. (2019), a techno-economic analysis
        of a thermoplastic blade compared to the standard thermoset epoxy blade
        using a 61.5m blade as basis. The baseline cost for the thermoset blade
        ($11.44/kg) is used here, converted to USD / metric ton.


        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Cost of manufacturing 1 metric ton of new turbine blade.

        """
        # TODO: Input parameters should be used instead of magic numbers or
        #  at least those numbers should be stored in variables.
        #  Those variables could have default values set up in the init method
        #  of the CostMethods class (this way they may not be modified by users
        #  but the code is better organized).
        return 11440.0


    @staticmethod
    def blade_transpo(path_dict):
        """
        Cost of transporting 1 metric ton of complete wind blade by 1 km.
        Currently the segment transportation cost is used as proxy.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Cost of transporting one segmented blade one kilometer. Units:
            USD/blade
        """
        _vkmt = path_dict['vkmt']
        _mass = path_dict['component mass']
        _year = path_dict['year']

        if _vkmt is None or _mass is None:
            return 0.0
        else:
            if _year < 2001.0 or 2002.0 <= _year < 2003.0:
                _cost = 4.35
            elif 2001.0 <= _year < 2002.0 or 2003.0 <= _year < 2019.0:
                _cost = 8.70
            elif 2019.0 <= _year < 2031.0:
                _cost = 13.05
            elif 2031.0 <= _year < 2044.0:
                _cost = 17.40
            elif 2044.0 <= _year <= 2050.0:
                _cost = 21.75
            else:
                warnings.warn(
                    'Year out of range for blade transport; setting cost = 17.40')
                _cost = 17.40

            return _cost * _vkmt / _mass
