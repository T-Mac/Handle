import threading
import socket
import select
import pickle

class Network:
	def __init__(self, handle):
		self.host = ''
		self.port = 50007
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((self.host, self.port))
		self.exit = False
		self.handle = handle
		self.inter = Interpret(self.handle)
		self.hand = pickle.dumps({'id':'handshake'})
		self.reply = pickle.dumps({'id':'reply')}
		
	def run(self):
		while not self.exit:
			self.sock.listen(1)
			self.conn, addr = self.sock.accept()
			self.connected = True
			while self.connected:
				x = select.select((self.conn,),(),(),60)
				if len(x[0]) != 0:
					data = self.sock.recv(1024)
					self.inter.parse(data)
				else:
					self.connected = False
					
					
	def handshake(self):
		data = self.sock.recv(1024)
		packet = pickle.loads(data)
		if packet['id'] == 'handshake':

				
				
				
class Interpret:
	def __init__(self, handle):
		self.handle = handle
		
	def parse(self, packet):
		data = pickle.loads(packet)
		if data['id'] == 'update':
			if data['item'] == 1:
				#Job update
				self.handle.addtask('network.job')
			if data['item'] == 2:
				#Full screen update
				self.handle.addtask('network.screen')
			if data['item'] == 3:
				#version update
				self.handle.addtask('network.version')
			if data['item'] == 4:
				#Full update
				self.handle.addtask('network.job')
				self.handle.addtask('network.screen')
				self.handle.addtask('network.version')
		if data['id'] == 'input':
			self.handle.addtask('handle.command')

	