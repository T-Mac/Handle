import pytest
import logging
LOGLVL = logging.DEBUG
logging.basicConfig(level=LOGLVL, format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
module_logger = logging.getLogger(__name__)
from multiprocessing import Process, Queue, Event
import lib.network
from os import urandom
import time
class Network(Process):
	def __init__(self, mode, host, port, test_data):
		self.mode = mode
		self.connection = lib.network.loadNetwork(mode, host, port, self.receive)
		self.connection.deamon = True
		self.lines = []
		self.test_data = test_data
		self.exit = Event()

		Process.__init__(self)
		
	def run(self):
		self.connection.start()
		self.connection.connected()
		if self.mode == 'server':
			time.sleep(2)

		for line in self.test_data:
			self.connection.send(line)
		print self.connection
		self.exit.set()
			
	def receive(self, line):
		print self.lines
		self.lines.append(line)

	def join(self):
		print self.lines
		self.connection.stop()
		print self.lines
		Process.join(self)

		return self.lines

@pytest.fixture
def host():
	return ('127.0.0.1', 10000)
	
@pytest.fixture 		
def client(host, data):
	return Network('client', host[0], host[1], data[0])

@pytest.fixture	
def server(host, data):
	return Network('server', host[0], host[1], data[1])
	
@pytest.fixture(scope= 'module')
def data():
	data = []
	for x in range(2):
		list = []
		for x in range(10):
			list.append(urandom(10))
		data.append(list)
	return data
	
class Test_Network(object):
	def test_network(self, client, server, data):
		server.start()
		client.start()
		raw_input()
		print client.join()
		print server.join()