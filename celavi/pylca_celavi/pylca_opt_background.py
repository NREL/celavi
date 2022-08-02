import pickle
import pandas as pd
import numpy as np
import time
import sys
from pyomo.environ import ConcreteModel, Set, Param, Var, Constraint, Objective, minimize, SolverFactory
import pyutilib.subprocess.GlobalData
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False


def model_celavi_lci_background(f_d, yr, fac_id, stage,material, route_id, uslci_tech_filename,uslci_emission_filename,uslci_process_filename,
                                lci_activity_locations):

    """
    Main function of this module which receives information from DES interface and runs the suppoeting optimization functions. 
    Creates the technology matrix and the final demand vector based on input data. 
    Performs necessary checks before and after the LCA  calculation. 
    
    Parameters
    ----------
    f_d: pd.Dataframe
      Dataframe from DES interface containing material flow information
    yr: int
      year of analysis
    fac_id: int
      facility id
    stage: str
      stage of analysis
    material: str
      material of LCA analysis
    route_id: str
        Unique identifier for transportation route.
    uslci_tech_filename: str
      filename for the USLCI inventory
    uslci_process_filename: str
      filename for the USLCI process
    uslci_emission_filename: str
      filename for the USLCI emissions

    lci_activity_locations
        Path to file that provides a correspondence between location
        identifiers in the US LCI.
    
    Returns
    -------
    pd.DataFrame
       Final LCA results in the form of a dataframe after performing after calculation checks

    """

    def solver(tech_matrix,F,process_emissions):
        
        """
        This function houses the solver to solve Xs = F. 
        Solves the Xs=F equation. 
        Solves the scaling vector.  

        Parameters
        ----------
        tech_matrix : numpy matrix
             technology matrix from the process inventory
        F : vector
             Final demand vector 
        process_emissions: str
             filename for the emissions dataframe
        
        Returns
        -------
        pd.DataFrame
            LCA results
        """
        tm = tech_matrix.to_numpy()
        det = np.linalg.det(tm)

        scv = np.linalg.solve(tm, F)
        scv_df = pd.DataFrame()
        scv_df['scaling vector'] = scv
        scv_df['process'] = uslci_process

        #Calculations for total emissions
        final_result = scv_df.merge(process_emissions, on = ['process'])
        final_result['total_emission'] = final_result['scaling vector'] * final_result['value']
        final_result['value'] = final_result['total_emission']
        em_result = final_result[['product','value','process','unit']]
        co2 = em_result[em_result['product'] == 'Carbon dioxide']
        emissions_results_total = final_result.groupby(['product','unit'])['value'].agg('sum').reset_index()
      
        return emissions_results_total

    
    def runner(tech_matrix, F,i,l,j,k,route_id,final_demand_scaler,process_emissions):

        """
        Calls the solver function and arranges and stores the results into a proper pandas dataframe. 
        
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
        k: str
            material
        route_id: str
            Unique identifier for transportation route.
        final_demand_scaler: int
            scaling variable number to ease optimization


        Returns
        -------
        pd.DataFrame
            Returns the final LCA reults in a properly arranged dataframe with all supplemental information

        """
        tim0 = time.time()
        res = pd.DataFrame()
        res = solver(tech_matrix, F,process_emissions)
        res['value'] = res['value']*final_demand_scaler
        if not res.empty:
          res.loc[:,'year'] =  i
          res.loc[:,'facility_id'] =  l
          res.loc[:,'stage'] = j
          res.loc[:,'material'] = k
          res.loc[:,'route_id'] = route_id
    
          print(str(i) +' - '+j + ' - ' + k, flush = True)
    
        else:                
          print(f"pylca-opt-background emission failed for {k} at {j} in {i}", flush = True) 
          pass       
        
    
        print(str(time.time() - tim0) + ' ' + 'taken to do this run',flush=True)
    
        return res
    

    process_emissions = pd.read_csv(uslci_emission_filename)
    #Creating the technology matrix for performing LCA caluclations
    tech_matrix = pd.read_csv(uslci_tech_filename,index_col ='conjoined_flownames')
    process_adder = pd.read_csv(uslci_process_filename)
    process_adder['product'] = process_adder['product'].str.lower()
    f_d['flow name'] = f_d['flow name'].str.lower()
    f_d = f_d.merge(process_adder, left_on = "flow name", right_on = "product")
    #This list of products and processes essentially help to determine the indexes and the products and processes
    #to which they belong. 
    uslci_products = pd.DataFrame(tech_matrix.index)
    uslci_process = list(tech_matrix.columns)


    #Have to edit this final demand to match the results from CELAVI
    #f_d['flow name'] = f_d['flow name'] +'@' + f_d['flow name']
    #f_d['flow name'] = f_d['flow name'].str.lower()
    f_d = f_d.drop_duplicates()
    f_d = f_d.sort_values(['year'])


    #Replace electricity    
    #f_d  = f_d .replace(to_replace='electricity@electricity', value='electricity, at grid, us, 2010@electricity, at grid, us, 2010')
    #f_d['flow name'] = f_d['flow name'] +'@' + f_d['location']
    #f_d['flow name'] = f_d['flow name'].str.lower()
    f_d['conjoined_flownames'] = f_d['conjoined_flownames'].str.lower()  
    f_d.to_csv('../../celavi-data/generated/intermediate_demand_foreground_uslci_data.csv', mode = 'a')
    #dataframe to debug connecting between foreground and background  
    uslci_products['conjoined_flownames'] = uslci_products['conjoined_flownames'].str.lower()  
    final_dem = uslci_products.merge(f_d, left_on='conjoined_flownames', right_on='conjoined_flownames', how='left')
    final_dem = final_dem.fillna(0)


    chksum = np.sum(final_dem['flow quantity'])
    if chksum == 0:
        print('Final demand construction failed. No value. csv file for error checking created. /n Check the intermediate demand file and final demand check file')
        final_dem.to_csv('../../celavi-data/generated/Final_demand_check_file.csv')
        uslci_products.to_csv('../../celavi-data/generated/uslciproducts_file.csv')
        f_d.to_csv('../../celavi-data/generated/demandforeground.csv')
        sys.exit(1)

    #To make the solution easier
    if chksum > 100000:
        final_demand_scaler = 100000
    elif chksum > 10000:
        final_demand_scaler = 10000
    elif chksum > 100:
        final_demand_scaler = 10
    else:
        final_demand_scaler = 0.1

    #print dataframe to debug connecting between foreground and background
    final_dem['flow quantity']= final_dem['flow quantity']/final_demand_scaler
    #To make the optimization easier
    F = final_dem['flow quantity'].to_numpy()
    res2 = runner(tech_matrix,F,yr,fac_id,stage,material,route_id,final_demand_scaler,process_emissions)
    
    return res2

