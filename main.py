import pandas as pd

from tinylca.physical_flow_lci import PhysicalFlowLCI

if __name__ == '__main__':
    # Import from the spreadsheet
    lci_input = pd.ExcelFile("input/suh-section-3.2.xlsx")
    direct_requirements_A = lci_input.parse("direct requirements")
    environmental_intervention_B = lci_input.parse("CO2 emission")
    functional_unit_y = lci_input.parse("functional unit")

    # Extract NumPy arrays out of the dataframes
    direct_requirements_A = direct_requirements_A.iloc[:, 1:].values
    environmental_intervention_B = environmental_intervention_B.values
    functional_unit_y = functional_unit_y.iloc[:, 1:].values

    # Put the inputs into the class
    lci = PhysicalFlowLCI(direct_requirements_A=direct_requirements_A,
                          environmental_intervention_B=environmental_intervention_B,
                          functional_unit_y=functional_unit_y)

    # Run the computation
    print(lci.compute_environmental_intervention())
