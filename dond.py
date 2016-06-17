import socket
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

# Função principal
def main():
	banker 		= Banker()
	contestant 	= Contestant()	
	briefcases 	= prepareBriefcases()

	contestantsocket, contestantaddress = contestants[0]
	bankersocket, bankeraddress 		= bankers[0]

	# Nesta etapa, o competidor escolhe a maleta inicial, que permanecerá fechada até o fim do jogo
	sendMessageToAll("Contestante esta escolhendo sua maleta...", 
			[conn for (conn, _) in bankers + spectators])

	while True:
		claimed = makeRequest("claim", contestantsocket, contestantaddress)

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
			sendMessageToAll("Contestante esta escolhendo uma maleta para ser aberta...", 
				[conn for (conn, _) in bankers + spectators])
			selected = makeRequest("select", contestantsocket, contestantaddress)

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
			sendMessageToAll("Contestante aceitou a proposta.", 
				[conn for (conn, _) in bankers + spectators])

			banker.loseAmount(bankeroffer)
			contestant.acceptOffer(bankeroffer)

			message = "A maleta tinha: " + contestant.getBriefcase().getAmount() + "\n"
			sendMessageToAll(message, 
				[conn for (conn, _) in contestants + bankers + spectators])
			
			message = "Competidor ganhou: " + bankeroffer
			sendMessageToAll(message, 
				[conn for (conn, _) in contestants + bankers + spectators])
			return
		elif answer.lower() in ["n", "nao", "não"]:
			sendMessageToAll("Contestante rejeitou a proposta.", 
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

if __name__ == "__main__":
	LIMIT = 1
	contestants = []
	bankers = []
	spectators = []

	HOST = ""
	PORT = 5000
	origin = (HOST, PORT)
	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp.settimeout(1.0)
	tcp.bind(origin)
	tcp.listen(1)

	print("Servidor iniciado.")
	print("Esperando jogadores...")

	try:
		while True:
			try:
				connection, client = tcp.accept()
				message = connection.recv(1024)
			except socket.timeout:
				continue

			if message == b'contestant':
				if len(contestants) < LIMIT:
					_thread.start_new_thread(playerConnected, (connection, client))

					print("Jogador conectou como contestante.")
					connection.sendto("Conectado como contestante.".encode(), client)
					sendMessageToAll("Jogador conectou como contestante.", 
						[conn for (conn, client) in contestants + bankers + spectators])

					contestants.append((connection, client))
				else:
					_thread.start_new_thread(playerConnected, (connection, client))
					
					print("Jogador conectou como expectador.")
					connection.sendto("Conectado como expectador.".encode(), client)
					sendMessageToAll("Jogador conectou como expectador.", 
						[conn for (conn, client) in contestants + bankers + spectators])

					spectators.append((connection, client))
			
			if message == b'banker' and len(bankers) < LIMIT:
				_thread.start_new_thread(playerConnected, (connection, client))

				print("Jogador conectou como banqueiro.")
				connection.sendto("Conectado como banqueiro.".encode(), client)
				sendMessageToAll("Jogador conectou como banqueiro.", 
					[conn for (conn, client) in contestants + bankers + spectators])

				bankers.append((connection, client))
			
			if contestants and bankers:
				print("Banqueiro e contestante conectados. Iniciando o jogo.")
				sendMessageToAll("Vamos comecar o jogo!", 
					[conn for (conn, client) in contestants + bankers + spectators])

				main()
	except (SystemExit, KeyboardInterrupt):
		print("Desligando servidor...")
	finally:
		tcp.close()