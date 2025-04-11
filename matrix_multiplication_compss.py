from pycompss.api.task import task
from pycompss.api.api import compss_wait_on

import numpy as np

MATRIX_SIZE = 20  # Define fixed matrix size

@task(returns=1)
def multiply_row(row, B):
    return np.dot(row, B)


def main():
    # Initialize matrices
    A = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)
    B = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)

    # Submit parallel tasks (1 per row)
    results = []
    for i in range(MATRIX_SIZE):
        results.append(multiply_row(np.copy(A[i, :]), B))

    # Wait for all tasks to finish and gather results
    final_rows = compss_wait_on(results)

    print("\nFinal Result (A x B):")
    final_matrix = np.vstack(final_rows)
    print(final_matrix)


if __name__ == "__main__":
    main()
