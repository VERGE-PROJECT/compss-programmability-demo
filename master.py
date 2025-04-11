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
    # Create and connect a TCP socket to the worker IP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, PORT))  # Establish connection to worker

        # Serialize task data (index, row, full matrix B)
        data = pickle.dumps((task_idx, row, B))
        s.sendall(struct.pack('>I', len(data)) + data)  # Send message length + data

        # Receive 4 bytes indicating the length of the response
        raw_len = s.recv(4)
        total_len = struct.unpack('>I', raw_len)[0]

        # Receive the full result data
        result_data = s.recv(total_len)

        return pickle.loads(result_data)  # Deserialize and return result
        
def main():
    A = np.random.rand(20, 20)  # Generate random matrix A
    B = np.random.rand(20, 20)  # Generate random matrix B
    results = [None] * 20       # Initialize list for result rows

    for row_idx in range(20):
        ip = worker_ips[row_idx % num_workers]  # Assign row to worker (round-robin)
        task_idx, result = send_task(ip, row_idx, A[row_idx], B)  # Send task to worker

        if result is not None:
            results[task_idx] = result  # Store received result at correct index

    # Reconstruct the final matrix C = A × B
    final_matrix = np.vstack([
        row if row is not None else np.zeros(20)  # Fill missing rows with zeros (fallback)
        for row in results
    ])

if __name__ == "__main__":
    main()