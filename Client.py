import socket
import struct
import threading
from curtsies import Input
import time
from time import sleep
from scapy.arch import get_if_addr

class Client:
    # GLOBALS - CONSTANTS
    UDP_PORT = 13117
    MAGIC_COOKIE = 0xfeedbeef
    M_TYPE = 0x2
    BUFFER_SIZE = 1024
    # COLORS
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __init__(self, team_name):
        self.team_name = team_name
        # UDP socket initiation
        self.udp_sock = socket.socket(socket.AF_INET, # Internet
                                        socket.SOCK_DGRAM) # UDP
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_sock.bind(('', self.UDP_PORT))
        self.game_over = True # Variable providing info whether to keep sending messages or not.

    def listening_for_requests(self):
        """
        Waits for connection invitations.
        Receives invitation request message, validates the data that has been sent.
        @return: decoded data - tuple of server data and server address.
        """
        while True:
            data, addr = self.udp_sock.recvfrom(self.BUFFER_SIZE) # buffer size is 1024 bytes
            print("recieved offer from {}, attempting to connect...".format(addr[0]))

            try:
                if self.check_data(data):
                    return struct.unpack('IbH',data), addr
            except:
                # Continue looking for connections if data is invalid.
                print('Data is not valid.')
                continue

    def check_data(self, data):
        """
        Validates that the sent data contains the MAGIC_COOKIE = 0xfeedbeef and M_TYPE = 0x2
        @param data: Received data to check.
        @return: True if data is valid, else False.
        """
        decoded_data = struct.unpack('IbH',data)
        if len(decoded_data) != 3 or decoded_data[0] != self.MAGIC_COOKIE or decoded_data[1] != self.M_TYPE:
            return False
        
        return True

    def initiate_tcp_connection(self, server_ip, server_tcp_port):
        """
        Initiates a new tcp socket connections given the server IP and PORT.
        As soon as client is connected to a server, the client sends his name(TEAM NAME) to the server.
        @param server_ip: IP address of the server.
        @param server_tcp_port: Server's port.
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
        Receives messages from server while game is ON and prints it.
        """
        while True:
            try:
                message = self.tcp_sock.recv(self.BUFFER_SIZE).decode('utf-8')
                if len(message) > 0:
                    print(f'{self.OKBLUE}{message}{self.ENDC}')

                if message.startswith('Game over!') or len(message) == 0:
                    self.game_over = True
                    print(f'{self.WARNING}Server disconnected, listening for offer requests...{self.ENDC}')
                    break
                # First message, client is waiting for it after the tcp connection.
                if message.startswith('Welcome'):
                    return True
            
            except KeyboardInterrupt as e:
                # Would be handled on main() function.
                raise e
            
            except:
                raise ConnectionRefusedError("Server is down.")
            
    
    def send_tcp_message(self, message):
        """
        Sends a message over a TCP socket connection.
        @param: message - the message that is being sent - String.
        """
        # encodes a utf-8 message to bytes and sends it.
        self.tcp_sock.send(bytes(message, 'utf-8'))

    def keyboard_event_handler(self):
        """
        Handles keyboard presses untill game is over.
        Every keyboard press detection is being sent untill time is over.
        """
        try:

            with Input(keynames='curses') as input_generator:
                e = input_generator.send(10)
                future = time.time() + 10
                while e is not None:
                    if self.game_over:
                        break
                    
                    self.send_tcp_message(str(e))
                    # holds the time left for the game.
                    curr = future - time.time()
                    e = input_generator.send(curr)
                    
        except KeyboardInterrupt as e:
            raise KeyboardInterrupt("Interaption.")

    def main(self):
        """
        Client main function, runs from the beginning of the Client.
        """
        print(f"{self.OKGREEN}Client started, listening for offer requests...{self.ENDC}")

        try:

            while True:
                # sleeps every game so the loop wouldn't run forever.
                sleep(1)
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
                        receive_message_t.start()

                        client.keyboard_event_handler()
                    
                        receive_message_t.join()
                    
                    client.tcp_sock.shutdown(socket.SHUT_RDWR)
                    client.tcp_sock.close()

                except ConnectionRefusedError as c:
                    print('Server disconnected')

                except Exception as e:
                    print('Game went wrong, reconnecting...')
                    continue

            
            
        except KeyboardInterrupt as e:
            print('KeyboardInterrupt')
            pass



        print("Client Done!")

        

if __name__ == "__main__":
    client = Client('Team Shirbit')
    client.main()
   


