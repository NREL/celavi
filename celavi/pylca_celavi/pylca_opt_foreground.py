#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 15 12:42:32 2020

@author: tghosh
"""


import warnings
import pandas as pd
import numpy as np
import sys
import multiprocessing
import time
import os
# import pyutilib.subprocess.GlobalData
from pyomo.environ import ConcreteModel, Set, Param, Var, Constraint, Objective, minimize
# pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False
warnings.filterwarnings("ignore")

try:
    os.remove('intermediate_demand.csv')
except FileNotFoundError:
    pass

    
#Reading in static and dynamics lca databases
print('>>>', os.getcwd())
df_dynamic = pd.read_csv('dynamic_secondary_lci_foreground.csv')

#We are integrating static lca with dynamics lca over here. 
def preprocessing(year,df_static):
    
    df_dynamic_year = df_dynamic[df_dynamic['year'] == year]
    frames = [df_static,df_dynamic_year]
    df = pd.concat(frames)
    
    
    
    df_input = df[df['input'] == True]
    df_output = df[df['input'] == False]
    
    df_input.loc[:,'value'] = df_input.loc[:,'value']  * (-1)
    df = pd.concat([df_input,df_output])
    
    
    
    #Removing flows without source because optimization problem becomes infeasible
    #Removing flows without source
    #For optimization to work, the technology matrix should not have any flows that do not have any production proceses.
    #Dummy flows need to be removed. 
    #This part removes the dummy flows and flows without any production processes from the X matrix. 
    process_input_with_process  =  pd.unique(df_output['product'])
    df['indicator'] = df['product'].isin(process_input_with_process)
    process_df = df[df['indicator'] == True]
    df_with_all_other_flows = df[df['indicator'] == False]
    
    del process_df['indicator']
    del df_with_all_other_flows['indicator']
    
    process_df.loc[:,'value'] = process_df.loc[:,'value'].astype(np.float64)
    return process_df,df_with_all_other_flows


def solver_optimization(tech_matrix,F,process, df_with_all_other_flows):
        X_matrix = tech_matrix.to_numpy()
        # Creation of a Concrete Model
        model = ConcreteModel()
        
        def set_create(a,b):
            i_list = []
            for i in range(a,b):
                i_list.append(i)
            return i_list
            
            
            
        model.i = Set(initialize=set_create(0,X_matrix.shape[0]), doc='indices')
        model.j = Set(initialize=set_create(0,X_matrix.shape[1]), doc='indices')
        
        
        def x_init(model,i,j):
            return X_matrix[i,j]
        model.x = Param(model.i, model.j, initialize=x_init, doc='technology matrix')
        
        
        def f_init(model,i):
            return F[i]
        
        model.f = Param(model.i, initialize=f_init, doc='Final demand')
        
        model.s = Var(model.j, bounds=(0,None), doc='Scaling Factor')
        
        def supply_rule(model, i):
          return sum(model.x[i,j]*model.s[j] for j in model.j) >= model.f[i]
        model.supply = Constraint(model.i, rule=supply_rule, doc='Equations')
        
        
        def objective_rule(model):
          return sum(model.s[j] for j in model.j)
        model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')
        
        
        def pyomo_postprocess(options=None, instance=None, results=None):
            df = pd.DataFrame.from_dict(model.s.extract_values(), orient='index', columns=[str(model.s)])
            return df
          #model.s.display()
          
        # This is an optional code path that allows the script to be run outside of
        # pyomo command-line.  For example:  python transport.py
            # This emulates what the pyomo command-line tools does
        from pyomo.opt import SolverFactory
        import pyomo.environ
        opt = SolverFactory("ipopt")
        results = opt.solve(model)
        solution = pyomo_postprocess(None, model, results)
        scaling_vector = pd.DataFrame()
        scaling_vector['process'] = process
        scaling_vector['scaling_factor'] = solution['s']

        results_df = df_with_all_other_flows.merge(scaling_vector, on = ['process'], how = 'left')
        
        results_df['value'] = abs(results_df['value']) * results_df['scaling_factor']
        results_df = results_df[results_df['value'] > 0]
        results_df = results_df.fillna(0)
        results_total = results_df.groupby(by = ['product','unit'])['value'].agg(sum).reset_index()
        
        return results_total


def electricity_corrector_before20(df):
    #This part is used to replace pre 2020 electricity flows with US'Electricity, at Grid, US, 2010'
    
    df = df.replace(to_replace='electricity', value='Electricity, at Grid, US, 2010')
    return df


def runner(tech_matrix,F,yr,i,j,k,final_demand_scaler,process,df_with_all_other_flows):
    res = pd.DataFrame()
    res= solver_optimization(tech_matrix, F,process,df_with_all_other_flows)
    res['value'] = res['value']*final_demand_scaler
    if res.empty == False:

       res.loc[:,'year'] =  yr
       res.loc[:,'facility_id'] = i
       res.loc[:,'stage'] = j
       res.loc[:,'material'] = k

    res = electricity_corrector_before20(res)

    # Intermediate demand is not required by the framewwork, but it is useful
    # for debugging.
    res.to_csv('intermediate_demand.csv',mode='a', header=False,index = False)
    return res


def model_celavi_lci(f_d,yr,fac_id,stage,material,df_static):

    f_d = f_d.drop_duplicates()
    f_d = f_d.dropna()
   
    final_lci_result = pd.DataFrame()
    #Running LCA for all years as obtained from CELAVI


    #Incorporating dynamics lci database
    process_df,df_with_all_other_flows = preprocessing(int(yr),df_static)
    #Creating the technoology matrix for performing LCA caluclations
    tech_matrix = process_df.pivot(index = 'product', columns = 'process', values = 'value' )
    tech_matrix = tech_matrix.fillna(0)
    #This list of products and processes essentially help to determine the indexes and the products and processes
    #to which they belong.
    products = list(tech_matrix.index)
    process = list(tech_matrix.columns)
    product_df = pd.DataFrame(products)
    final_dem = product_df.merge(f_d, left_on = 0, right_on = 'flow name', how = 'left')
    final_dem = final_dem.fillna(0)
    chksum = np.sum(final_dem['flow quantity'])
    if chksum == 0:
        print('No proper final demand for '+str(yr)+' '+stage+' '+material) 
        return pd.DataFrame()
    
    else:
        F = final_dem['flow quantity']
        #Dividing by scaling value to solve scaling issues
        F = F/100000
    
        res = runner(tech_matrix,F,yr,fac_id,stage,material,100000,process,df_with_all_other_flows)            
        res.columns = ['flow name','unit','flow quantity','year','facility_id','stage','material']
       
    
        return res






