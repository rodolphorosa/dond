import socket
from banker import Banker

HOST = "127.0.0.1"
PORT = 5000

destiny = (HOST,PORT)

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.connect(destiny)
tcp.send(b"banker")

def makeOffer(tcp):
	message = input("Entre com uma oferta: ")
	tcp.sendall(message.encode())

while True:
	servermessage = tcp.recv(4096)
	if servermessage.decode() == "makeoffer":
		makeOffer(tcp)
	else:
		print(servermessage.decode())
tcp.close()