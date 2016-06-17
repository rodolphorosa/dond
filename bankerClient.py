import socket, sys
from banker import Banker

HOST = "127.0.0.1"
PORT = 5000

if len(sys.argv) > 1:
	HOST = sys.argv[1]

	if len(sys.argv) > 2:
		PORT = int(sys.argv[2])

		if len(sys.argv) > 3:
			print("Modo de usar:", sys.argv[0], "<ip-do-servidor> <porta-do-servidor>")
			sys.exit()

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