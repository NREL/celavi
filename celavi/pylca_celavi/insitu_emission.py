
# INSITU EMISSION CALCULATOR

import warnings
import pandas as pd
warnings.filterwarnings("ignore")
import numpy as np
from pyomo.environ import ConcreteModel, Set, Param, Var, Constraint, Objective, minimize

# The following two lines are needed for execution on HPC
# import pyutilib.subprocess.GlobalData
# pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False

#We are integrating static lca with dynamics lca over here. 
def preprocessing(year,df_static):

    """
    This function preprocesses the process inventory before the LCA calculation. It joins the dynamic LCA
    inventory with the static LCA inventory. Removes dummy processes with no output from the inventory. 

    Parameters
    ----------
    year : str
        year of LCA calculation
    df_static : pd.DataFrame
        lca inventory static 

    
    Returns
    -------
    pd.DataFrame
       cleaned process inventory merged with dynamic data
    pd.DataFrame   
       inventory with no product flows

    """
    df = df_static
    df_input = df[df['input'] == True]
    df_output = df[df['input'] == False]
    df_input.loc[:, 'value'] = df_input.loc[:, 'value'] * (-1)
    df = pd.concat([df_input, df_output])
    
    # Removing flows without source because optimization problem becomes infeasible
    # Removing flows without source
    # For optimization to work, the technology matrix should not have any flows that do not have any production proceses.
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


def solver_optimization(tech_matrix,F,process, df_with_all_other_flows):

    """
    This function houses the optimizer for solve Xs = F. 
    Solves the Xs=F equation. 
    Solves the scaling vector.  

    Parameters
    ----------
    tech_matrix : numpy matrix
         technology matrix from the process inventory
    F : vector
         Final demand vector 
    process: str
         filename for the dynamic inventory   
    df_with_all_other_flows: pd.DataFrame
         lca inventory with no product flows

    
    Returns
    -------
    pd.DataFrame
       LCA results
    """

    X_matrix = tech_matrix.to_numpy()
    # Creation of a Concrete Model
    model = ConcreteModel()

    def set_create(a, b):
        i_list = []
        for i in range(a, b):
            i_list.append(i)
        return i_list

    model.i = Set(initialize=set_create(0, X_matrix.shape[0]), doc='indices')
    model.j = Set(initialize=set_create(0, X_matrix.shape[1]), doc='indices')

    def x_init(model, i, j):
        return X_matrix[i, j]
    model.x = Param(model.i, model.j, initialize=x_init, doc='technology matrix')

    def f_init(model, i):
        return F[i]

    model.f = Param(model.i, initialize=f_init, doc='Final demand')
    model.s = Var(model.j, bounds=(0, None), doc='Scaling Factor')

    def supply_rule(model, i):
      return sum(model.x[i, j] * model.s[j] for j in model.j) >= model.f[i]
    model.supply = Constraint(model.i, rule=supply_rule, doc='Equations')

    def objective_rule(model):
      return sum(model.s[j] for j in model.j)
    model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')

    def pyomo_postprocess(options=None, instance=None, results=None):
        df = pd.DataFrame.from_dict(model.s.extract_values(), orient='index', columns=[str(model.s)])
        return df



    # This emulates what the pyomo command-line tools does
    from pyomo.opt import SolverFactory
    import pyomo.environ

    opt = SolverFactory("ipopt")
    results = opt.solve(model)
    solution = pyomo_postprocess(None, model, results)
    scaling_vector = pd.DataFrame()
    scaling_vector['process'] = process
    scaling_vector['scaling_factor'] = solution['s']

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
        process inventory

    Returns
    -------
    pd.DataFrame
       process inventory with electricity flows before 2020 converted to the base electricity
       mix flow in USLCI. 
    """

    
    df = df.replace(to_replace='electricity', value='Electricity, at Grid, US, 2010')
    return df

def runner(tech_matrix,F,yr,i,j,k,final_demand_scaler,process,df_with_all_other_flows):

    """
    Runs the optimization function and creates final data frame in proper format

    Parameters
    ----------
    tech matrix: pd.Dataframe
         technology matrix built from the process inventory. 
    F: final demand series vector
         final demand of the LCA problem
    yr: int
         year of analysis
    i: int
         facility ID
    j: str
        stage
    k: sr
        material
    final_demand_scaler: int
        scaling variable number to ease optimization
    process: list
        list of processes included in the technology matrix
    df_with_all_other_flows: pd.DataFrame
        Dataframe with flows in the inventory which do not have a production process. 
    

    Returns
    -------
    pd.DataFrame
       Dataframe with LCA results
    """

    
    res = pd.DataFrame()
    res= solver_optimization(tech_matrix, F,process,df_with_all_other_flows)
    res['value'] = res['value']*final_demand_scaler
    if res.empty == False:        
       res.loc[:,'year'] =  yr
       res.loc[:,'facility_id'] = i
       res.loc[:,'stage'] = j
       res.loc[:,'material'] = k
    else:        
       print("optimization insitu emission failed")
    
    res = electricity_corrector_before20(res)
    return res


def model_celavi_lci_insitu(f_d, yr, fac_id, stage, material, df_emissions):


    """
    This is used for calculating insitu emissions
    Creates technology matrix and final demand vector from inventory data
    Runs the PyLCA optimizer to perform LCA calculations
    Conforms results to a dataframe 

    Parameters
    ----------
    f_d: Dataframe 
    Dataframe from DES 
    
    yr: int
    Year of calculation

    fac_id: int
    Facility ID of facility being evaluated

    stage: str 
    Stage of facility being evaluated

    material: str
    material being evaluated

    df_emission: df
    Emissons inventory

    Returns
    -------
    pd.DataFrame
         Insitu emissions within a Dataframe after LCA calculations
    """


    f_d = f_d.drop_duplicates()
    f_d = f_d.dropna()

    final_lci_result = pd.DataFrame()
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
    if chksum != 0:
        F = final_dem['flow quantity']
        # Dividing by scaling value to solve scaling issues
        F = F / 100000

        res = runner(tech_matrix, F, yr, fac_id, stage, material, 100000, process, df_with_all_other_flows)
        # r es.columns = ['flow name', 'unit', 'flow quantity', 'year', 'stage', 'material']
        # res = model_celavi_lci_background(res, yr, stage, material)
        res.columns = ['flow name', 'unit', 'flow quantity', 'year', 'facility_id', 'stage', 'material']
        return res
    else:
        return pd.DataFrame()
