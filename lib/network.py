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
		self.pre = pickle.dumps({'id':'preamble'})
		self.eol = pickle.dumps({'id':'eol')}
		self.netlock = threading.Lock()
		
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
		self.conn.shutdown(SHUT_RDWR)
		self.conn.close() 
					
							
	def sendData(self, packet):
		self.netlock.acquire()
		self.conn.send(self.pre)
		self.conn.send(packet)
		self.conn.send(self.eol)
		self.netlock.release()

				
				
				
class Interpret:
	def __init__(self, handle):
		self.handle = handle
		
	def parse(self, packet):
		data = pickle.loads(packet)
		if data['id'] == 'preamble':
			self.handle.netlock.acquire()
		if data['id'] == 'eol':
			self.handle.netlock.release()
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

	