import socket
import threading
from time import sleep

class Server:
    IP = socket.gethostbyname(socket.gethostname())
    UDP_PORT = 13117
    TCP_PORT = 50000

    magic_cookie = b'11111110111011011011111011101111'
    m_type = b'00000010'
    server_port = b'1100001101010000'
    udp_offer = magic_cookie + m_type + server_port

    def __init__(self):
        self.sending_udp_messages = False

        self.udp_sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP

        # setting up udp socket for broadcasting to all clients
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        
        self.tcp_sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_STREAM) # TCP
        self.tcp_sock.settimeout(1)

        self.tcp_sock.bind((self.IP, self.TCP_PORT))


        self.client_list = []

    
    def send_udp_message(self):
        self.sending_udp_messages = True
        print("Server started, listening on ip address {}".format(self.IP))

        for i in range(10):
            print(i)
            self.udp_sock.sendto(self.udp_offer, ('<broadcast>', self.UDP_PORT))
            sleep(1)

        self.sending_udp_messages = False

    def accept_connections(self):

        while self.sending_udp_messages:
            try:
                client_socket, client_address = self.tcp_sock.accept()

                client_thread = threading.Thread(target=self.get_team_name, args=(client_socket,client_address))
                client_thread.start()

            except socket.timeout:
                continue


    def get_team_name(self, client_socket, client_address):
        # TODO: put in try and catch!
        team_name = client_socket.recv(1024).decode('utf-8')
        print(team_name)

        self.client_list.append((client_socket, client_address, team_name))




if __name__ == "__main__":
    server = Server()
    # server.main()
    server.tcp_sock.listen()
    udp_message_thread = threading.Thread(target=server.send_udp_message)
    udp_message_thread.start()
    
    tcp_receive_thread = threading.Thread(target=server.accept_connections)
    tcp_receive_thread.start()

    udp_message_thread.join()
    tcp_receive_thread.join()

    print(server.client_list)

    # server.send_udp_message()