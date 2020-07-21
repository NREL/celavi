import numpy as np


class PhysicalFlowLCI:
    """
    This class implements physical flow LCI from the Suh Section 3.2
    """

    def __init__(self, direct_requirements_A, environmental_intervention_B, functional_unit_y):
        """
        Parameters
        ----------
        direct_requirements_A : numpy.array
            The direct requirements matrix. Columns are processes and
            rows are functions of those processes.

        environmental_intervention_B : numpy.array
            The row vector that is the environmental intervention for each
            process. (Such as kg of CO2)

        functional_unit_y : numpy.array
            The column vector that has the functional units for which
            environmental intervention should be calculated.
        """
        self.direct_requirements_A = direct_requirements_A
        self.environmental_intervention_B = environmental_intervention_B
        self.functional_unit_y = functional_unit_y

    def compute_environmental_intervention(self):
        """
        This method computes the environmental intervention as calculated
        with:

        1. The direct requirements matrix A

        2. The environmental intervention row vector B

        3. Functional unit of product system column vector y

        Returns
        -------
        float
            The environmental intervention q.
        """
        A = self.direct_requirements_A
        A_inv = np.linalg.inv(A)
        B = self.environmental_intervention_B
        y = self.functional_unit_y
        q = B.dot(A_inv).dot(y)
        result = float(q.squeeze())
        return result
