import socket
from contestant import Contestant

HOST = "127.0.0.1"
PORT = 5000

destiny = (HOST,PORT)

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.connect(destiny)
tcp.send(b"contestant")

def claimCase(tcp):
	message = input("Escolha uma maleta (1/26): ")
	tcp.sendall(message.encode())

def selectCase(tcp):
	message = input("Escolha uma maleta para ser aberta (1/26): ")
	tcp.sendall(message.encode())

def handleOffer(tcp):
	message = input("Topa ou não topa? [S/N]: ")
	tcp.sendall(message.encode())

while True:
	servermessage = tcp.recv(4096)
	if servermessage.decode() == "claim":
		claimCase(tcp)
	elif servermessage.decode() == "select":
		selectCase(tcp)
	elif servermessage.decode() == "agreement":
		handleOffer(tcp)
	else:
		print(servermessage.decode())
tcp.close()