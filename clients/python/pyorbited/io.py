import socket
LQUEUE_SIZE = 500
BUFFER_SIZE = 4096

def server_socket(port):
    """Return a listening socket bound to the given interface and port.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("localhost", port))
    sock.listen(LQUEUE_SIZE)
    return sock


def client_socket(addr, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)
    sock.connect_ex((addr, port))
    return sock    
