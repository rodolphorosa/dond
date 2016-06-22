import socket, time, sys
import _thread
from random import shuffle
from banker import Banker 
from contestant import Contestant 
from briefcase import Briefcase 

nchoises = { 1:6, 2:5, 3:4, 4:3, 5:2 } # Numero de maletas a serem abertas por rodada

# Inicializa as maletas de forma aleatória
def prepareBriefcases():
	cases 	= {}
	values 	= [value.replace("\n", "") for value in open("VALUES").readlines()]

	shuffle(values)

	briefcases = {}
	for index in range(len(values)):
		briefcase = Briefcase(str(index + 1), values[index])
		briefcases[index+1] = briefcase
	return briefcases

# Retorna o número de maletas a serem abertas na rodada
def calculateRoundChoices(currentround):
	if currentround < 6: return nchoises[currentround]
	return 1

# Envia mensagem pier to pier
def sendMessageToClient(message, socket, address):
	encodedmessage = message.encode()
	socket.sendto(encodedmessage, address)

# Envia mensagem broadcast
def sendMessageToAll(message, sockets):
	encodedmessage = message.encode()
	for socket in sockets:
		socket.sendall(encodedmessage)

# Faz uma requisição a um cliente
def makeRequest(message, socket, address):
	encodedmessage = message.encode()
	socket.sendto(encodedmessage, address)
	answer = socket.recv(1024)
	return answer.decode()

# Invocada quando um jogador conecta ao servidor
def playerConnected(connection, client):
	print("Conectado pelo jogador: ", client)

def countOpenCases(briefcases):
	sum = 0
	for briefcase in briefcases.keys():
		if briefcases[briefcase].isOpen() or briefcases[briefcase].isClaimed():
			sum = sum + 1
	return sum

# Envia mensagens apropriadas sobre a conexão do jogador
def connectPlayerAs(role):
	print("Jogador conectou como " + role + ".")
	connection.sendto(("Conectado como " + role + ".").encode(), client)
	sendMessageToAll("Jogador conectou como " + role + ".", 
		[conn for (conn, client) in contestants + bankers + spectators])

# Função principal
def main():
	banker 		= Banker()
	contestant 	= Contestant()	
	briefcases 	= prepareBriefcases()

	contestantsocket, contestantaddress = contestants[0]
	bankersocket, bankeraddress 		= bankers[0]

	# Nesta etapa, o competidor escolhe a maleta inicial, que permanecerá fechada até o fim do jogo
	sendMessageToAll("Contestante esta escolhendo sua maleta...\n", 
			[conn for (conn, _) in bankers + spectators])

	while True:
		claimed = makeRequest("claim", contestantsocket, contestantaddress)
		
		if not claimed.strip():
			continue

		if int(claimed) > 26 or int(claimed) < 1:
			sendMessageToClient("Esta maleta nao existe\n", contestantsocket, contestantaddress)
			continue
		
		briefcase = briefcases[int(claimed)]

		if briefcase.isOpen() or briefcase.isClaimed():
			sendMessageToClient("Maleta ja foi escolhida\n", contestantsocket, contestantaddress)
			continue

		contestant.claimBriefcase(briefcase)
		briefcase.claimCase()
		message = "Maleta escolhida: " + claimed + "\n"
		sendMessageToAll(message, 
			[conn for (conn, client) in contestants + bankers + spectators])
		break

	# Executa as rodadas até que o apostador aceite a proposta do banqueiro ou restem apenas uma maleta fechada
	currentround = 1

	while True:
		cases_to_open 	= calculateRoundChoices(currentround)
		open_cases 		= 0

		while open_cases < cases_to_open:
			sendMessageToAll("Contestante esta escolhendo uma maleta para ser aberta...\n", 
				[conn for (conn, _) in bankers + spectators])
			selected = makeRequest("select", contestantsocket, contestantaddress)

			if not selected.strip():
				continue

			if int(selected) > 26 or int(selected) < 1:
				sendMessageToClient("Esta maleta nao existe\n", contestantsocket, contestantaddress)
				continue
			
			briefcase = briefcases[int(selected)]

			if briefcase.isOpen() or briefcase.isClaimed():
				sendMessageToClient("Maleta ja foi escolhida\n", contestantsocket, contestantaddress)
				continue

			briefcase.openCase()
			message = "Maleta escolhida: " + str(briefcase.getNumber()) + "\nValor: " + str(briefcase.getAmount()) + "\n"
			sendMessageToAll(message, 
				[conn for (conn, _) in contestants + bankers + spectators])
			open_cases = open_cases + 1
		
		sendMessageToAll("Banqueiro esta fazendo uma proposta...\n", 
				[conn for (conn, _) in contestants + spectators])
		bankeroffer = makeRequest("makeoffer", bankersocket, bankeraddress)

		message = "Oferta do banqueiro: " + bankeroffer + "\n"
		sendMessageToAll(message, 
				[conn for (conn, _) in contestants + spectators])

		sendMessageToAll("Contestante esta decidindo se topa ou nao topa a proposta...\n", 
				[conn for (conn, _) in bankers + spectators])
		answer = makeRequest("agreement", contestantsocket, contestantaddress)

		if answer.lower() in ["s", "sim"]:
			sendMessageToAll("Contestante aceitou a proposta.\n", 
				[conn for (conn, _) in bankers + spectators])

			banker.loseAmount(bankeroffer)
			contestant.acceptOffer(bankeroffer)

			message = "A maleta tinha: " + contestant.getBriefcase().getAmount() + "\n"
			sendMessageToAll(message, 
				[conn for (conn, _) in contestants + bankers + spectators])
			
			message = "Competidor ganhou: " + bankeroffer + "\n"
			sendMessageToAll(message, 
				[conn for (conn, _) in contestants + bankers + spectators])
			return
		elif answer.lower() in ["n", "nao", "não"]:
			sendMessageToAll("Contestante rejeitou a proposta.\n", 
				[conn for (conn, _) in bankers + spectators])

			if countOpenCases(briefcases) == 24:
				last = [briefcases[case] for case in briefcases.keys() if not briefcases[case].isOpen() and not briefcases[case].isClaimed()]
				
				message = "Ultima maleta: " + last[0].getNumber() + "\nValor: " + last[0].getAmount() + "\n"
				sendMessageToAll(message, 
					[conn for (conn, _) in contestants + bankers + spectators])
				
				message = "Competidor ganhou: " + contestant.getBriefcase().getAmount()
				sendMessageToAll(message, 
					[conn for (conn, _) in contestants + bankers + spectators])
				return
			currentround = currentround + 1
			continue

def checkGameStart():
	# checa se existe um banqueiro e um contestante
	# conectados em intervalos de um segundo
	while True:
		if contestants and bankers:
			print("Banqueiro e contestante conectados. Iniciando o jogo.")
			sendMessageToAll("Vamos comecar o jogo!", 
				[conn for (conn, client) in contestants + bankers + spectators])

			main()

			time.sleep(1.0)

			for (conn, client) in contestants + bankers + spectators:
				conn.sendall(b"end")

			print("Encerrando jogo...")

			bankers.clear()
			contestants.clear()
			spectators.clear()

			print("Esperando jogadores...")

		time.sleep(1.0)

def handleConnection(connection, client):
	success = False

	# recebe e gerencia o papel do jogador conectado
	while not success:
		try:
			message = connection.recv(1024)
		except socket.timeout:
			continue

		if message == b'contestant':
			playerConnected(connection, client)

			if len(contestants) < LIMIT:
				sendMessageToClient("ok", connection, client)
				connectPlayerAs('contestante')
				contestants.append((connection, client))
				success = True
			else:
				sendMessageToClient("not", connection, client)

		elif message == b'banker':
			playerConnected(connection, client)

			if len(bankers) < LIMIT:
				sendMessageToClient("ok", connection, client)
				connectPlayerAs('banqueiro')
				bankers.append((connection, client))
				success = True
			else:
				sendMessageToClient("not", connection, client)

		elif message == b'spectator':
			sendMessageToClient("ok", connection, client)

			playerConnected(connection, client)
			connectPlayerAs('expectador')
			spectators.append((connection, client))
			success = True
		
		else:
			sendMessageToClient("invalid", connection, client)

if __name__ == "__main__":
	LIMIT = 1
	contestants = []
	bankers = []
	spectators = []

	HOST = ""
	PORT = 5000

	# checa se uma porta foi dada
	if len(sys.argv) > 1:
		PORT = int(sys.argv[1])

		if len(sys.argv) > 2:
			print("Modo de usar:", sys.argv[0], "<porta-do-servidor>")
			sys.exit()

	# inicia o servidor
	origin = (HOST, PORT)
	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp.settimeout(1.0)
	tcp.bind(origin)
	tcp.listen(1)

	print("Servidor iniciado.")
	print("Esperando jogadores...")

	# inicia a thread que checa se o jogo pode iniciar
	_thread.start_new_thread(checkGameStart, ())

	# começa a esperar por conexões de clientes
	try:
		while True:
			try:
				connection, client = tcp.accept()
			except socket.timeout:
				continue

			_thread.start_new_thread(handleConnection, (connection, client))
	except (SystemExit, KeyboardInterrupt):
		print("Desligando servidor...")
		sendMessageToAll("end", 
			[conn for (conn, client) in contestants + bankers + spectators])
	finally:
		tcp.close()