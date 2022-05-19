import numpy as np
import scipy.stats as st
import warnings

from celavi.scenario import apply_array_uncertainty

class CostMethods:
    """
    Functions for calculating processing and transportation costs throughout
    the supply chain. The methods in this Class must be re-written to
    correspond to each case study; in general, these methods are not reusable
    across different supply chains or technologies.


    """

    def __init__(self, seed, run):
        """
        Provide a random number generator and model run to all uncertain
        CostMethods.

        Parameters
        ----------
        seed : np.random.default_rng
            Instantiated random number generator for uncertainty analysis.

        run : int
            Model run number.
        """
        self.seed = seed
        self.run = run

    @staticmethod
    def zero_method(path_dict):
        """
        Cost method that returns a cost of zero under all circumstances.

        Parameters
        ----------
        path_dict : dict
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
        if path_dict['cost uncertainty']['landfilling']['uncertainty'] == 'random':
            _c = path_dict['cost uncertainty']['landfilling']['c']
            _loc = path_dict['cost uncertainty']['landfilling']['loc']
            _scale = path_dict['cost uncertainty']['landfilling']['scale']
            return st.triang.rvs(c=_c,loc=_loc*_fee,scale=_scale*_fee, random_state=self.seed)
        elif path_dict['cost uncertainty']['landfilling']['uncertainty'] == 'array':
            # in post-2020 (last historical data point)
            if _year >= 2021:
                # use an array of parameter values from config
                # model run is the index
                # parse as float value (defaults to string)
                _m = apply_array_uncertainty(
                    path_dict['cost uncertainty']['landfilling']['m'],
                    self.run
                    )
                _b = apply_array_uncertainty(
                    path_dict['cost uncertainty']['landfilling']['b'],
                    self.run
                    )
                # fee model = point-slope form of a line
                return _m * _year + _b
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
        path_dict : dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
        _cost : float
            Cost in USD per metric ton of removing a blade from an
            in-use turbine. Equivalent to 1/3 the rotor teardown cost divided
            by the blade mass.
        """

        _year = path_dict['year']
        _mass = path_dict['component mass']
        _cost = 1467.08 * _year - 2933875.40 # Linear national average cost model

        if path_dict['cost uncertainty']['rotor teardown']['uncertainty'] == 'random':
            _c = path_dict['cost uncertainty']['rotor teardown']['c']
            _loc = path_dict['cost uncertainty']['rotor teardown']['loc']
            _scale = path_dict['cost uncertainty']['rotor teardown']['scale']
            return st.triang.rvs(c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed) / _mass
        elif path_dict['cost uncertainty']['rotor teardown']['uncertainty'] == 'array':
            if _year >= 2021:
                _m = apply_array_uncertainty(
                    path_dict['cost uncertainty']['rotor teardown']['m'],
                    self.run
                    )
                _b = apply_array_uncertainty(
                    path_dict['cost uncertainty']['rotor teardown']['b'],
                    self.run
                    )
                return (_m * _year  + _b) / _mass
            else:
                return _cost / _mass
        else:
            return _cost / _mass



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
        _year = path_dict['year']

        if path_dict['cost uncertainty']['segmenting']['uncertainty'] == 'random':
            _c = path_dict['cost uncertainty']['segmenting']['c']
            _loc = path_dict['cost uncertainty']['segmenting']['loc']
            _scale = path_dict['cost uncertainty']['segmenting']['scale']
            return st.triang.rvs(c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed)
        elif path_dict['cost uncertainty']['segmenting']['uncertainty'] == 'array':
            if _year >= 2021:
                return apply_array_uncertainty(
                    path_dict['cost uncertainty']['segmenting']['b'],
                    self.run
                    )
            else:
                return _cost
        else:
            return _cost



    def coarse_grinding_onsite(self, path_dict):
        """
        Cost method for coarsely grinding turbine blades onsite at a wind
        power plant. This calculation uses industrial learning-by-doing
        to gradually reduce costs over time.
        
        The coarse grinding, coarse grinding onsite, and fine grinding cost models
        allow for array uncertainty in the initial cost or in the learning rate, 
        or random uncertainty in the actual cost which depends on cumulative mass
        processed. The logic for applying array uncertainty in these cost models
        is as follows: IF the uncertainty type is 'array' AND there are no
        parameter arrays in the cost uncertainty dictionary, THEN the learning rate
        must have an array of values which are applied separately to each model run.
        This logic is different from the uncertainty logic applied to all other cost
        models, which do not have parameters stored outside the cost uncertainty
        dictionary.

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
        _learn_dict = path_dict['learning']['coarse grinding']

        _learn_rate = apply_array_uncertainty(
            _learn_dict['learn rate'],
            self.run
            )        

        # Implement uncertainty on initial cost before applying learning model
        if path_dict['cost uncertainty']['coarse grinding onsite']['uncertainty'] == 'array':
            # Array uncertainty is applied to the initial cost or to the learning rate
            # (array uncertainty for the actual cost is implemented through the learning rate)
            _initial_cost = apply_array_uncertainty(
                path_dict['cost uncertainty']['coarse grinding onsite']['initial cost'],
                self.run
                )
        else:
            # Random uncertainty applied to the actual cost, or no uncertainty
            _initial_cost = path_dict['cost uncertainty']['coarse grinding onsite']['initial cost']

        # If the "cumul" value is None, then there has been no processing
        # through coarse grinding and the initial cumul value from the config
        # file is used

        if _learn_dict['cumul'] is not None:
            coarsegrind_cumul = max(
                1,
                _learn_dict['cumul']
            )
        else:
            coarsegrind_cumul = _learn_dict['initial cumul']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        coarsegrind_learning = coarsegrind_cumul ** _learn_rate

        _cost = _initial_cost * coarsegrind_learning

        if path_dict['cost uncertainty']['coarse grinding onsite']['uncertainty'] == 'random':
            _c = path_dict['cost uncertainty']['coarse grinding onsite']['c']
            _loc = path_dict['cost uncertainty']['coarse grinding onsite']['loc']
            _scale = path_dict['cost uncertainty']['coarse grinding onsite']['scale']
            return st.triang.rvs(c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed)
        else:
            return _cost



    def coarse_grinding(self, path_dict):
        """
        Cost method for coarsely grinding turbine blades at a mechanical
        recycling facility. This calculation uses industrial learning-by-doing
        to gradually reduce costs over time.

        The coarse grinding, coarse grinding onsite, and fine grinding cost models
        allow for array uncertainty in the initial cost or in the learning rate, 
        or random uncertainty in the actual cost which depends on cumulative mass
        processed. The logic for applying array uncertainty in these cost models
        is as follows: IF the uncertainty type is 'array' AND there are no
        parameter arrays in the cost uncertainty dictionary, THEN the learning rate
        must have an array of values which are applied separately to each model run.
        This logic is different from the uncertainty logic applied to all other cost
        models, which do not have parameters stored outside the cost uncertainty
        dictionary.

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
        _learn_dict = path_dict['learning']['coarse grinding']

        _learn_rate = apply_array_uncertainty(
            _learn_dict['learn rate'],
            self.run
            )

        # Implement uncertainty on initial cost before applying learning model
        if path_dict['cost uncertainty']['coarse grinding']['uncertainty'] == 'array':
            # Array uncertainty is applied to the initial cost or to the learning rate
            # (array uncertainty for the actual cost is implemented through the learning rate)
            _initial_cost = apply_array_uncertainty(
                path_dict['cost uncertainty']['coarse grinding']['initial cost'],
                self.run
                )
        else:
            # Random uncertainty applied to the actual cost, or no uncertainty
            _initial_cost = path_dict['cost uncertainty']['coarse grinding']['initial cost']

        # If the "cumul" value is None, then there has been no processing
        # through coarse grinding and the initial cumul value from the config
        # file is used

        if _learn_dict['cumul'] is not None:
            coarsegrind_cumul = max(
                1,
                _learn_dict['cumul']
            )
        else:
            coarsegrind_cumul = _learn_dict['initial cumul']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        coarsegrind_learning = coarsegrind_cumul ** _learn_rate

        _cost = _initial_cost * coarsegrind_learning

        if path_dict['cost uncertainty']['coarse grinding']['uncertainty'] == 'random':
            _c = path_dict['cost uncertainty']['coarse grinding']['c']
            _loc = path_dict['cost uncertainty']['coarse grinding']['loc']
            _scale = path_dict['cost uncertainty']['coarse grinding']['scale']
            return st.triang.rvs(c=_c, loc=_loc*_cost, scale=_scale*_cost, random_state=self.seed)
        else:
            return _cost



    def fine_grinding(self, path_dict):
        """
        Cost method for finely grinding turbine blades at a mechanical
        recycling facility. This calculation uses industrial learning-by-doing
        to gradually reduce costs over time.
        
        The coarse grinding, coarse grinding onsite, and fine grinding cost models
        allow for array uncertainty in the initial cost or in the learning rate, 
        or random uncertainty in the actual cost which depends on cumulative mass
        processed. The logic for applying array uncertainty in these cost models
        is as follows: IF the uncertainty type is 'array' AND there are no
        parameter arrays in the cost uncertainty dictionary, THEN the learning rate
        must have an array of values which are applied separately to each model run.
        This logic is different from the uncertainty logic applied to all other cost
        models, which do not have parameters stored outside the cost uncertainty
        dictionary.

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
        _learn_dict = path_dict['learning']['fine grinding']

        _learn_rate = apply_array_uncertainty(
            _learn_dict['learn rate'],
            self.run
            )

        # Implement uncertainty on parameters: array or random
        if path_dict['cost uncertainty']['fine grinding']['uncertainty'] == 'array':
            _loss = apply_array_uncertainty(
                path_dict['path_split']['fine grinding']['fraction'],
                self.run
            )
            _initial_cost = apply_array_uncertainty(
               path_dict['cost uncertainty']['fine grinding']['initial cost'],
               self.run
            )
            _revenue = apply_array_uncertainty(
                path_dict['cost uncertainty']['fine grinding']['revenue']['b'],
                self.run
            )
        elif path_dict['cost uncertainty']['fine grinding']['uncertainty'] == 'random':
            # Random uncertainty applies only to the revenue
            _loss = path_dict['path_split']['fine grinding']['fraction']
            _initial_cost = path_dict['cost uncertainty']['fine grinding']['initial cost']
            # Parameters for fine grinding revenue
            _c_fgr = path_dict['cost uncertainty']['fine grinding']['revenue']['c']
            _loc_fgr = path_dict['cost uncertainty']['fine grinding']['revenue']['loc']
            _scale_fgr = path_dict['cost uncertainty']['fine grinding']['revenue']['scale']
            _revenue = st.triang.rvs(
                c=_c_fgr,
                loc=_loc_fgr * path_dict['cost uncertainty']['fine grinding']['revenue']['b'],
                scale=_scale_fgr * path_dict['cost uncertainty']['fine grinding']['revenue']['b'],
                random_state=self.seed
            )            
        else:
            # No uncertainty
            _loss = path_dict['path_split']['fine grinding']['fraction']
            _initial_cost = path_dict['cost uncertainty']['fine grinding']['initial cost']
            _revenue = path_dict['cost uncertainty']['fine grinding']['revenue']['b']

        # If the "cumul" value is None, then there has been no processing
        # through fine grinding and the initial cumul value from the config
        # file is used
        if _learn_dict['cumul'] is not None:
            _finegrind_cumul = max(
                1,
                _learn_dict['cumul']
            )
        else:
            _finegrind_cumul = _learn_dict['initial cumul']
        
        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        _finegrind_learning = _finegrind_cumul ** _learn_rate

        # calculate process cost based on total input mass (no material loss
        # yet) (USD/metric ton)
        _cost = _initial_cost * _finegrind_learning

        # calculate revenue based on total output mass accounting for material
        # loss (USD/metric ton)
        _revenue = (1 - _loss) * _revenue
        
        # calculate additional cost of landfilling the lost material
        # (USD/metric ton)
        _landfill = self.landfilling(path_dict)

        if path_dict['cost uncertainty']['fine grinding']['uncertainty'] == 'random':
            # Parameters for fine grinding cost
            _c_fg = path_dict['cost uncertainty']['fine grinding']['actual cost']['c']
            _loc_fg = path_dict['cost uncertainty']['fine grinding']['actual cost']['loc']
            _scale_fg = path_dict['cost uncertainty']['fine grinding']['actual cost']['scale']
            _cost_unc = st.triang.rvs(
                c=_c_fg, loc=_loc_fg * _cost, scale=_scale_fg * _cost, random_state=self.seed
            ) + _landfill - _revenue
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
        if path_dict['cost uncertainty']['coprocessing']['uncertainty'] == 'random':
            _revenue = path_dict['cost uncertainty']['coprocessing']['b']
            _c = path_dict['cost uncertainty']['coprocessing']['c']
            _loc = path_dict['cost uncertainty']['coprocessing']['loc']
            _scale = path_dict['cost uncertainty']['coprocessing']['scale']
            return -1.0 * st.triang.rvs(c=_c, loc = _loc*_revenue, scale=_scale*_revenue, random_state=self.seed)
        elif path_dict['cost uncertainty']['coprocessing']['uncertainty'] == 'array':
            return -1.0 * apply_array_uncertainty(
                path_dict['cost uncertainty']['coprocessing']['b'],
                self.run
                )
        else:
            return -1.0 * path_dict['cost uncertainty']['coprocessing']['b']



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
                _cost = apply_array_uncertainty(
                    path_dict['cost uncertainty']['segment transpo']['cost 1'],
                    self.run
                )
            elif 2001.0 <= _year < 2002.0 or 2003.0 <= _year < 2019.0:
                _cost = apply_array_uncertainty(
                    path_dict['cost uncertainty']['segment transpo']['cost 2'],
                    self.run
                )
            elif 2019.0 <= _year < 2031.0:
                _cost = apply_array_uncertainty(
                    path_dict['cost uncertainty']['segment transpo']['cost 3'],
                    self.run
                )
            elif 2031.0 <= _year < 2044.0:
                _cost = apply_array_uncertainty(
                    path_dict['cost uncertainty']['segment transpo']['cost 4'],
                    self.run
                )
            elif 2044.0 <= _year <= 2050.0:
                _cost = apply_array_uncertainty(
                    path_dict['cost uncertainty']['segment transpo']['cost 5'],
                    self.run
                )
            else:
                warnings.warn(
                    'Year out of range for segment transport; using cost 4')
                _cost = apply_array_uncertainty(
                    path_dict['cost uncertainty']['segment transpo']['cost 4'],
                    self.run
                )

            if path_dict['cost uncertainty']['segment transpo']['uncertainty'] == 'random':
                _c = path_dict['cost uncertainty']['segment transpo']['c']
                _loc = path_dict['cost uncertainty']['segment transpo']['loc']
                _scale = path_dict['cost uncertainty']['segment transpo']['scale']
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
        _cost = 0.0011221 * _year - 2.1912399
        if _vkmt is None:
            return 0.0
        else:
            if path_dict['cost uncertainty']['shred transpo'] == 'array':
                if _year >= 2021.0:
                    _m = apply_array_uncertainty(
                        path_dict['cost uncertainty']['shred transpo']['m'],
                        self.run
                        )
                    _b = apply_array_uncertainty(
                        path_dict['cost uncertainty']['shred transpo']['b'],
                        self.run
                        )                        
                    return (_m * _year + _b) * _vkmt
                else:
                    return _cost * _vkmt

            if path_dict['cost uncertainty']['shred transpo'] == 'random':
                _c = path_dict['cost uncertainty']['shred transpo']['c']
                _loc = path_dict['cost uncertainty']['shred transpo']['loc']
                _scale = path_dict['cost uncertainty']['shred transpo']['scale']
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
        if path_dict['cost uncertainty']['manufacturing']['uncertainty'] == 'array' and path_dict['year'] > 2021.0:
            _cost = apply_array_uncertainty(
                path_dict['cost uncertainty']['manufacturing']['b'],
                self.run
                )
        if path_dict['cost uncertainty']['manufacturing']['uncertainty'] == 'random':
            _c = path_dict['cost uncertainty']['manufacturing']['c']
            _loc = path_dict['cost uncertainty']['manufacturing']['loc']
            _scale = path_dict['cost uncertainty']['manufacturing']['scale']
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
        return self.segment_transpo(path_dict)
