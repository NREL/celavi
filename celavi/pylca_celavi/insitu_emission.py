"""
Methods for calculating insitu or process-level emissions.
"""

import pandas as pd
import numpy as np

def preprocessing(df_static):
    """
    Preprocesses the process material and energy input inventory before the LCA calculations are performed 
    and removes dummy processes with no output from the background inventory.

    Parameters
    ----------
    df_static : pd.DataFrame
        Static insitu inventory. Columns are derived from the processes with insitu emissions.
    
    Returns
    -------
    pd.DataFrame
        Preprocessed background inventory. Columns are derived from the background LCI database being used.
    
    pd.DataFrame   
        Background inventory with no product flows. Columns are derived from the background LCI database being used.
    """
    df = df_static
    df_input = df[df['input'] == True]
    df_output = df[df['input'] == False]
    df_input.loc[:, 'value'] = df_input.loc[:, 'value'] * (-1)
    df = pd.concat([df_input, df_output])
    
    # Removing flows without source
    # Dummy flows need to be removed.
    # This part removes the dummy flows and flows without any production processes from the X matrix.
    process_input_with_process = pd.unique(df_output['product'])
    df['indicator'] = df['product'].isin(process_input_with_process)
    process_df = df[df['indicator'] == True]
    df_with_all_other_flows = df[df['indicator'] == False]
    
    del process_df['indicator']
    del df_with_all_other_flows['indicator']
    
    process_df.loc[:, 'value'] = process_df.loc[:, 'value'].astype(np.float64)
    return process_df, df_with_all_other_flows


def solver(tech_matrix, F, process, df_with_all_other_flows):
    """
    Calculates the process scaling vector s by solving the Xs = F material balance equations.

    Parameters
    ----------
    tech_matrix: array
        Technology matrix (two-dimensional array) generated from the background inventory. Columns are derived from the background LCI database being used.
    F: array
        Final demand vector (one-dimensional array) representing supply chain material and energy inputs.
    process: list
        List of process names corresponding to the scaling vector s.  
    df_with_all_other_flows: pandas.DataFrame
        Background process inventory with no product flows. Columns are derived from the background LCI database being used.

    Returns
    -------
    pandas.DataFrame
        LCIA results: Mass pollutant flows associated with the supply chain's material and energy inputs.
        Columns:
            - product: str
                Name of pollutant.
            - unit: str
                Unit for pollutant flow.
            - value: float
                Pollutant flow quantity.
    """
    tm = tech_matrix.to_numpy()
    scv = np.linalg.solve(tm, F)

    scaling_vector = pd.DataFrame()
    scaling_vector['process'] = process
    scaling_vector['scaling_factor'] = scv

    results_df = df_with_all_other_flows.merge(scaling_vector, on=['process'], how='left')

    results_df['value'] = abs(results_df['value']) * results_df['scaling_factor']
    results_df = results_df[results_df['value'] > 0]
    results_df = results_df.fillna(0)
    results_total = results_df.groupby(by=['product', 'unit'])['value'].agg(sum).reset_index()

    return results_total

def electricity_corrector_before20(df):
    """
    This function is used to replace pre 2020 electricity flows with the base electricity mix flow
    in the USLCI inventory Electricity, at Grid, US, 2010'
    
    Parameters
    ----------
    df: pd.DataFrame
        Background process inventory. Columns are derived from the background LCI database being used.

    Returns
    -------
    pd.DataFrame
       Background process inventory with electricity flows before 2020 converted to the base electricity
       mix flow in USLCI. Columns are derived from the background LCI database being used.
    """
    df = df.replace(to_replace='electricity', value='Electricity, at Grid, US, 2010')
    return df

def runner_insitu(
    tech_matrix,
    F,
    yr,
    i,
    j,
    k,
    state,
    final_demand_scaler,
    process,
    df_with_all_other_flows
    ):
    """
    Runs the solver function and creates final data frame in proper format

    Parameters
    ----------
    tech matrix: pd.Dataframe
        Technology matrix form of the background process inventory. 
    F: pd.Series
        Final demand vector with supply chain material and energy inputs.
    yr: int
        Model year
    i: int
        facility ID
    j: str
        Name of supply chain stage
    k: str
        Name of material
    state: str
        State where the facility is located.
    final_demand_scaler: int
        Integer for scaling final demand and avoiding badly scaled matrix calculations.
    process: list
        List of processes included in the technology matrix
    df_with_all_other_flows: pd.DataFrame
        Dataframe with flows in the inventory which do not have a production process. 
    
    Returns
    -------
    pd.DataFrame
        Returns the pollutant inventory (pollutant mass flows) for processing material k through facility i in year yr.
        Columns:
            - product: str
            - unit: str
            - value: float
            - year: int
            - facility_id: int
            - stage: str
            - material: str
            - route_id: str
            - state: str
    """
    res = pd.DataFrame()
    res = solver(tech_matrix, F, process, df_with_all_other_flows) 
    res['value'] = res['value']*final_demand_scaler
    if  not res.empty:        
       res.loc[:,'year'] =  yr
       res.loc[:,'facility_id'] = i
       res.loc[:,'stage'] = j
       res.loc[:,'material'] = k
       res.loc[:,'state'] = state
    else:        
       print(f"Insitu emission calculation failed for {k} at {j} in {yr}")
    
    res = electricity_corrector_before20(res)
    res['route_id'] = None
    return res


def model_celavi_lci_insitu(f_d, yr, fac_id, stage, material, state, df_emissions, verbose):
    """
    Calculate insitu (process-level or Scope 1) emissions.

    Creates technology matrix and final demand vector from the background inventory. 
    Runs the PyLCA solver to calculate pollutant mass flows.
    Returns insitue pollutant mass flows as a DataFrame.

    Parameters
    ----------
    f_d: pandas.DataFrame 
        Final demand for the process with insitu emissions.
    yr: int
        Model year.
    fac_id: int
        Facility ID of facility being evaluated
    stage: str 
        Supply chain stage.
    material: str
        Material being processed.
    df_emission: pandas.DataFrame
        Insitu emissons inventory.
        Columns:
            - ?
    verbose: int
        Controls the level of progress reporting from this method.

    Returns
    -------
    pd.DataFrame
        Insitu mass pollutant flows for processing "material" through "fac_id".
        Columns:
            - flow name: str
                Name of pollutant
            - flow unit: str
                Pollutant unit
            - flow quantity: float
                Quantity of pollutant produced
            - year: int
                Model year
            - facility_id: int
                ID of supply chain facility producing these pollutants
            - stage: str
                Supply chain stage at this facility
            - material: str
                Material being processed
            - route_id: str
                UUID for route, for transportation calculations
            - state: str
                State in which facility is located
    """
    f_d = f_d.drop_duplicates()
    f_d = f_d.dropna()
    # Running LCA for all years as obtained from CELAVI
    # Incorporating dynamics lci database
    process_df, df_with_all_other_flows = preprocessing(int(yr), df_emissions)
    # Creating the technology matrix for performing LCA calculations
    tech_matrix = process_df.pivot(index='product', columns='process', values='value')
    tech_matrix = tech_matrix.fillna(0)
    # This list of products and processes essentially help to determine the indexes and the products and processes
    # to which they belong.
    products = list(tech_matrix.index)
    process = list(tech_matrix.columns)
    product_df = pd.DataFrame(products)
    final_dem = product_df.merge(f_d, left_on=0, right_on='flow name', how='left')
    final_dem = final_dem.fillna(0)
    chksum = np.sum(final_dem['flow quantity'])
    F = final_dem['flow quantity']
    if chksum <= 0:
        if verbose == 1:
            print('LCA emissions inventory does not exist for %s %s %s' % (str(yr), stage, material))
        return pd.DataFrame()
        #Returns blank dataframe if not inventory is present
    
    elif chksum > 100000:
            final_demand_scaler = 10000
    elif chksum > 10000:
            final_demand_scaler = 1000
    elif chksum > 100:
            final_demand_scaler = 10
    else:
            final_demand_scaler = 1

    # Dividing by scaling value to solve scaling issues
    F = F / final_demand_scaler

    res = runner_insitu(tech_matrix, F, yr, fac_id, stage, material, state, final_demand_scaler, process, df_with_all_other_flows)
    if len(res.columns) != 9:
        print(f'model_celavi_lci: res has {len(res.columns)}; needs 9 columns',
              flush=True)
        return pd.DataFrame(columns = ['flow name', 'flow unit', 'flow quantity', 'year', 'facility_id', 'stage', 'material','route_id', 'state'])
    else:
        res.columns = ['flow name', 'flow unit', 'flow quantity', 'year', 'facility_id', 'stage', 'material','route_id','state']
        return res
