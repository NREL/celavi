import numpy as np
import scipy.stats as st
import warnings


class CostMethods:
    """
    Functions for calculating processing and transportation costs throughout
    the supply chain. The methods in this Class must be re-written to
    correspond to each case study; in general, these methods are not reusable
    across different supply chains or technologies.


    """

    def __init__(self, seed, run):
        """
        Provide a random number generator to all uncertain CostMethods.

        """
        self.seed = seed
        self.run = run
        # @TODO Check that all uncertainty types are random, array, or blank
        # @TODO Run length check on all cost models with array uncertainty type


    @staticmethod
    def zero_method(path_dict):
        """
        Cost method that returns a cost of zero under all circumstances.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes.

        Returns
        -------
        float
            Use this method for any processing step or transportation edge with
            no associated cost.
        """
        return 0.0


    def landfilling(self, path_dict):
        """
        Linear tipping fee model based on historical national average 
        tipping fees.

        Parameters
        ----------
        path_dict : dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
        _fee : float
            Landfill tipping fee in USD/metric ton
        """
        _year = path_dict['year']
        _fee = 1.5921*_year - 3155.3 # deterministic national average
        if path_dict['cost_uncertainty']['landfilling']['uncertainty'] == 'random':
            _c = path_dict['cost_uncertainty']['landfilling']['c']
            _loc = path_dict['cost_uncertainty']['landfilling']['loc']
            _scale = path_dict['cost_uncertainty']['landfilling']['scale']
            return st.triang.rvs(c=_c,loc=_loc*_fee,scale=_scale*_fee, random_state=self.seed)
        elif path_dict['cost_uncertainty']['landfilling']['uncertainty'] == 'array':
            # in post-2020 (last historical data point)
            if _year >= 2021:
                # use an array of parameter values from config
                # model run is the index
                # parse as float value (defaults to string)
                # @NOTE Way to avoid using eval?
                _m = eval(path_dict['cost_uncertainty']['landfilling']['m'][self.run])
                # fee model = point-slope form of a line
                return _m * (_year - 2020) + 59.23
            else:
                # if the year is 2020 or earlier, just return the historical model
                return _fee
        else:
            return _fee



    def rotor_teardown(self, path_dict):
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
        _cost = (42.6066109 * _year ** 2 -
                 170135.7518957 * _year +
                 169851728.663209) / _mass

        if path_dict['cost_uncertainty']['rotor_teardown']:
            _c = path_dict['cost_uncertainty']['rotor_teardown']['c']
            _loc = path_dict['cost_uncertainty']['rotor_teardown']['loc']
            _scale = path_dict['cost_uncertainty']['rotor_teardown']['scale']
            return st.triang.rvs(c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed)
        else:
            return _cost



    def segmenting(self, path_dict):
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
        _cost = 27.56
        if path_dict['cost_uncertainty']['segmenting']:
            _c = path_dict['cost_uncertainty']['segmenting']['c']
            _loc = path_dict['cost_uncertainty']['segmenting']['loc']
            _scale = path_dict['cost_uncertainty']['segmenting']['scale']
            return st.triang.rvs(c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed)
        else:
            return _cost



    def coarse_grinding_onsite(self, path_dict):
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

        _cost = _dict['initial cost'] * coarsegrind_learning

        if path_dict['cost_uncertainty']['coarse_grinding_onsite']:
            _c = path_dict['cost_uncertainty']['coarse_grinding_onsite']['c']
            _loc = path_dict['cost_uncertainty']['coarse_grinding_onsite']['loc']
            _scale = path_dict['cost_uncertainty']['coarse_grinding_onsite']['scale']
            return st.triang.rvs(c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed)
        else:
            return _cost



    def coarse_grinding(self, path_dict):
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

        _cost = _dict['initial cost'] * coarsegrind_learning

        if path_dict['cost_uncertainty']['coarse_grinding']:
            _c = path_dict['cost_uncertainty']['coarse_grinding']['c']
            _loc = path_dict['cost_uncertainty']['coarse_grinding']['loc']
            _scale = path_dict['cost_uncertainty']['coarse_grinding']['scale']
            return st.triang.rvs(c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed)
        else:
            return _cost



    def fine_grinding(self, path_dict):
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
        _year = path_dict['year']

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
        _landfill = _loss * 8.0E-30 * np.exp(0.0352 * _year)

        if path_dict['cost_uncertainty']['fine_grinding']:
            # Parameters for fine grinding cost
            _c_fg = path_dict['cost_uncertainty']['fine_grinding']['c']
            _loc_fg = path_dict['cost_uncertainty']['fine_grinding']['loc']
            _scale_fg = path_dict['cost_uncertainty']['fine_grinding']['scale']
            # Parameters for landfilling cost
            _c_lf = path_dict['cost_uncertainty']['landfilling']['c']
            _loc_lf = path_dict['cost_uncertainty']['landfilling']['loc']
            _scale_lf = path_dict['cost_uncertainty']['landfilling']['scale']
            # Parameters for fine grinding revenue
            _c_fgr = path_dict['cost_uncertainty']['fine_grinding_revenue']['c']
            _loc_fgr = path_dict['cost_uncertainty']['fine_grinding_revenue']['loc']
            _scale_fgr = path_dict['cost_uncertainty']['fine_grinding_revenue']['scale']

            _cost_unc = st.triang.rvs(
                c=_c_fg, loc=_loc_fg * _cost, scale=_scale_fg * _cost, random_state=self.seed
            ) + st.triang.rvs(
                c=_c_lf, loc=_loc_lf * _landfill, scale=_scale_lf * _landfill, random_state=self.seed
            ) - st.triang.rvs(
                c=_c_fgr, loc=_loc_fgr * _revenue, scale=_scale_fgr * _revenue, random_state=self.seed
            )

            return _cost_unc
        else:
            # returns processing cost, reduced by learning, minus revenue which
            # stays constant over time (USD/metric ton)
            return _cost + _landfill - _revenue



    def coprocessing(self, path_dict):
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

        _revenue = 10.37
        if path_dict['cost_uncertainty']['coprocessing']:
            _c = path_dict['cost_uncertainty']['coprocessing']['c']
            _loc = path_dict['cost_uncertainty']['coprocessing']['loc']
            _scale = path_dict['cost_uncertainty']['coprocessing']['scale']
            return -1.0*st.triang.rvs(c=_c, loc = _loc*_revenue, scale=_scale*_revenue, random_state=self.seed)
        else:
            return -1.0 * _revenue



    def segment_transpo(self, path_dict):
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

            if path_dict['cost_uncertainty']['segment_transpo']:
                _c = path_dict['cost_uncertainty']['segment_transpo']['c']
                _loc = path_dict['cost_uncertainty']['segment_transpo']['loc']
                _scale = path_dict['cost_uncertainty']['segment_transpo']['scale']
                return st.triang.rvs(
                    c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed
                ) * _vkmt / _mass
            else:
                return _cost * _vkmt / _mass



    def shred_transpo(self, path_dict):
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
        _year = path_dict['year']
        if _vkmt is None:
            return 0.0
        else:
            _cost = 0.0011221 * _year - 2.1912399

            if path_dict['cost_uncertainty']['shred_transpo']:
                _c = path_dict['cost_uncertainty']['shred_transpo']['c']
                _loc = path_dict['cost_uncertainty']['shred_transpo']['loc']
                _scale = path_dict['cost_uncertainty']['shred_transpo']['scale']
                return st.triang.rvs(
                    c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed
                ) * _vkmt
            else:
                return _cost * _vkmt



    def manufacturing(self, path_dict):
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
        _cost = 11440.0

        if path_dict['cost_uncertainty']['manufacturing']:
            _c = path_dict['cost_uncertainty']['manufacturing']['c']
            _loc = path_dict['cost_uncertainty']['manufacturing']['loc']
            _scale = path_dict['cost_uncertainty']['manufacturing']['scale']
            return st.triang.rvs(c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed)
        else:
            return _cost



    def blade_transpo(self, path_dict):
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

            if path_dict['cost_uncertainty']['blade_transpo']:
                _c = path_dict['cost_uncertainty']['blade_transpo']['c']
                _loc = path_dict['cost_uncertainty']['blade_transpo']['loc']
                _scale = path_dict['cost_uncertainty']['blade_transpo']['scale']
                return st.triang.rvs(
                    c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed
                ) * _vkmt / _mass
            else:
                return _cost * _vkmt / _mass
