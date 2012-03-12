import threading
import socket
import pickle
import Queue
import time
import select
import logging
import os
class Network:
	def __init__(self, mode, stack, port):
		
		self.inq = Queue.Queue(maxsize=0)
		self.outq = stack
		self.closed = threading.Event()
		self.port = port
		if mode == 'client':
			self.controller = Client(self.inq, self.outq, self.closed, self.port)	
			logging.basicConfig(level=logging.DEBUG, filename='client.log', format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		if mode == 'server':
			self.controller = Server(self.inq, self.outq, self.closed, self.port)
			logging.basicConfig(level=logging.DEBUG, filename='server.log', format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	def send(self, packet):
		logging.debug('ffffffff')
		#print 'ggggggg'
		self.inq.put(packet)
		logging.debug('put packet in queue')	
	def start(self):
		#print 'starting'
		self.controller.setup()
		#print 'setup finished'
		self.controller.start()
	
	def exit(self):
		self.controller.exit = True
		self.closed.wait()

class Send(threading.Thread):
	def __init__(self, response, socklock, queue, connected, running):
		self.response = response
		self.socklock = socklock
		self.queue = queue
		self.connected = connected
		self.running = running
		self.exit = False
		self.logger = logging.getLogger('Send')
		threading.Thread.__init__(self)
		
	def run(self):
		self.logger.debug('Send thread started')
		self.running.acquire()
		self.logger.debug('Semaphore acquired')
		while not self.exit:
			self.logger.debug('Waiting for connection....')
			self.connected.wait(5)
			if self.connected.isSet():
				try:
					item = self.queue.get(5)
				except Queue.Empty:
					pass
				else:
					self.logger.debug('Calling Send....')
					self.logger.debug('packet:' + str(item))
					self.send(item)
		self.logger.debug('Exiting')
		self.running.release()

	def send(self, packet):
#		self.logger.debug('Aquiring Lock')
#		self.socklock.acquire()
#		self.logger.debug('Calling Connect')
#		self.connect()
#		self.logger.debug('Sending Packet')
#		self.socket.send(pickle.dumps(packet))
#		self.socket.send(pickle.dumps({'id':'eol'}))
#		self.logger.debug('Packet Sent')
#		self.socklock.release()
#		self.logger.debug('Released Lock')
		x = select.select((),(self.socket,),(),60)			
		if len(x[1]) != 0:
			self.logger.debug('sending.........')
			self.socket.send(pickle.dumps(packet))
		
	def setsocket(self, sock):
		self.logger.debug('Send Socket Set')
		self.socket = sock
		
	def connect(self):
		self.logger.debug('COnnect Packet Sent')
		self.socket.send(pickle.dumps({'id':'preamble'}))
#		self.socklock.release()
		self.logger.debug('Waiting for reply....')
		self.response.wait()
#		self.socklock.acquire()
		self.logger.debug('Got Reply')
		self.response.clear()
		
		
class Receive(threading.Thread):
	def __init__(self, response, socklock, stack, connected, disconnected, running, exitsig):
		self.response = response
		self.socklock = socklock
		self.stack = stack
		self.connected = connected
		self.disconnected = disconnected
		self.running = running
		self.exit = False
		self.exitsig = exitsig
		self.logger = logging.getLogger('Receive')
		threading.Thread.__init__(self)
		
	def run(self):
		self.logger.debug('Receive waiting for connection')
		self.running.acquire()
		self.logger.debug('Recieve aquiring semaphore')
		while not self.exit:
			self.logger.debug('checking connection')
			self.connected.wait(5)
			if self.connected.isSet():
				self.logger.debug('waiting for packet')
				x = select.select([self.socket,self.exitsig,],(),(),60)
				if len(x[0]) != 0:
					if x[0][0] == self.socket:
						self.logger.debug('packet here...')
						data = self.socket.recv(1024)
						testdata = pickle.loads(data)
						self.logger.debug('packet recieve' + str(testdata))
						self.parse(data)
				else:
					self.connected.clear()
					self.disconnected.set()
		self.logger.debug('Receive Exiting')
		self.running.release()

	def parse(self, packet):
		data = pickle.loads(packet)
		if data['id'] == 'preamble':
			self.logger.debug('receive preamble aquiribng lock')
			self.socklock.acquire()
			self.logger.debug('got lock sending response')
			self.socket.send(pickle.dumps({'id':'accept'}))
			self.logger.debug('response sent')
		if data['id'] == 'accept':
			self.logger.debug('got accept seting response event')
			self.response.set()
		if data['id'] == 'eol':
			self.logger.debug('eol received releasing lock')
		#	self.socklock.release()
		if data['id'] == 'update':
		#	self.socklock.release()
			if data['item'] == 1:
				#Job update
				self.stack.put('network.job')
			if data['item'] == 2:
				#Full screen update
				self.stack.put('network.screen')
			if data['item'] == 3:
				#version update
				self.stack.put('network.version')
			if data['item'] == 4:
				#Full update
				self.stack.put('network.job')
				self.stack.put('network.screen')
				self.stack.put('network.version')
		if data['id'] == 'input':
		#	self.socklock.release()
			self.stack.put({'id':'handle.command', 'data':data['data']})
		if data['id'] == 'test':
		#	self.socklock.release()
			self.logger.debug('got test packet')
			self.stack.put(data['item'])
		#if data['id'] == 'keepalive':
		#	self.socklock.release()
		if data['id'] == 'clientup':
			if self.data['item'] == 'line':
				self.stack.put({'id':'client.lineup', 'data':data['data']})
			elif self.data['item'] == 'screen':
				self.stack.put({'id':'client.screen', 'data':data['data']})
			elif self.data['item'] == 'job':
				self.stack.put({'id':'client.job', 'data':data['data']})
			elif self.data['item'] == 'version':	
				self.stack.put({'id':'client.version', 'data':data['data']})


	def setsocket(self, sock):
		self.socket = sock

class Server(threading.Thread):
	def __init__(self, inq, outq, closed, port):
		self.host = ''
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind((self.host, self.port))
		self.connected = threading.Event()
		self.disconnected = threading.Event()
		self.socklock = threading.Lock()
		self.response = threading.Event()
		self.running = threading.Semaphore(3)
		self.inq = inq
		self.outq = outq
		self.closed = closed
		self.exitsig = os.pipe()
		self.exit = False
		threading.Thread.__init__(self)
	
	def setup(self):
		logging.debug('Startup Initiated')
		self.send = Send(self.response, self.socklock, self.inq, self.connected, self.running)
		self.receive = Receive(self.response, self.socklock, self.outq, self.connected, self.disconnected, self.running,self.exitsig[0])
		self.keepalive = KeepAlive(self.socklock, self.connected, self.inq, self.running, self.exitsig[0])
		self.send.start()
		self.receive.start()
		self.keepalive.start()
		logging.debug('Startup Finished')
		
	def listen(self):
		logging.debug('Listening for connection')
		self.sock.listen(1)
		self.conn, addr = self.sock.accept()
		logging.debug('accepted connection')
		self.send.setsocket(self.conn)
		self.receive.setsocket(self.conn)
		self.connected.set()
		logging.debug('set sockets and connected flag')
			
	def run(self):
		self.listen()
		while not self.exit:
			self.disconnected.wait(5)
			if self.disconnected.isSet():
				logging.debug('Disconnected calling listen')
				self.listen()
		logging.debug('calling shutdown')
		self.shutdown()

	def shutdown(self):
		#print 'exiting'
		self.send.exit = True
		self.receive.exit = True
		self.keepalive.exit = True
		os.write(self.exitsig[1], 'exit')
		self.running.acquire(True)
		logging.debug('sem 1 aquired')
		self.running.acquire(True)
		logging.debug('sem2 acquired')
		self.running.acquire(True)
		logging.debug('sem3 acquired')
		self.conn.shutdown(SHUT_RDWR)
		self.conn.close()
		self.socket.close()
		logging.debug('closed sockets')
		self.closed.set()
		logging.debug('set closed event')

class Client(threading.Thread):
	def __init__(self, inq, outq, closed, port):
		self.host = '127.0.0.1'
		self.port = port
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connected = threading.Event()
		self.disconnected = threading.Event()
		self.socklock = threading.Lock()
		self.response = threading.Event()
		self.closed = closed
		self.inq = inq
		self.outq = outq	
		self.running = threading.Semaphore(3)
		self.exit = False
		self.exitsig = os.pipe()
		threading.Thread.__init__(self)
		
	def run(self):
		self.connect()
		while not self.exit:
			self.disconnected.wait(5)
			if self.disconnected.isSet():
				logging.debug('Disconnected')
				self.connect()
		logging.debug('Calling shutdown')
		self.shutdown()
		
		
	def connect(self):
		logging.debug('Connecting.....')
		self.socket.connect((self.host, self.port))
		logging.debug('Connected')
		self.connected.set()
		
	def setup(self):
		logging.debug('Setup Started')
		self.send = Send(self.response, self.socklock, self.inq, self.connected, self.running)
		self.receive = Receive(self.response, self.socklock, self.outq, self.connected, self.disconnected, self.running, self.exitsig[0])
		self.send.setsocket(self.socket)
		self.receive.setsocket(self.socket)
		self.keepalive = KeepAlive(self.socklock, self.connected, self.inq, self.running, self.exitsig[0])
		self.send.start()
		self.receive.start()
		self.keepalive.start()
		logging.debug('Setup Finished')
		
	def shutdown(self):
		logging.debug('Sutting Down')
		self.send.exit = True
		self.receive.exit = True
		self.keepalive.exit = True
		os.write(self.exitsig[1], 'exit')
		self.running.acquire(True)
		logging.debug('acquired sem1')
		self.running.acquire(True)
		logging.debug('acquired sem2')
		self.running.acquire(True)
		logging.debug('acquired sem3')
		self.socket.shutdown(SHUT_RDWR)
		self.socket.close()
		logging.debug('closed socket')
		self.closed.set()
		logging.debug('closed event set')

class KeepAlive(threading.Thread):
	def __init__(self, socklock, connected, inq, running, exitsig):
		self.socklock = socklock
		self.connected = connected
		self.exit = False
		self.packet = {'id':'keepalive'}
		self.running = running
		self.inq = inq
		self.exitsig = exitsig
		threading.Thread.__init__(self)
	def run(self):
		self.running.acquire()
		logging.debug('aquired semaphore kepalive')
		while not self.exit:	
			self.connected.wait(5)
			if self.connected.isSet():
				self.inq.put(self.packet)
				select((self.exitsig,),(),(),15)
		logging.debug('Keepalive exiting')
		self.running.release()
			
class Server2(threading.Thread):
	def __init__(self, mode, port, inq, outq, closed):
		self.mode = mode
		self.port = port
		self.inq = inq
		self.outq = outq
		self.closed = closed
		if self.mode == 'client':
			self.client_setup()
		elif self.mode == 'server':
			self.server_setup()	
		
	def client_setup(self):
		self.host = '127.0.0.1'
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
					
		
	
	
		
	
