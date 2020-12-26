import socket

class Client:
    UDP_PORT = 13117
    offer_size = 56
    magic_cookie = '11111110111011011011111011101111'
    m_type = '00000010'

    def __init__(self, team_name):
        self.team_name = team_name

        self.udp_sock = socket.socket(socket.AF_INET, # Internet
                                        socket.SOCK_DGRAM) # UDP
        self.udp_sock.bind(('', self.UDP_PORT))

        self.tcp_sock = socket.socket(socket.AF_INET, # Internet
                                        socket.SOCK_STREAM) # TCP

        
    def listening_for_requests(self):
        while True:

            print("Client started, listening for offer requests...")

            data, addr = self.udp_sock.recvfrom(1024) # buffer size is 1024 bytes
            
            print("recieved offer from {}, attempting to connect...".format(addr[0]))

            if self.check_data(data):
                return data.decode('utf-8'), addr

    def check_data(self, data):
        decoded_data = data.decode('utf-8')
        if len(decoded_data) != self.offer_size or decoded_data[0:32] != self.magic_cookie or decoded_data[32:40] != self.m_type:
            return False
        
        return True

    def initiate_tcp_connection(self, server_ip, server_tcp_port):
        print(server_ip)
        self.tcp_sock.connect(('172.1.0.61', server_tcp_port))

        self.tcp_sock.send(bytes(self.team_name+'\n', 'utf-8'))

        

if __name__ == "__main__":
    client = Client('Shirbit')
    server_data, server_addres = client.listening_for_requests()

    print(server_addres)
    server_ip, server_tcp_port = server_addres[0], int(server_data[40:], 2)
    
    client.initiate_tcp_connection(server_ip, server_tcp_port)
