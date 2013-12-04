from server import Server
from client import Client
def loadNetwork(mode):
	if mode == 'client':
		return Client()
	elif mode == 'server':
		return Server()
	else:
		return False