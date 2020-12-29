import socket
import threading
import random
import struct
from time import sleep

class Server:
    # IP = socket.gethostbyname(socket.gethostname())
    IP = '172.18.0.61'
    UDP_PORT = 13117
    TCP_PORT = 50000

    # magic_cookie = b'11111110111011011011111011101111'
    magic_cookie = 0xfeedbeef
    # m_type = b'00000010'
    m_type = 0x2
    # server_port = b'1100001101010000'
    server_port = 50000
    udp_offer = magic_cookie + m_type + server_port

    def __init__(self):
        self.sending_udp_messages = False
        self.receive_m = False

        self.client_list = []

        self.udp_sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP

        # setting up udp socket for broadcasting to all clients
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        
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
        print("Server started, listening on ip address {}".format(self.IP))

        for i in range(10):
            print(i)
            # self.udp_sock.sendto(self.udp_offer, ('<broadcast>', self.UDP_PORT))
            self.udp_sock.sendto(struct.pack('IbH', self.magic_cookie, self.m_type, self.server_port), ('<broadcast>', self.UDP_PORT))
            sleep(1)

        self.sending_udp_messages = False

    def accept_connections(self):
        """
        accepts connection requests and client's team name
        from clients while still sending offer requests.
        """
        while self.sending_udp_messages:
            try:
                client_socket, client_address = self.tcp_sock.accept()

                client_thread = threading.Thread(target=self.get_team_name, args=(client_socket,client_address))
                client_thread.start()

            except socket.timeout:
                # print("socket timed out")
                continue


    def get_team_name(self, client_socket, client_address):
        """
        recieves the client's team name and saves it with additional data to client_list
        @param client_socket: tuple of 5, the client's socket
        @param client_address: tuple of 2, the client's IP and port
        """
        # TODO: put in try and catch!
        team_name = client_socket.recv(1024).decode('utf-8')
        # print(team_name)

        self.client_list.append((client_socket, client_address, team_name))

    def assign_to_groups(self):
        """
        divides randomly all clients in client_list in to two groups.
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
        creates a start game message
        """
        m = 'Welcome to Keyboard Spamming Battle Royale.\n'
        m += 'Group 1:\n==\n'
        for c in group_a:
            m += c[2]
        
        m += 'Group 2:\n==\n'
        for c in group_b:
            m += c[2]

        m += 'Start pressing keys on your keyboard as fast as you can!!'

        return m

    def send_tcp_message(self, message):
        """
        sends message to all clients over tcp
        @param message: String to send
        """
        for client in self.client_list:
            client[0].send(bytes(message, 'utf-8'))

    def release_clients(self):
        """
        closes connection to all clients in the end of a game
        """
        for c in self.client_list:
            try:
                c[0].shutdown(socket.SHUT_RDWR)
                c[0].close()
            except Exception as identifier:
                continue
            

        self.client_list = []

    def get_tcp_messages(self, counter_a, counter_b):
        """
        opens a thread for each client so the server can recieve incoming messages from all clients simultansouly
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
        recieve a message from a single client
        """
        while self.receive_m:
            m = sock.recv(1024)
            # print(len(m.decode('utf-8')))
            counter[sock] += 1

    def create_game_end_message(self, group_a, counter_a, group_b, counter_b):
        """
        creates an end game message
        """
        sum_a = sum(counter_a.values())
        sum_b = sum(counter_b.values())
        winner = -1

        m = 'Game over!\nGroup 1 typed in {} characters. Group 2 typed in {} characters.\n'.format(sum_a, sum_b)
        if sum_a >= sum_b:
            winner = 1
            m += 'Group 1 wins!\n\n'
        else:
            winner = 2
            m += 'Group 2 wins!\n\n'

        m += 'Congratulations to the winners:\n==\n'

        if winner == 1:
            for i in group_a:
                m += i[2] + '\n'

        else:
            for i in group_b:
                m += i[2] + '\n'

        return m

    def main(self):
        """
        main game loop
        """
        server.tcp_sock.listen()
        try:

            while True:
                udp_message_thread = threading.Thread(target=server.send_udp_message)
                udp_message_thread.setDaemon(True)
                udp_message_thread.start()
                
                tcp_receive_thread = threading.Thread(target=server.accept_connections)
                tcp_receive_thread.setDaemon(True)
                tcp_receive_thread.start()

                udp_message_thread.join()
                tcp_receive_thread.join()

                if len(server.client_list) < 2:
                    print("not enough players!")
                    server.release_clients()
                    continue

                group_a, group_b = server.assign_to_groups()

                print("group_a: {}".format(group_a))
                print("group_b: {}".format(group_b))



                # Game mode

                counter_group_a = {}
                counter_group_b = {}

                for s in group_a:
                    counter_group_a[s[0]] = 0
                
                for s in group_b:
                    counter_group_b[s[0]] = 0

                # server.get_tcp_messages(counter_group_a, counter_group_b)
                x = threading.Thread(target=server.get_tcp_messages, args=(counter_group_a, counter_group_b))
                x.start()

                game_start_message = server.create_game_start_message(group_a, group_b)
                server.send_tcp_message(game_start_message)

                x.join()

                print()
                print(counter_group_a)
                print()
                print(counter_group_b)
                print()
                # print("Game Over!")


                print(server.create_game_end_message(group_a, counter_group_a, group_b, counter_group_b))
                # server.send_tcp_message("Game over!")

                server.release_clients()
        except KeyboardInterrupt as e:
            print("Server Done!")


        




if __name__ == "__main__":
    server = Server()
    server.main()
    # server.tcp_sock.listen()
    # try:

    #     while True:
    #         udp_message_thread = threading.Thread(target=server.send_udp_message)
    #         udp_message_thread.setDaemon(True)
    #         udp_message_thread.start()
            
    #         tcp_receive_thread = threading.Thread(target=server.accept_connections)
    #         tcp_receive_thread.setDaemon(True)
    #         tcp_receive_thread.start()

    #         udp_message_thread.join()
    #         tcp_receive_thread.join()

    #         if len(server.client_list) < 2:
    #             print("not enough players!")
    #             server.release_clients()
    #             continue

    #         group_a, group_b = server.assign_to_groups()

    #         print("group_a: {}".format(group_a))
    #         print("group_b: {}".format(group_b))



    #         # Game mode

    #         counter_group_a = {}
    #         counter_group_b = {}

    #         for s in group_a:
    #             counter_group_a[s[0]] = 0
            
    #         for s in group_b:
    #             counter_group_b[s[0]] = 0

    #         # server.get_tcp_messages(counter_group_a, counter_group_b)
    #         x = threading.Thread(target=server.get_tcp_messages, args=(counter_group_a, counter_group_b))
    #         x.start()

    #         game_start_message = server.create_game_start_message(group_a, group_b)
    #         server.send_tcp_message(game_start_message)

    #         x.join()

    #         print()
    #         print(counter_group_a)
    #         print()
    #         print(counter_group_b)
    #         print()
    #         # print("Game Over!")


    #         print(server.create_game_end_message(group_a, counter_group_a, group_b, counter_group_b))
    #         # server.send_tcp_message("Game over!")

    #         server.release_clients()
    # except KeyboardInterrupt as e:
    #     print("Server Done!")



    # server.tcp_sock.shutdown(socket.SHUT_RDWR)
    # server.tcp_sock.close()

    # server.start_game()

    # server.send_udp_message()