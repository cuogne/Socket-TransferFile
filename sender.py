import os
import socket
import threading

SERVER_DATA_PATH = 'resources'
TEXT_FILE = 'text.txt'
BUFFER_SIZE = 4096

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((socket.gethostname(), 9876))
server.listen(5)
file_lock = threading.Lock()
print(f"Server started at {server.getsockname()}")

# doc danh sach file trong thu muc resources va ghi vao file text.txt
# ham nay chi ghi tu dong cho file text.txt de kh phai nhap thu cong (co the comment lai)
def write_text():
    resources_dir = os.path.join(os.path.dirname(__file__), SERVER_DATA_PATH)
    text_file = os.path.join(os.path.dirname(__file__), TEXT_FILE)
    
    with open(text_file, 'w') as f:
        for file_name in os.listdir(resources_dir):
            file_path = os.path.join(resources_dir, file_name)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                f.write(f"{file_name}|{file_size}\n")

def handle_client(client_sock, addr):
    try:
        # doc danh sach file cho phep tai
        text_file = os.path.join(os.path.dirname(__file__), TEXT_FILE)
        with open(text_file, 'r') as f:
            file_list = f.read()

        # gui danh sach file cho client
        client_sock.send(file_list.encode())

        while True:
            # nhan yeu cau file download tu client
            # request = f"{file_name}|{start}-{end}".encode() (ben client)
            try:
                request = client_sock.recv(BUFFER_SIZE).decode().strip()
            except ConnectionResetError:
                print(f"Connection reset by peer {addr}")
                break
            if not request:
                break
            
            # xu li du lieu {file_name}|{start}-{end}
            parts = request.split('|') # tach file_name va range
            
            if len(parts) != 2:
                # sai format request
                client_sock.send("Invalid request format.".encode())
                continue

            file_name, range_str = parts                # luu file_name vao, con range_str la {start}-{end}
            start, end = map(int, range_str.split('-')) # tach start va end

            resources_dir = os.path.join(os.path.dirname(__file__), SERVER_DATA_PATH)
            file_path = os.path.join(resources_dir, file_name)

            if not os.path.isfile(file_path):
                client_sock.send(f"File {file_name} not found.".encode())
                continue

            with file_lock:
                with open(file_path, 'rb') as f:
                    f.seek(start)               # di chuyen con tro den vi tri bat dau
                    remaining = end - start     # tinh so byte con lai can gui
                    while remaining > 0:
                        # doc va gui du lieu cho client
                        chunk = f.read(min(BUFFER_SIZE, remaining))
                        if not chunk:
                            break
                        client_sock.sendall(chunk) # sendall de dam bao gui het du lieu
                        remaining -= len(chunk)   # cap nhat so byte con lai can gui
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        client_sock.close()

def run():
    write_text()
    try:
        while True:
            client_sock, addr = server.accept()
            print(f"Connected by {addr}")
            thread = threading.Thread(target=handle_client, args=(client_sock, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    run()