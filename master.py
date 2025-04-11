import socket
import pickle
import struct
import sys
import numpy as np

PORT = 10000
MATRIX_SIZE = 20  # Define fixed size for square matrices A and B

def send_with_length(sock, data):
    """Send 4-byte length-prefixed data."""
    length = struct.pack('>I', len(data))  # 4-byte big-endian length
    sock.sendall(length + data)

def receive_all(sock, expected_len):
    """Receive exactly expected_len bytes from socket."""
    data = b''
    while len(data) < expected_len:
        packet = sock.recv(4096)
        if not packet:
            break
        data += packet
    return data

def receive_with_length(sock):
    """Receive 4-byte length-prefixed data."""
    raw_len = sock.recv(4)
    if not raw_len:
        return None
    total_len = struct.unpack('>I', raw_len)[0]
    return receive_all(sock, total_len)

def send_task(ip, task_idx, row, B):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, PORT))

            # Serialize and send task
            data = pickle.dumps((task_idx, row, B))
            send_with_length(s, data)

            # Receive result
            result_data = receive_with_length(s)
            if result_data is None:
                print(f"No response from {ip}")
                return None, None

            task_idx, result_row = pickle.loads(result_data)
            print(f"Received result for row {task_idx} from {ip}")
            return task_idx, result_row

    except Exception as e:
        print(f"Error communicating with {ip}: {e}")
        return None, None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 master.py ip1 ip2 ip3 ...")
        sys.exit(1)

    worker_ips = sys.argv[1:]
    num_workers = len(worker_ips)

    A = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)
    B = np.random.rand(MATRIX_SIZE, MATRIX_SIZE)

    print("[*] Matrix A shape:", A.shape)
    print("[*] Matrix B shape:", B.shape)

    results = [None] * MATRIX_SIZE

    for row_idx in range(MATRIX_SIZE):
        ip = worker_ips[row_idx % num_workers]  # Round-robin assignment
        print(f"Sending row {row_idx} to worker {ip}")
        task_idx, result = send_task(ip, row_idx, A[row_idx], B)
        if result is not None:
            results[task_idx] = result
        else:
            print(f"Failed to compute row {row_idx}")

    print("\nFinal Result (A x B):")
    for i, row in enumerate(results):
        if row is not None:
            print(f"Row {i}: {row}")
        else:
            print(f"Row {i}: [ERROR: No result]")

    final_matrix = np.vstack([
        r if r is not None else np.zeros(MATRIX_SIZE)
        for r in results
    ])
    print("\nFull Matrix Result:")
    print(final_matrix)

if __name__ == "__main__":
    main()

def send_task(ip, task_idx, row, B):
    s.connect((ip, PORT))
    data = pickle.dumps((task_idx, row, B))
    s.sendall(struct.pack('>I', len(data)) + data)

    raw_len = s.recv(4)
    total_len = struct.unpack('>I', raw_len)[0]
    result_data = s.recv(total_len)

    return pickle.loads(result_data)