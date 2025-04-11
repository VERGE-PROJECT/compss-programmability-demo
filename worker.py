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
    # Create a TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))     # Bind to specified host and port
        server_socket.listen()               # Start listening for incoming connections

        while True:
            conn, _ = server_socket.accept()  # Accept an incoming connection
            with conn:
                raw_len = conn.recv(4)  # Receive 4 bytes indicating message length
                total_len = struct.unpack('>I', raw_len)[0]  # Unpack length value

                data = conn.recv(total_len)  # Receive the full message
                task_idx, row, B = pickle.loads(data)  # Deserialize task inputs

                result = np.dot(row, B)  # Perform row × matrix multiplication

                result_data = pickle.dumps((task_idx, result))  # Serialize result
                conn.sendall(struct.pack('>I', len(result_data)) + result_data)  # Send length + result

if __name__ == "__main__":
    main()
