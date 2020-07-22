"""
Python model "tiny-sd copy.py"
Translated using PySD version 0.10.0
"""
from __future__ import division
import numpy as np
from pysd import utils
import xarray as xr

from pysd.py_backend.functions import cache
from pysd.py_backend import functions

_subscript_dict = {}

_namespace = {
    'TIME': 'time',
    'Time': 'time',
    'changing fraction reuse': 'changing_fraction_reuse',
    'lowest cost pathway': 'lowest_cost_pathway',
    'check fraction sum': 'check_fraction_sum',
    'reuse favorability over linear': 'reuse_favorability_over_linear',
    'Fraction Reuse': 'fraction_reuse',
    'remanufacture favorability': 'remanufacture_favorability',
    'rate of increasing recycle fraction': 'rate_of_increasing_recycle_fraction',
    'recycle favorability': 'recycle_favorability',
    'rate of increasing reuse fraction': 'rate_of_increasing_reuse_fraction',
    'increasing fraction recycle': 'increasing_fraction_recycle',
    'rate of increasing remanufacture fraction': 'rate_of_increasing_remanufacture_fraction',
    'reuse favorability': 'reuse_favorability',
    'Cumulative Recycle': 'cumulative_recycle',
    'Cumulative Remanufacture': 'cumulative_remanufacture',
    'recycle process learning': 'recycle_process_learning',
    'allowable turbine component remanufacture': 'allowable_turbine_component_remanufacture',
    'allowable turbine component reuse': 'allowable_turbine_component_reuse',
    'remanufacture process learning': 'remanufacture_process_learning',
    'tallying remanufacture': 'tallying_remanufacture',
    'tallying reuse': 'tallying_reuse',
    'remaining remanufacture': 'remaining_remanufacture',
    'remaining reuse': 'remaining_reuse',
    'Cumulative Reuse': 'cumulative_reuse',
    'reuse process learning': 'reuse_process_learning',
    'tallying recycle': 'tallying_recycle',
    'Recycle Process Cost': 'recycle_process_cost',
    'recycled material cost': 'recycled_material_cost',
    'remanufactured material cost': 'remanufactured_material_cost',
    'initial cost of recycling process': 'initial_cost_of_recycling_process',
    'initial cost of remanufacturing process': 'initial_cost_of_remanufacturing_process',
    'Remanufacture Process Cost': 'remanufacture_process_cost',
    'Reuse Process Cost': 'reuse_process_cost',
    'increasing fraction remanufacture': 'increasing_fraction_remanufacture',
    'initial cost of reuse process': 'initial_cost_of_reuse_process',
    'reused material cost': 'reused_material_cost',
    'cost of transportation': 'cost_of_transportation',
    'increase recycle': 'increase_recycle',
    'increase remanufacture': 'increase_remanufacture',
    'increase reuse': 'increase_reuse',
    'cost of landfilling': 'cost_of_landfilling',
    'cost of extraction and production': 'cost_of_extraction_and_production',
    'fraction used product reused initial value': 'fraction_used_product_reused_initial_value',
    'Fraction Recycle': 'fraction_recycle',
    'Fraction Remanufacture': 'fraction_remanufacture',
    'reusing': 'reusing',
    'fraction used product disposed': 'fraction_used_product_disposed',
    'fraction used product recycled initial value': 'fraction_used_product_recycled_initial_value',
    'fraction used product remanufactured initial value':
    'fraction_used_product_remanufactured_initial_value',
    'remanufacturing': 'remanufacturing',
    'recycling': 'recycling',
    'linear material cost': 'linear_material_cost',
    'annual demand': 'annual_demand',
    'component mass': 'component_mass',
    'remanufacture favorability over linear': 'remanufacture_favorability_over_linear',
    'recycle favorability over linear': 'recycle_favorability_over_linear',
    'one Year': 'one_year',
    'one Unit': 'one_unit',
    'aggregating recycled materials': 'aggregating_recycled_materials',
    'aggregating remanufactured products': 'aggregating_remanufactured_products',
    'aggregating reused products': 'aggregating_reused_products',
    'annual virgin material demand': 'annual_virgin_material_demand',
    'recycling failed remanufactured': 'recycling_failed_remanufactured',
    'relative landfill': 'relative_landfill',
    'Products in Use': 'products_in_use',
    'fraction used product reused in other sectors':
    'fraction_used_product_reused_in_other_sectors',
    'cumulative landfill fraction': 'cumulative_landfill_fraction',
    'disposing': 'disposing',
    'distributing': 'distributing',
    'environmental impact from landfill transportation':
    'environmental_impact_from_landfill_transportation',
    'environmental impact from recycling transportation':
    'environmental_impact_from_recycling_transportation',
    'environmental impact from remanufacturing transportation':
    'environmental_impact_from_remanufacturing_transportation',
    'environmental impact from reuse transportation':
    'environmental_impact_from_reuse_transportation',
    'Products at End of Life': 'products_at_end_of_life',
    'landfilling nonrecyclables': 'landfilling_nonrecyclables',
    'Products Sent to Other Sectors': 'products_sent_to_other_sectors',
    'Raw Material Extraction': 'raw_material_extraction',
    'reaching end of life': 'reaching_end_of_life',
    'environmental impact per kgyear': 'environmental_impact_per_kgyear',
    'extracting': 'extracting',
    'landfilling': 'landfilling',
    'Production': 'production',
    'Material Distribution': 'material_distribution',
    'remanufacturing nonreusables': 'remanufacturing_nonreusables',
    'initial construction time': 'initial_construction_time',
    'Landfill and Incineration': 'landfill_and_incineration',
    'Landfill Transport': 'landfill_transport',
    'Product Distribution': 'product_distribution',
    'Product Remanufacture': 'product_remanufacture',
    'landfilling failed remanufactured': 'landfilling_failed_remanufactured',
    'shipping': 'shipping',
    'tallying extraction': 'tallying_extraction',
    'Total Extraction': 'total_extraction',
    'Material Recycle': 'material_recycle',
    'number of turbines': 'number_of_turbines',
    'producing': 'producing',
    'Product Reuse': 'product_reuse',
    'reusing in other sectors': 'reusing_in_other_sectors',
    'turbine assembly time': 'turbine_assembly_time',
    'environmental impact of extracting process': 'environmental_impact_of_extracting_process',
    'environmental impact of recycling process': 'environmental_impact_of_recycling_process',
    'environmental impact of remanufacturing process':
    'environmental_impact_of_remanufacturing_process',
    'environmental impact of transportation': 'environmental_impact_of_transportation',
    'environmental impact of reusing process': 'environmental_impact_of_reusing_process',
    'recycled material strategic value': 'recycled_material_strategic_value',
    'remanufactured material strategic value': 'remanufactured_material_strategic_value',
    'reused material strategic value': 'reused_material_strategic_value',
    'miles from end use location to recycling facility':
    'miles_from_end_use_location_to_recycling_facility',
    'miles from end use location to remanufacturing facility':
    'miles_from_end_use_location_to_remanufacturing_facility',
    'miles from end use location to reuse facility':
    'miles_from_end_use_location_to_reuse_facility',
    'miles from reuse facility to product distribution facility':
    'miles_from_reuse_facility_to_product_distribution_facility',
    'miles from reuse facility to remanufacturing facility':
    'miles_from_reuse_facility_to_remanufacturing_facility',
    'miles from extraction to production facility': 'miles_from_extraction_to_production_facility',
    'miles from recycling facility to landfill': 'miles_from_recycling_facility_to_landfill',
    'miles from remanufacturing facility to landfill':
    'miles_from_remanufacturing_facility_to_landfill',
    'miles from end use location to landfill': 'miles_from_end_use_location_to_landfill',
    'miles from recycling to distribution facility':
    'miles_from_recycling_to_distribution_facility',
    'miles from remanufacturing facility to recycling facility':
    'miles_from_remanufacturing_facility_to_recycling_facility',
    'miles from remanufacturing facility to product distribution facility':
    'miles_from_remanufacturing_facility_to_product_distribution_facility',
    'supply chain delay': 'supply_chain_delay',
    'initial components in use': 'initial_components_in_use',
    'fraction of recycling to landfill': 'fraction_of_recycling_to_landfill',
    'fraction of remanufacture to landfill': 'fraction_of_remanufacture_to_landfill',
    'fraction remanufactured product to recycle': 'fraction_remanufactured_product_to_recycle',
    'fraction reused product remanufactured': 'fraction_reused_product_remanufactured',
    'component lifetime': 'component_lifetime',
    'FINAL TIME': 'final_time',
    'INITIAL TIME': 'initial_time',
    'SAVEPER': 'saveper',
    'TIME STEP': 'time_step'
}

__pysd_version__ = "0.10.0"

__data = {'scope': None, 'time': lambda: 0}


def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


def time():
    return __data['time']()


@cache('step')
def changing_fraction_reuse():
    """
    Real Name: b'changing fraction reuse'
    Original Eqn: b'IF THEN ELSE(check fraction sum < 1 - rate of increasing reuse fraction\\\\ :AND: Fraction Reuse < 1 - rate of increasing reuse fraction\\\\ , increase reuse * rate of increasing reuse fraction\\\\ , 0) * IF THEN ELSE(remaining reuse <= 10, -1, 1)'
    Units: b'Dmnl/year'
    Limits: (None, None)
    Type: component

    b''
    """
    return functions.if_then_else(
        check_fraction_sum() < 1 - rate_of_increasing_reuse_fraction()
        and fraction_reuse() < 1 - rate_of_increasing_reuse_fraction(),
        increase_reuse() * rate_of_increasing_reuse_fraction(), 0) * functions.if_then_else(
            remaining_reuse() <= 10, -1, 1)


@cache('step')
def lowest_cost_pathway():
    """
    Real Name: b'lowest cost pathway'
    Original Eqn: b'MIN(reuse favorability over linear, remanufacture favorability over linear\\\\ , recycle favorability over linear, 1000)'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b''
    """
    # Alicia changed this from
    #
    # return np.minimum(reuse_favorability_over_linear(), remanufacture_favorability_over_linear(),
    #                       recycle_favorability_over_linear(), 1000)
    #
    # to
    #
    return min(reuse_favorability_over_linear(), remanufacture_favorability_over_linear(),
                      recycle_favorability_over_linear(), 1000)


@cache('step')
def check_fraction_sum():
    """
    Real Name: b'check fraction sum'
    Original Eqn: b'Fraction Reuse + Fraction Remanufacture + Fraction Recycle'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b''
    """
    return fraction_reuse() + fraction_remanufacture() + fraction_recycle()


@cache('step')
def reuse_favorability_over_linear():
    """
    Real Name: b'reuse favorability over linear'
    Original Eqn: b'reused material cost / linear material cost'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return reused_material_cost() / linear_material_cost()


@cache('step')
def fraction_reuse():
    """
    Real Name: b'Fraction Reuse'
    Original Eqn: b'INTEG (changing fraction reuse, fraction used product reused initial value)'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b''
    """
    return _integ_fraction_reuse()


@cache('step')
def remanufacture_favorability():
    """
    Real Name: b'remanufacture favorability'
    Original Eqn: b'IF THEN ELSE(lowest cost pathway = remanufacture favorability over linear\\\\ , remanufacture favorability over linear, 10)'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return functions.if_then_else(
        lowest_cost_pathway() == remanufacture_favorability_over_linear(),
        remanufacture_favorability_over_linear(), 10)


@cache('step')
def rate_of_increasing_recycle_fraction():
    """
    Real Name: b'rate of increasing recycle fraction'
    Original Eqn: b'WITH LOOKUP ( recycle favorability, ([(0,0)-(10,0.01)],(0,0.01),(0.275229,0.00964912),(0.422018,0.00995614),(1,0.0090825\\\\ ),(1.40673,0.00929825),(2,0),(10,0 ) ))'
    Units: b''
    Limits: (None, None)
    Type: component

    b'\\n    !recycle favorability'
    """
    return functions.lookup(recycle_favorability(), [0, 0.275229, 0.422018, 1, 1.40673, 2, 10],
                            [0.01, 0.00964912, 0.00995614, 0.0090825, 0.00929825, 0, 0])


@cache('step')
def recycle_favorability():
    """
    Real Name: b'recycle favorability'
    Original Eqn: b'IF THEN ELSE(lowest cost pathway = recycle favorability over linear\\\\ , recycle favorability over linear, 10)'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return functions.if_then_else(lowest_cost_pathway() == recycle_favorability_over_linear(),
                                  recycle_favorability_over_linear(), 10)


@cache('step')
def rate_of_increasing_reuse_fraction():
    """
    Real Name: b'rate of increasing reuse fraction'
    Original Eqn: b'WITH LOOKUP ( reuse favorability, ([(0,0)-(10,0.01)],(0,0.01),(0.275229,0.00903509),(0.519878,0.00833333),(0.99,0.00758772\\\\ ),(1,0),(2,0),(10,0) ))'
    Units: b''
    Limits: (None, None)
    Type: component

    b'\\n    !reuse favorability\\n    !rate of increasing fraction reuse'
    """
    return functions.lookup(reuse_favorability(), [0, 0.275229, 0.519878, 0.99, 1, 2, 10],
                            [0.01, 0.00903509, 0.00833333, 0.00758772, 0, 0, 0])


@cache('step')
def increasing_fraction_recycle():
    """
    Real Name: b'increasing fraction recycle'
    Original Eqn: b'IF THEN ELSE(check fraction sum < 1 - rate of increasing recycle fraction\\\\ :AND: Fraction Recycle < 1 - rate of increasing recycle fraction\\\\ , increase recycle * rate of increasing recycle fraction\\\\ , 0)'
    Units: b'Dmnl/year'
    Limits: (None, None)
    Type: component

    b''
    """
    return functions.if_then_else(
        check_fraction_sum() < 1 - rate_of_increasing_recycle_fraction()
        and fraction_recycle() < 1 - rate_of_increasing_recycle_fraction(),
        increase_recycle() * rate_of_increasing_recycle_fraction(), 0)


@cache('step')
def rate_of_increasing_remanufacture_fraction():
    """
    Real Name: b'rate of increasing remanufacture fraction'
    Original Eqn: b'WITH LOOKUP ( remanufacture favorability, ([(0,0)-(10,0.008)],(0,0.00736842),(0.165138,0.00526316),(0.360856,0.00342105),(0.550459\\\\ ,0.00184211),(1,0),(2,0),(10,0 ) ))'
    Units: b''
    Limits: (None, None)
    Type: component

    b'\\n    !remanufacture favorability'
    """
    return functions.lookup(remanufacture_favorability(),
                            [0, 0.165138, 0.360856, 0.550459, 1, 2, 10],
                            [0.00736842, 0.00526316, 0.00342105, 0.00184211, 0, 0, 0])


@cache('step')
def reuse_favorability():
    """
    Real Name: b'reuse favorability'
    Original Eqn: b'IF THEN ELSE(lowest cost pathway = reuse favorability over linear, reuse favorability over linear, 10)'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return functions.if_then_else(lowest_cost_pathway() == reuse_favorability_over_linear(),
                                  reuse_favorability_over_linear(), 10)


@cache('step')
def cumulative_recycle():
    """
    Real Name: b'Cumulative Recycle'
    Original Eqn: b'INTEG ( tallying recycle, 0)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_cumulative_recycle()


@cache('step')
def cumulative_remanufacture():
    """
    Real Name: b'Cumulative Remanufacture'
    Original Eqn: b'INTEG ( tallying remanufacture, 0)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_cumulative_remanufacture()


@cache('step')
def recycle_process_learning():
    """
    Real Name: b'recycle process learning'
    Original Eqn: b'-0.05 * TREND(Cumulative Recycle, 0.5 , 0 ) * MAX(0, Recycle Process Cost\\\\ )'
    Units: b'USD/each'
    Limits: (None, None)
    Type: component

    b''
    """
    return -0.05 * _trend_cumulative_recycle_05_0() * np.maximum(0, recycle_process_cost())


@cache('run')
def allowable_turbine_component_remanufacture():
    """
    Real Name: b'allowable turbine component remanufacture'
    Original Eqn: b'0.9'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.05)
    Type: constant

    b'Upper limit on the fraction of turbines in the plant before EOL turbine \\n    \\t\\tcomponents must be dealt with another way (not reusing). Represents the \\n    \\t\\ttechnical limitations of remanufacturing and prevents infinite \\n    \\t\\tremanufacturing.'
    """
    return 0.9


@cache('run')
def allowable_turbine_component_reuse():
    """
    Real Name: b'allowable turbine component reuse'
    Original Eqn: b'0.2'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.05)
    Type: constant

    b'Upper limit on the fraction of turbine components in the plant that can be \\n    \\t\\treused before the components must be dealt with another way at EOL. \\n    \\t\\tRepresents technical limitations of reuse and the max lifetime that \\n    \\t\\tturbine components offer.'
    """
    return 0.2


@cache('step')
def remanufacture_process_learning():
    """
    Real Name: b'remanufacture process learning'
    Original Eqn: b'-0.05 * TREND(Cumulative Remanufacture, 0.5 , 0 ) * MAX(0, Remanufacture Process Cost\\\\ )'
    Units: b'USD/each'
    Limits: (None, None)
    Type: component

    b''
    """
    return -0.05 * _trend_cumulative_remanufacture_05_0() * np.maximum(
        0, remanufacture_process_cost())


@cache('step')
def tallying_remanufacture():
    """
    Real Name: b'tallying remanufacture'
    Original Eqn: b'aggregating remanufactured products'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return aggregating_remanufactured_products()


@cache('step')
def tallying_reuse():
    """
    Real Name: b'tallying reuse'
    Original Eqn: b'aggregating reused products'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return aggregating_reused_products()


@cache('step')
def remaining_remanufacture():
    """
    Real Name: b'remaining remanufacture'
    Original Eqn: b'allowable turbine component remanufacture * number of turbines - Cumulative Remanufacture'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b'calculates the number of turbine components that can still be \\n    \\t\\tremanufactured'
    """
    return allowable_turbine_component_remanufacture() * number_of_turbines(
    ) - cumulative_remanufacture()


@cache('step')
def remaining_reuse():
    """
    Real Name: b'remaining reuse'
    Original Eqn: b'allowable turbine component reuse * number of turbines - Cumulative Reuse\\\\ - Fraction Reuse * number of turbines'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b'calculates the number of turbine components that can still be reused'
    """
    return allowable_turbine_component_reuse() * number_of_turbines() - cumulative_reuse(
    ) - fraction_reuse() * number_of_turbines()


@cache('step')
def cumulative_reuse():
    """
    Real Name: b'Cumulative Reuse'
    Original Eqn: b'INTEG ( tallying reuse, 0)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_cumulative_reuse()


@cache('step')
def reuse_process_learning():
    """
    Real Name: b'reuse process learning'
    Original Eqn: b'-0.05 * TREND(Cumulative Reuse, 0.5 , 0 ) * MAX(0, Reuse Process Cost)'
    Units: b'USD/each'
    Limits: (None, None)
    Type: component

    b''
    """
    return -0.05 * _trend_cumulative_reuse_05_0() * np.maximum(0, reuse_process_cost())


@cache('step')
def tallying_recycle():
    """
    Real Name: b'tallying recycle'
    Original Eqn: b'aggregating recycled materials'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return aggregating_recycled_materials()


@cache('step')
def recycle_process_cost():
    """
    Real Name: b'Recycle Process Cost'
    Original Eqn: b'INTEG ( recycle process learning, initial cost of recycling process)'
    Units: b'USD/each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_recycle_process_cost()


@cache('step')
def recycled_material_cost():
    """
    Real Name: b'recycled material cost'
    Original Eqn: b'( ( miles from end use location to recycling facility * cost of transportation\\\\ * component mass + Recycle Process Cost ) + fraction remanufactured product to recycle * ( miles from remanufacturing facility to recycling facility * cost of transportation\\\\ * component mass + Recycle Process Cost ) + ( miles from recycling to distribution facility * cost of transportation\\\\ * component mass ) ) - recycled material strategic value'
    Units: b'USD/each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return ((miles_from_end_use_location_to_recycling_facility() * cost_of_transportation() *
             component_mass() + recycle_process_cost()) +
            fraction_remanufactured_product_to_recycle() *
            (miles_from_remanufacturing_facility_to_recycling_facility() *
             cost_of_transportation() * component_mass() + recycle_process_cost()) +
            (miles_from_recycling_to_distribution_facility() * cost_of_transportation() *
             component_mass())) - recycled_material_strategic_value()


@cache('step')
def remanufactured_material_cost():
    """
    Real Name: b'remanufactured material cost'
    Original Eqn: b'( ( miles from end use location to remanufacturing facility * cost of transportation\\\\ * component mass + Remanufacture Process Cost ) + fraction reused product remanufactured * ( miles from reuse facility to remanufacturing facility\\\\ * cost of transportation * component mass + Remanufacture Process Cost ) + ( miles from remanufacturing facility to product distribution facility\\\\ * cost of transportation\\\\ * component mass ) ) - remanufactured material strategic value'
    Units: b'USD/each'
    Limits: (None, None)
    Type: component

    b''
    """
    return (
        (miles_from_end_use_location_to_remanufacturing_facility() * cost_of_transportation() *
         component_mass() + remanufacture_process_cost()) +
        fraction_reused_product_remanufactured() *
        (miles_from_reuse_facility_to_remanufacturing_facility() * cost_of_transportation() *
         component_mass() + remanufacture_process_cost()) +
        (miles_from_remanufacturing_facility_to_product_distribution_facility() *
         cost_of_transportation() * component_mass())) - remanufactured_material_strategic_value()


@cache('run')
def initial_cost_of_recycling_process():
    """
    Real Name: b'initial cost of recycling process'
    Original Eqn: b'75'
    Units: b'USD/each'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 75


@cache('run')
def initial_cost_of_remanufacturing_process():
    """
    Real Name: b'initial cost of remanufacturing process'
    Original Eqn: b'100'
    Units: b'USD/each'
    Limits: (0.0, None, 0.01)
    Type: constant

    b''
    """
    return 100


@cache('step')
def remanufacture_process_cost():
    """
    Real Name: b'Remanufacture Process Cost'
    Original Eqn: b'INTEG ( remanufacture process learning, initial cost of remanufacturing process)'
    Units: b'USD/each'
    Limits: (None, None)
    Type: component

    b''
    """
    return _integ_remanufacture_process_cost()


@cache('step')
def reuse_process_cost():
    """
    Real Name: b'Reuse Process Cost'
    Original Eqn: b'INTEG ( reuse process learning, initial cost of reuse process)'
    Units: b'USD/each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_reuse_process_cost()


@cache('step')
def increasing_fraction_remanufacture():
    """
    Real Name: b'increasing fraction remanufacture'
    Original Eqn: b'IF THEN ELSE(check fraction sum < 1 - rate of increasing remanufacture fraction\\\\ :AND: Fraction Remanufacture < 1 - rate of increasing remanufacture fraction\\\\ , increase remanufacture * rate of increasing remanufacture fraction\\\\ , 0)'
    Units: b'Dmnl/year'
    Limits: (None, None)
    Type: component

    b''
    """
    return functions.if_then_else(
        check_fraction_sum() < 1 - rate_of_increasing_remanufacture_fraction()
        and fraction_remanufacture() < 1 - rate_of_increasing_remanufacture_fraction(),
        increase_remanufacture() * rate_of_increasing_remanufacture_fraction(), 0)


@cache('run')
def initial_cost_of_reuse_process():
    """
    Real Name: b'initial cost of reuse process'
    Original Eqn: b'55'
    Units: b'USD/each'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 55


@cache('step')
def reused_material_cost():
    """
    Real Name: b'reused material cost'
    Original Eqn: b'miles from end use location to reuse facility * cost of transportation * component mass\\\\ + Reuse Process Cost + miles from reuse facility to product distribution facility * cost of transportation\\\\ * component mass - reused material strategic value'
    Units: b'USD/each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return miles_from_end_use_location_to_reuse_facility() * cost_of_transportation(
    ) * component_mass() + reuse_process_cost(
    ) + miles_from_reuse_facility_to_product_distribution_facility() * cost_of_transportation(
    ) * component_mass() - reused_material_strategic_value()


@cache('step')
def cost_of_transportation():
    """
    Real Name: b'cost of transportation'
    Original Eqn: b'WITH LOOKUP ( Time, ([(0,0.4)-(100,0.5)],(0,0.5),(100,0.5) ))'
    Units: b'USD/metric ton/mile'
    Limits: (None, None)
    Type: component

    b'NREL technical report, "Analysis of Transportation and Logistics \\n    \\t\\tChallenges Affecting the Deployment of Larger Wind Turbines: Summary of \\n    \\t\\tResults"'
    """
    return functions.lookup(time(), [0, 100], [0.5, 0.5])


@cache('step')
def increase_recycle():
    """
    Real Name: b'increase recycle'
    Original Eqn: b'IF THEN ELSE(recycle favorability over linear < 1, 1, 0)'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b''
    """
    return functions.if_then_else(recycle_favorability_over_linear() < 1, 1, 0)


@cache('step')
def increase_remanufacture():
    """
    Real Name: b'increase remanufacture'
    Original Eqn: b'IF THEN ELSE(remanufacture favorability over linear < 1, 1, 0)'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b''
    """
    return functions.if_then_else(remanufacture_favorability_over_linear() < 1, 1, 0)


@cache('step')
def increase_reuse():
    """
    Real Name: b'increase reuse'
    Original Eqn: b'IF THEN ELSE(reuse favorability over linear < 1, 1, 0)'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b''
    """
    return functions.if_then_else(reuse_favorability_over_linear() < 1, 1, 0)


@cache('step')
def cost_of_landfilling():
    """
    Real Name: b'cost of landfilling'
    Original Eqn: b'WITH LOOKUP ( Time, ([(0,0)-(100,100)],(0,70),(100,70) ))'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b'$70 - $120 USD/metric ton is the range from source, "Construction and Demolition \\n    \\t\\tWaste Characterization and Market Analysis Report", prepared for CT Dept \\n    \\t\\tof Energy and Env Protection by Green Seal Environmental, Inc.\\t\\tValue used is midpoint of the above range.'
    """
    return functions.lookup(time(), [0, 100], [70, 70])


@cache('step')
def cost_of_extraction_and_production():
    """
    Real Name: b'cost of extraction and production'
    Original Eqn: b'WITH LOOKUP ( Time, ([(0,0)-(100,75)],(0,40),(100,65) ))'
    Units: b'USD/each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return functions.lookup(time(), [0, 100], [40, 65])


@cache('run')
def fraction_used_product_reused_initial_value():
    """
    Real Name: b'fraction used product reused initial value'
    Original Eqn: b'0'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b''
    """
    return 0


@cache('step')
def fraction_recycle():
    """
    Real Name: b'Fraction Recycle'
    Original Eqn: b'INTEG ( increasing fraction recycle, fraction used product recycled initial value)'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b''
    """
    return _integ_fraction_recycle()


@cache('step')
def fraction_remanufacture():
    """
    Real Name: b'Fraction Remanufacture'
    Original Eqn: b'INTEG ( increasing fraction remanufacture, fraction used product remanufactured initial value)'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b''
    """
    return _integ_fraction_remanufacture()


@cache('step')
def reusing():
    """
    Real Name: b'reusing'
    Original Eqn: b'INTEGER( reaching end of life * Fraction Reuse )'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return int(reaching_end_of_life() * fraction_reuse())


@cache('step')
def fraction_used_product_disposed():
    """
    Real Name: b'fraction used product disposed'
    Original Eqn: b'1 - Fraction Reuse - fraction used product reused in other sectors\\\\ - Fraction Remanufacture - Fraction Recycle'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b'default value 0.67'
    """
    return 1 - fraction_reuse() - fraction_used_product_reused_in_other_sectors(
    ) - fraction_remanufacture() - fraction_recycle()


@cache('run')
def fraction_used_product_recycled_initial_value():
    """
    Real Name: b'fraction used product recycled initial value'
    Original Eqn: b'0'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b''
    """
    return 0


@cache('run')
def fraction_used_product_remanufactured_initial_value():
    """
    Real Name: b'fraction used product remanufactured initial value'
    Original Eqn: b'0'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b''
    """
    return 0


@cache('step')
def remanufacturing():
    """
    Real Name: b'remanufacturing'
    Original Eqn: b'reaching end of life * Fraction Remanufacture'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return reaching_end_of_life() * fraction_remanufacture()


@cache('step')
def recycling():
    """
    Real Name: b'recycling'
    Original Eqn: b'INTEGER(reaching end of life * Fraction Recycle)'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return int(reaching_end_of_life() * fraction_recycle())


@cache('step')
def linear_material_cost():
    """
    Real Name: b'linear material cost'
    Original Eqn: b'cost of extraction and production + miles from extraction to production facility\\\\ * cost of transportation * component mass + ( ( miles from end use location to landfill * cost of transportation * component mass + cost of landfilling * component mass ) + ( miles from remanufacturing facility to landfill * cost of transportation\\\\ * component mass + cost of landfilling * component mass\\\\ ) + ( miles from recycling facility to landfill * cost of transportation\\\\ * component mass + cost of landfilling * component mass\\\\ ) )'
    Units: b'USD/each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return cost_of_extraction_and_production() + miles_from_extraction_to_production_facility(
    ) * cost_of_transportation() * component_mass() + (
        (miles_from_end_use_location_to_landfill() * cost_of_transportation() * component_mass() +
         cost_of_landfilling() * component_mass()) +
        (miles_from_remanufacturing_facility_to_landfill() * cost_of_transportation() *
         component_mass() + cost_of_landfilling() * component_mass()) +
        (miles_from_recycling_facility_to_landfill() * cost_of_transportation() * component_mass()
         + cost_of_landfilling() * component_mass()))


@cache('step')
def annual_demand():
    """
    Real Name: b'annual demand'
    Original Eqn: b'( number of turbines * TIME STEP / turbine assembly time ) / one Year * PULSE TRAIN(initial construction time, turbine assembly time , component lifetime + supply chain delay, 1000 )'
    Units: b'each/year'
    Limits: (0.0, None, 10000.0)
    Type: component

    b'The values are made up. The shape of the curve covers some initial BOS \\n    \\t\\tconstruction of the wind farm, followed by full turbine installation, \\n    \\t\\tfollowed by regular O&M over the lifetime of the farm, followed by 2 more \\n    \\t\\trounds of turbine replacement and continued O&M.'
    """
    return (number_of_turbines() * time_step() /
            turbine_assembly_time()) / one_year() * functions.pulse_train(
                __data['time'], initial_construction_time(), turbine_assembly_time(),
                component_lifetime() + supply_chain_delay(), 1000)


@cache('run')
def component_mass():
    """
    Real Name: b'component mass'
    Original Eqn: b'5'
    Units: b'metric ton/each'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 5


@cache('step')
def remanufacture_favorability_over_linear():
    """
    Real Name: b'remanufacture favorability over linear'
    Original Eqn: b'remanufactured material cost / linear material cost'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return remanufactured_material_cost() / linear_material_cost()


@cache('step')
def recycle_favorability_over_linear():
    """
    Real Name: b'recycle favorability over linear'
    Original Eqn: b'recycled material cost / linear material cost'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return recycled_material_cost() / linear_material_cost()


@cache('run')
def one_year():
    """
    Real Name: b'one Year'
    Original Eqn: b'1'
    Units: b'year'
    Limits: (1.0, 1.0)
    Type: constant

    b''
    """
    return 1


@cache('run')
def one_unit():
    """
    Real Name: b'one Unit'
    Original Eqn: b'1'
    Units: b'each'
    Limits: (1.0, 1.0)
    Type: constant

    b''
    """
    return 1


@cache('step')
def aggregating_recycled_materials():
    """
    Real Name: b'aggregating recycled materials'
    Original Eqn: b'recycling + recycling failed remanufactured - landfilling nonrecyclables\\\\'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return recycling() + recycling_failed_remanufactured() - landfilling_nonrecyclables()


@cache('step')
def aggregating_remanufactured_products():
    """
    Real Name: b'aggregating remanufactured products'
    Original Eqn: b'remanufacturing + remanufacturing nonreusables - landfilling failed remanufactured\\\\ - recycling failed remanufactured'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return remanufacturing() + remanufacturing_nonreusables() - landfilling_failed_remanufactured(
    ) - recycling_failed_remanufactured()


@cache('step')
def aggregating_reused_products():
    """
    Real Name: b'aggregating reused products'
    Original Eqn: b'reusing - remanufacturing nonreusables'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return reusing() - remanufacturing_nonreusables()


@cache('step')
def annual_virgin_material_demand():
    """
    Real Name: b'annual virgin material demand'
    Original Eqn: b'annual demand - aggregating recycled materials - aggregating reused products - aggregating remanufactured products'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return annual_demand() - aggregating_recycled_materials() - aggregating_reused_products(
    ) - aggregating_remanufactured_products()


@cache('step')
def recycling_failed_remanufactured():
    """
    Real Name: b'recycling failed remanufactured'
    Original Eqn: b'(remanufacturing + remanufacturing nonreusables) * fraction remanufactured product to recycle\\\\'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b'components that could not be put back into a using product'
    """
    return (remanufacturing() +
            remanufacturing_nonreusables()) * fraction_remanufactured_product_to_recycle()


@cache('step')
def relative_landfill():
    """
    Real Name: b'relative landfill'
    Original Eqn: b'( reaching end of life - (landfilling + landfilling failed remanufactured\\\\ + landfilling nonrecyclables) ) / ( reaching end of life\\\\ + 0.001)'
    Units: b'Dmnl'
    Limits: (None, None)
    Type: component

    b''
    """
    return (reaching_end_of_life() -
            (landfilling() + landfilling_failed_remanufactured() +
             landfilling_nonrecyclables())) / (reaching_end_of_life() + 0.001)


@cache('step')
def products_in_use():
    """
    Real Name: b'Products in Use'
    Original Eqn: b'INTEG ( shipping-reaching end of life, initial components in use)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_products_in_use()


@cache('run')
def fraction_used_product_reused_in_other_sectors():
    """
    Real Name: b'fraction used product reused in other sectors'
    Original Eqn: b'0'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b''
    """
    return 0


@cache('step')
def cumulative_landfill_fraction():
    """
    Real Name: b'cumulative landfill fraction'
    Original Eqn: b'Landfill and Incineration / (Total Extraction + 0.001)'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return landfill_and_incineration() / (total_extraction() + 0.001)


@cache('step')
def disposing():
    """
    Real Name: b'disposing'
    Original Eqn: b'reaching end of life * fraction used product disposed'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return reaching_end_of_life() * fraction_used_product_disposed()


@cache('step')
def distributing():
    """
    Real Name: b'distributing'
    Original Eqn: b'extracting + aggregating recycled materials'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return extracting() + aggregating_recycled_materials()


@cache('step')
def environmental_impact_from_landfill_transportation():
    """
    Real Name: b'environmental impact from landfill transportation'
    Original Eqn: b'environmental impact of transportation * landfilling * miles from end use location to landfill\\\\'
    Units: b'impact/year'
    Limits: (None, None)
    Type: component

    b''
    """
    return environmental_impact_of_transportation() * landfilling(
    ) * miles_from_end_use_location_to_landfill()


@cache('step')
def environmental_impact_from_recycling_transportation():
    """
    Real Name: b'environmental impact from recycling transportation'
    Original Eqn: b'environmental impact of transportation * ( recycling * miles from end use location to recycling facility\\\\ + recycling failed remanufactured * miles from remanufacturing facility to recycling facility\\\\ + landfilling nonrecyclables * miles from recycling facility to landfill\\\\ + aggregating recycled materials * miles from recycling to distribution facility\\\\ )'
    Units: b'impact/year'
    Limits: (None, None)
    Type: component

    b''
    """
    return environmental_impact_of_transportation() * (
        recycling() * miles_from_end_use_location_to_recycling_facility() +
        recycling_failed_remanufactured() *
        miles_from_remanufacturing_facility_to_recycling_facility() +
        landfilling_nonrecyclables() * miles_from_recycling_facility_to_landfill() +
        aggregating_recycled_materials() * miles_from_recycling_to_distribution_facility())


@cache('step')
def environmental_impact_from_remanufacturing_transportation():
    """
    Real Name: b'environmental impact from remanufacturing transportation'
    Original Eqn: b'environmental impact of transportation * ( remanufacturing * miles from end use location to remanufacturing facility\\\\ + remanufacturing nonreusables * miles from reuse facility to remanufacturing facility\\\\ + aggregating remanufactured products * miles from remanufacturing facility to product distribution facility\\\\ + landfilling failed remanufactured * miles from remanufacturing facility to landfill\\\\ )'
    Units: b'impact/year'
    Limits: (None, None)
    Type: component

    b''
    """
    return environmental_impact_of_transportation() * (
        remanufacturing() * miles_from_end_use_location_to_remanufacturing_facility() +
        remanufacturing_nonreusables() * miles_from_reuse_facility_to_remanufacturing_facility() +
        aggregating_remanufactured_products() *
        miles_from_remanufacturing_facility_to_product_distribution_facility() +
        landfilling_failed_remanufactured() * miles_from_remanufacturing_facility_to_landfill())


@cache('step')
def environmental_impact_from_reuse_transportation():
    """
    Real Name: b'environmental impact from reuse transportation'
    Original Eqn: b'environmental impact of transportation * ( reusing * miles from end use location to reuse facility + aggregating reused products * miles from reuse facility to product distribution facility\\\\ )'
    Units: b'impact/year'
    Limits: (None, None)
    Type: component

    b'total mileage * environmental impact per kgmile'
    """
    return environmental_impact_of_transportation() * (
        reusing() * miles_from_end_use_location_to_reuse_facility() +
        aggregating_reused_products() *
        miles_from_reuse_facility_to_product_distribution_facility())


@cache('step')
def products_at_end_of_life():
    """
    Real Name: b'Products at End of Life'
    Original Eqn: b'INTEG ( reaching end of life-disposing-recycling-remanufacturing\\\\ -reusing-reusing in other sectors, 0)'
    Units: b'each'
    Limits: (-1.0, None)
    Type: component

    b''
    """
    return _integ_products_at_end_of_life()


@cache('step')
def landfilling_nonrecyclables():
    """
    Real Name: b'landfilling nonrecyclables'
    Original Eqn: b'(recycling + recycling failed remanufactured) * fraction of recycling to landfill\\\\'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return (recycling() + recycling_failed_remanufactured()) * fraction_of_recycling_to_landfill()


@cache('step')
def products_sent_to_other_sectors():
    """
    Real Name: b'Products Sent to Other Sectors'
    Original Eqn: b'INTEG ( reusing in other sectors, 0)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_products_sent_to_other_sectors()


@cache('step')
def raw_material_extraction():
    """
    Real Name: b'Raw Material Extraction'
    Original Eqn: b'INTEG ( -extracting, 1e+10)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_raw_material_extraction()


@cache('step')
def reaching_end_of_life():
    """
    Real Name: b'reaching end of life'
    Original Eqn: b'DELAY FIXED ( shipping, component lifetime , 0 , 0)'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b'* used to be a DELAY CONVEYOR( shipping ,\\t\\t                product lifetime , \\t\\t                0 ,\\t\\t                initprofile , \\t\\t                initial products at end of life , \\t\\t                product lifetime )\\t\\t* first argument to DELAY CONVEYOR was originally transporting * IF THEN \\n    \\t\\tELSE(Products in Use <= 0, 0, 1)'
    """
    return _delay_shipping_roundcomponent_lifetime__time_step___time_step_0_component_lifetime__time_step(
    )


@cache('step')
def environmental_impact_per_kgyear():
    """
    Real Name: b'environmental impact per kgyear'
    Original Eqn: b'( aggregating reused products * environmental impact of reusing process\\\\ + aggregating remanufactured products * environmental impact of remanufacturing process\\\\ + aggregating recycled materials * environmental impact of recycling process\\\\ + extracting * environmental impact of extracting process + environmental impact from landfill transportation + environmental impact from recycling transportation + environmental impact from remanufacturing transportation + environmental impact from reuse transportation ) / (Products in Use\\\\ + 0.001)'
    Units: b'impact/(each*year)'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return (
        aggregating_reused_products() * environmental_impact_of_reusing_process() +
        aggregating_remanufactured_products() * environmental_impact_of_remanufacturing_process() +
        aggregating_recycled_materials() * environmental_impact_of_recycling_process() +
        extracting() * environmental_impact_of_extracting_process() +
        environmental_impact_from_landfill_transportation() +
        environmental_impact_from_recycling_transportation() +
        environmental_impact_from_remanufacturing_transportation() +
        environmental_impact_from_reuse_transportation()) / (products_in_use() + 0.001)


@cache('step')
def extracting():
    """
    Real Name: b'extracting'
    Original Eqn: b'annual virgin material demand'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return annual_virgin_material_demand()


@cache('step')
def landfilling():
    """
    Real Name: b'landfilling'
    Original Eqn: b'disposing'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return disposing()


@cache('step')
def production():
    """
    Real Name: b'Production'
    Original Eqn: b'INTEG ( aggregating remanufactured products + distributing - producing\\\\ , 100)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_production()


@cache('step')
def material_distribution():
    """
    Real Name: b'Material Distribution'
    Original Eqn: b'INTEG ( aggregating recycled materials+extracting-distributing\\\\ , 100)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_material_distribution()


@cache('step')
def remanufacturing_nonreusables():
    """
    Real Name: b'remanufacturing nonreusables'
    Original Eqn: b'reusing * fraction reused product remanufactured\\\\'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return reusing() * fraction_reused_product_remanufactured()


@cache('run')
def initial_construction_time():
    """
    Real Name: b'initial construction time'
    Original Eqn: b'2'
    Units: b'year'
    Limits: (0.0, 10.0, 0.25)
    Type: constant

    b''
    """
    return 2


@cache('step')
def landfill_and_incineration():
    """
    Real Name: b'Landfill and Incineration'
    Original Eqn: b'INTEG ( landfilling+landfilling failed remanufactured+landfilling nonrecyclables\\\\ , 0)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_landfill_and_incineration()


@cache('step')
def landfill_transport():
    """
    Real Name: b'Landfill Transport'
    Original Eqn: b'INTEG ( disposing-landfilling, 0)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_landfill_transport()


@cache('step')
def product_distribution():
    """
    Real Name: b'Product Distribution'
    Original Eqn: b'INTEG ( aggregating reused products + producing - shipping, 100)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_product_distribution()


@cache('step')
def product_remanufacture():
    """
    Real Name: b'Product Remanufacture'
    Original Eqn: b'INTEG ( remanufacturing+remanufacturing nonreusables-aggregating remanufactured products\\\\ -landfilling failed remanufactured-recycling failed remanufactured\\\\ , 0)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_product_remanufacture()


@cache('step')
def landfilling_failed_remanufactured():
    """
    Real Name: b'landfilling failed remanufactured'
    Original Eqn: b'(remanufacturing + remanufacturing nonreusables) * fraction of remanufacture to landfill\\\\'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return (remanufacturing() +
            remanufacturing_nonreusables()) * fraction_of_remanufacture_to_landfill()


@cache('step')
def shipping():
    """
    Real Name: b'shipping'
    Original Eqn: b'DELAY FIXED ( producing + aggregating reused products, supply chain delay, 0, 0)'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _delay_producingaggregating_reused_products_roundsupply_chain_delay__time_step___time_step_0_supply_chain_delay__time_step(
    )


@cache('step')
def tallying_extraction():
    """
    Real Name: b'tallying extraction'
    Original Eqn: b'extracting'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return extracting()


@cache('step')
def total_extraction():
    """
    Real Name: b'Total Extraction'
    Original Eqn: b'INTEG ( tallying extraction, 0)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_total_extraction()


@cache('step')
def material_recycle():
    """
    Real Name: b'Material Recycle'
    Original Eqn: b'INTEG ( recycling+recycling failed remanufactured-aggregating recycled materials\\\\ -landfilling nonrecyclables, 0)'
    Units: b'each'
    Limits: (-0.1, None)
    Type: component

    b'aka recycling'
    """
    return _integ_material_recycle()


@cache('run')
def number_of_turbines():
    """
    Real Name: b'number of turbines'
    Original Eqn: b'200'
    Units: b'each'
    Limits: (0.0, None, 1.0)
    Type: constant

    b''
    """
    return 200


@cache('step')
def producing():
    """
    Real Name: b'producing'
    Original Eqn: b'distributing + aggregating remanufactured products'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return distributing() + aggregating_remanufactured_products()


@cache('step')
def product_reuse():
    """
    Real Name: b'Product Reuse'
    Original Eqn: b'INTEG ( reusing-aggregating reused products-remanufacturing nonreusables\\\\ , 0)'
    Units: b'each'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return _integ_product_reuse()


@cache('step')
def reusing_in_other_sectors():
    """
    Real Name: b'reusing in other sectors'
    Original Eqn: b'reaching end of life * fraction used product reused in other sectors\\\\'
    Units: b'each/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return reaching_end_of_life() * fraction_used_product_reused_in_other_sectors()


@cache('run')
def turbine_assembly_time():
    """
    Real Name: b'turbine assembly time'
    Original Eqn: b'1'
    Units: b'year'
    Limits: (0.0, 5.0, 0.25)
    Type: constant

    b''
    """
    return 1


@cache('run')
def environmental_impact_of_extracting_process():
    """
    Real Name: b'environmental impact of extracting process'
    Original Eqn: b'15'
    Units: b'impact/each'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 15


@cache('run')
def environmental_impact_of_recycling_process():
    """
    Real Name: b'environmental impact of recycling process'
    Original Eqn: b'11'
    Units: b'impact/each'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 11


@cache('run')
def environmental_impact_of_remanufacturing_process():
    """
    Real Name: b'environmental impact of remanufacturing process'
    Original Eqn: b'8'
    Units: b'impact/each'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 8


@cache('run')
def environmental_impact_of_transportation():
    """
    Real Name: b'environmental impact of transportation'
    Original Eqn: b'0.01'
    Units: b'impact/(each*mile)'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 0.01


@cache('run')
def environmental_impact_of_reusing_process():
    """
    Real Name: b'environmental impact of reusing process'
    Original Eqn: b'5'
    Units: b'impact/each'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 5


@cache('run')
def recycled_material_strategic_value():
    """
    Real Name: b'recycled material strategic value'
    Original Eqn: b'0'
    Units: b'USD/each'
    Limits: (0.0, 100.0)
    Type: constant

    b'value of using recycled material  - reduces overall cost of recycled \\n    \\t\\tmaterial'
    """
    return 0


@cache('run')
def remanufactured_material_strategic_value():
    """
    Real Name: b'remanufactured material strategic value'
    Original Eqn: b'0'
    Units: b'USD/each'
    Limits: (0.0, 100.0)
    Type: constant

    b'value of using remanufactured material - reduces overall remanufactured \\n    \\t\\tmaterial cost'
    """
    return 0


@cache('run')
def reused_material_strategic_value():
    """
    Real Name: b'reused material strategic value'
    Original Eqn: b'0'
    Units: b'USD/each'
    Limits: (0.0, 100.0)
    Type: constant

    b'negative cost representing the value of using reused material instead of \\n    \\t\\tvirgin'
    """
    return 0


@cache('run')
def miles_from_end_use_location_to_recycling_facility():
    """
    Real Name: b'miles from end use location to recycling facility'
    Original Eqn: b'10'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 10


@cache('run')
def miles_from_end_use_location_to_remanufacturing_facility():
    """
    Real Name: b'miles from end use location to remanufacturing facility'
    Original Eqn: b'10'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 10


@cache('run')
def miles_from_end_use_location_to_reuse_facility():
    """
    Real Name: b'miles from end use location to reuse facility'
    Original Eqn: b'10'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 10


@cache('run')
def miles_from_reuse_facility_to_product_distribution_facility():
    """
    Real Name: b'miles from reuse facility to product distribution facility'
    Original Eqn: b'10'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 10


@cache('run')
def miles_from_reuse_facility_to_remanufacturing_facility():
    """
    Real Name: b'miles from reuse facility to remanufacturing facility'
    Original Eqn: b'0'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 0


@cache('run')
def miles_from_extraction_to_production_facility():
    """
    Real Name: b'miles from extraction to production facility'
    Original Eqn: b'20'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 20


@cache('run')
def miles_from_recycling_facility_to_landfill():
    """
    Real Name: b'miles from recycling facility to landfill'
    Original Eqn: b'10'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 10


@cache('run')
def miles_from_remanufacturing_facility_to_landfill():
    """
    Real Name: b'miles from remanufacturing facility to landfill'
    Original Eqn: b'10'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 10


@cache('run')
def miles_from_end_use_location_to_landfill():
    """
    Real Name: b'miles from end use location to landfill'
    Original Eqn: b'20'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 20


@cache('run')
def miles_from_recycling_to_distribution_facility():
    """
    Real Name: b'miles from recycling to distribution facility'
    Original Eqn: b'10'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 10


@cache('run')
def miles_from_remanufacturing_facility_to_recycling_facility():
    """
    Real Name: b'miles from remanufacturing facility to recycling facility'
    Original Eqn: b'0'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 0


@cache('run')
def miles_from_remanufacturing_facility_to_product_distribution_facility():
    """
    Real Name: b'miles from remanufacturing facility to product distribution facility'
    Original Eqn: b'10'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 10


@cache('run')
def supply_chain_delay():
    """
    Real Name: b'supply chain delay'
    Original Eqn: b'0.5'
    Units: b'year'
    Limits: (0.0, None)
    Type: constant

    b'default value 0.5'
    """
    return 0.5


@cache('run')
def initial_components_in_use():
    """
    Real Name: b'initial components in use'
    Original Eqn: b'0'
    Units: b'each'
    Limits: (0.0, None)
    Type: constant

    b'At the start of the model run, the wind farm has not yet been established \\n    \\t\\tand so no material is in use.'
    """
    return 0


@cache('run')
def fraction_of_recycling_to_landfill():
    """
    Real Name: b'fraction of recycling to landfill'
    Original Eqn: b'0.01'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b'default value 0.01'
    """
    return 0.01


@cache('run')
def fraction_of_remanufacture_to_landfill():
    """
    Real Name: b'fraction of remanufacture to landfill'
    Original Eqn: b'0.01'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b'default value 0.01'
    """
    return 0.01


@cache('run')
def fraction_remanufactured_product_to_recycle():
    """
    Real Name: b'fraction remanufactured product to recycle'
    Original Eqn: b'0.01'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b''
    """
    return 0.01


@cache('run')
def fraction_reused_product_remanufactured():
    """
    Real Name: b'fraction reused product remanufactured'
    Original Eqn: b'0.01'
    Units: b'Dmnl'
    Limits: (None, None)
    Type: constant

    b''
    """
    return 0.01


@cache('step')
def component_lifetime():
    """
    Real Name: b'component lifetime'
    Original Eqn: b'25 - TIME STEP'
    Units: b'year'
    Limits: (0.0, None)
    Type: component

    b'default value 25'
    """
    return 25 - time_step()


@cache('run')
def final_time():
    """
    Real Name: b'FINAL TIME'
    Original Eqn: b'100'
    Units: b'year'
    Limits: (None, None)
    Type: constant

    b'The final time for the simulation.'
    """
    return 100


@cache('run')
def initial_time():
    """
    Real Name: b'INITIAL TIME'
    Original Eqn: b'0'
    Units: b'year'
    Limits: (None, None)
    Type: constant

    b'The initial time for the simulation.'
    """
    return 0


@cache('step')
def saveper():
    """
    Real Name: b'SAVEPER'
    Original Eqn: b'TIME STEP'
    Units: b'year'
    Limits: (0.0, None)
    Type: component

    b'The frequency with which output is stored.'
    """
    return time_step()


@cache('run')
def time_step():
    """
    Real Name: b'TIME STEP'
    Original Eqn: b'0.25'
    Units: b'year'
    Limits: (0.0, None)
    Type: constant

    b'The time step for the simulation.'
    """
    return 0.25


_integ_fraction_reuse = functions.Integ(lambda: changing_fraction_reuse(),
                                        lambda: fraction_used_product_reused_initial_value())

_integ_cumulative_recycle = functions.Integ(lambda: tallying_recycle(), lambda: 0)

_integ_cumulative_remanufacture = functions.Integ(lambda: tallying_remanufacture(), lambda: 0)

_trend_cumulative_recycle_05_0 = functions.Trend(lambda: cumulative_recycle(), lambda: 0.5,
                                                 lambda: 0)

_trend_cumulative_remanufacture_05_0 = functions.Trend(lambda: cumulative_remanufacture(),
                                                       lambda: 0.5, lambda: 0)

_integ_cumulative_reuse = functions.Integ(lambda: tallying_reuse(), lambda: 0)

_trend_cumulative_reuse_05_0 = functions.Trend(lambda: cumulative_reuse(), lambda: 0.5, lambda: 0)

_integ_recycle_process_cost = functions.Integ(lambda: recycle_process_learning(),
                                              lambda: initial_cost_of_recycling_process())

_integ_remanufacture_process_cost = functions.Integ(
    lambda: remanufacture_process_learning(), lambda: initial_cost_of_remanufacturing_process())

_integ_reuse_process_cost = functions.Integ(lambda: reuse_process_learning(),
                                            lambda: initial_cost_of_reuse_process())

_integ_fraction_recycle = functions.Integ(lambda: increasing_fraction_recycle(),
                                          lambda: fraction_used_product_recycled_initial_value())

_integ_fraction_remanufacture = functions.Integ(
    lambda: increasing_fraction_remanufacture(),
    lambda: fraction_used_product_remanufactured_initial_value())

_integ_products_in_use = functions.Integ(lambda: shipping() - reaching_end_of_life(),
                                         lambda: initial_components_in_use())

_integ_products_at_end_of_life = functions.Integ(
    lambda: reaching_end_of_life() - disposing() - recycling() - remanufacturing() - reusing() -
    reusing_in_other_sectors(), lambda: 0)

_integ_products_sent_to_other_sectors = functions.Integ(lambda: reusing_in_other_sectors(),
                                                        lambda: 0)

_integ_raw_material_extraction = functions.Integ(lambda: -extracting(), lambda: 1e+10)

_delay_shipping_roundcomponent_lifetime__time_step___time_step_0_component_lifetime__time_step = functions.Delay(
    lambda: shipping(), lambda: round(component_lifetime() / time_step()) * time_step(), lambda: 0,
    lambda: component_lifetime() / time_step())

_integ_production = functions.Integ(
    lambda: aggregating_remanufactured_products() + distributing() - producing(), lambda: 100)

_integ_material_distribution = functions.Integ(
    lambda: aggregating_recycled_materials() + extracting() - distributing(), lambda: 100)

_integ_landfill_and_incineration = functions.Integ(
    lambda: landfilling() + landfilling_failed_remanufactured() + landfilling_nonrecyclables(),
    lambda: 0)

_integ_landfill_transport = functions.Integ(lambda: disposing() - landfilling(), lambda: 0)

_integ_product_distribution = functions.Integ(
    lambda: aggregating_reused_products() + producing() - shipping(), lambda: 100)

_integ_product_remanufacture = functions.Integ(
    lambda: remanufacturing() + remanufacturing_nonreusables(
    ) - aggregating_remanufactured_products() - landfilling_failed_remanufactured() -
    recycling_failed_remanufactured(), lambda: 0)

_delay_producingaggregating_reused_products_roundsupply_chain_delay__time_step___time_step_0_supply_chain_delay__time_step = functions.Delay(
    lambda: producing() + aggregating_reused_products(),
    lambda: round(supply_chain_delay() / time_step()) * time_step(), lambda: 0,
    lambda: supply_chain_delay() / time_step())

_integ_total_extraction = functions.Integ(lambda: tallying_extraction(), lambda: 0)

_integ_material_recycle = functions.Integ(
    lambda: recycling() + recycling_failed_remanufactured() - aggregating_recycled_materials() -
    landfilling_nonrecyclables(), lambda: 0)

_integ_product_reuse = functions.Integ(
    lambda: reusing() - aggregating_reused_products() - remanufacturing_nonreusables(), lambda: 0)
