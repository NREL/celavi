"""
Python model "natl-wind-importable.py"
Translated using PySD version 0.10.0
"""
from __future__ import division

from pysd.py_backend.functions import cache
from pysd.py_backend import functions
from time import gmtime, strftime
import pandas as pd
import numpy as np
import pdb
_subscript_dict = {}

_namespace = {
    'TIME': 'time',
    'Time': 'time',
    'recycle research annual cost reduction': 'recycle_research_annual_cost_reduction',
    'one metric ton': 'one_metric_ton',
    'one MW': 'one_mw',
    'one Year': 'one_year',
    'tallying recycle': 'tallying_recycle',
    'tallying remanufacture': 'tallying_remanufacture',
    'tallying reuse': 'tallying_reuse',
    'Cumulative Recycle': 'cumulative_recycle',
    'Cumulative Remanufacture': 'cumulative_remanufacture',
    'Cumulative Reuse': 'cumulative_reuse',
    'recycle process cost': 'recycle_process_cost',
    'cost of extraction and production': 'cost_of_extraction_and_production',
    'remanufacture process cost': 'remanufacture_process_cost',
    'reuse process cost': 'reuse_process_cost',
    'miles from extraction to production facility': 'miles_from_extraction_to_production_facility',
    'extraction and production learning rate': 'extraction_and_production_learning_rate',
    'recycle learning rate': 'recycle_learning_rate',
    'initial cost of extraction and production': 'initial_cost_of_extraction_and_production',
    'remanufacture learning rate': 'remanufacture_learning_rate',
    'reuse learning rate': 'reuse_learning_rate',
    'remanufactured material cost': 'remanufactured_material_cost',
    'recycled material cost': 'recycled_material_cost',
    'linear material cost': 'linear_material_cost',
    'reused material cost': 'reused_material_cost',
    'initial cost of recycling process': 'initial_cost_of_recycling_process',
    'initial cost of remanufacturing process': 'initial_cost_of_remanufacturing_process',
    'initial cost of reuse process': 'initial_cost_of_reuse_process',
    'cost of transportation': 'cost_of_transportation',
    'cost of landfilling': 'cost_of_landfilling',
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
    'fiberglass use metric ton per MW': 'fiberglass_use_metric_ton_per_mw',
    'material use per year': 'material_use_per_year',
    'material selection': 'material_selection',
    'steel use metric ton per MW': 'steel_use_metric_ton_per_mw',
    'average turbine capacity': 'average_turbine_capacity',
    'average turbine capacity trendline': 'average_turbine_capacity_trendline',
    'average turbine capacity data': 'average_turbine_capacity_data',
    'adding capacity': 'adding_capacity',
    'Cumulative Capacity': 'cumulative_capacity',
    'installed capacity per year data': 'installed_capacity_per_year_data',
    'Fraction Reuse': 'fraction_reuse',
    'changing fraction reuse': 'changing_fraction_reuse',
    'check fraction sum': 'check_fraction_sum',
    'Fraction Recycle': 'fraction_recycle',
    'Fraction Remanufacture': 'fraction_remanufacture',
    'rate of increasing reuse fraction': 'rate_of_increasing_reuse_fraction',
    'recycle favorability': 'recycle_favorability',
    'recycle favorability over linear': 'recycle_favorability_over_linear',
    'increase recycle': 'increase_recycle',
    'increase remanufacture': 'increase_remanufacture',
    'increase reuse': 'increase_reuse',
    'increasing fraction recycle': 'increasing_fraction_recycle',
    'increasing fraction remanufacture': 'increasing_fraction_remanufacture',
    'lowest cost pathway': 'lowest_cost_pathway',
    'rate of increasing recycle fraction': 'rate_of_increasing_recycle_fraction',
    'rate of increasing remanufacture fraction': 'rate_of_increasing_remanufacture_fraction',
    'reuse favorability': 'reuse_favorability',
    'reuse favorability over linear': 'reuse_favorability_over_linear',
    'remanufacture favorability over linear': 'remanufacture_favorability_over_linear',
    'remanufacture favorability': 'remanufacture_favorability',
    'fraction used product reused initial value': 'fraction_used_product_reused_initial_value',
    'fraction used product recycled initial value': 'fraction_used_product_recycled_initial_value',
    'fraction used product remanufactured initial value':
    'fraction_used_product_remanufactured_initial_value',
    'shipping': 'shipping',
    'Landfill and Incineration': 'landfill_and_incineration',
    'Products Sent to Other Sectors': 'products_sent_to_other_sectors',
    'Products at End of Life': 'products_at_end_of_life',
    'landfilling': 'landfilling',
    'total fraction': 'total_fraction',
    'annual demand': 'annual_demand',
    'aggregating recycled materials': 'aggregating_recycled_materials',
    'aggregating remanufactured products': 'aggregating_remanufactured_products',
    'aggregating reused products': 'aggregating_reused_products',
    'annual virgin material demand': 'annual_virgin_material_demand',
    'Product Reuse': 'product_reuse',
    'distributing': 'distributing',
    'extracting': 'extracting',
    'Raw Material Extraction': 'raw_material_extraction',
    'reaching end of life': 'reaching_end_of_life',
    'recycling': 'recycling',
    'fraction used product disposed': 'fraction_used_product_disposed',
    'remanufacturing': 'remanufacturing',
    'remanufacturing nonreusables': 'remanufacturing_nonreusables',
    'landfilling failed remanufactured': 'landfilling_failed_remanufactured',
    'landfilling nonrecyclables': 'landfilling_nonrecyclables',
    'Material Distribution': 'material_distribution',
    'Material Recycle': 'material_recycle',
    'producing': 'producing',
    'Product Distribution': 'product_distribution',
    'Product Remanufacture': 'product_remanufacture',
    'tallying extraction': 'tallying_extraction',
    'Production': 'production',
    'Products in Use': 'products_in_use',
    'Total Extraction': 'total_extraction',
    'reusing in other sectors': 'reusing_in_other_sectors',
    'recycling failed remanufactured': 'recycling_failed_remanufactured',
    'reusing': 'reusing',
    'fraction used product reused in other sectors':
    'fraction_used_product_reused_in_other_sectors',
    'supply chain delay': 'supply_chain_delay',
    'initial components in use': 'initial_components_in_use',
    'fraction of recycling to landfill': 'fraction_of_recycling_to_landfill',
    'fraction of remanufacture to landfill': 'fraction_of_remanufacture_to_landfill',
    'fraction remanufactured product to recycle': 'fraction_remanufactured_product_to_recycle',
    'fraction reused product remanufactured': 'fraction_reused_product_remanufactured',
    'component lifetime': 'component_lifetime',
    'relative landfill': 'relative_landfill',
    'cumulative landfill fraction': 'cumulative_landfill_fraction',
    'extract prod lci': 'extract_prod_lci',
    'extract prod inputs': 'extract_prod_inputs',
    'transportation lci': 'transportation_lci',
    'extract prod transportation inputs': 'extract_prod_transportation_inputs',
    'recycling transportation inputs': 'recycling_transportation_inputs',
    'remanufacturing transportation inputs': 'remanufacturing_transportation_inputs',
    'reuse transportation inputs': 'reuse_transportation_inputs',
    'transportation inputs': 'transportation_inputs',
    'recycling lci': 'recycling_lci',
    'recycling inputs': 'recycling_inputs',
    'reusing lci': 'reusing_lci',
    'reusing inputs': 'reusing_inputs',
    'remanufacturing lci': 'remanufacturing_lci',
    'remanufacturing inputs': 'remanufacturing_inputs',
    'aggregate inputs': 'aggregate_inputs',
    'FINAL TIME': 'final_time',
    'INITIAL TIME': 'initial_time',
    'SAVEPER': 'saveper',
    'TIME STEP': 'time_step'
}

__pysd_version__ = "0.10.0"

__data = {'scope': None, 'time': lambda: 0}


# read in input data as-is
# @todo Error handling and data checking for LCI data connection?
_lci_input = pd.read_csv('lci.csv')

# Melt to a dataframe with columns: input unit, input name, material,
# process, quantity
# ignore original index columns created when data was read in
lci_melt = pd.melt(_lci_input,
                   id_vars=['input unit', 'input name', 'material'],
                   value_vars=['extraction and production',
                               'transportation',
                               'reusing', 'remanufacturing', 'recycling',
                               'landfilling'],
                   var_name='process', value_name='quantity')

def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


def time():
    return __data['time']()

@cache('run')
def run_id():
    # use the date and time of the model run to identify different results files
    # @todo create functionality to include scenario name or replace date/time with scenario name
    _run_id = strftime('%m-%d-%Y_%H%M%S')

    return _run_id

@cache('run')
def recycle_research_annual_cost_reduction():
    """
    Real Name: b'recycle research annual cost reduction'
    Original Eqn: b'0.003'
    Units: b''
    Limits: (None, None)
    Type: constant

    b''
    """
    return 0.003

@cache('run')
def one_metric_ton():
    """
    Real Name: b'one metric ton'
    Original Eqn: b'1'
    Units: b'metric ton'
    Limits: (None, None)
    Type: constant

    b''
    """
    return 1


@cache('run')
def one_mw():
    """
    Real Name: b'one MW'
    Original Eqn: b'1'
    Units: b'MW'
    Limits: (1.0, 1.0, 1.0)
    Type: constant

    b'Conversion factor for 1 MW'
    """
    return 1


@cache('run')
def one_year():
    """
    Real Name: b'one Year'
    Original Eqn: b'1'
    Units: b'year'
    Limits: (1.0, 1.0)
    Type: constant

    b'Conversion factor for 1 year'
    """
    return 1


@cache('step')
def tallying_recycle():
    """
    Real Name: b'tallying recycle'
    Original Eqn: b'aggregating recycled materials'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return aggregating_recycled_materials()


@cache('step')
def tallying_remanufacture():
    """
    Real Name: b'tallying remanufacture'
    Original Eqn: b'aggregating remanufactured products'
    Units: b'metric ton/year'
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
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return aggregating_reused_products()


@cache('step')
def cumulative_recycle():
    """
    Real Name: b'Cumulative Recycle'
    Original Eqn: b'INTEG ( tallying recycle, 0)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'tracks total recycling in wind energy sector'
    """
    return _integ_cumulative_recycle()


@cache('step')
def cumulative_remanufacture():
    """
    Real Name: b'Cumulative Remanufacture'
    Original Eqn: b'INTEG ( tallying remanufacture, 0)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'tracks total remanufacturing by material mass in wind energy sector'
    """
    return _integ_cumulative_remanufacture()


@cache('step')
def cumulative_reuse():
    """
    Real Name: b'Cumulative Reuse'
    Original Eqn: b'INTEG ( tallying reuse, 0)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'tracks total reusing by material mass (not individual products) in wind \\n    \\t\\tenergy sector'
    """
    return _integ_cumulative_reuse()


@cache('step')
def recycle_process_cost():
    """
    Real Name: b'recycle process cost'
    Original Eqn: b'initial cost of recycling process * (Cumulative Recycle/one metric ton + 1)^(-1*recycle learning rate\\\\ ) - recycle research annual cost reduction * (Time - 1980) * initial cost of recycling process'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return initial_cost_of_recycling_process() * (cumulative_recycle() / one_metric_ton() + 1)**(
        -1 * recycle_learning_rate()) - recycle_research_annual_cost_reduction() * (
            time() - 1980) * initial_cost_of_recycling_process()


@cache('step')
def cost_of_extraction_and_production():
    """
    Real Name: b'cost of extraction and production'
    Original Eqn: b'initial cost of extraction and production * (Total Extraction / one metric ton + 1)^\\\\ (-1*extraction and production learning rate)'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b'time dependent function for total extraction and production cost'
    """
    return initial_cost_of_extraction_and_production() * (
        total_extraction() / one_metric_ton() + 1)**(-1 *
                                                     extraction_and_production_learning_rate())


@cache('step')
def remanufacture_process_cost():
    """
    Real Name: b'remanufacture process cost'
    Original Eqn: b'initial cost of remanufacturing process * (Cumulative Remanufacture/one metric ton +\\\\ 1)^(-1*remanufacture learning rate)'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return initial_cost_of_remanufacturing_process() * (
        cumulative_remanufacture() / one_metric_ton() + 1)**(-1 * remanufacture_learning_rate())


@cache('step')
def reuse_process_cost():
    """
    Real Name: b'reuse process cost'
    Original Eqn: b'initial cost of reuse process * (Cumulative Reuse / one metric ton + 1)^(-1*reuse learning rate\\\\ )'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return initial_cost_of_reuse_process() * (cumulative_reuse() / one_metric_ton() +
                                              1)**(-1 * reuse_learning_rate())


@cache('run')
def miles_from_extraction_to_production_facility():
    """
    Real Name: b'miles from extraction to production facility'
    Original Eqn: b'200'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 200


@cache('run')
def extraction_and_production_learning_rate():
    """
    Real Name: b'extraction and production learning rate'
    Original Eqn: b'-0.357'
    Units: b'USD/metric ton/year'
    Limits: (None, None)
    Type: constant

    b'accounts for learning-by-doing, assuming that extraction and production is \\n    \\t\\talways being used in economy even if not active in this model'
    """
    return -0.357


@cache('run')
def recycle_learning_rate():
    """
    Real Name: b'recycle learning rate'
    Original Eqn: b'0.05'
    Units: b'Dmnl'
    Limits: (None, None)
    Type: constant

    b''
    """
    return 0.05


@cache('run')
def initial_cost_of_extraction_and_production():
    """
    Real Name: b'initial cost of extraction and production'
    Original Eqn: b'65'
    Units: b'USD/metric ton'
    Limits: (0.0, None, 1.0)
    Type: constant

    b''
    """
    return 65


@cache('run')
def remanufacture_learning_rate():
    """
    Real Name: b'remanufacture learning rate'
    Original Eqn: b'0.05'
    Units: b'Dmnl'
    Limits: (None, None)
    Type: constant

    b''
    """
    return 0.05


@cache('run')
def reuse_learning_rate():
    """
    Real Name: b'reuse learning rate'
    Original Eqn: b'0.05'
    Units: b'Dmnl'
    Limits: (-0.2, 0.0)
    Type: constant

    b''
    """
    return 0.05


@cache('step')
def remanufactured_material_cost():
    """
    Real Name: b'remanufactured material cost'
    Original Eqn: b'miles from end use location to remanufacturing facility * cost of transportation + remanufacture process cost + fraction reused product remanufactured * ( miles from reuse facility to remanufacturing facility\\\\ * cost of transportation + remanufacture process cost ) + miles from remanufacturing facility to product distribution facility * cost of transportation - remanufactured material strategic value'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b'Total cost associated with using remanufactured materials in new turbines, \\n    \\t\\tincluding transportation.'
    """
    return miles_from_end_use_location_to_remanufacturing_facility() * cost_of_transportation(
    ) + remanufacture_process_cost() + fraction_reused_product_remanufactured() * (
        miles_from_reuse_facility_to_remanufacturing_facility() * cost_of_transportation() +
        remanufacture_process_cost()
    ) + miles_from_remanufacturing_facility_to_product_distribution_facility(
    ) * cost_of_transportation() - remanufactured_material_strategic_value()


@cache('step')
def recycled_material_cost():
    """
    Real Name: b'recycled material cost'
    Original Eqn: b'miles from end use location to recycling facility * cost of transportation + recycle process cost + fraction remanufactured product to recycle * ( miles from remanufacturing facility to recycling facility\\\\ * cost of transportation + recycle process cost ) + miles from recycling to distribution facility * cost of transportation - recycled material strategic value'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b'Total cost associated with using recycled materials in new turbines, \\n    \\t\\tincluding transportation.'
    """
    return miles_from_end_use_location_to_recycling_facility() * cost_of_transportation(
    ) + recycle_process_cost() + fraction_remanufactured_product_to_recycle() * (
        miles_from_remanufacturing_facility_to_recycling_facility() * cost_of_transportation() +
        recycle_process_cost()) + miles_from_recycling_to_distribution_facility(
        ) * cost_of_transportation() - recycled_material_strategic_value()


@cache('step')
def linear_material_cost():
    """
    Real Name: b'linear material cost'
    Original Eqn: b'cost of extraction and production + miles from extraction to production facility * cost of transportation + miles from end use location to landfill * cost of transportation + miles from remanufacturing facility to landfill * cost of transportation + miles from recycling facility to landfill * cost of transportation + cost of landfilling'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b'Total cost associated with using virgin materials in new turbines and then \\n    \\t\\tlandfilling those materials at end of life, including transportation'
    """
    return cost_of_extraction_and_production() + miles_from_extraction_to_production_facility(
    ) * cost_of_transportation() + miles_from_end_use_location_to_landfill(
    ) * cost_of_transportation() + miles_from_remanufacturing_facility_to_landfill(
    ) * cost_of_transportation() + miles_from_recycling_facility_to_landfill(
    ) * cost_of_transportation() + cost_of_landfilling()


@cache('step')
def reused_material_cost():
    """
    Real Name: b'reused material cost'
    Original Eqn: b'miles from end use location to reuse facility * cost of transportation + reuse process cost + miles from reuse facility to product distribution facility * cost of transportation - reused material strategic value'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b'Total cost associated with using reused materials in new turbines, \\n    \\t\\tincluding transportation.'
    """
    return miles_from_end_use_location_to_reuse_facility() * cost_of_transportation(
    ) + reuse_process_cost() + miles_from_reuse_facility_to_product_distribution_facility(
    ) * cost_of_transportation() - reused_material_strategic_value()


@cache('run')
def initial_cost_of_recycling_process():
    """
    Real Name: b'initial cost of recycling process'
    Original Eqn: b'200'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 200


@cache('run')
def initial_cost_of_remanufacturing_process():
    """
    Real Name: b'initial cost of remanufacturing process'
    Original Eqn: b'250'
    Units: b'USD/metric ton'
    Limits: (0.0, None, 0.01)
    Type: constant

    b''
    """
    return 250


@cache('run')
def initial_cost_of_reuse_process():
    """
    Real Name: b'initial cost of reuse process'
    Original Eqn: b'125'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: constant

    b''
    """
    return 125


@cache('step')
def cost_of_transportation():
    """
    Real Name: b'cost of transportation'
    Original Eqn: b'WITH LOOKUP ( Time, ([(1980,0)-(2050,0.5)],(1980,0.5),(2020,0.5),(2050,0.5) ))'
    Units: b'USD/metric ton/mile'
    Limits: (0.0, None)
    Type: component

    b'NREL technical report, "Analysis of Transportation and Logistics \\n    \\t\\tChallenges Affecting the Deployment of Larger Wind Turbines: Summary of \\n    \\t\\tResults"'
    """
    return functions.lookup(time(), [1980, 2020, 2050], [0.5, 0.5, 0.5])


@cache('step')
def cost_of_landfilling():
    """
    Real Name: b'cost of landfilling'
    Original Eqn: b'WITH LOOKUP ( Time, ([(1980,60)-(2050,100)],(1980,95),(2050,95) ))'
    Units: b'USD/metric ton'
    Limits: (0.0, None)
    Type: component

    b'$70 - $120 USD/metric ton is the range from source, "Construction and Demolition \\n    \\t\\tWaste Characterization and Market Analysis Report", prepared for CT Dept \\n    \\t\\tof Energy and Env Protection by Green Seal Environmental, Inc.\\t\\tValue used is midpoint of the above range.'
    """
    return functions.lookup(time(), [1980, 2050], [95, 95])


@cache('run')
def recycled_material_strategic_value():
    """
    Real Name: b'recycled material strategic value'
    Original Eqn: b'0'
    Units: b'USD/metric ton'
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
    Units: b'USD/metric ton'
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
    Units: b'USD/metric ton'
    Limits: (0.0, 100.0)
    Type: constant

    b'value of using reused materials - reduces overall reused material cost'
    """
    return 0


@cache('run')
def miles_from_end_use_location_to_recycling_facility():
    """
    Real Name: b'miles from end use location to recycling facility'
    Original Eqn: b'100'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 100


@cache('run')
def miles_from_end_use_location_to_remanufacturing_facility():
    """
    Real Name: b'miles from end use location to remanufacturing facility'
    Original Eqn: b'100'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 100


@cache('run')
def miles_from_end_use_location_to_reuse_facility():
    """
    Real Name: b'miles from end use location to reuse facility'
    Original Eqn: b'100'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 100


@cache('run')
def miles_from_reuse_facility_to_product_distribution_facility():
    """
    Real Name: b'miles from reuse facility to product distribution facility'
    Original Eqn: b'100'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 100


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
def miles_from_recycling_facility_to_landfill():
    """
    Real Name: b'miles from recycling facility to landfill'
    Original Eqn: b'100'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 100


@cache('run')
def miles_from_remanufacturing_facility_to_landfill():
    """
    Real Name: b'miles from remanufacturing facility to landfill'
    Original Eqn: b'100'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 100


@cache('run')
def miles_from_end_use_location_to_landfill():
    """
    Real Name: b'miles from end use location to landfill'
    Original Eqn: b'200'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 200


@cache('run')
def miles_from_recycling_to_distribution_facility():
    """
    Real Name: b'miles from recycling to distribution facility'
    Original Eqn: b'100'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 100


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
    Original Eqn: b'100'
    Units: b'mile'
    Limits: (0.0, 500.0, 1.0)
    Type: constant

    b''
    """
    return 100


@cache('step')
def fiberglass_use_metric_ton_per_mw():
    """
    Real Name: b'fiberglass use metric ton per MW'
    Original Eqn: b'WITH LOOKUP ( average turbine capacity, ([(0,0)-(10,20)],(0.001,14.35),(0.1,14.05),(0.2,13.75),(0.5,12.84),(1,11.32),(1.5,9.8\\\\ ),(2,8.281),(2.5,6.762),(3,6.8),(10,6.8) ))'
    Units: b'metric ton/MW'
    Limits: (0.0, None)
    Type: component

    b'Data taken from and interpolated from USGS Wind Energy in the US report, values for \\n    \\t\\tfiberglass.\\t\\tApproximate fiberglass use in metric tons per MW turbine nameplate \\n    \\t\\tcapacity, developed from USGS data tables and estimated change in \\n    \\t\\tfiberglass use per change in MW.'
    """
    return functions.lookup(average_turbine_capacity(),
                            [0.001, 0.1, 0.2, 0.5, 1, 1.5, 2, 2.5, 3, 10],
                            [14.35, 14.05, 13.75, 12.84, 11.32, 9.8, 8.281, 6.762, 6.8, 6.8])


@cache('step')
def material_use_per_year():
    """
    Real Name: b'material use per year'
    Original Eqn: b'installed capacity per year data * ( steel use metric ton per MW*material selection + fiberglass use metric ton per MW\\\\ *(1-material selection) )'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Converts installed capacity data to material use using the materal use per MW data \\n    \\t\\tfor either steel or fiberglass, depending on the value of material \\n    \\t\\tselection. \\t\\tmaterial selection is a Boolean parameter that controls whether the steel \\n    \\t\\tor fiberglass data is used in this calculation'
    """
    return installed_capacity_per_year_data() * (
        steel_use_metric_ton_per_mw() * material_selection() + fiberglass_use_metric_ton_per_mw() *
        (1 - material_selection()))


@cache('run')
def material_selection():
    """
    Real Name: b'material selection'
    Original Eqn: b'1'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 1.0)
    Type: constant

    b'select 1 for steel, 0 for fiberglass'
    """
    return 1


@cache('step')
def steel_use_metric_ton_per_mw():
    """
    Real Name: b'steel use metric ton per MW'
    Original Eqn: b'WITH LOOKUP ( average turbine capacity, ([(0,0)-(6,200)],(0,0),(0.001,132.1),(0.01,132.1),(0.1,131.1),(0.5,126.5),(1,120.75\\\\ ),(1.5,115),(2,109.2),(2.5,103.5),(3,103),(3.5,102.5),(4,102),(4.5,101.5),(5,101),(\\\\ 6,100) ))'
    Units: b'metric ton/MW'
    Limits: (0.0, None)
    Type: component

    b'Approximate steel use in metric tons per MW turbine nameplate capacity, \\n    \\t\\tdeveloped from USGS data tables and estimated change in steel use per \\n    \\t\\tchange in MW.'
    """
    return functions.lookup(average_turbine_capacity(),
                            [0, 0.001, 0.01, 0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6], [
                                0, 132.1, 132.1, 131.1, 126.5, 120.75, 115, 109.2, 103.5, 103,
                                102.5, 102, 101.5, 101, 100
                            ])


@cache('step')
def average_turbine_capacity():
    """
    Real Name: b'average turbine capacity'
    Original Eqn: b'IF THEN ELSE(Time <= 2019, average turbine capacity data, average turbine capacity trendline)'
    Units: b'MW'
    Limits: (0.0, None)
    Type: component

    b'Switch variable that returns the historical capacity data for 2019 and \\n    \\t\\tprior time steps, and the trendline projections for times after 2019.'
    """
    return functions.if_then_else(time() <= 2019, average_turbine_capacity_data(),
                                  average_turbine_capacity_trendline())


@cache('step')
def average_turbine_capacity_trendline():
    """
    Real Name: b'average turbine capacity trendline'
    Original Eqn: b'one MW * (0.0694 * Time / one Year - 137.81)'
    Units: b'MW'
    Limits: (None, None)
    Type: component

    b'Linear trendline based on average turbine capacity data from the US Wind \\n    \\t\\tTurbine Database (same data as in average turbine capacity data)'
    """
    return one_mw() * (0.0694 * time() / one_year() - 137.81)


@cache('step')
def average_turbine_capacity_data():
    """
    Real Name: b'average turbine capacity data'
    Original Eqn: b'WITH LOOKUP ( Time, ([(0,0)-(2019,10)],(1980,0.1),(2019,2.1) ))'
    Units: b'MW'
    Limits: (None, None)
    Type: component

    b'Historical data on the average turbine capacity installed in each year \\n    \\t\\t1980 - 2019'
    """
    capacity_data = pd.read_csv('wind.csv',
                                usecols=['year', 'avg turbine capacity mw'])

    return functions.lookup(time(),
                            np.array(capacity_data['year']),
                            np.array(capacity_data['avg turbine capacity mw']))


@cache('step')
def adding_capacity():
    """
    Real Name: b'adding capacity'
    Original Eqn: b'installed capacity per year data'
    Units: b'MW/year'
    Limits: (0.0, None)
    Type: component

    b'Converts installed capacity data into a flow for cumulative tracking'
    """
    return installed_capacity_per_year_data()


@cache('step')
def cumulative_capacity():
    """
    Real Name: b'Cumulative Capacity'
    Original Eqn: b'INTEG ( adding capacity/TIME STEP, 0)'
    Units: b'MW'
    Limits: (0.0, None)
    Type: component

    b'Cumulative installed turbine capacity without accounting for turbines \\n    \\t\\taging out of use and not being replaced'
    """
    return _integ_cumulative_capacity()


@cache('step')
def installed_capacity_per_year_data():
    """
    Real Name: b'installed capacity per year data'
    Original Eqn: b'WITH LOOKUP ( Time, ([(1980,0)-(2050,40)],(1980,1),(1990,10),(2000,20),(2010,40),(2020,30),(2030,30),(2040\\\\ ,30),(2050,30) ))'
    Units: b'MW/year'
    Limits: (0.0, None)
    Type: component

    b'Contains historical data on installed turbine capacity for years 1980 - \\n    \\t\\t2019 and projected installation for years 2020 - 2050.'
    """
    installation_data = pd.read_csv('wind.csv', usecols=['year', 'mw installed'])

    return functions.lookup(time(),
                            np.array(installation_data['year']),
                            np.array(installation_data['mw installed']))


@cache('step')
def fraction_reuse():
    """
    Real Name: b'Fraction Reuse'
    Original Eqn: b'INTEG ( changing fraction reuse, fraction used product reused initial value)'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b'fraction of end-of-life material sent to remanufacturing in each time \\n    \\t\\tstep, before system losses and leakage'
    """
    return _integ_fraction_reuse()


@cache('step')
def changing_fraction_reuse():
    """
    Real Name: b'changing fraction reuse'
    Original Eqn: b'IF THEN ELSE(check fraction sum < 1 - rate of increasing reuse fraction :AND: Fraction Reuse < 1 - rate of increasing reuse fraction, increase reuse * rate of increasing reuse fraction / TIME STEP, 0)'
    Units: b'Dmnl/year'
    Limits: (None, None)
    Type: component

    b'Increases the fraction of end-of-life material sent through the reuse \\n    \\t\\tpathway, if that increase will not put the total fraction of material sent \\n    \\t\\tthrough circular pathways or the fraction sent to reuse over 1'
    """
    return functions.if_then_else(
        check_fraction_sum() < 1 - rate_of_increasing_reuse_fraction()
        and fraction_reuse() < 1 - rate_of_increasing_reuse_fraction(),
        increase_reuse() * rate_of_increasing_reuse_fraction() / time_step(), 0)


@cache('step')
def check_fraction_sum():
    """
    Real Name: b'check fraction sum'
    Original Eqn: b'Fraction Reuse + Fraction Remanufacture + Fraction Recycle'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b'adds the material fractions sent through circularity pathways as a mass \\n    \\t\\tbalance check'
    """
    return fraction_reuse() + fraction_remanufacture() + fraction_recycle()


@cache('step')
def fraction_recycle():
    """
    Real Name: b'Fraction Recycle'
    Original Eqn: b'INTEG ( increasing fraction recycle, fraction used product recycled initial value)'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b'fraction of end-of-life material sent to recycling in each time step, \\n    \\t\\tbefore system losses and leakage'
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

    b'fraction of end-of-life material sent to remanufacturing in each time \\n    \\t\\tstep, before system losses and leakage'
    """
    return _integ_fraction_remanufacture()


@cache('step')
def rate_of_increasing_reuse_fraction():
    """
    Real Name: b'rate of increasing reuse fraction'
    Original Eqn: b'WITH LOOKUP ( reuse favorability, ([(0,0)-(10,0.01)],(0,0.0075),(0.275229,0.006),(0.519878,0.005),(0.99,0.004),(1,0),\\\\ (2,0),(10,0) ))'
    Units: b'Dmnl'
    Limits: (None, None)
    Type: component

    b'\\n    !reuse favorability\\n    !rate of increasing fraction reuse\\t\\tGraphical function translating degree of favorability that reuse has over \\n    \\t\\tthe other circular pathways into an increase in the fraction of \\n    \\t\\tend-of-life materials sent to reuse'
    """
    return functions.lookup(reuse_favorability(), [0, 0.275229, 0.519878, 0.99, 1, 2, 10],
                            [0.0075, 0.006, 0.005, 0.004, 0, 0, 0])


@cache('step')
def recycle_favorability():
    """
    Real Name: b'recycle favorability'
    Original Eqn: b'IF THEN ELSE(lowest cost pathway = recycle favorability over linear, recycle favorability over linear, 10)'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b'Returns recycle favorability over linear only if recycling is the lowest \\n    \\t\\tcost among the circular pathways; otherwise, returns 10 and recycling is \\n    \\t\\tnot implemented/increased in that time step'
    """
    return functions.if_then_else(lowest_cost_pathway() == recycle_favorability_over_linear(),
                                  recycle_favorability_over_linear(), 10)


@cache('step')
def recycle_favorability_over_linear():
    """
    Real Name: b'recycle favorability over linear'
    Original Eqn: b'recycled material cost / linear material cost'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b'Ratio of recycled to linear material cost. A lower favorability value \\n    \\t\\tindicates a lower-cost pathway'
    """
    return recycled_material_cost() / linear_material_cost()


@cache('step')
def increase_recycle():
    """
    Real Name: b'increase recycle'
    Original Eqn: b'IF THEN ELSE(recycle favorability over linear < 1, 1, 0)'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b'Returns 1 if recycling is lower cost compared to the linear pathway. This \\n    \\t\\tmakes it possible to implement or increase recycling, if recycling is also \\n    \\t\\tlowest cost compared to the other circular pathways. Otherwise, recycling \\n    \\t\\tis not implemented/increased.'
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

    b'Returns 1 if remanufacturing is lower cost compared to the linear pathway. \\n    \\t\\tThis makes it possible to implement or increase remanufacturing, if \\n    \\t\\tremanufacturing is also lowest cost compared to the other circular \\n    \\t\\tpathways. Otherwise, remanufacturing is not implemented/increased.'
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

    b'Returns 1 if reusing is lower cost compared to the linear pathway. This \\n    \\t\\tmakes it possible to implement or increase reusing, if reusing is also \\n    \\t\\tlowest cost compared to the other circular pathways. Otherwise, reusing is \\n    \\t\\tnot implemented/increased.'
    """
    return functions.if_then_else(reuse_favorability_over_linear() < 1, 1, 0)


@cache('step')
def increasing_fraction_recycle():
    """
    Real Name: b'increasing fraction recycle'
    Original Eqn: b'IF THEN ELSE(check fraction sum < 1 - rate of increasing recycle fraction :AND: Fraction Recycle < 1 - rate of increasing recycle fraction, increase recycle * rate of increasing recycle fraction / TIME STEP, 0)'
    Units: b'Dmnl/year'
    Limits: (None, None)
    Type: component

    b'Defines the conditions under which the fraction of end-of-life material \\n    \\t\\tsent to recycling increases. The total material fraction sent through \\n    \\t\\tcircular pathways, including the prospective increase in recycling (rate \\n    \\t\\tof increasing recycle fraction), must be less than 1. The recycle \\n    \\t\\tfraction, including the prospective increase, must also be less than 1. \\n    \\t\\tUnder those conditions, the prospective increase in recycling is \\n    \\t\\timplemented.'
    """
    return functions.if_then_else(
        check_fraction_sum() < 1 - rate_of_increasing_recycle_fraction()
        and fraction_recycle() < 1 - rate_of_increasing_recycle_fraction(),
        increase_recycle() * rate_of_increasing_recycle_fraction() / time_step(), 0)


@cache('step')
def increasing_fraction_remanufacture():
    """
    Real Name: b'increasing fraction remanufacture'
    Original Eqn: b'IF THEN ELSE(check fraction sum < 1 - rate of increasing remanufacture fraction :AND: Fraction Remanufacture < 1 - rate of increasing remanufacture fraction, increase remanufacture * rate of increasing remanufacture fraction / TIME STEP\\\\ , 0)'
    Units: b'Dmnl/year'
    Limits: (None, None)
    Type: component

    b'Defines the conditions under which the fraction of end-of-life material \\n    \\t\\tsent to remanufacturing increases. The total material fraction sent \\n    \\t\\tthrough circular pathways, including the prospective increase in \\n    \\t\\tremanufacturing (rate of increasing remanufacture fraction), must be less \\n    \\t\\tthan 1. The remanufacture fraction, including the prospective increase, \\n    \\t\\tmust also be less than 1. Under those conditions, the prospective increase \\n    \\t\\tin remanufacturing is implemented.'
    """
    return functions.if_then_else(
        check_fraction_sum() < 1 - rate_of_increasing_remanufacture_fraction()
        and fraction_remanufacture() < 1 - rate_of_increasing_remanufacture_fraction(),
        increase_remanufacture() * rate_of_increasing_remanufacture_fraction() / time_step(), 0)


@cache('step')
def lowest_cost_pathway():
    """
    Real Name: b'lowest cost pathway'
    Original Eqn: b'MIN(reuse favorability over linear, MIN(remanufacture favorability over linear, MIN(recycle favorability over linear, 1000)))'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b'Uses nested MINs in place of deleted MIN LIST macro'
    """
    return np.minimum(
        reuse_favorability_over_linear(),
        np.minimum(remanufacture_favorability_over_linear(),
                   np.minimum(recycle_favorability_over_linear(), 1000)))


@cache('step')
def rate_of_increasing_recycle_fraction():
    """
    Real Name: b'rate of increasing recycle fraction'
    Original Eqn: b'WITH LOOKUP ( recycle favorability, ([(0,0)-(10,0.01)],(0,0.01),(0.275229,0.00964912),(0.422018,0.00995614),(1,0.0090825\\\\ ),(1.40673,0.00929825),(2,0),(10,0 ) ))'
    Units: b'Dmnl'
    Limits: (None, None)
    Type: component

    b'\\n    !recycle favorability\\t\\tGraphical function translating degree of favorability that recycle has \\n    \\t\\tover the other circular pathways into an increase in the fraction of \\n    \\t\\tend-of-life materials sent to recycling'
    """
    return functions.lookup(recycle_favorability(), [0, 0.275229, 0.422018, 1, 1.40673, 2, 10],
                            [0.01, 0.00964912, 0.00995614, 0.0090825, 0.00929825, 0, 0])


@cache('step')
def rate_of_increasing_remanufacture_fraction():
    """
    Real Name: b'rate of increasing remanufacture fraction'
    Original Eqn: b'WITH LOOKUP ( remanufacture favorability, ([(0,0)-(10,0.008)],(0,0.00736842),(0.165138,0.00526316),(0.360856,0.00342105),(0.550459\\\\ ,0.00184211),(1,0),(2,0),(10,0 ) ))'
    Units: b'Dmnl'
    Limits: (None, None)
    Type: component

    b'\\n    !remanufacture favorability\\t\\tGraphical function translating degree of favorability that remanufacture \\n    \\t\\thas over the other circular pathways into an increase in the fraction of \\n    \\t\\tend-of-life materials sent to remanufacture'
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

    b'Returns reuse favorability over linear only if reusing is the lowest cost \\n    \\t\\tamong the circular pathways; otherwise, returns 10 and reusing is not \\n    \\t\\timplemented/increased in that time step'
    """
    return functions.if_then_else(lowest_cost_pathway() == reuse_favorability_over_linear(),
                                  reuse_favorability_over_linear(), 10)


@cache('step')
def reuse_favorability_over_linear():
    """
    Real Name: b'reuse favorability over linear'
    Original Eqn: b'reused material cost / linear material cost'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b'Ratio of reused to linear material cost. A lower favorability value, less \\n    \\t\\tthan 1, indicates a lower-cost pathway'
    """
    return reused_material_cost() / linear_material_cost()


@cache('step')
def remanufacture_favorability_over_linear():
    """
    Real Name: b'remanufacture favorability over linear'
    Original Eqn: b'remanufactured material cost / linear material cost'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b'Ratio of remanufactured to linear material cost. A lower favorability \\n    \\t\\tvalue, less than 1, indicates a lower-cost pathway'
    """
    return remanufactured_material_cost() / linear_material_cost()


@cache('step')
def remanufacture_favorability():
    """
    Real Name: b'remanufacture favorability'
    Original Eqn: b'IF THEN ELSE(lowest cost pathway = remanufacture favorability over linear, remanufacture favorability over linear, 10)'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b'Returns remanufacture favorability over linear only if remanufacturing is \\n    \\t\\tthe lowest cost among the circular pathways; otherwise, returns 10 and \\n    \\t\\tremanufacturing is not implemented/increased in that time step'
    """
    return functions.if_then_else(
        lowest_cost_pathway() == remanufacture_favorability_over_linear(),
        remanufacture_favorability_over_linear(), 10)


@cache('run')
def fraction_used_product_reused_initial_value():
    """
    Real Name: b'fraction used product reused initial value'
    Original Eqn: b'0'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b'Fraction of end-of-life material sent to the reuse pathway at the \\n    \\t\\tbeginning of the model run, year 1980.'
    """
    return 0


@cache('run')
def fraction_used_product_recycled_initial_value():
    """
    Real Name: b'fraction used product recycled initial value'
    Original Eqn: b'0.3'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b'Fraction of end-of-life material sent to the recycle pathway at the beginning of the \\t\\n    \\t\\tmodel run, year 1980.\\t\\tStarting value is an estimate of early-80s steel recycling rates, \\n    \\t\\tapproximated from a 1991 steel production statistic from the USGS Iron & \\n    \\t\\tSteel Mineral Commodity Summary from 1996. Source link: \\n    \\t\\thttps://s3-us-west-2.amazonaws.com/prd-wret/assets/palladium/production/min\\n    \\t\\teral-pubs/iron-steel/isteemcs96.pdf'
    """
    return 0.3


@cache('run')
def fraction_used_product_remanufactured_initial_value():
    """
    Real Name: b'fraction used product remanufactured initial value'
    Original Eqn: b'0'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b'Fraction of end-of-life material sent to the remanufacture pathway at the \\n    \\t\\tbeginning of the model run, year 1980.'
    """
    return 0


@cache('step')
def shipping():
    """
    Real Name: b'shipping'
    Original Eqn: b'DELAY1(producing + aggregating reused products, supply chain delay)'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'reused products are combined with newly manufactured and remanufactured \\n    \\t\\tproducts, with an assumed delay caused by supply chain logistics'
    """
    return _delay_producingaggregating_reused_products_supply_chain_delay_producingaggregating_reused_products_1(
    )


@cache('step')
def landfill_and_incineration():
    """
    Real Name: b'Landfill and Incineration'
    Original Eqn: b'INTEG ( landfilling+landfilling failed remanufactured+landfilling nonrecyclables, 0)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'Accumulates total end-of-life materials landfilled or incinerated; \\n    \\t\\tRepresents total system losses.'
    """
    return _integ_landfill_and_incineration()


@cache('step')
def products_sent_to_other_sectors():
    """
    Real Name: b'Products Sent to Other Sectors'
    Original Eqn: b'INTEG ( reusing in other sectors, 0)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'Accumulates the mass of end-of-life materials that leave the energy \\n    \\t\\ttechnology system for another sector, instead of being kept within the \\n    \\t\\toriginal system'
    """
    return _integ_products_sent_to_other_sectors()


@cache('step')
def products_at_end_of_life():
    """
    Real Name: b'Products at End of Life'
    Original Eqn: b'INTEG ( reaching end of life-landfilling-recycling-remanufacturing-reusing-reusing in other sectors\\\\ , 0)'
    Units: b'metric ton'
    Limits: (-1.0, None)
    Type: component

    b'Flow splitter'
    """
    return _integ_products_at_end_of_life()


@cache('step')
def landfilling():
    """
    Real Name: b'landfilling'
    Original Eqn: b'reaching end of life - reusing - remanufacturing - recycling - reusing in other sectors'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return reaching_end_of_life() - reusing() - remanufacturing() - recycling(
    ) - reusing_in_other_sectors()


@cache('step')
def total_fraction():
    """
    Real Name: b'total fraction'
    Original Eqn: b'fraction used product disposed+check fraction sum+fraction used product reused in other sectors'
    Units: b''
    Limits: (None, None)
    Type: component

    b''
    """
    return fraction_used_product_disposed() + check_fraction_sum(
    ) + fraction_used_product_reused_in_other_sectors()


@cache('step')
def annual_demand():
    """
    Real Name: b'annual demand'
    Original Eqn: b'material use per year'
    Units: b'metric ton/year'
    Limits: (0.0, None, 10000.0)
    Type: component

    b'quantifies demand for materials of all type going into newly installed \\n    \\t\\twind turbines in each time step'
    """
    return material_use_per_year()


@cache('step')
def aggregating_recycled_materials():
    """
    Real Name: b'aggregating recycled materials'
    Original Eqn: b'MIN(recycling + recycling failed remanufactured - landfilling nonrecyclables, 0.99*annual demand\\\\ )'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Total recycled materials available in each time step, accounting for \\n    \\t\\tleakage'
    """
    return np.minimum(
        recycling() + recycling_failed_remanufactured() - landfilling_nonrecyclables(),
        0.99 * annual_demand())


@cache('step')
def aggregating_remanufactured_products():
    """
    Real Name: b'aggregating remanufactured products'
    Original Eqn: b'remanufacturing + remanufacturing nonreusables - landfilling failed remanufactured - recycling failed remanufactured'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Total remanufactured materials available in each time step, accounting for \\n    \\t\\tleakage'
    """
    return remanufacturing() + remanufacturing_nonreusables() - landfilling_failed_remanufactured(
    ) - recycling_failed_remanufactured()


@cache('step')
def aggregating_reused_products():
    """
    Real Name: b'aggregating reused products'
    Original Eqn: b'reusing - remanufacturing nonreusables'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Total reused materials available in each time step, accounting for leakage'
    """
    return reusing() - remanufacturing_nonreusables()


@cache('step')
def annual_virgin_material_demand():
    """
    Real Name: b'annual virgin material demand'
    Original Eqn: b'MAX(0, annual demand - aggregating recycled materials - aggregating reused products - aggregating remanufactured products\\\\ )'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Takes the difference between total material demand and available secondary \\n    \\t\\tmaterial, to calculate the quantity of virgin material needed'
    """
    return np.maximum(
        0,
        annual_demand() - aggregating_recycled_materials() - aggregating_reused_products() -
        aggregating_remanufactured_products())


@cache('step')
def product_reuse():
    """
    Real Name: b'Product Reuse'
    Original Eqn: b'INTEG ( reusing-aggregating reused products-remanufacturing nonreusables, 0)'
    Units: b'metric ton'
    Limits: (-10.0, 10.0)
    Type: component

    b'Flow aggregator and splitter'
    """
    return _integ_product_reuse()


@cache('step')
def distributing():
    """
    Real Name: b'distributing'
    Original Eqn: b'extracting + aggregating recycled materials'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Recycled materials and freshly extracted virgin materials are aggregated \\n    \\t\\tand sent to material distribution'
    """
    return extracting() + aggregating_recycled_materials()


@cache('step')
def extracting():
    """
    Real Name: b'extracting'
    Original Eqn: b'annual virgin material demand'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b''
    """
    return annual_virgin_material_demand()


@cache('step')
def raw_material_extraction():
    """
    Real Name: b'Raw Material Extraction'
    Original Eqn: b'INTEG ( -extracting, 1e+15)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'Tracks cumulative raw material extraction. Starting value is set \\n    \\t\\tarbitrarily high.'
    """
    return _integ_raw_material_extraction()


@cache('step')
def reaching_end_of_life():
    """
    Real Name: b'reaching end of life'
    Original Eqn: b'DELAY N(shipping, component lifetime , 0 , 1 )'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Outflow of materials in turbines at end-of-life'
    """
    return _delay_shipping_component_lifetime_0_1()


@cache('step')
def recycling():
    """
    Real Name: b'recycling'
    Original Eqn: b'INTEGER(reaching end of life * Fraction Recycle)'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Materials in end-of-life products being sent for recycling - will be \\n    \\t\\tbroken down into component materials and re-made into a functionally new \\n    \\t\\tproduct'
    """
    return int(reaching_end_of_life() * fraction_recycle())


@cache('step')
def fraction_used_product_disposed():
    """
    Real Name: b'fraction used product disposed'
    Original Eqn: b'1 - Fraction Reuse - fraction used product reused in other sectors - Fraction Remanufacture\\\\ - Fraction Recycle'
    Units: b'Dmnl'
    Limits: (0.0, 1.0)
    Type: component

    b'Fraction of end-of-life materials not sent to a circular pathway or \\n    \\t\\tanother sector, calculated by difference. Logic checks on the circularity \\n    \\t\\tfractions ensure the disposed fraction does not drop below 0.'
    """
    return 1 - fraction_reuse() - fraction_used_product_reused_in_other_sectors(
    ) - fraction_remanufacture() - fraction_recycle()


@cache('step')
def remanufacturing():
    """
    Real Name: b'remanufacturing'
    Original Eqn: b'reaching end of life * Fraction Remanufacture'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Materials in end-of-life products being sent for remanufacturing'
    """
    return reaching_end_of_life() * fraction_remanufacture()


@cache('step')
def remanufacturing_nonreusables():
    """
    Real Name: b'remanufacturing nonreusables'
    Original Eqn: b'reusing * fraction reused product remanufactured'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Leakage from the reuse pathway to the remanufacture pathway. Represents \\n    \\t\\tmaterials in products where reuse was attempted but not possible.'
    """
    return reusing() * fraction_reused_product_remanufactured()


@cache('step')
def landfilling_failed_remanufactured():
    """
    Real Name: b'landfilling failed remanufactured'
    Original Eqn: b'(remanufacturing + remanufacturing nonreusables) * fraction of remanufacture to landfill'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'System loss representing materials in products that were sent for \\n    \\t\\tremanufacturing but were lost along the way'
    """
    return (remanufacturing() +
            remanufacturing_nonreusables()) * fraction_of_remanufacture_to_landfill()


@cache('step')
def landfilling_nonrecyclables():
    """
    Real Name: b'landfilling nonrecyclables'
    Original Eqn: b'(recycling + recycling failed remanufactured) * fraction of recycling to landfill'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'System loss representing materials that were too contaminated or \\n    \\t\\tothwerwise could not be recycled'
    """
    return (recycling() + recycling_failed_remanufactured()) * fraction_of_recycling_to_landfill()


@cache('step')
def material_distribution():
    """
    Real Name: b'Material Distribution'
    Original Eqn: b'INTEG ( aggregating recycled materials+extracting-distributing, 0)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'Flow aggregator. Value should remain very close to zero (allowing for some \\n    \\t\\trounding error) throughout model run'
    """
    return _integ_material_distribution()


@cache('step')
def material_recycle():
    """
    Real Name: b'Material Recycle'
    Original Eqn: b'INTEG ( recycling + recycling failed remanufactured - aggregating recycled materials - landfilling nonrecyclables, 0)'
    Units: b'metric ton'
    Limits: (-0.1, None)
    Type: component

    b'Flow aggregator and splitter. Value should remain very close to zero \\n    \\t\\tthroughout model run.'
    """
    return _integ_material_recycle()


@cache('step')
def producing():
    """
    Real Name: b'producing'
    Original Eqn: b'distributing + aggregating remanufactured products'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'remanufactured products and newly manufactured products containing virgin \\n    \\t\\tmaterials and/or recycled materials'
    """
    return distributing() + aggregating_remanufactured_products()


@cache('step')
def product_distribution():
    """
    Real Name: b'Product Distribution'
    Original Eqn: b'INTEG ( aggregating reused products + producing - shipping, 0)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'Flow aggregator. Value should remain very close to zero (allowing for some \\n    \\t\\trounding error) throughout model run'
    """
    return _integ_product_distribution()


@cache('step')
def product_remanufacture():
    """
    Real Name: b'Product Remanufacture'
    Original Eqn: b'INTEG ( remanufacturing + remanufacturing nonreusables - aggregating remanufactured products - landfilling failed remanufactured - recycling failed remanufactured, 0)'
    Units: b'metric ton'
    Limits: (-10.0, 10.0)
    Type: component

    b'Flow aggregator and splitter'
    """
    return _integ_product_remanufacture()


@cache('step')
def tallying_extraction():
    """
    Real Name: b'tallying extraction'
    Original Eqn: b'extracting / TIME STEP'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'Flow to keep track of total virgin material extraction'
    """
    return extracting() / time_step()


@cache('step')
def production():
    """
    Real Name: b'Production'
    Original Eqn: b'INTEG ( aggregating remanufactured products + distributing - producing, 0)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'Flow aggregator. Value should remain very close to zero (allowing for some \\n    \\t\\trounding error) throughout model run'
    """
    return _integ_production()


@cache('step')
def products_in_use():
    """
    Real Name: b'Products in Use'
    Original Eqn: b'INTEG ( shipping-reaching end of life, initial components in use)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'Materials within turbines currently in use - may be virgin, recycled, or \\n    \\t\\tremanufactured or reused products'
    """
    return _integ_products_in_use()


@cache('step')
def total_extraction():
    """
    Real Name: b'Total Extraction'
    Original Eqn: b'INTEG ( tallying extraction, 0)'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: component

    b'Keeps track of cumulative virgin material extraction, for calculating \\n    \\t\\tcircularity metrics or other bookkeeping'
    """
    return _integ_total_extraction()


@cache('step')
def reusing_in_other_sectors():
    """
    Real Name: b'reusing in other sectors'
    Original Eqn: b'reaching end of life * fraction used product reused in other sectors'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'End-of-life materials sent for use in another sector'
    """
    return reaching_end_of_life() * fraction_used_product_reused_in_other_sectors()


@cache('step')
def recycling_failed_remanufactured():
    """
    Real Name: b'recycling failed remanufactured'
    Original Eqn: b'(remanufacturing + remanufacturing nonreusables) * fraction remanufactured product to recycle'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'end-of-life materials in components that could not be put back into a \\n    \\t\\tworking product'
    """
    return (remanufacturing() +
            remanufacturing_nonreusables()) * fraction_remanufactured_product_to_recycle()


@cache('step')
def reusing():
    """
    Real Name: b'reusing'
    Original Eqn: b'INTEGER( reaching end of life * Fraction Reuse)'
    Units: b'metric ton/year'
    Limits: (0.0, None)
    Type: component

    b'End-of-life materials contained in products to be reused'
    """
    return int(reaching_end_of_life() * fraction_reuse())


@cache('run')
def fraction_used_product_reused_in_other_sectors():
    """
    Real Name: b'fraction used product reused in other sectors'
    Original Eqn: b'0'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b'Fraction of end-of-life materials sent for use (etc) in another sector \\n    \\t\\trather than the original energy technology system'
    """
    return 0


@cache('run')
def supply_chain_delay():
    """
    Real Name: b'supply chain delay'
    Original Eqn: b'0.5'
    Units: b'year'
    Limits: (0.0, 3.0, 0.25)
    Type: constant

    b'Shipping and other logistical delays in the energy technology supply \\n    \\t\\tchain. Default value 0.5 years or 6 months'
    """
    return 0.5


@cache('run')
def initial_components_in_use():
    """
    Real Name: b'initial components in use'
    Original Eqn: b'0'
    Units: b'metric ton'
    Limits: (0.0, None)
    Type: constant

    b'Set to 0 to assume no commercial-scale wind turbines installed prior to \\n    \\t\\t1980 - simplifying assumption.'
    """
    return 0


@cache('run')
def fraction_of_recycling_to_landfill():
    """
    Real Name: b'fraction of recycling to landfill'
    Original Eqn: b'0.05'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b'Loss fraction: amount of materials sent to recycling that are lost and \\n    \\t\\tlandfilled or incinerated instead. Default value 0.01'
    """
    return 0.05


@cache('run')
def fraction_of_remanufacture_to_landfill():
    """
    Real Name: b'fraction of remanufacture to landfill'
    Original Eqn: b'0.05'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b'Loss fraction: amount of materials sent to remanufacturing that are lost \\n    \\t\\tand landfilled or incinerated instead. Default value 0.01'
    """
    return 0.05


@cache('run')
def fraction_remanufactured_product_to_recycle():
    """
    Real Name: b'fraction remanufactured product to recycle'
    Original Eqn: b'0.01'
    Units: b'Dmnl'
    Limits: (0.0, 1.0, 0.01)
    Type: constant

    b'Leakage fraction: amount of materials sent to remanufacturing that were \\n    \\t\\ttoo degraded and had to be recycled instead.'
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

    b'Leakage fraction: amount of materials in components sent for reuse that \\n    \\t\\twere too degraded and had to be remanufactured instead.'
    """
    return 0.01


@cache('run')
def component_lifetime():
    """
    Real Name: b'component lifetime'
    Original Eqn: b'20'
    Units: b'year'
    Limits: (0.0, 50.0, 0.5)
    Type: constant

    b'Years that newly installed wind turbines remain in use, on average, before \\n    \\t\\tan end-of-life process is needed. Default value 20 or 25, depending on \\n    \\t\\tassumptions.'
    """
    return 20


@cache('step')
def relative_landfill():
    """
    Real Name: b'relative landfill'
    Original Eqn: b'( reaching end of life - (landfilling + landfilling failed remanufactured + landfilling nonrecyclables\\\\ ) ) / ( reaching end of life + 0.001)'
    Units: b'Dmnl'
    Limits: (None, None)
    Type: component

    b'Circularity metric placeholder'
    """
    return (reaching_end_of_life() -
            (landfilling() + landfilling_failed_remanufactured() +
             landfilling_nonrecyclables())) / (reaching_end_of_life() + 0.001)

@cache('run')
def material_name():
    """:key
    An attempt to convert the material_selection() numeric Boolean into a
    string that can filter the LCI input dataset
    """

    # @todo Update the material filtering with addl values
    if material_selection() == 1:
        _material_name = 'fiberglass'
    elif material_selection()== 0:
        _material_name = 'steel'
    else:
        _material_name = 'carbon fiber'

    return _material_name


@cache('run')
def extract_prod_lci(lci_data=lci_melt):
    """
    Filters complete LCI input dataset to include only inputs to the extraction
    and production processes
    """

    _extract_prod_lci = lci_data[(lci_data['process']=='extraction and production') & (lci_data['material']==material_name())]

    return _extract_prod_lci


@cache('run')
def recycling_lci(lci_data=lci_melt):
    """
    Filters complete LCI input dataset to include only inputs to the recycling
    process
    """

    _recycling_lci = lci_data[(lci_data['process']=='recycling') & (lci_data['material']==material_name())]

    return _recycling_lci


@cache('run')
def remanufacturing_lci(lci_data=lci_melt):
    """
    Filters complete LCI input dataset to include only inputs to the
    remanufcturing process
    """

    _remanufacturing_lci = lci_data[(lci_data['process']=='remanufacturing') & (lci_data['material']==material_name())]

    return _remanufacturing_lci


@cache('run')
def transportation_lci(lci_data=lci_melt):
    """
    Filters complete LCI input dataset to include only inputs to the transpo
    process

    @note I'm not aware of emission factors that will let us calculate emissions
    by mass and distance, only distance - we may need to change the calcs s.t.
    they're subject only to mass
    @todo add data and calcualtions to convert mass moved into trips taken
    """

    # @todo filtering by material may work differently for transpo

    _transpo_lci = lci_data[lci_data['process']=='transportation']

    return _transpo_lci


@cache('run')
def reusing_lci(lci_data=lci_melt):
    """
    Filters complete LCI input dataset to include only inputs to the reusing
    process
    """

    _reusing_lci = lci_data[(lci_data['process']=='reusing') & (lci_data['material']==material_name())]

    return _reusing_lci


@cache('step')
def extract_prod_transportation_inputs():
    """
    Scales LCI transpo inputs for all transpo involved in the linear pathway,
    including material leakage from the circular system to the landfill
    """

    _inputs = transportation_lci().copy()

    _scaling_quantity = landfilling() * miles_from_end_use_location_to_landfill() + \
                        extracting() * miles_from_extraction_to_production_facility() + \
                        landfilling_failed_remanufactured() * miles_from_remanufacturing_facility_to_landfill() + \
                        landfilling_nonrecyclables() * miles_from_recycling_facility_to_landfill()

    _inputs.loc[:,'quantity'] = _inputs.loc[:,'quantity'] * _scaling_quantity

    return _inputs


@cache('step')
def recycling_transportation_inputs():
    """
    Scales LCI transpo inputs for transportation in the recycling pathway
    """

    _inputs = transportation_lci().copy()

    _scaling_quantity = recycling() * miles_from_end_use_location_to_recycling_facility() + \
                        recycling_failed_remanufactured() * miles_from_remanufacturing_facility_to_recycling_facility() + \
                        landfilling_nonrecyclables() * miles_from_recycling_facility_to_landfill() +\
                        aggregating_recycled_materials() * miles_from_recycling_to_distribution_facility()

    _inputs.loc[:,'quantity'] = _inputs.loc[:,'quantity'] * _scaling_quantity

    return _inputs


@cache('step')
def remanufacturing_transportation_inputs():
    """
    Scales LCI transpo inputs for transportation in the remanufacturing pathway
    """

    _inputs = transportation_lci().copy()

    _scaling_quantity = remanufacturing() * miles_from_end_use_location_to_remanufacturing_facility() + \
                        remanufacturing_nonreusables() * miles_from_reuse_facility_to_remanufacturing_facility() + \
                        aggregating_remanufactured_products() * miles_from_remanufacturing_facility_to_product_distribution_facility() + \
                        landfilling_failed_remanufactured() * miles_from_remanufacturing_facility_to_landfill()

    _inputs.loc[:,'quantity'] = _inputs.loc[:,'quantity'] * _scaling_quantity

    return _inputs


@cache('step')
def reuse_transportation_inputs():
    """
    Scales LCI transpo inputs for transportation in the reuse pathway
    """

    _inputs = transportation_lci().copy()

    _scaling_quantity = reusing() * miles_from_end_use_location_to_reuse_facility() + \
                        aggregating_reused_products() * miles_from_reuse_facility_to_product_distribution_facility()

    _inputs.loc[:,'quantity'] = _inputs.loc[:,'quantity'] * _scaling_quantity

    return _inputs


@cache('step')
def transportation_inputs():
    """
    Sums inputs from all four transportation types by combining the data frames
    and then summing the quantity column on input-material-process combinations
    """

    # sum input quantity within input-material-process combinations
    _transpo_inputs = pd.concat([extract_prod_transportation_inputs(),
                                 recycling_transportation_inputs(),
                                 remanufacturing_transportation_inputs(),
                                 reuse_transportation_inputs()]).groupby(['input unit', 'input name', 'material', 'process'],
                                                                         as_index=False).sum()

    return _transpo_inputs


@cache('step')
def extract_prod_inputs():
    """
    Scales the extraction LCI by the amount of raw material extracted
    """
    _inputs = extract_prod_lci()

    _scaling_quantity = extracting()

    _inputs.loc[:,'quantity'] = _inputs.loc[:,'quantity'] * _scaling_quantity

    return _inputs


@cache('step')
def recycling_inputs():
    """
    Scales the recycling LCI by metric tons of material sent through recycling
    pathway
    """
    _inputs = recycling_lci()

    _scaling_quantity = aggregating_recycled_materials()

    _inputs.loc[:,'quantity'] = _inputs.loc[:,'quantity'] * _scaling_quantity

    return _inputs


@cache('step')
def remanufacturing_inputs():
    """
    Scales the remanufacturing LCI by metric tons of material sent through
    remanufacturing pathway
    """
    _inputs = remanufacturing_lci()

    _scaling_quantity = aggregating_remanufactured_products()

    _inputs.loc[:,'quantity'] = _inputs.loc[:,'quantity'] * _scaling_quantity

    return _inputs


@cache('step')
def reusing_inputs():
    """
    Scales the reusing LCI by metric tons of material sent through reusing
    pathway
    """
    _inputs = reusing_lci()

    _scaling_quantity = aggregating_reused_products()

    _inputs.loc[:,'quantity'] = _inputs.loc[:,'quantity'] * _scaling_quantity

    return _inputs


@cache('step')
def aggregate_inputs():
    """
    Calculates total material and energy inputs/gate-to-gate LCI for the entire
    system, per time step

    Saves the total LCI in a data frame for postprocessing and impact calculation
    """

    _out = pd.concat([extract_prod_inputs(), recycling_inputs(),
                      reusing_inputs(), remanufacturing_inputs(),
                      transportation_inputs()])

    # add Time column that contains model time (years+quarters)
    _out.insert(len(_out.columns), 'model time', time(), allow_duplicates=False)

    if time()==1982.00:
        # create new file to store results
        _out.to_csv('total_lci' + run_id() + '.csv',
                    index=False,header=True,mode='a+')

    else:
        # update file with results from this time step without writing
        # a header row
        _out.to_csv('total_lci' + run_id() + '.csv',
                    index=False,header=False,mode='a+')

    return None


@cache('step')
def cumulative_landfill_fraction():
    """
    Real Name: b'cumulative landfill fraction'
    Original Eqn: b'Landfill and Incineration / (Total Extraction + 0.001)'
    Units: b'Dmnl'
    Limits: (0.0, None)
    Type: component

    b'Circularity metric placeholder'
    """
    return landfill_and_incineration() / (total_extraction() + 0.001)


@cache('run')
def final_time():
    """
    Real Name: b'FINAL TIME'
    Original Eqn: b'2050'
    Units: b'year'
    Limits: (None, None)
    Type: constant

    b'The final time for the simulation.'
    """
    return 2050


@cache('run')
def initial_time():
    """
    Real Name: b'INITIAL TIME'
    Original Eqn: b'1982'
    Units: b'year'
    Limits: (None, None)
    Type: constant

    b'The initial time for the simulation.'
    """
    return 1982


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


_integ_cumulative_recycle = functions.Integ(lambda: tallying_recycle(), lambda: 0)

_integ_cumulative_remanufacture = functions.Integ(lambda: tallying_remanufacture(), lambda: 0)

_integ_cumulative_reuse = functions.Integ(lambda: tallying_reuse(), lambda: 0)

_integ_cumulative_capacity = functions.Integ(lambda: adding_capacity() / time_step(), lambda: 0)

_integ_fraction_reuse = functions.Integ(lambda: changing_fraction_reuse(),
                                        lambda: fraction_used_product_reused_initial_value())

_integ_fraction_recycle = functions.Integ(lambda: increasing_fraction_recycle(),
                                          lambda: fraction_used_product_recycled_initial_value())

_integ_fraction_remanufacture = functions.Integ(
    lambda: increasing_fraction_remanufacture(),
    lambda: fraction_used_product_remanufactured_initial_value())

_delay_producingaggregating_reused_products_supply_chain_delay_producingaggregating_reused_products_1 = functions.Delay(
    lambda: producing() + aggregating_reused_products(), lambda: supply_chain_delay(),
    lambda: producing() + aggregating_reused_products(), lambda: 1)

_integ_landfill_and_incineration = functions.Integ(
    lambda: landfilling() + landfilling_failed_remanufactured() + landfilling_nonrecyclables(),
    lambda: 0)

_integ_products_sent_to_other_sectors = functions.Integ(lambda: reusing_in_other_sectors(),
                                                        lambda: 0)

_integ_products_at_end_of_life = functions.Integ(
    lambda: reaching_end_of_life() - landfilling() - recycling() - remanufacturing() - reusing() -
    reusing_in_other_sectors(), lambda: 0)

_integ_product_reuse = functions.Integ(
    lambda: reusing() - aggregating_reused_products() - remanufacturing_nonreusables(), lambda: 0)

_integ_raw_material_extraction = functions.Integ(lambda: -extracting(), lambda: 1e+15)

_delay_shipping_component_lifetime_0_1 = functions.Delay(lambda: shipping(),
                                                         lambda: component_lifetime(), lambda: 0,
                                                         lambda: 1)

_integ_material_distribution = functions.Integ(
    lambda: aggregating_recycled_materials() + extracting() - distributing(), lambda: 0)

_integ_material_recycle = functions.Integ(
    lambda: recycling() + recycling_failed_remanufactured() - aggregating_recycled_materials() -
    landfilling_nonrecyclables(), lambda: 0)

_integ_product_distribution = functions.Integ(
    lambda: aggregating_reused_products() + producing() - shipping(), lambda: 0)

_integ_product_remanufacture = functions.Integ(
    lambda: remanufacturing() + remanufacturing_nonreusables(
    ) - aggregating_remanufactured_products() - landfilling_failed_remanufactured() -
    recycling_failed_remanufactured(), lambda: 0)

_integ_production = functions.Integ(
    lambda: aggregating_remanufactured_products() + distributing() - producing(), lambda: 0)

_integ_products_in_use = functions.Integ(lambda: shipping() - reaching_end_of_life(),
                                         lambda: initial_components_in_use())

_integ_total_extraction = functions.Integ(lambda: tallying_extraction(), lambda: 0)
