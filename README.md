# Parallelization Demo: Manual Sockets vs. PyCOMPSs

This repository contains a small experiment comparing two approaches to parallelizing matrix multiplication:

1. **Manual socket-based multiprocessing** (`master.py` + `worker.py`).   
2. **PyCOMPSs-based parallelization** (`matrix_multiplication_compss.py`).

The goal is to show that expressing parallel tasks in PyCOMPSs requires substantially less low-level coordination than implementing your own socket protocol.

---

## 1. File overview

- `master.py`  
  - Generates matrices `A` and `B` (20×20).  
  - Sends each row of `A` along with matrix `B` to a worker via TCP.  
  - Receives the results and reconstructs the output matrix.  

- `worker.py`  
  - Listens on TCP port `10000`.  
  - Receives serialized tasks via `pickle`, computes `row × B` with NumPy, and sends the row result back.  

- `matrix_multiplication_compss.py`  
  - Defines a PyCOMPSs task using `@task`.  
  - Launches one task per row of `A`.  
  - Uses `compss_wait_on` to retrieve all computed rows. 

All implementations use `MATRIX_SIZE = 20`.

---

# How to run the example **without PyCOMPSs**

The manual version consists of two scripts:

* `worker.py` (one or more workers)
* `master.py` (the controller that distributes work)

Both scripts must be running for the computation to complete.

---

## 1. Prepare the worker machines

### 1.1 Ensure Python and NumPy are installed

On each worker:

```bash
pip install numpy
```

### 1.2 Start each worker

On every machine that should act as a worker, run:

```bash
python worker.py
```

By default, the worker:

* Listens on **0.0.0.0:10000**
* Waits for tasks sent by the master
* Computes `row × B` and sends the result back

You can start multiple workers on different machines, or on the same machine if you modify ports manually.

---

## 2. Configure the master

Open `master.py` and define the IP addresses of your workers.
Example:

```python
worker_ips = [
    "192.168.1.10",
    "192.168.1.11",
]
num_workers = len(worker_ips)
```

All workers must already be running before launching the master.

Make sure port **10000** is reachable from the master.

---

## 3. Run the master

On the machine that acts as the master:

```bash
python master.py
```

The master:

1. Generates two 20×20 matrices `A` and `B`.
2. Sends one row of `A` at a time to workers in round-robin order.
3. Receives computed rows from the workers.
4. Builds the final matrix by stacking all returned rows.

If a worker never responds, that row becomes a zero row in the final matrix (based on the script’s fallback logic).

---

## How to run the example **with PyCOMPSs** (Kubernetes + Helm)

This version assumes you run `matrix_multiplication_compss.py` inside a COMPSs-enabled container on a Kubernetes cluster, using a Helm chart similar to the one in the `Helm-matmul` repository. ([GitHub][1])

### 1. Prerequisites

You need:

1. **A container image with COMPSs**

   * The image must contain:

     * The COMPSs runtime and PyCOMPSs bindings.
     * Python 3 and `numpy`.
     * Your script `matrix_multiplication_compss.py` in the container filesystem.
   * This image will be referenced in the chart’s `values.yaml` (e.g. `image.repository` and `image.tag`).

2. **A Kubernetes cluster**

   * Reachable from your machine via `kubectl`.
   * Enough resources for one COMPSs master pod and several worker pods (at least similar to the default: 2 workers, 4 CPU / 4 GB RAM each). ([GitHub][1])

3. **Helm installed locally**

   * Helm v3 client configured to talk to your cluster.

4. **The Helm chart**

   * Clone the chart repository (as in the example):

     ```bash
     git clone https://gitlab.bsc.es/ppc-bsc/software/compss-matmul-helm.git
     cd compss-matmul-helm
     ```

     The GitHub repo `VERGE-PROJECT/Helm-matmul` documents this same chart and its usage. ([GitHub][1])

---

### 2. Adapt the chart for your matrix_multiplication_compss.py

Edit `values.yaml`:

1. **Set the COMPSs image**

   In the `image` section (names can vary, but typically):

   ```yaml
   image:
     repository: your-registry/your-compss-image
     tag: your-tag
     pullPolicy: Always
   ```

   Ensure this image includes `matrix_multiplication_compss.py` and the COMPSs runtime.

2. **Adjust master/worker resources and counts**

   Use the defaults as a starting point (e.g. 2 workers, 4 CPU / 4 RAM). ([GitHub][1])

3. **Adapt the application command/arguments**

   The example chart is designed to run a COMPSs matmul application (e.g. `matmul.py -b ... -e ...`). ([GitHub][1])

   For your case, configure the command in `values.yaml` (or corresponding template values) so that the master container runs something equivalent to:

   ```bash
   runcompss --lang=python matrix_multiplication_compss.py
   ```

   Optionally add arguments or environment variables if your script expects any.

---

### 3. Deploy to Kubernetes with Helm

From the chart directory (`compss-matmul-helm`):

1. **Optional: choose a namespace**

   ```bash
   kubectl create namespace compss-demo   # if not already created

   # or reuse an existing namespace
   ```

2. **Install the chart**

   * Default namespace:

     ```bash
     helm install compss-matmul .
     ```

   * Custom namespace (recommended):

     ```bash
     helm install compss-matmul --namespace compss-demo .
     ```

   The Helm-matmul README shows the same pattern for installing the chart. ([GitHub][1])

3. **Check that pods are running**

   ```bash
   kubectl get pods --namespace compss-demo
   ```

   You should see:

   * One master pod (running COMPSs + your script).
   * N worker pods (configured in `values.yaml`).

---

### 4. What happens at runtime

Inside the master container:

1. `runcompss` starts the PyCOMPSs runtime.
2. `matrix_multiplication_compss.py`:

   * Generates matrices `A` and `B`.
   * Submits one COMPSs task per row (via `@task`-decorated function).
   * Uses `compss_wait_on` to collect all results.
3. The COMPSs runtime automatically distributes tasks to the worker pods, using the k8s resources configured through the chart.

No manual socket handling is required; the runtime manages communication and task scheduling.

---

### 5. Optional: volumes and metrics (if you need them)

The example chart also supports:

* **Master volume**: a `local-storage` PersistentVolume/PersistentVolumeClaim so that the master pod’s results can be written to a host path. ([GitHub][1])
* **Prometheus metrics**: integration via Pushgateway to export execution times (`matmul_total_time`). ([GitHub][1])

For a simple demo of programmability vs. manual sockets, you can ignore these and keep the default settings.

[1]: https://github.com/VERGE-PROJECT/Helm-matmul "GitHub - VERGE-PROJECT/Helm-matmul"

