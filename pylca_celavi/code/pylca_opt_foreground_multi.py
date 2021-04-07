#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 15 12:42:32 2020

@author: tghosh
"""


import warnings
import pandas as pd
warnings.filterwarnings("ignore")
import numpy as np
import sys
import multiprocessing
import time
import os
import pyutilib.subprocess.GlobalData
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False



    
#Reading in static and dynamics lca databases
df_static = pd.read_csv('secondary_foreground_process.csv')
df_dynamic = pd.read_csv('dynamic_secondary_lci_foreground.csv')

#We are integrating static lca with dynamics lca over here. 
def preprocessing(year):
    
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
        # Import of the pyomo module
        from pyomo.environ import ConcreteModel,Set,Param,Var,Constraint,Objective,minimize
         
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
        if __name__ == '__main__':
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

def runner(tech_matrix, F,i,j,k,l,m,n,p,final_demand_scaler,process,df_with_all_other_flows):
    
            res = pd.DataFrame()
            res= solver_optimization(tech_matrix, F,process,df_with_all_other_flows)
            res['value'] = res['value']*final_demand_scaler
            if res.empty == False:
               res.loc[:,'year'] =  i
               res.loc[:,'stage'] = j
               res.loc[:,'material'] = k
               res.loc[:,'scenario'] = l
               res.loc[:,'coarse grinding location'] = m
               res.loc[:,'distance to recycling facility'] = n
               res.loc[:,'distance to cement plant'] = p
               print(str(i) +' - '+j + ' - ' + k + ' - ' + l + ' - ' + m + ' - ' + str(n) + ' - ' + str(p))
 
            res.to_csv('temp.csv',mode='a', header=False,index = False)      

def model_celavi_lci(f_d):

    f_d = f_d.drop_duplicates()
    f_d = f_d.dropna()
    f_d = f_d.rename(columns = {'process':'stage'})
    f_d = f_d.sort_values(['year'])
    years = list(pd.unique(f_d['year']))
    
    final_lci_result = pd.DataFrame()
    processes = []
    #Running LCA for all years as obtained from CELAVI
    for i in years:
        #Doing LCA for years after 2018
            fd_cur = f_d[f_d['year'] == i]
            stage = list(pd.unique(fd_cur['stage']))
            for j in stage:               
                fd_cur2 = fd_cur[fd_cur['stage'] == j]
                material = list(pd.unique(fd_cur2['material']))
                for k in material:
                    fd_cur3 = fd_cur2[fd_cur2['material'] == k]
                    scenario = list(pd.unique(fd_cur3['scenario']))
                    for l in scenario:
                        fd_cur4 = fd_cur3[fd_cur3['scenario'] == l] 
                        coarse_grind = list(pd.unique(fd_cur4['coarse grinding location']))
                        for m in coarse_grind:
                            fd_cur5 = fd_cur4[fd_cur4['coarse grinding location'] == m]  
                            dist1 = list(pd.unique(fd_cur5['distance to recycling facility']))
                            for n in dist1:
                                fd_cur6 = fd_cur5[fd_cur5['distance to recycling facility'] == n]
                                dist2 = list(pd.unique(fd_cur6['distance to cement plant']))
                                for p in dist2:
                                    fd_cur7 = fd_cur6[fd_cur6['distance to cement plant'] == p] 

                                    fd_cur8 = fd_cur7[['flow name','flow quantity']]
                                    #Incorporating dynamics lci database
                                    process_df,df_with_all_other_flows = preprocessing(int(i))
                                    #Creating the technoology matrix for performing LCA caluclations
                                    tech_matrix = process_df.pivot(index = 'product', columns = 'process', values = 'value' )
                                    tech_matrix = tech_matrix.fillna(0)
                                    #This list of products and processes essentially help to determine the indexes and the products and processes
                                    #to which they belong.
                                    products = list(tech_matrix.index)
                                    process = list(tech_matrix.columns)
                                    product_df = pd.DataFrame(products)                       
                                    final_dem = product_df.merge(fd_cur8, left_on = 0, right_on = 'flow name', how = 'left')
                                    final_dem = final_dem.fillna(0)
                                    F = final_dem['flow quantity']
                                    #Dividing by scaling value to solve scaling issues
                                    F = F/100000
                                    p = multiprocessing.Process(target = runner, args = (tech_matrix, F,i,j,k,l,m,n,p,100000,process,df_with_all_other_flows))
                                    processes.append(p)
                                    p.start() 
                                    #runner(tech_matrix, F,i,j,k,l,m,n,p,100000,process,df_with_all_other_flows)


    for process in processes:
       process.join() 




       
tim0 = time.time()  
f_d = pd.read_csv('celavi-pylca-input-subset.csv') 
process_emission = f_d[f_d['direction'] == 'output'] 
process_emission.to_csv('process_emission_insitu.csv',index=False)
#f_d = f_d[f_d['direction'] == 'input']
model_celavi_lci(f_d)



final_res = pd.read_csv('temp.csv',header = None)
final_res = final_res.drop_duplicates()
column_names = ['flow name','flow unit','flow quantity','year','stage','material','scenario','coarse grinding location','distance to recycling facility','distance to cement plant']
final_res.columns = list(column_names)
final_res = final_res.drop_duplicates()
final_res.to_csv('foreground_results_processed_multi.csv', index = False)
os.remove('temp.csv')
print(time.time() - tim0)




