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
tcp.settimeout(1.0)
tcp.connect(destiny)
tcp.send(b"banker")

def getInput(prompt):
	message = ""

	while not message:
		message = input(prompt)

	return message

def makeOffer(tcp):
	message = getInput("Entre com uma oferta: ")
	tcp.sendall(message.encode())

try:
	while True:
		try:
			servermessage = tcp.recv(4096)
		except socket.timeout:
			continue

		if servermessage.decode() == "makeoffer":
			makeOffer(tcp)
		elif servermessage.decode() == "end":
			sys.exit(0)
		else:
			print(servermessage.decode())
except (SystemExit, KeyboardInterrupt):
	print("Saindo do jogo...")
finally:
	tcp.close()