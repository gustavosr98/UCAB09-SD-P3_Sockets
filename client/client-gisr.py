# CLI Parameters
import argparse

# Berkeley sockets API
import socket

# Cryptography libraries
from base64 import b64decode
from hashlib import md5


class Client:
    def __init__(self, username: str, socketTCP, socketUDP ):
        self.username = username
        self.socketTCP = socketTCP
        self.socketUDP = socketUDP

    # CLIENT
    def showMessage(self):
        try:
            self.setSocketTCP()
            self.setSocketUDP()

            self.sayHi()
            self.setMessageLength()
            self.giveMeMessage()
            self.tryToReadMessage()
            self.validateChecksum()
            self.sayBye()

            self.printMessage()
        except Exception as e:
            print(e)

    # SOCKETS UDP
    def setSocketUDP(self):
        try:    
            self.sockUDP: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sockUDP.bind(self.socketUDP)
        except:
            raise Exception('ERROR: Listenning port busy or invalid')
    
    def tryToReadMessage(self, maxAttemps=5, timeout=7):
        attempCount = 0
        response = ''
        self.sockUDP.settimeout(timeout)
        while attempCount < maxAttemps and not(hasattr(self, 'responseUDP')):
            try:
                response, address = self.sockUDP.recvfrom(1024)
                self.responseUDP = (b64decode(response)).decode('utf-8')
            except:
                print(f'Attemp number: {attempCount+1} ...')
                attempCount += 1

        if not(hasattr(self, 'responseUDP')):
            raise Exception('ERROR: Max attemps reached')

    # SOCKETS TCP
    def setSocketTCP(self):
        try:
            self.sockTCP: socket.socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self.sockTCP.settimeout(10)
            self.sockTCP.connect(self.socketTCP)
        except:
            raise Exception('ERROR: Unable to connect with the server')
    
    def setLastResponseTCP(self):
        response: str = self.sockTCP.recv(1024).decode('utf-8').strip()
        reponseCode: str = response.split(' ')[0]
        message: str =  " ".join(response.split(' ')[1:])
        self.lastReponseTCP = {}
        self.lastReponseTCP["code"]: str = reponseCode
        self.lastReponseTCP["message"]: str = message

    def sendCommand(self, command: str):
        self.sockTCP.send(command.encode())
        self.setLastResponseTCP()
        if (self.lastReponseTCP["code"] != 'ok'):
            message = self.lastReponseTCP["message"]
            # complement = ''
            
            # if message == :  
            
            raise Exception(f'ERROR: {message}')
        
    # COMMANDS
    def sayHi(self):
        command = f'helloiam {self.username}'
        self.sendCommand(command)

    def setMessageLength(self):
        command = 'msglen'
        self.sendCommand(command)
        self.messageLength: int = int(self.lastReponseTCP["message"]) 
    
    def giveMeMessage(self):
        command = f'givememsg {str(self.socketUDP[1])}'
        self.sendCommand(command)
    
    def getChecksum(self):
        command = f'givememsg {str(self.socketUDP[1])}'
        self.sendCommand(command)
    
    def validateChecksum(self):
        command = f'chkmsg {str(md5(self.responseUDP.encode()).hexdigest())}'
        self.sendCommand(command)
    
    def sayBye(self):
        command = 'bye'
        self.sendCommand(command)

    # OTHERS   
    def printMessage(self):
        print()
        print(f'El mensaje para {self.username} es 📩:')
        print()
        print(self.responseUDP)
        print()


def getArguments():
    parser = argparse.ArgumentParser(
        prog='client-gisr',
        description="""
            Client requester to get a secret message with TCP and get it with UDP. 🌐
            Author: GiSR - Gustavo Sánchez 📟
        """
    )
    parser.add_argument("-u", "--username", dest = "username", help="Username (Mandatory)", required=True)
    parser.add_argument("-sip", "--server_ip", dest = "server_ip", default = "10.2.126.2", help="Server IP. Default: 10.2.126.2")
    parser.add_argument("-sport", "--server_port", dest = "server_port", default = 19876, help="Server TCP Port. Default: 19876", type=int)
    parser.add_argument("-lport", "--listenning_port", dest = "listenning_port", default = 12345, help="Listenning UDP Port. Default: 12345", type=int)
    
    return parser.parse_args()

if __name__ == "__main__":
    args = getArguments()

    client = Client(
        username = args.username, 
        socketTCP = ( args.server_ip, args.server_port ),
        socketUDP = ( '0.0.0.0', args.listenning_port )
    )
    client.showMessage()
