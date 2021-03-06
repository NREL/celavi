import pickle
import pandas as pd
import numpy as np
import time
from pyomo.environ import ConcreteModel, Set, Param, Var, Constraint, Objective, minimize, SolverFactory
import pyutilib.subprocess.GlobalData
pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False


def model_celavi_lci_background(f_d, yr, fac_id, stage,material, route_id, uslci_filename,
                                lci_activity_locations):

    """
    Main function of this module which receives information from DES interface and runs the suppoeting optimization functions. 
    Creates the technology matrix and the final demand vector based on input data. 
    Performs necessary checks before and after the LCA optimization calculation. 
    
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
    uslci_filename: str
      filename for the USLCI inventory
    lci_activity_locations
        Path to file that provides a correspondence between location
        identifiers in the US LCI.
    
    Returns
    -------
    pd.DataFrame
       Final LCA results in the form of a dataframe after performing after calculation checks

    """
    processes = {}
    processes = pickle.load( open( uslci_filename, "rb" ))
    
    def process_product_func():

        """
        This function is creating a dataframe of processes and all their products from the USLCI database. 
        The dataframe considers the name of the process as well as the location and the names of the product flows.
        This ensures that when networks are created, the locations of the networks are also matched.

        Parameters
        ----------

        Returns
        -------
        pd.DataFrame
            Dataframe from USLCI listing process and products along with other supplemental information
         
        """
        p_list = []
        pr_list = []
        unit_list = []
        value_list = []
        loc_list =[]
    
        for i in processes:
            for j in processes[i].exchanges:
                if j.flow.category_path[0]  == "Technosphere Flows" and j.input == False:
                    p_list.append(processes[i].name+'@'+ processes[i].location.name)
                    #pr_list.append(processes[i].name+'@'+ processes[i].location.name+'@'+exch[k].flow.name)
                    pr_list.append(j.flow.name)
                    unit_list.append(j.unit.name)
                    value_list.append(j.amount)
                    loc_list.append(processes[i].location.name)
            #if c>1:
                #print(processes[i].name+' has more than one reference output and is an OpenLCA error')
       
        process_product = pd.DataFrame({'process':p_list,'product':pr_list,'location':loc_list,'unit':unit_list,'value':value_list})
        process_product['input'] = False
        process_product = process_product.drop_duplicates()
        
        return process_product
    
    
    flows_without_location = []
    
    
    def process_input_func():

        """
        This function creates a dataframe for only the inputs of the different processes
        There also the flows are matched with the locations saw that when the network is created
        the location of the exchanges are also matched.
        
        Parameters:
        -----------

        Returns:
        --------
        pd.DataFrame
           Dataframe with processes along with their flow inputs. 

        """
    
        p_list = []
        pr_list = []
        unit_list = []
        value_list = []
        loc_list =[]
        
        for i in processes:
            for j in processes[i].exchanges:
                if j.input == True:
                    p_list.append(processes[i].name  + '@' + str(processes[i].location.name))
                    pr_list.append(j.flow.name)
                    unit_list.append( j.unit.name)
                    value_list.append(j.amount)
                    loc_list.append(processes[i].location.name)
    
        process_input = pd.DataFrame({'process':p_list,'inputs':pr_list,'location':loc_list,'unit':unit_list,'value':value_list})
        process_input['input'] = True
        process_input= process_input.drop_duplicates()
        return process_input
    
    

    def process_emission_func():
        
        """
        This function is used for creating a dataframe that extracts out the emission flows
        from the USLCI database and creates a dataframe
        Need to add air water and soil separation later

        Parameters:
        -----------

        Returns:
        --------
        pd.DataFrame
            Dataframe with processes and their respective emissions. 

        """

        p_list = []
        pr_list = []
        unit_list = []
        value_list = []
    
        for i in processes:
            for j in processes[i].exchanges:
                if j.flow.category_path[0] == 'Elementary flows' and j.input == False:
                    p_list.append(processes[i].name  + '@' + str(processes[i].location.name))
                    pr_list.append(j.flow.name)
                    unit_list.append( j.unit.name)
                    value_list.append(j.amount)
    
        process_emission = pd.DataFrame({'process':p_list,'product':pr_list,'unit':unit_list,'value':value_list})
        process_emission['input'] = False
        process_emission = process_emission.drop_duplicates()
        return process_emission
    
    process_product = process_product_func()
    process_input = process_input_func()
    process_emission = process_emission_func()
    
    #Removing flows without source because optimization problem becomes infeasible
    #Removing flows without source
    #For optimization to work, the technology matrix should not have any flows that do not have any production proceses.
    #Dummy flows need to be removed. 
    #This part removes the dummy flows and flows without any production processes from the X matrix. 
    def process_input_refine():
        """
        This function creates a dataframe for only the inputs of the different processes
        #here also the flows are matched with the locations saw that when the network is created
        #the location of the exchanges are also matched.
        
        Parameters:
        -----------

        Returns:
        --------
        pd.DataFrame
            refined Dataframe with processes and their respective inputs.         
        
        
        """
        p_list = []
        pr_list = []
        from_p_list = []
        unit_list = []
        value_list = []
        loc_list =[]
        
        for i in processes:
            for j in processes[i].exchanges:
                if j.input == True:
                    try:
                        from_p_list.append(j.default_provider.name)
                        p_list.append(processes[i].name  + '@' + str(processes[i].location.name))
                        pr_list.append(j.flow.name)                    
                        unit_list.append(j.unit.name)
                        value_list.append(j.amount)
                        loc_list.append(str(j.default_provider.location))
                    except:
                        pass
    
        process_input = pd.DataFrame({'process':p_list,'inputs':pr_list,'from_process':from_p_list,'location':loc_list,'unit':unit_list,'value':value_list})
        process_input['input'] = True
        process_input = process_input.drop_duplicates()
        return process_input
    
    process_input_with_process = process_input_refine()
    
    removed_flows = process_input.merge(process_input_with_process,on = ['process', 'inputs', 'unit', 'value', 'input'], how = 'left',indicator = True)
    removed_flows = removed_flows[removed_flows['_merge'] == 'left_only']
    del removed_flows['_merge']     
    
    #We would like to account for sequestration of emissions (input of flows) in the processes. For that reason, we are updating
    #the process emissions database with emission flows that are consumed in the processes. 
    def process_emission_input_func():
        #These function is used for creating a dataframe that extracts out the emission flows
        #from the USLCI database and creates a dataframe
        p_list = []
        pr_list = []
        unit_list = []
        value_list = []
    
        for i in processes:
            for j in processes[i].exchanges:
                if j.flow.category_path[0] == 'Elementary flows' and j.input == True:
                    p_list.append(processes[i].name  + '@' + str(processes[i].location.name))
                    pr_list.append(j.flow.name)
                    unit_list.append( j.unit.name)
                    value_list.append(j.amount)
    
    
        process_emission = pd.DataFrame({'process':p_list,'product':pr_list,'unit':unit_list,'value':value_list})
        process_emission['input'] = True
        process_emission['value'] = process_emission['value'] * -1
        process_emission = process_emission.drop_duplicates()
        return process_emission
    
    process_emission_input = process_emission_input_func()
    frames = [process_emission_input,process_emission]
    process_emissions = pd.concat(frames)
    process_emissions = process_emissions.groupby(by = ['process','product','unit'])['value'].agg('sum').reset_index()
    del process_emission, process_emission_input,process_input,processes
    
    process_product['conjoined_flownames'] = process_product['product'] + '@'+ process_product['process']
    #uniquechk = list(pd.unique(process_product['conjoined_flownames']))
    #Unique check passed
    process_product = process_product[['process','conjoined_flownames','location', 'unit', 'value', 'input']]
    #Removing negative product flows
    process_product = process_product[process_product['value'] > 0]
    
    
    location = pd.read_csv(lci_activity_locations)
    process_input_with_process = process_input_with_process.merge(location, left_on = 'location', right_on = 'old_name')
    process_input_with_process['location'] = process_input_with_process['new_name']
    process_input_with_process['conjoined_flownames'] = process_input_with_process['inputs']+ '@' + process_input_with_process['from_process'] + '@' + process_input_with_process['location'] 
    #uniquechk = list(pd.unique(process_input_with_process['conjoined_flownames']))
    process_input_with_process = process_input_with_process[['process','conjoined_flownames','location', 'unit', 'value', 'input']]
    process_input_with_process['value'] = process_input_with_process['value'] * -1
    
    #joining the two databases
    process_df = pd.concat([process_input_with_process,process_product])
    process_df['value'] = process_df['value'].astype(np.float64)
    
    #This is due to an error in USLCI for the Paper fines uncoated flow which exists both in the input and output
    process_df = process_df[process_df['value'] != -7.6657]
    process_df = process_df[process_df['value'] != -0.7901]
    
    #Removing byproducts but it is not required. 
    #process_df = process_df.drop_duplicates ( subset = cols, keep = 'first')
    
    #Creating the technoology matrix for performing LCA caluclations
    tech_matrix = process_df.pivot(index = 'conjoined_flownames', columns = 'process', values = 'value')
    tech_matrix = tech_matrix.fillna(0)
    
    #This list of products and processes essentially help to determine the indexes and the products and processes
    #to which they belong. 
    uslci_products = list(tech_matrix.index)
    uslci_process = list(tech_matrix.columns)
    X_matrix = tech_matrix.to_numpy()
    
    splitted_names1 = []
    for i in uslci_products:
        splitted_names1.append(i.split("@", 1)[0] + '@'+ i.split("@", 1)[1].split("@", 1)[0])
    #This database is used to match the names of the flows in the celavi results
    #with the uslci flows
    uslci_product_df = pd.DataFrame(list(splitted_names1))
    #All unique flows. Need to match this wtih the final demand. 
    
    
    def solver_optimization(tech_matrix,F):
        
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
        
        #This is the BOTTLENECK of the code. 
        def supply_rule(model, i):
          return sum(model.x[i,j]*model.s[j] for j in model.j) >= model.f[i]    
        model.supply = Constraint(model.i, rule=supply_rule, doc='Equations')    
    
        def objective_rule(model):
          return sum(model.s[j] for j in model.j)
        model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')
    
        def pyomo_postprocess(options=None, instance=None, results=None):
            df = pd.DataFrame.from_dict(model.s.extract_values(), orient='index', columns=[str(model.s)])
            return df
          
        # This is an optional code path that allows the script to be run outside of
        # pyomo command-line.  For example:  python transport.py
    
        # This emulates what the pyomo command-line tools does
        opt = SolverFactory("glpk")
        
        results = opt.solve(model)        
        solution = pyomo_postprocess(None, model, results)   
        scaling_vector = pd.DataFrame()
        #The process emissions do not have any location. That is the reason we have to remove the location information
        #and then merge with the processes. 
        scaling_vector['process'] = uslci_process
        scaling_vector['scaling_factor'] = solution['s']         
       
        #Calculations for total emissions
        emissions_results_df = process_emissions.merge(scaling_vector, on = ['process'], how = 'left')
        emissions_results_df['value'] = emissions_results_df['value'] * emissions_results_df['scaling_factor']
        emissions_results_df = emissions_results_df[emissions_results_df['value'] > 0]
        emissions_results_df = emissions_results_df.fillna(0)
        #All emission are grouped and summed up together in this dataframe
        emissions_results_total = emissions_results_df.groupby(by = ['product','unit'])['value'].agg(sum).reset_index()
    
        #Calculations for total product flows only
        #For this calculation we need the locations names as processes are tied to locations
        scaling_vector['process'] = uslci_process
        product_results_df = process_product.merge(scaling_vector, on = ['process'], how = 'left')
        product_results_df['value'] = product_results_df['value'] * product_results_df['scaling_factor']
        product_results_df = product_results_df[product_results_df['value'] > 0]
        product_results_df = product_results_df.fillna(0)
        #All emission are grouped and summed up together in this dataframe
        product_results_total = product_results_df.groupby(by = ['conjoined_flownames','unit'])['value'].agg(sum).reset_index()
    
        return emissions_results_total,product_results_total
            
    
    def runner(tech_matrix, F,i,l,j,k,route_id,final_demand_scaler):

        """
        Calls the optimization function and arranges and stores the results into a proper pandas dataframe. 
        
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
        res2 = pd.DataFrame()
        res,res2 = solver_optimization(tech_matrix, F)
        res['value'] = res['value']*final_demand_scaler
        if not res.empty:
          res.loc[:,'year'] =  i
          res.loc[:,'facility_id'] =  l
          res.loc[:,'stage'] = j
          res.loc[:,'material'] = k
          res.loc[:, 'route_id'] = route_id
    
          print(str(i) +' - '+j + ' - ' + k)
    
        else:                
          print(f"optimization pylca-opt-background emission failed for {k} at {j} in {i}") 
          pass
       
        if not res2.empty:
          res2.loc[:,'year'] =  i
          res2.loc[:,'facility_id'] =  l
          res2.loc[:,'stage'] = j
          res2.loc[:,'material'] = k
          res2.loc[:, 'route_id'] = route_id
    
        else:
           print(f"optimization pylca-opt-background emission failed for {k} at {j} in {i}")
           pass
    
        print(str(time.time() - tim0) + ' ' + 'taken to do this run',flush=True)
    
        return res
    

    
    #Have to edit this final demand to match the results from CELAVI
    f_d['flow name'] = f_d['flow name'] +'@' + f_d['flow name']
    f_d = f_d.drop_duplicates()
    f_d = f_d.sort_values(['year'])


    #Replace electricity    
    f_d  = f_d .replace(to_replace='electricity@electricity', value='electricity, at grid@electricity, at grid, us, 2010')

    uslci_product_df[0] = uslci_product_df[0].str.lower()
    f_d['flow name'] = f_d['flow name'].str.lower()

    final_dem = uslci_product_df.merge(f_d, left_on=0, right_on='flow name', how='left')
    final_dem = final_dem.fillna(0)
    chksum = np.sum(final_dem['flow quantity'])
    #To make the optimization easier
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
    F = final_dem['flow quantity']
    res2 = runner(tech_matrix,F,yr,fac_id,stage,material,route_id,final_demand_scaler)
    
    return res2
