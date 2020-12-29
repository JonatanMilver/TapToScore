import socket
import struct
import threading
from curtsies import Input
import time
from time import sleep

class Client:
    # GLOBALS
    UDP_PORT = 13117
    MAGIC_COOKIE = 0xfeedbeef
    M_TYPE = 0x2

    def __init__(self, team_name):
        self.team_name = team_name

        self.udp_sock = socket.socket(socket.AF_INET, # Internet
                                        socket.SOCK_DGRAM) # UDP
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_sock.bind(('', self.UDP_PORT))
        self.game_over = True

    def listening_for_requests(self):
        """
        Waits for connection invitations.
        Receives invitation request message, validates the data that has been sent.
        :return - decoded data - tuple of server data and server address.
        """
        while True:
            data, addr = self.udp_sock.recvfrom(1024) # buffer size is 1024 bytes
            
            print("recieved offer from {}, attempting to connect...".format(addr[0]))

            try:
                                         # remove ! only for checks on out server!
                if self.check_data(data) and (addr[0] == '172.18.0.61'):
                    return struct.unpack('IbH',data), addr
            except:
                # Continue looking for connections if data is invalid.
                print('Data is not valid.')
                continue

    def check_data(self, data):
        """
        Validates that the sent data contains the magic_cookie = 0xfeedbeef and m_type = 0x2
        If data is not valid, returns false.
        """
        decoded_data = struct.unpack('IbH',data)
        if len(decoded_data) != 3 or decoded_data[0] != self.MAGIC_COOKIE or decoded_data[1] != self.M_TYPE:
            return False
        
        return True

    def initiate_tcp_connection(self, server_ip, server_tcp_port):
        """
        Initiates a new tcp socket connections given the server IP and PORT.
        As soon as client is connected to a server, the client sends his name(TEAM NAME) to the server.
        """
        try:
            self.tcp_sock = socket.socket(socket.AF_INET, # Internet
                                            socket.SOCK_STREAM) # TCP
            self.tcp_sock.connect((server_ip, server_tcp_port))

            self.tcp_sock.send(bytes(self.team_name+'\n', 'utf-8'))

        except:
            print("Initiation went wrong.")

    def receive_message(self):
        """
        Receives messages from server while game is ON.
        """
        while True:
            try:
                message = self.tcp_sock.recv(1024).decode('utf-8')
                print(message)

                if message.startswith('Game over!') or len(message) == 0:
                    self.game_over = True
                    print('Server disconnected, listening for offer requests...')
                    break

                if message.startswith('Welcome'):
                    return True
            
            except KeyboardInterrupt as e:
                raise e
            
            except:
                # raise Exception("receive fell")
                raise ConnectionRefusedError("Server is down.")
            
    
    def send_tcp_message(self, message):
        """
        Sends a message over a TCP socket connection.
        :param - message - the message that is being sent - String.
        """
        # encodes a utf-8 message to bytes and sends it.
        self.tcp_sock.send(bytes(message, 'utf-8'))

    def keyboard_event_handler(self):
        """
        Handles keyboard presses untill game is over.
        Every keyboard press detection is being sent.
        """
        try:

            with Input(keynames='curses') as input_generator:
                e = input_generator.send(10)
                future = time.time() + 10
                while e is not None:
                    if self.game_over:
                        break
                    print(repr(e))
                    self.send_tcp_message(str(e))
                    curr = future - time.time()
                    e = input_generator.send(curr)
                    
        except KeyboardInterrupt as e:
            raise KeyboardInterrupt("Interaption.")

    def main(self):
        print("Client started, listening for offer requests...")

        try:

            while True:
                try:
                    # looking for a Server
                    server_data, server_addres = client.listening_for_requests()

                    server_ip, server_tcp_port = server_addres[0], server_data[2]
                    
                    # Connecting to a server
                    client.initiate_tcp_connection(server_ip, server_tcp_port)

                    #Waiting for game to start
                    receive_start_msg = client.receive_message()

                    # Game mode
                    if receive_start_msg:
                        client.game_over = False
                        receive_message_t = threading.Thread(target=client.receive_message)
                        # receive_message_t.setDaemon(True)
                        receive_message_t.start()

                    # keyboard_event_handler_t = threading.Thread(target=client.keyboard_event_handler)
                    # keyboard_event_handler_t.start()
                        client.keyboard_event_handler()
                    
                        receive_message_t.join()
                    
                    client.tcp_sock.shutdown(socket.SHUT_RDWR)
                    client.tcp_sock.close()

                except ConnectionRefusedError as c:
                    print('Server disconnected')

            
            
        except KeyboardInterrupt as e:
            print('KeyboardInterrupt')
            pass
        # except ConnectionRefusedError as c:
        #     print('closing client due to server disconnected')


        print("Client Done!")

        

if __name__ == "__main__":
    client = Client('Shirbit')
    client.main()
   


