from pycompss.api.task import task
from pycompss.api.api import compss_wait_on

import numpy as np

MATRIX_SIZE = 20  # Define fixed matrix size

@task(returns=1)
def multiply_row(row, B):
    # COMPSs task
    return np.dot(row, B)

def main():
    # Generate two random square matrices A and B
    A = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)
    B = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)

    # Submit one task per row of matrix A
    results = []
    for i in range(MATRIX_SIZE):
        results.append(multiply_row(np.copy(A[i, :]), B))

    # Wait for all parallel tasks to complete and retrieve results
    final_rows = compss_wait_on(results)

    # Stack rows to form the final result matrix
    final_matrix = np.vstack(final_rows)


if __name__ == "__main__":
    main()
