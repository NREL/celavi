# TODO: @jwalzber = continue vet & comment task by reviewing this file HERE
#  i) Use develop branch and not master branch
#  ii) Review status: 15/19 files were reviewed
#  TODO: @jwalzber = Check if other classes from data manager module than
#   StandardScenarios, TransportationGraph and TransportationNodeLocations
#   are used elsewhere (if not: indicate to remove them).

# TODO: Add a short module docstring above the code to:
#  1) provide authors, date of creation
#  2) give a high level description (2-3 lines) of what the module does
#  3) write any other relevant information

# TODO: Consider generalizing "pylca_opt_foreground.py",
#  "pylca_opt_background.py", and "insitu_emission.py": a lot of code in
#  those two modules are similar. For instance creating the tech_matrix,
#  products and process lists, most of the pre-processing function etc. A
#  class with more general function could be created and an instance of the
#  class could be created when needed for the functions that compute the insitu
#  emissions and foreground (part that are not similar between the two cases
#  would be defined in those functions). A boolean, such as "insitu_emission",
#  could be used for the code to differentiate inputs manipulations when needed
#  (e.g., for the line "res.to_csv('intermediate_demand.csv', mode='a',
#  header=False, index=False)" which is in pylca_opt_foreground.py, but not in
#  insitu_emission.py or pylca_opt_background.py.

# INSITU EMISSION CALCULATOR

import warnings
import pandas as pd
warnings.filterwarnings("ignore")
import numpy as np
from pyomo.environ import ConcreteModel, Set, Param, Var, Constraint, Objective, minimize

# The following two lines are needed for execution on HPC
# import pyutilib.subprocess.GlobalData
# pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False

# We are integrating static lca with dynamics lca over here.
# TODO: Consider removing year if not used (or better yet, consider
#  generalizing function that it can be used in both "pylca_opt_foreground.py"
#  and "insitu_emission.py").
def preprocessing(year, df_static):
    # TODO: add docstrings to explain input variables and what the function
    #  does.
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


def solver_optimization(tech_matrix, F, process, df_with_all_other_flows):
    # TODO: add docstrings to explain input variables and what the function
    #  does.
    X_matrix = tech_matrix.to_numpy()
    # Creation of a Concrete Model
    model = ConcreteModel()

    def set_create(a, b):
        # TODO: add docstrings to explain input variables and what the function
        #  does.
        i_list = []
        for i in range(a, b):
            i_list.append(i)
        return i_list

    model.i = Set(initialize=set_create(0, X_matrix.shape[0]), doc='indices')
    model.j = Set(initialize=set_create(0, X_matrix.shape[1]), doc='indices')

    def x_init(model, i, j):
        # TODO: add docstrings to explain input variables and what the function
        #  does.
        return X_matrix[i, j]
    model.x = Param(model.i, model.j, initialize=x_init, doc='technology matrix')

    def f_init(model, i):
        # TODO: add docstrings to explain input variables and what the function
        #  does.
        return F[i]

    model.f = Param(model.i, initialize=f_init, doc='Final demand')
    model.s = Var(model.j, bounds=(0, None), doc='Scaling Factor')

    def supply_rule(model, i):
        # TODO: add docstrings to explain input variables and what the function
        #  does.
      return sum(model.x[i, j] * model.s[j] for j in model.j) >= model.f[i]
    model.supply = Constraint(model.i, rule=supply_rule, doc='Equations')

    def objective_rule(model):
        # TODO: add docstrings to explain input variables and what the function
        #  does.
      return sum(model.s[j] for j in model.j)
    model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')

    def pyomo_postprocess(options=None, instance=None, results=None):
        # TODO: add docstrings to explain input variables and what the function
        #  does.
        df = pd.DataFrame.from_dict(model.s.extract_values(), orient='index', columns=[str(model.s)])
        return df

      # TODO: If not used, consider removing commented line below
      # model.s.display()

    # TODO: what is the optional code path? The code below solve the
    #  optimization problem so I don't think is optional?
    # This is an optional code path that allows the script to be run outside of
    # pyomo command-line.  For example:  python transport.py
        # This emulates what the pyomo command-line tools does
    # TODO: If there is no reason why not, consider move up the line below to
    #  have it with other imports
    from pyomo.opt import SolverFactory
    # TODO: if pyomo.environ is not used, consider removing
    import pyomo.environ
    # TODO: Consider explaining why the ipopt solver is used in
    #  "insitu_emission.py" but the glpk solver is used in
    #  pylca_opt_foreground and pylca_opt_background (if generalizing the three
    #  modules, the solver could be an input of the class (or function)).
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
    # TODO: add docstrings to explain input variables and what the function
    #  does.
    # This part is used to replace pre 2020 electricity flows with US'Electricity, at Grid, US, 2010'
    
    df = df.replace(to_replace='electricity', value='Electricity, at Grid, US, 2010')
    return df

def runner(tech_matrix, F, yr, i, j, k, final_demand_scaler, process, df_with_all_other_flows):
    # TODO: add docstrings to explain input variables and what the function
    #  does.

    # TODO: consider correcting indentation of the lines below

            res = pd.DataFrame()
            res = solver_optimization(tech_matrix, F, process, df_with_all_other_flows)
            res['value'] = res['value'] * final_demand_scaler
            if res.empty == False:
               # TODO: consider correcting indentation of the four lines below
               res.loc[:, 'year'] = yr
               res.loc[:, 'facility_id'] = i
               res.loc[:, 'stage'] = j
               res.loc[:, 'material'] = k

            # TODO: consider adding some explanation for the line below. For instance,
            #  why isn't there a condition below or in the
            #  "electricity_corrector_before20" function to only replace 'electricity'
            #  by 'Electricity, at Grid, US, 2010' when yr is below 2020 (for rows
            #  with yr < 2020)
            res = electricity_corrector_before20(res)
            return res


def model_celavi_lci_insitu(f_d, yr, fac_id, stage, material, df_emissions):
    # TODO: add docstrings to explain input variables and what the function
    #  does.

    f_d = f_d.drop_duplicates()
    f_d = f_d.dropna()

    # TODO: remove final_lci_result if not used
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
        # TODO: consider explaining what is the scaling value and have it as
        #  an input variable of the function (with default value) or at least
        #  a stored in an explicit variable, especially
        #  because it used twice.
        # Dividing by scaling value to solve scaling issues
        F = F / 100000

        res = runner(tech_matrix, F, yr, fac_id, stage, material, 100000, process, df_with_all_other_flows)
        # TODO: If not used, consider removing commented lines below
        # r es.columns = ['flow name', 'unit', 'flow quantity', 'year', 'stage', 'material']
        # res = model_celavi_lci_background(res, yr, stage, material)
        res.columns = ['flow name', 'unit', 'flow quantity', 'year', 'facility_id', 'stage', 'material']
        return res
    else:
        return pd.DataFrame()
