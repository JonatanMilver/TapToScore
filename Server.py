import socket
import threading
import random
import struct
from time import sleep
from scapy.arch import get_if_addr

class Server:
    #GLOBALS - CONSTANTS
    IP = get_if_addr('eth1')
    UDP_PORT = 13117
    TCP_PORT = 50000
    HEADER = 1024 #MSG_HEADER

    BROADCAST_IP = '172.1.255.255'

    MAGIC_COOKIE = 0xfeedbeef
    M_TYPE = 0x2
    SERVER_PORT = 50000
    udp_offer = MAGIC_COOKIE + M_TYPE + SERVER_PORT

    def __init__(self):
        self.sending_udp_messages = False # Tells the TCP conn when to stop accepting clients.
        self.receive_m = False

        self.client_list = [] #Connected clients via TCP will be appended.

        self.udp_sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP

        # setting up udp socket for broadcasting to all clients
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # initializing TCP socket
        self.tcp_sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_STREAM) # TCP
        self.tcp_sock.settimeout(0.1)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock.bind((self.IP, self.TCP_PORT))

    
    def send_udp_message(self):
        """
        Broadcast offer requests to all clients over a udp connection,
        sends a message every second for 10 seconds.
        """
        self.sending_udp_messages = True 

        for i in range(10):
            print('sending message number {}...'.format(i))
            self.udp_sock.sendto(struct.pack('IbH', self.MAGIC_COOKIE, self.M_TYPE, self.SERVER_PORT), (self.BROADCAST_IP, self.UDP_PORT))
            sleep(1)

        self.sending_udp_messages = False

    def accept_connections(self):
        """
        Accepts connection requests and client's team name
        from clients while still sending offer requests.
        """
        while self.sending_udp_messages:
            try:
                client_socket, client_address = self.tcp_sock.accept()

                client_thread = threading.Thread(target=self.get_team_name, args=(client_socket,client_address))
                client_thread.start()

            except socket.timeout:
                continue


    def get_team_name(self, client_socket, client_address):
        """
        Recieves the client's team name and saves it with additional data to client_list.
        @param client_socket: tuple of 5, the client's socket
        @param client_address: tuple of 2, the client's IP and port
        """
        team_name = client_socket.recv(1024).decode('utf-8')
        self.client_list.append((client_socket, client_address, team_name))

    def assign_to_groups(self):
        """
        Divides randomly all clients in client_list in to two groups.
        """
        group_a, group_b = [], []
        client_copy = list(self.client_list)
        l = len(self.client_list)

        for i in range(l//2):
            r = random.randint(0, len(client_copy)-1)

            group_a.append(client_copy[r])
            client_copy.pop(r)
        
        for client in client_copy:
            group_b.append(client)

        return group_a, group_b

    def create_game_start_message(self, group_a, group_b):
        """
        Creates a start game message with the teams' names.
        @param group_a: connected clients.
        @param group_b: connected clients.
        """
        msg = 'Welcome to Keyboard Spamming Battle Royale.\n'
        msg += 'Group 1:\n==\n'
        for c in group_a:
            msg += c[2]
        
        msg += 'Group 2:\n==\n'
        for c in group_b:
            msg += c[2]

        msg += 'Start pressing keys on your keyboard as fast as you can!!'
        return msg

    def send_tcp_message(self, message):
        """
        Sends message to all clients over tcp.
        @param message: String to send
        """
        for client in self.client_list:
            client[0].send(bytes(message, 'utf-8'))

    def release_clients(self):
        """
        Closes connection to all clients in the end of a game.
        """
        for client in self.client_list:
            try:
                client[0].shutdown(socket.SHUT_RDWR)
                client[0].close()
            except Exception as identifier:
                continue
            
        # nullifies the list for next game.
        self.client_list = []

    def get_tcp_messages(self, counter_a, counter_b):
        """
        Opens a thread for each client so the server can recieve incoming messages from all clients simultanously
        @param counter_a: a dict with keys as clients (3-tuple) from group_a and 0 for its values (number of recieved messages per client)
        @param counter_b: same as counter_a for group_b
        """
        self.receive_m = True

        for sock in counter_a:
            threading.Thread(target=self.get_message, args=(sock, counter_a)).start()
            
        for sock in counter_b:
            threading.Thread(target=self.get_message, args=(sock, counter_b)).start()

        sleep(10)

        self.receive_m = False

        
    def get_message(self, sock, counter):
        """
        Recieves a message from a single client.
        @param sock: Socket of the client.
        @param counter: a dict with keys as clients (3-tuple) from group_a and count value for its values (number of recieved messages per client)
        """
        while self.receive_m:
            m = sock.recv(self.HEADER)
            counter[sock] += 1

    def create_game_end_message(self, group_a, counter_a, group_b, counter_b):
        """
        Creates an end game message.
        @param group_a: All clients from the first group.
        @param counter_a: The dictionary that is holding the amount of keyboard presses for each of group_a's clients.
        @param group_b: All clients from the second group.
        @param counter_a: The dictionary that is holding the amount of keyboard presses for each of group_b's clients.
        """
        sum_a = sum(counter_a.values())
        sum_b = sum(counter_b.values())
        winner = -1
        # Beginning of end-game message
        msg = 'Game over!\nGroup 1 typed in {} characters. Group 2 typed in {} characters.\n'.format(sum_a, sum_b)
        if sum_a >= sum_b:
            winner = 1
            msg += 'Group 1 wins!\n\n'
        else:
            winner = 2
            msg += 'Group 2 wins!\n\n'

        msg += 'Congratulations to the winners:\n==\n'

        if winner == 1:
            for i in group_a:
                msg += i[2] + '\n'

        else:
            for i in group_b:
                msg += i[2] + '\n'

        return msg

    def main(self):
        """
        Main game loop, runs without stopping.
        """

        print("Server started, listening on ip address {}".format(self.IP))

        server.tcp_sock.listen()
        try:

            while True:
                # A sleep so that loop wouldn't run forever.
                print('Waiting 5 seconds')
                sleep(5)
                # Thread initiation to send udp message on broadcast.
                udp_message_thread = threading.Thread(target=server.send_udp_message)
                udp_message_thread.setDaemon(True)
                udp_message_thread.start()
                
                # Thread initiation to receive tcp connections.
                tcp_receive_thread = threading.Thread(target=server.accept_connections)
                tcp_receive_thread.setDaemon(True)
                tcp_receive_thread.start()

                udp_message_thread.join()
                tcp_receive_thread.join()

                if len(server.client_list) < 1:
                    print("No players!")
                    continue

                group_a, group_b = server.assign_to_groups()

                # Game mode

                counter_group_a = {}
                counter_group_b = {}
                for s in group_a:
                    counter_group_a[s[0]] = 0
                
                for s in group_b:
                    counter_group_b[s[0]] = 0

                # Thread initiation to start listening for client's messages.
                x = threading.Thread(target=server.get_tcp_messages, args=(counter_group_a, counter_group_b))
                x.start()

                game_start_message = server.create_game_start_message(group_a, group_b)
                # Game start
                server.send_tcp_message(game_start_message)

                x.join()
                # End of game
                server.send_tcp_message(server.create_game_end_message(group_a, counter_group_a, group_b, counter_group_b))

                server.release_clients()

                print("Game Over, sending out offer requests...")

        except KeyboardInterrupt as e:
            print("Server Done!")


        




if __name__ == "__main__":
    server = Server()
    server.main()