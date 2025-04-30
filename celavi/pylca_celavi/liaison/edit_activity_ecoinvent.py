import sys
import pandas as pd

def electricity_correction(exchange_ob):
    """
    We need an additional correction. All instances of electricity flows needs to be changed with high voltage electricity since LiAISON ReEDS only produces state mixes of high voltage electricity but
    includes transmission. But we are adding 2% losses here. 
    
    Parameters:
    ----------
    exchange_obj: Ecoinvent exchange object
        Ecoinvent flow datasets

    Returns:
    -------
    name_of_flow: str
        name of the flow to be changed
    value: float
        value of the flow ( amount )

    """
    if ('market group for electricity, medium voltage' in exchange_ob['name']) or ('market group for electricity, low voltage' in exchange_ob['name']) or ('market for electricity, high voltage' in exchange_ob['name']) or ('market for electricity, medium voltage' in exchange_ob['name']) or ('market for electricity, low voltage' in exchange_ob['name']):
        name_of_flow = 'market group for electricity, high voltage'
        value = exchange_ob['amount'] * 1.02
    else:
        name_of_flow = exchange_ob['name']
        value = exchange_ob['amount']

    return name_of_flow,value


def modify_electricity_grid_mix_and_solar_glass_removal(process_selected_as_foreground,year_of_study,location_under_study,data_dir):
    """
    This function searches for activities and edits the ecoinvent activity as a foreground process in the chosen location
    It extracts every flow in the chosen foreground process, creates a dataframe from it and changes the location
    It also changes the electricity flow name

    Parameters:
    ----------
    dictionary: dictionary
        This contains the entire ecoinvent database as a dictionary with key name as processes and locations

    Returns:
    -------
    """
    print('Editing activities within ecoinvent to US location and US state wise grid mix',flush=True)
    new_location = str(location_under_study)

    # These variables are used to create inventory dataframe
    process = []
    flow = []
    value = []
    unit = []
    input_1 = []
    year = []
    comments = []
    type_1 = []
    process_location = []
    supplying_location = []
    flow_code = []

    # These variables are used to create the emissions and process bridge dataframes
    common_name = []
    ecoinvent_name = []
    common_emission_name = []
    ecoinvent_emission_name = []
    code = []
    code_emission = []


    #Extracting ecoinvent database for activity and flows and creating a LiAISON friendly dataframe
    for exch in process_selected_as_foreground.exchanges():
            process.append(process_selected_as_foreground['name'])            
            
            unit.append(exch['unit'])

            name_of_flow,amount = electricity_correction(exch)
            value.append(amount)
            flow.append(name_of_flow)

            if exch['type'] == 'production':
                input_1.append(False)
                type_1.append('production')
                supplying_location.append(exch['location'])
                flow_code.append(exch['input'][1])
            

            elif exch['type'] =='technosphere':
                input_1.append(True)
                type_1.append('technosphere')
                common_name.append(name_of_flow)
                ecoinvent_name.append(name_of_flow)
                code.append(exch['input'][1])

                #Appending 0 to flow code for technosphere since we want to change the location of these flows. 
                #They need to be searched in the proper location
                flow_code.append(0)
                supplying_location.append(new_location)
            

            elif exch['type'] =='biosphere':
                input_1.append(False)
                type_1.append('biosphere')
                supplying_location.append('None')
                common_emission_name.append(exch['name'])
                ecoinvent_emission_name.append(exch['name'])
                code_emission.append(exch['input'][1])
                flow_code.append(exch['input'][1])


            year.append(year_of_study)
            comments.append('None')
            process_location.append(new_location)
            

    # Creating of the inventory dataframe
    example = pd.DataFrame(columns=['process', 'flow', 'value', 'unit', 'input', 'year', 'comments', 'type',
           'process_location', 'supplying_location'])
    
    example['process'] = process
    example['flow'] = flow
    example['value'] = value
    example['unit'] = unit
    example['input'] = input_1
    example['year'] = year
    example['comments'] = comments
    example['type'] = type_1
    example['process_location'] = process_location
    example['supplying_location'] = supplying_location
    example['code'] = flow_code

    #Sanity check to write the dataframe. Can be deleted later
    name_of_process = process_selected_as_foreground['name'].replace("/","per")
    example.to_csv(data_dir+name_of_process+str(year_of_study)+location_under_study+'.csv',index=False)
    run_filename = example

    # Removal of solar glass iron from the inventory for the panel production activity. 
    if process_selected_as_foreground['name'] == "photovoltaic panel production, multi-Si wafer":
            example2 = example[example['flow'] != "solar glass production, low-iron"]
            example2 = example2[example2['flow'] != "tempering, flat glass"]
            print('Removed glass production from the inventory',flush = True)
            example2.to_csv(data_dir+name_of_process+str(year_of_study)+location_under_study+'.csv',index=False)
            run_filename = example2

    return run_filename


def module_disassembly_glass_content(process_selected_as_foreground,year_of_study,functional_unit,input_dir):
    """
    This function is used to convert kilograms of solar glass in module manufacturing to number of modules to square meter
    This is because Ecoinvent works with module as square meter
    Parameters:
    ===========
    process_selected_as_foreground: activity object brightway2
        the process under study
    year_of_study: str
        year of study
    functional_unit: float
        amount to do LCA on

    Returns:
    =========
    function_unit:float
        Modified functional unit

    """

    
    glass_module_df = pd.read_csv(input_dir+"glasspermodule_pvice.csv")
    if process_selected_as_foreground == "module disassembly":
        #Convert the function unit
        chosen_year_df = glass_module_df[glass_module_df['year'] == int(year_of_study)].reset_index()
        glass_metrictonne_per_module = chosen_year_df.loc[0,'glass_metrictonne_per_module']
        glass_kilogram_per_module = glass_metrictonne_per_module * 1000
        # functional unit is solar glass kilograms
        module_number = functional_unit/glass_kilogram_per_module   
        print('Functional unit of process ',process_selected_as_foreground,' changed from ',functional_unit,' solar glass kilograms to ',module_number,' number of modules',flush=True)
        return module_number
    else:
        return functional_unit




def module_required_for_solar_glass(process_selected_as_foreground,year_of_study,functional_unit,input_dir):
    """
    This function is used to convert kilograms of solar glass in module manufacturing to number of modules to square meter
    This is because Ecoinvent works with module as square meter
    Parameters:
    ===========
    process_selected_as_foreground: activity object brightway2
        the process under study
    year_of_study: str
        year of study
    functional_unit: float
        amount to do LCA on

    Returns:
    =========
    function_unit:float
        Modified functional unit

    """
    glass_module_df = pd.read_csv(input_dir+"glasspermodule_pvice.csv")
    if process_selected_as_foreground['name'] == "photovoltaic panel production, multi-Si wafer":
        #Convert the function unit
        chosen_year_df = glass_module_df[glass_module_df['year'] == int(year_of_study)].reset_index()
        glass_metrictonne_per_module = chosen_year_df.loc[0,'glass_metrictonne_per_module']
        glass_kilogram_per_module = glass_metrictonne_per_module * 1000
        # functional unit is solar glass kilograms
        module_number = functional_unit/glass_kilogram_per_module
        squaremeter_of_modules = module_number * 2 #1 module = 2 square meter
        print('Functional unit of process ',process_selected_as_foreground['name'],' changed from ',functional_unit,' solar glass kilograms to ',squaremeter_of_modules,' square meter of modules',flush=True)
        return squaremeter_of_modules


    else:
        #return the original functional unit
        return functional_unit


def module_installation_for_solar_glass(process_selected_as_foreground,year_of_study,functional_unit,input_dir):
    """
    This function is used to convert kilograms of solar glass in module manufacturing to units of installation
    This is because Ecoinvent works with module installation as unit
    Parameters:
    ===========
    process_selected_as_foreground: activity object brightway2
        the process under study
    year_of_study: str
        year of study
    functional_unit: float
        amount to do LCA on

    Returns:
    =========
    function_unit:float
        Modified functional unit

    """
    glass_module_df = pd.read_csv(input_dir+"glasspermodule_pvice.csv")
    if process_selected_as_foreground['name'] == "electric installation, 570 kWp photovoltaic plant, at plant":
        #Convert the function unit
        chosen_year_df = glass_module_df[glass_module_df['year'] == int(year_of_study)].reset_index()
        glass_metrictonne_per_module = chosen_year_df.loc[0,'glass_metrictonne_per_module']
        glass_kilogram_per_module = glass_metrictonne_per_module * 1000
        # functional unit is solar glass kilograms
        module_number = functional_unit/glass_kilogram_per_module       
        mwproduction = module_number * chosen_year_df.loc[0,'MWdc_per_module']
        kwproduction = mwproduction*1000
        installation_unit = kwproduction / 570 # From the plant capacity activity in Ecoinvent
        print('Functional unit of process ',process_selected_as_foreground['name'],' changed from ',functional_unit,' solar glass kilograms to ',installation_unit,' units of installation',flush=True)
        return installation_unit


    else:
        #return the original functional unit
        return functional_unit


def window_frame(process_selected_as_foreground,year_of_study,functional_unit):
    """
    This function is used to convert kilograms of glass in window manufacturing to square meter of window aluminum frame
    This is because Ecoinvent works with window frame as square meter
    Parameters:
    ===========
    process_selected_as_foreground: activity object brightway2
        the process under study
    year_of_study: str
        year of study
    functional_unit: float
        amount to do LCA on

    Returns:
    =========
    function_unit:float
        Modified functional unit

    """
    if process_selected_as_foreground['name'] == "window frame production, aluminium, U=1.6 W/m2K":
        #Convert the function unit
        m2_per_kg = 0.131578947 # From comstock file
        sqm_frame = m2_per_kg * functional_unit # Functional unit is in kilograms of window glass
        print('Functional unit of process ',process_selected_as_foreground['name'],' changed from ',functional_unit,' window glass kilograms to ',sqm_frame,' square meter frame',flush=True)
        return sqm_frame


    else:
        #return the original functional unit
        return functional_unit

def landfilling_functional_unit(process_selected_as_foreground,functional_unit):
    """
    This function is used to change the sign of the landfilling functional unit since its negative in Ecoinvent
    Parameters:
    ===========
    process_selected_as_foreground: activity object brightway2
        the process under study
    functional_unit: float
        amount to do LCA on

    Returns:
    =========
    function_unit:float
        Modified functional unit

    """ 
    if process_selected_as_foreground['name'] == "treatment of municipal solid waste, sanitary landfill":
        print('Functional unit of process ',process_selected_as_foreground['name'],' changed from ',functional_unit,' landfilling kilograms to ',functional_unit*(-1),' kilograms',flush=True)
        return functional_unit*(-1)
    else:
        #return the original functional unit
        return functional_unit



