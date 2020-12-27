import socket
import struct

class Client:
    UDP_PORT = 13117
    offer_size = 56
    magic_cookie = 0xfeedbeef
    m_type = 0x2

    def __init__(self, team_name):
        self.team_name = team_name

        self.udp_sock = socket.socket(socket.AF_INET, # Internet
                                        socket.SOCK_DGRAM) # UDP
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_sock.bind(('', self.UDP_PORT))

        self.tcp_sock = socket.socket(socket.AF_INET, # Internet
                                        socket.SOCK_STREAM) # TCP

        
    def listening_for_requests(self):
        while True:

            print("Client started, listening for offer requests...")

            data, addr = self.udp_sock.recvfrom(1024) # buffer size is 1024 bytes
            
            print("recieved offer from {}, attempting to connect...".format(addr[0]))

            try:
                if self.check_data(data):
                    # return data.decode('utf-8'), addr
                    return struct.unpack('IbH',data), addr
            except:
                print('check_data went wrong')
                continue

    def check_data(self, data):
        decoded_data = struct.unpack('IbH',data)
        if len(decoded_data) != 3 or decoded_data[0] != self.magic_cookie or decoded_data[1] != self.m_type:
            return False
        
        return True

    def initiate_tcp_connection(self, server_ip, server_tcp_port):
        print(server_ip)
        self.tcp_sock.connect((server_ip, server_tcp_port))

        self.tcp_sock.send(bytes(self.team_name+'\n', 'utf-8'))

    def receive_message(self):
        while True:
            message = self.tcp_sock.recv(1024).decode('utf-8')
            print(message)

            if message.startswith('Game over!') or len(message) == 0:
                break


        

if __name__ == "__main__":
    client = Client('Shirbit')
    server_data, server_addres = client.listening_for_requests()

    print(server_addres)
    server_ip, server_tcp_port = server_addres[0], server_data[2]
    
    client.initiate_tcp_connection(server_ip, server_tcp_port)



    client.receive_message()


