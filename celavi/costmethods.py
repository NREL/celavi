import pandas as pd
import numpy as np
import warnings

class CostMethods:
    """

    """

    def __init__(self,
                 step_costs_file : str = '../celavi-data/inputs/step_costs.csv',
                 transpo_edges_file : str = '../celavi-data/inputs/transpo_edges.csv'):
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

        self.step_costs = pd.read_csv(step_costs_file)
        self.transpo_edges = pd.read_csv(transpo_edges_file)


    @staticmethod
    def zero_method(**kwargs):
        """
        Cost method that returns a cost of zero under all circumstances.

        Keyword Arguments
        -----------------
        None

        Returns
        -------
        float
            Use this method for any processing step or transportation edge with
            no associated cost
        """
        return 0.0


    @staticmethod
    def landfilling(**kwargs):
        """
        Tipping fee model based on national average tipping fees and year-over-
        year percent increase of 3.5%.

        Keyword Arguments
        -----------------
        year
            Model year obtained from DES model (timestep converted to year)

        Returns
        -------
        _fee
            Landfill tipping fee in USD/metric ton
        """
        _year = kwargs['year']
        _fee = 8.0E-30 * np.exp(0.0352 * _year)
        return _fee


    @staticmethod
    def rotor_teardown(**kwargs):
        """
        Cost (USD/metric ton) of removing one metric ton of blade from the
        turbine. The cost of removing a single blade is calculated as one-third
        the rotor teardown cost, and this cost is divided by blade mass to
        calculate rotor teardown per metric ton of blade material.

        Keyword Arguments
        -----------------
        year
            Model year obtained from DES model (timestep converted to year)

        component_mass
            Average blade mass obtained from DES model

        Returns
        -------
        _cost
            Cost in USD per metric ton of removing a blade from an
            in-use turbine. Equivalent to 1/3 the rotor teardown cost divided
            by the blade mass.
        """
        _year = kwargs['year']
        _mass = kwargs['component_mass']
        _cost = 42.6066109 * _year ** 2 - 170135.7518957 * _year +\
                169851728.663209
        return _cost / _mass


    @staticmethod
    def segmenting(**kwargs):
        """
        Cost method for blade segmenting into 30m sections performed on-site at
        the wind power plant.

        Keyword Arguments
        -----------------
        None

        Returns
        -------
            Cost (USD/metric ton) of cutting a turbine blade into 30-m segments
        """
        return 27.56


    @staticmethod
    def coarse_grinding_onsite(**kwargs):
        """
        Cost method for coarsely grinding turbine blades onsite at a wind
        power plant. This calculation uses industrial learning-by-doing
        to gradually reduce costs over time.

        Keyword Arguments
        -----------------
        coarsegrind_cumul
            Current cumulative production (blade mass processed through coarse
            grinding)

        coarsegrind_cumul_initial
            Cumulative production when the model run begins. Value is provided
            on CostGraph instantiation and cannot be zero.

        coarsegrind_initial_cost
            Cost in USD/metric ton of coarse grinding when the model run
            begins.

        coarsegrind_learnrate
            Rate of cost reduction via learning-by-doing for coarse grinding.
            Must be negative. Unitless.

        Returns
        -------
            Current cost of coarse grinding one metric ton of segmented blade
            material onsite at a wind power plant.
        """
        # If no updated cumulative production value is passed in, use the
        # initial value from CostGraph instantiation

        if 'coarsegrind_cumul' in kwargs:
            coarsegrind_cumul = max(1, kwargs['coarsegrind_cumul'])
        else:
            coarsegrind_cumul = kwargs['coarsegrind_cumul_initial']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        coarsegrind_learning = coarsegrind_cumul ** kwargs['coarsegrind_learnrate']

        return kwargs['coarsegrind_initial_cost'] * coarsegrind_learning


    @staticmethod
    def coarse_grinding(**kwargs):
        """
        Cost method for coarsely grinding turbine blades at a mechanical
        recycling facility. This calculation uses industrial learning-by-doing
        to gradually reduce costs over time.

        Keyword Arguments
        -----------------
        coarsegrind_cumul
            Current cumulative production (blade mass processed through coarse
            grinding)

        coarsegrind_cumul_initial
            Cumulative production when the model run begins. Value is provided
            on CostGraph instantiation and cannot be zero.

        coarsegrind_initial_cost
            Cost in USD/metric ton of coarse grinding when the model run
            begins.

        coarsegrind_learnrate
            Rate of cost reduction via learning-by-doing for coarse grinding.
            Must be negative. Unitless.

        Returns
        -------
            Current cost of coarse grinding one metric ton of segmented blade
            material in a mechanical recycling facility.
        """

        # If no updated cumulative production value is passed in, use the
        # initial value from CostGraph instantiation

        if 'coarsegrind_cumul' in kwargs:
            coarsegrind_cumul = max(1, kwargs['coarsegrind_cumul'])
        else:
            coarsegrind_cumul = kwargs['coarsegrind_cumul_initial']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        coarsegrind_learning = coarsegrind_cumul ** kwargs['coarsegrind_learnrate']

        return kwargs['coarsegrind_initial_cost'] * coarsegrind_learning


    @staticmethod
    def fine_grinding(**kwargs):
        """
        Cost method for finely grinding turbine blades at a mechanical
        recycling facility. This calculation uses industrial learning-by-doing
        to gradually reduce costs over time.

        Keyword Arguments
        -----------------
        finegrind_cumul
            Current cumulative production (blade mass processed through fine
            grinding)

        finegrind_cumul_initial
            Cumulative production when the model run begins. Value is provided
            on CostGraph instantiation and cannot be zero.

        finegrind_initial_cost
            Cost in USD/metric ton of fine grinding when the model run
            begins.

        finegrind_revenue
            Revenue in USD/metric ton from sales of finely ground blade
            material. Further use of material is outside the scope of this
            study.

        finegrind_material_loss
            Fraction of total blade material lost during fine grinding.
            Unitless. This is the amount of finely ground blade material that
            must be landfilled.

        finegrind_learnrate
            Rate of cost reduction via learning-by-doing for fine grinding.
            Must be negative. Unitless.

        year
            Model year provided by DES

        Returns
        -------
            Net cost (process cost plus landfilling cost minus revenue) of fine
            grinding one metric ton of blade material at a mechanical recycling
            facility and disposing of material losses in a landfill.
        """

        # If no updated cumulative production value is passed in, use the
        # initial value from CostGraph instantiation
        if 'finegrind_cumul' in kwargs:
            _finegrind_cumul = max(1, kwargs['finegrind_cumul'])
        else:
            _finegrind_cumul = kwargs['finegrind_cumul_initial']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        _finegrind_learning = _finegrind_cumul ** kwargs['finegrind_learnrate']

        # get fine grinding material loss
        _loss = kwargs['finegrind_material_loss']

        # calculate process cost based on total input mass (no material loss
        # yet) (USD/metric ton)
        _cost = kwargs['finegrind_initial_cost'] * _finegrind_learning

        # calculate revenue based on total output mass accounting for material
        # loss (USD/metric ton)
        _revenue = (1 - _loss) * kwargs['finegrind_revenue']

        # calculate additional cost of landfilling the lost material
        # (USD/metric ton)
        # see the landfilling method - this cost model is identical
        _landfill = _loss * 3.0E-29 * np.exp(0.0344 * kwargs['year'])

        # returns processing cost, reduced by learning, minus revenue which
        # stays constant over time (USD/metric ton)
        return _cost + _landfill - _revenue



    @staticmethod
    def coprocessing(**kwargs):
        """
        Cost method that calculates revenue from sale of coarsely-ground blade
        material to cement co-processing plant.

        Returns
        -------
            Revenue (USD/metric ton) from selling 1 metric ton of ground blade
             to cement co-processing plant
        """
        return -10.37


    @staticmethod
    def segment_transpo(**kwargs):
        """
        Calculate segment transportation cost in USD/metric ton

        Keyword Arguments
        -----------------
        vkmt
            Distance traveled by blade segment. Unit: vehicle-kilometer

        component_mass
            Average blade mass in the current model year. Unit: metric tons

        year
            Current model year.

        Returns
        -------
            Cost of transporting one segmented blade one kilometer. Units:
            USD/blade
        """
        _vkmt = kwargs['vkmt']
        _mass = kwargs['component_mass']
        _year = kwargs['year']

        if np.isnan(_vkmt) or np.isnan(_mass):
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


    @staticmethod
    def shred_transpo(**kwargs):
        """
        Cost method for calculating shredded blade transportation costs (truck)
        in USD/metric ton.

        Keyword Arguments
        -----------------
        vkmt
            Distance traveled in kilometers

        Returns
        -------
            Cost of transporting 1 metric ton of shredded blade material by
            one kilometer. Units: USD/metric ton.
        """
        _vkmt = kwargs['vkmt']
        if np.isnan(_vkmt):
            return 0.0
        else:
            return 0.08 * _vkmt


    @staticmethod
    def finegrind_shred_transpo(**kwargs):
        """
        Cost method for calculating lost material transportation costs (truck)
        in USD/metric ton by accounting for the fraction of material lost from
        the fine grinding step. @note Assume that the transportation to
        landfill is one-tenth the distance to the next use facility.

        Keyword Arguments
        -----------------
        vkmt
            Distance traveled in kilometers

        finegrind_material_loss
            Fraction of material lost. Used to scale down the distance.

        Returns
        -------
            Cost of transporting material_loss metric ton of shredded blade
            material by one kilometer. Units: USD/metric ton.
        """
        _vkmt = kwargs['vkmt']
        _loss = kwargs['finegrind_material_loss']
        if np.isnan(_vkmt):
            return 0.0
        else:
            return 0.08 * (1 - _loss) * _vkmt

    @staticmethod
    def finegrind_loss_transpo(**kwargs):
        """

        Keyword Arguments
        ----------
        vkmt
            Distance traveled in kilometers

        finegrind_material_loss
            Fraction of material lost. Used to scale down the distance.

        Returns
        -------

        """
        _vkmt = kwargs['vkmt']
        _loss = kwargs['finegrind_material_loss']
        if np.isnan(_vkmt):
            return 0.0
        else:
            return 0.08 * _loss * _vkmt


    @staticmethod
    def manufacturing(**kwargs):
        """
        Cost method for calculating blade manufacturing costs in USD/metric
        ton. Data sourced from Murray et al. (2019), a techno-economic analysis
        of a thermoplastic blade compared to the standard thermoset epoxy blade
        using a 61.5m blade as basis. The baseline cost for the thermoset blade
        ($11.44/kg) is used here, converted to USD / metric ton.


        Keyword Arguments
        -----------------
        None

        Parameters
        ----------
        None

        Returns
        -------
            Cost of manufacturing 1 metric ton of new turbine blade.

        """
        return 11440.0


    @staticmethod
    def blade_transpo(**kwargs):
        """
        @TODO Check for updated blade transportation costs.

        Cost of transporting 1 metric ton of complete wind blade by 1 km.
        Currently the segment transportation cost is used as proxy.

        Keyword Arguments
        -----------------
        vkmt
            Distance traveled by blade segment. Unit: vehicle-kilometer

        component_mass
            Average blade mass in the current model year. Unit: metric tons

        year
            Current model year.

        Returns
        -------
            Cost of transporting one segmented blade one kilometer. Units:
            USD/blade
        """
        _vkmt = kwargs['vkmt']
        _mass = kwargs['component_mass']
        _year = kwargs['year']

        if np.isnan(_vkmt) or np.isnan(_mass):
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
