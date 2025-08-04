import socket
import threading

LISTENING_ADDR = '0.0.0.0'
LISTENING_PORT = 8888

BLOCKED_DOMAINS = [
    "facebook.com",
    "twitter.com"
]

def is_blocked(request_data):
    for domain in BLOCKED_DOMAINS:
        if domain.encode() in request_data:
            return True
    return False

def handle_client(client_socket):
    request = client_socket.recv(8192)

    if is_blocked(request):
        print("Requête bloque")
        client_socket.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n<b>Access Denied by Proxy Filter</b>")
        client_socket.close()
        return

    try:
        first_line = request.decode(errors='ignore').split('\n')[0]
        url = first_line.split(' ')[1]
        http_pos = url.find("://")
        if http_pos != -1:
            url = url[(http_pos+3):]

        port_pos = url.find(":")
        path_pos = url.find("/")
        if path_pos == -1:
            path_pos = len(url)

        webserver = ""
        port = 80

        if port_pos == -1 or path_pos < port_pos:
            port = 80
            webserver = url[:path_pos]
        else:
            port = int(url[(port_pos+1):][:path_pos-port_pos-1])
            webserver = url[:port_pos]

        print(f"Requête autorisee vers {webserver}:{port}")

        proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_server.connect((webserver, port))
        proxy_server.sendall(request)

        while True:
            data = proxy_server.recv(8192)
            if len(data) > 0:
                client_socket.send(data)
            else:
                break

        proxy_server.close()
        client_socket.close()

    except Exception as e:
        print(f"Erreur : {e}")
        client_socket.close()

def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LISTENING_ADDR, LISTENING_PORT))
    server.listen(100)
    print(f"Proxy en écoute sur {LISTENING_ADDR}:{LISTENING_PORT}...")

    while True:
        client_socket, addr = server.accept()
        print(f"Connexion de {addr}")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == '__main__':
    start_proxy()
