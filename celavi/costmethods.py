from random import seed
import scipy.stats as st
import warnings

from typing import Dict

from celavi.uncertainty_methods import apply_array_uncertainty, apply_stoch_uncertainty


class CostMethods:
    """
    Functions for calculating processing and transportation costs throughout
    the supply chain. The methods in this Class must be re-written to
    correspond to each case study; in general, these methods are not reusable
    across different supply chains or technologies.


    """

    def __init__(self, start_year, seed, run):
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
        self.start_year = start_year
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

        if path_dict['cost uncertainty']['landfilling']['uncertainty'] == 'stochastic':
            # get draws from probability distributions if the model run just started
            # otherwise, use the stored values that were already drawn
            if _year == self.start_year:
                _m = apply_stoch_uncertainty(
                    path_dict['cost uncertainty']['landfilling']['m'],
                    seed=self.seed
                    )
                if isinstance(path_dict['cost uncertainty']['landfilling']['m'], dict):
                    path_dict['cost uncertainty']['landfilling']['m']['value'] = _m
                
                _b = apply_stoch_uncertainty(
                    path_dict['cost uncertainty']['landfilling']['b'],
                    seed=self.seed
                )
                if isinstance(path_dict['cost uncertainty']['landfilling']['b'],dict):
                    path_dict['cost uncertainty']['landfilling']['b']['value'] = _b
            else:
                _m = path_dict['cost uncertainty']['landfilling']['m']['value']
                _b = path_dict['cost uncertainty']['landfilling']['b']['value']
        elif path_dict['cost uncertainty']['landfilling']['uncertainty'] == 'array':
            # use an array of parameter values from config
            # model run is the index
            _m = apply_array_uncertainty(
                path_dict['cost uncertainty']['landfilling']['m'],
                self.run
                )
            _b = apply_array_uncertainty(
                path_dict['cost uncertainty']['landfilling']['b'],
                self.run
                )
        else:
            # with no uncertainty
            _m = path_dict['cost uncertainty']['landfilling']['m']
            _b = path_dict['cost uncertainty']['landfilling']['b']
        # fee model = point-slope form of a line
        return _m * (_year - 2000.0) + _b

    def process_cost_loss_revenue_model(self, path_dict, process):
        """
        Cost method

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes
        process
            String of the process (as written in the scenario.yaml file) which
            uses this simple cost, loss, revenue model

        Returns
        -------
            Net cost (process costs minus revenues) of any one metric ton of
            material at different facilities and disposing of material losses
            in a landfill (accounting for associated costs)
        """
        _learn_dict = path_dict['learning'][process]

        # Implement uncertainty on parameters: array or random
        if path_dict['cost uncertainty'][process]['uncertainty'] == 'array':
            _learn_rate = apply_array_uncertainty(
                _learn_dict['learn rate'],
                self.run
                )
            try:
                _loss = apply_array_uncertainty(
                    path_dict['path_split'][process]['fraction'],
                    self.run
                    )
            except KeyError:
                _loss = 0.0
            _initial_cost = apply_array_uncertainty(
               path_dict['cost uncertainty'][process]['initial cost'],
               self.run
               )
            _revenue = apply_array_uncertainty(
                path_dict['cost uncertainty'][process]['revenue'],
                self.run
                )

        elif path_dict['cost uncertainty'][process]['uncertainty'] == 'stochastic':
            if path_dict['year'] == self.start_year:
                try:
                    _loss = apply_stoch_uncertainty(
                        path_dict['path_split'][process]['fraction'],
                        seed=self.seed
                        )
                except KeyError:
                    _loss = 0.0
                _learn_rate = -1.0 * apply_stoch_uncertainty(
                    _learn_dict['learn rate'],
                    seed=self.seed
                    )
                _initial_cost = apply_stoch_uncertainty(
                    path_dict['cost uncertainty'][process]['initial cost'],
                    seed=self.seed
                    )
                _revenue = apply_stoch_uncertainty(
                    path_dict['cost uncertainty'][process]['revenue'],
                    seed=self.seed
                    )
                if isinstance(path_dict['path_split'][process]['fraction'],dict):
                    path_dict['path_split'][process]['fraction']['value'] = _loss
                if isinstance(_learn_dict['learn rate'], dict):
                    _learn_dict['learn rate']['value'] = _learn_rate
                if isinstance(path_dict['cost uncertainty'][process]['initial cost'],dict):
                    path_dict['cost uncertainty'][process]['initial cost']['value'] = _initial_cost
                if isinstance(path_dict['cost uncertainty'][process]['revenue'], dict):
                    path_dict['cost uncertainty'][process]['revenue']['value'] = _revenue
            else:
                try:
                    _loss = path_dict['path_split'][process]['fraction']['value']
                except KeyError:
                    _loss = 0.0
                _learn_rate = _learn_dict['learn rate']['value']
                _initial_cost = path_dict['cost uncertainty'][process]['initial cost']['value']
                _revenue = path_dict['cost uncertainty'][process]['revenue']['value']
        else:
            # No uncertainty
            _learn_rate = apply_array_uncertainty(_learn_dict['learn rate'], self.run)
            try:
                _loss = apply_array_uncertainty(
                    path_dict['path_split'][process]['fraction'],
                    self.run
                    )
            except KeyError:
                _loss = 0.0
            _initial_cost = path_dict['cost uncertainty'][process]['initial cost']
            _revenue = path_dict['cost uncertainty'][process]['revenue']

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
        _landfill = _loss * self.landfilling(path_dict)

        return _cost + _landfill - _revenue

    def solar_glass_manufacturing(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'solar glass manufacturing')
    
    def solar_glass_manufacturing_from_cullet(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'solar glass manufacturing from cullet')
    
    def solar_glass_recovery(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'solar glass recovery')
    
    def module_manufacturing(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'module manufacturing')
    
    def module_installation(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'module installation')

    def module_uninstallation(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'module uninstallation')

    def module_disassembly(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'module disassembly')

    def window_glass_manufacturing(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'window glass manufacturing')

    def window_manufacturing(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'window manufacturing')

    def window_installation(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'window installation')

    def window_uninstallation(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'window uninstallation')

    def window_glass_recovery(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'window glass recovery')

    def solar_glass_cullet_manufacturing(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'solar glass cullet manufacturing')

    def window_glass_cullet_manufacturing(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'window glass cullet manufacturing')

    def glass_wool_manufacturing(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'glass wool manufacturing')
    
    def scm_manufacturing(self, path_dict):
        """
        See process_cost_loss_revenue_model method
        """
        return self.process_cost_loss_revenue_model(
            path_dict, 'scm manufacturing')

    def transportation_cost_model(self, path_dict, transport_process):
        """
        Cost method for calculating transportation costs (truck)
        in USD/metric ton.

        Parameters
        ----------
        path_dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes

        Returns
        -------
            Cost of transporting 1 metric ton of material by
            one kilometer. Units: USD/metric ton.
        """
        _vkmt = path_dict['vkmt']  # _vkmt is in km
        _year = path_dict['year']

        if _vkmt is None:
            return 0.0
        else:
            if path_dict['cost uncertainty'][transport_process]['uncertainty'] == 'array':
                _m = apply_array_uncertainty(
                    path_dict['cost uncertainty'][transport_process]['m'],
                    self.run
                    )
                _b = apply_array_uncertainty(
                    path_dict['cost uncertainty'][transport_process]['b'],
                    self.run
                    )
            elif path_dict['cost uncertainty'][transport_process]['uncertainty'] == 'stochastic':
                if _year == self.start_year:
                    _m = apply_stoch_uncertainty(
                        path_dict['cost uncertainty'][transport_process]['m'],
                        seed=self.seed
                    )
                    if isinstance(path_dict['cost uncertainty'][transport_process]['m'],dict):
                        path_dict['cost uncertainty'][transport_process]['m']['value'] = _m
                    _b = apply_stoch_uncertainty(
                        path_dict['cost uncertainty'][transport_process]['b'],
                        seed=self.seed
                    )
                    if isinstance(path_dict['cost uncertainty'][transport_process]['b'],dict):
                        path_dict['cost uncertainty'][transport_process]['b']['value'] = _b
                else:
                    _m = path_dict['cost uncertainty'][transport_process]['m']['value']
                    _b = path_dict['cost uncertainty'][transport_process]['b']['value']
            else:
                # with no uncertainty
                _m = path_dict['cost uncertainty'][transport_process]['m']
                _b = path_dict['cost uncertainty'][transport_process]['b']
        
            return (_m * (_year - 2000.0) + _b) * _vkmt

    def primary_material(self, path_dict):
        """
        See transportation_cost_model method
        """
        return self.transportation_cost_model(
            path_dict, 'primary material')

    def technology(self, path_dict):
        """
        See transportation_cost_model method
        """
        return self.transportation_cost_model(
            path_dict, 'technology')

    def eol_material(self, path_dict):
        """
        See transportation_cost_model method
        """
        return self.transportation_cost_model(
            path_dict, 'eol material')

    def waste(self, path_dict):
        """
        See transportation_cost_model method
        """
        return self.transportation_cost_model(
            path_dict, 'waste')

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

        # Implement uncertainty on initial cost before applying learning model
        if path_dict['cost uncertainty']['coarse grinding']['uncertainty'] == 'array':
            _learn_rate = apply_array_uncertainty(
                _learn_dict['learn rate'],
                self.run
                )  
            # Array uncertainty is applied to the initial cost or to the learning rate
            # (array uncertainty for the actual cost is implemented through the learning rate)
            _initial_cost = apply_array_uncertainty(
                path_dict['cost uncertainty']['coarse grinding']['initial cost'],
                self.run
                )
        elif path_dict['cost uncertainty']['coarse grinding']['uncertainty'] == 'stochastic':
            if path_dict['year'] == self.start_year:
                    _initial_cost = apply_stoch_uncertainty(
                        path_dict['cost uncertainty']['coarse grinding']['initial cost'],
                        seed=self.seed
                    )
                    _learn_rate = -1.0 * apply_stoch_uncertainty(
                        _learn_dict['learn rate'],
                        seed=self.seed
                    )                    
                    if isinstance(path_dict['cost uncertainty']['coarse grinding']['initial cost'],dict):
                        path_dict['cost uncertainty']['coarse grinding']['initial cost']['value'] = _initial_cost
                    if isinstance(_learn_dict['learn rate'], dict):
                        _learn_dict['learn rate']['value'] = _learn_rate                    
            else:
                _initial_cost = path_dict['cost uncertainty']['coarse grinding']['initial cost']['value']
                _learn_rate = _learn_dict['learn rate']['value']
        else:
            # with no uncertainty
            _learn_rate = apply_array_uncertainty(_learn_dict['learn rate'], self.run)
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
        # apply cost reduction to initial cost
        return _initial_cost * coarsegrind_cumul ** _learn_rate

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

       
        # Implement uncertainty on parameters: array or random
        if path_dict['cost uncertainty']['fine grinding']['uncertainty'] == 'array':
            _learn_rate = apply_array_uncertainty(
                _learn_dict['learn rate'],
                self.run
                )
            _loss = apply_array_uncertainty(
                path_dict['path_split']['fine grinding']['fraction'],
                self.run
                )
            _initial_cost = apply_array_uncertainty(
               path_dict['cost uncertainty']['fine grinding']['initial cost'],
               self.run
               )
            _revenue = apply_array_uncertainty(
                path_dict['cost uncertainty']['fine grinding']['revenue'],
                self.run
                )

        elif path_dict['cost uncertainty']['fine grinding']['uncertainty'] == 'stochastic':
            if path_dict['year'] == self.start_year:
                _loss = apply_stoch_uncertainty(
                    path_dict['path_split']['fine grinding']['fraction'],
                    seed=self.seed
                    )
                _learn_rate = -1.0 * apply_stoch_uncertainty(
                    _learn_dict['learn rate'],
                    seed=self.seed
                    )
                _initial_cost = apply_stoch_uncertainty(
                    path_dict['cost uncertainty']['fine grinding']['initial cost'],
                    seed=self.seed
                    )
                _revenue = apply_stoch_uncertainty(
                    path_dict['cost uncertainty']['fine grinding']['revenue'],
                    seed=self.seed
                    )
                if isinstance(path_dict['path_split']['fine grinding']['fraction'],dict):
                    path_dict['path_split']['fine grinding']['fraction']['value'] = _loss
                if isinstance(_learn_dict['learn rate'], dict):
                    _learn_dict['learn rate']['value'] = _learn_rate
                if isinstance(path_dict['cost uncertainty']['fine grinding']['initial cost'],dict):
                    path_dict['cost uncertainty']['fine grinding']['initial cost']['value'] = _initial_cost
                if isinstance(path_dict['cost uncertainty']['fine grinding']['revenue'], dict):
                    path_dict['cost uncertainty']['fine grinding']['revenue']['value'] = _revenue
            else:
                _loss = path_dict['path_split']['fine grinding']['fraction']['value']
                _learn_rate = _learn_dict['learn rate']['value']
                _initial_cost = path_dict['cost uncertainty']['fine grinding']['initial cost']['value']
                _revenue = path_dict['cost uncertainty']['fine grinding']['revenue']['value']
        else:
            # No uncertainty
            _learn_rate = apply_array_uncertainty(_learn_dict['learn rate'], self.run)
            _loss = apply_array_uncertainty(
                path_dict['path_split']['fine grinding']['fraction'],
                self.run
                )
            _initial_cost = path_dict['cost uncertainty']['fine grinding']['initial cost']
            _revenue = path_dict['cost uncertainty']['fine grinding']['revenue']

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
        _landfill = _loss * self.landfilling(path_dict)

        return _cost + _landfill - _revenue

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
            if path_dict['cost uncertainty']['shred transpo']['uncertainty'] == 'array':
                _m = apply_array_uncertainty(
                    path_dict['cost uncertainty']['shred transpo']['m'],
                    self.run
                    )
                _b = apply_array_uncertainty(
                    path_dict['cost uncertainty']['shred transpo']['b'],
                    self.run
                    )
            elif path_dict['cost uncertainty']['shred transpo']['uncertainty'] == 'stochastic':
                if _year == self.start_year:
                    _m = apply_stoch_uncertainty(
                        path_dict['cost uncertainty']['shred transpo']['m'],
                        seed=self.seed
                    )
                    if isinstance(path_dict['cost uncertainty']['shred transpo']['m'],dict):
                        path_dict['cost uncertainty']['shred transpo']['m']['value'] = _m
                    _b = apply_stoch_uncertainty(
                        path_dict['cost uncertainty']['shred transpo']['b'],
                        seed=self.seed
                    )
                    if isinstance(path_dict['cost uncertainty']['shred transpo']['b'],dict):
                        path_dict['cost uncertainty']['shred transpo']['b']['value'] = _b
                else:
                    _m = path_dict['cost uncertainty']['shred transpo']['m']['value']
                    _b = path_dict['cost uncertainty']['shred transpo']['b']['value']
            else:
                # with no uncertainty
                _m = path_dict['cost uncertainty']['shred transpo']['m']
                _b = path_dict['cost uncertainty']['shred transpo']['b']
        
            return (_m * (_year - 2000.0) + _b) * _vkmt
