import socket, sys

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

def choose():
	role = ""
	prompt = "Escolha seu papel no jogo (banker, contestant, spectator):\n"

	while not role:
		role = input(prompt).lower()

	return role

def getInput(prompt):
	message = ""

	while not message:
		message = input(prompt)

	return message

def claimCase(tcp):
	message = getInput("Escolha uma maleta (1/26): ")
	tcp.sendall(message.encode())

def selectCase(tcp):
	message = getInput("Escolha uma maleta para ser aberta (1/26): ")
	tcp.sendall(message.encode())

def handleOffer(tcp):
	message = getInput("Topa ou nao topa? [S/N]: ")
	tcp.sendall(message.encode())

def makeOffer(tcp):
	message = getInput("Entre com uma oferta: ")
	tcp.sendall(message.encode())

def beABanker():
	while True:
		try:
			servermessage = tcp.recv(4096).decode()
		except socket.timeout:
			continue

		for message in servermessage.split("\n"):
			if message == "makeoffer":
				makeOffer(tcp)
			elif message == "end":
				sys.exit(0)
			else:
				print(message)

def beAContestant():
	while True:
		try:
			servermessage = tcp.recv(4096).decode()
		except socket.timeout:
			continue

		for message in servermessage.split("\n"):
			if message == "claim":
				claimCase(tcp)
			elif message == "select":
				selectCase(tcp)
			elif message == "agreement":
				handleOffer(tcp)
			elif message == "end":
				sys.exit(0)
			else:
				print(message)

def beASpectator():
	while True:
		try:
			servermessage = tcp.recv(4096).decode()

			for message in servermessage.split("\n"):
				if message == "end":
					sys.exit(0)
				else:
					print(message)

		except socket.timeout:
			continue

servermessage = "".encode()

while servermessage.decode() != "ok":
	role = choose()
	tcp.send(role.encode())

	while True:
		try:
			servermessage = tcp.recv(4096)
			break
		except socket.timeout:
			continue

	if servermessage.decode() == "not":
		print("Ja existe um", role, "conectado. Escolha outro papel.")
	elif servermessage.decode() == "invalid":
		print("Papel invalido.")

try:
	if role == "banker":
		beABanker()
	elif role == "contestant":
		beAContestant()
	elif role == "spectator":
		beASpectator()
except (SystemExit, KeyboardInterrupt):
	print("Saindo do jogo...")
finally:
	tcp.close()