import socket
import time

def test_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('localhost', 5000))
        print("Connected to server!")
        time.sleep(5)
    finally:
        client.close()
