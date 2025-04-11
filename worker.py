import socket
import pickle
import numpy as np
import struct

HOST = '0.0.0.0'
PORT = 10000

def multiply(row, B):
    return np.dot(row, B)

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

def send_with_length(sock, data):
    """Send 4-byte length-prefixed data."""
    length = struct.pack('>I', len(data))
    sock.sendall(length + data)

def main():
    print(f"Worker listening on port {PORT}...")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()

        while True:
            conn, addr = server_socket.accept()
            with conn:
                print(f"Connected by master at {addr}")

                data = receive_with_length(conn)
                if not data:
                    print("No data received.")
                    continue

                try:
                    task_idx, row, B = pickle.loads(data)
                except Exception as e:
                    print(f"Error deserializing data: {e}")
                    continue

                print(f"Received task for row {task_idx}")
                result = multiply(row, B)

                result_data = pickle.dumps((task_idx, result))
                send_with_length(conn, result_data)
                print(f"Sent result for row {task_idx}")

if __name__ == "__main__":
    main()
