import socket
import threading
import os

HOST = '192.168.1.4'  # listen all interfaces
PORT = 12345
users = {
    'sapkota': 'sapkota',
    'admin': 'admin123',
}
clients = {}  # username -> client_socket

lock = threading.Lock()

def broadcast(msg, exclude_user=None):
    with lock:
        for user, sock in clients.items():
            if user != exclude_user:
                try:
                    sock.send(msg)
                except:
                    pass

def handle_client(client_sock, addr):
    print(f"[NEW CONNECTION] {addr}")
    username = None
    try:
        while True:
            data = client_sock.recv(4096)
            if not data:
                break
            text = data.decode(errors='ignore')
            if text.startswith("LOGIN::"):
                _, user, pwd = text.split("::", 2)
                if users.get(user) == pwd:
                    with lock:
                        clients[user] = client_sock
                    username = user
                    client_sock.send(b"OK")
                    broadcast(f"MSG::Server::{user} joined.".encode())
                    print(f"{user} logged in")
                else:
                    client_sock.send(b"FAIL")
            elif text.startswith("MSG::") and username:
                # broadcast chat message
                broadcast(data, exclude_user=username)
            elif text.startswith("FILE::") and username:
                # Header: FILE::<filename>::<filesize>
                _, filename, filesize = text.split("::")
                filesize = int(filesize)
                client_sock.send(b"READY")  # acknowledge to send file data

                # receive file bytes
                received = 0
                with open(os.path.join("downloads", filename), "wb") as f:
                    while received < filesize:
                        chunk = client_sock.recv(min(4096, filesize - received))
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)
                print(f"Received file {filename} from {username}")
                broadcast(f"MSG::Server::{username} sent file {filename}".encode(), exclude_user=username)
            else:
                # unknown or not logged in message
                client_sock.send(b"ERR")
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        client_sock.close()
        if username:
            with lock:
                clients.pop(username, None)
            broadcast(f"MSG::Server::{username} left.".encode())
            print(f"{username} disconnected")

def main():
    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"Server listening on {HOST}:{PORT}")

    try:
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down")
    finally:
        server.close()

if __name__ == "__main__":
    main()
