import threading
import socket
import pickle
import Queue
import time
import select
import logging
class Network:
	def __init__(self, mode, stack):
		
		self.inq = Queue.Queue(maxsize=0)
		self.outq = stack
		self.closed = threading.Event()
		if mode == 'client':
			self.controller = Client(self.inq, self.outq, self.closed)	
			logging.basicConfig(level=logging.DEBUG, filename='client.log', format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		if mode == 'server':
			self.controller = Server(self.inq, self.outq, self.closed)
			logging.basicConfig(level=logging.DEBUG, filename='server.log', format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	def send(self, packet):
		self.inq.put(packet)
		
	def start(self):
		print 'starting'
		self.controller.setup()
		print 'setup finished'
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
		threading.Thread.__init__(self)
		
	def run(self):
		logging.debug('Send thread started')
		self.running.acquire()
		logging.debug('Semaphore acquired')
		while not self.exit:
			logging.debug('Waiting for connection....')
			self.connected.wait(5)
			if self.connected.isSet():
				try:
					item = self.queue.get_nowait()
				except Queue.Empty:
					pass
				else:
					logging.debug('Calling Send....')
					self.send(item)
		logging.debug('Exiting')
		self.running.release()
			
	def send(self, packet):
		logging.debug('Aquiring Lock')
		self.socklock.acquire()
		logging.debug('Calling Connect')
		self.connect()
		logging.debug('Sending Packet')
		self.socket.send(packet)
		self.socket.send(pickle.dumps({'id':'eol'}))
		logging.debug('Packet Sent')
		self.socklock.release()
		logging.debug('Released Lock')
	
	def setsocket(self, sock):
		logging.debug('Send Socket Set')
		self.socket = sock
		
	def connect(self):
		logging.debug('COnnect Packet Sent')
		self.socket.send(pickle.dumps({'id':'preamble'}))
		logging.debug('Waiting for reply....')
		self.response.wait()
		logging.debug('Got Reply')
		self.response.clear()
		
		
class Receive(threading.Thread):
	def __init__(self, response, socklock, stack, connected, disconnected, running):
		self.response = response
		self.socklock = socklock
		self.stack = stack
		self.connected = connected
		self.disconnected = disconnected
		self.running = running
		self.exit = False
		threading.Thread.__init__(self)
		
	def run(self):
		logging.debug('Receive waiting for connection')
		self.running.acquire()
		logging.debug('Recieve aquiring semaphore')
		while not self.exit:
			logging.debug('checking connection')
			self.connected.wait(5)
			if self.connected.isSet():
				logging.debug('waiting for packet')
				x = select.select((self.socket,),(),(),60)
				if len(x[0]) != 0:
					logging.debug('packet here...')
					data = self.socket.recv(1024)
					testdata = pickle.loads(data)
					logging.debug('packet recieve' + str(testdata))
					self.parse(data)
				else:
					self.connected.clear()
					self.disconnected.set()
		logging.debug('Receive Exiting')
		self.running.release()
					
	def parse(self, packet):
		data = pickle.loads(packet)
		if data['id'] == 'preamble':
			logging.debug('receive preamble aquiribng lock')
			self.socklock.acquire()
			logging.debug('got lock sending response')
			self.socket.send(pickle.dumps({'id':'accept'}))
			logging.debug('response sent')
		if data['id'] == 'accept':
			logging.debug('got accept seting response event')
			self.response.set()
		if data['id'] == 'eol':
			logging.debug('eol received releasing lock')
			self.socklock.release()
		if data['id'] == 'update':
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
			self.stack.put('handle.command')
		if data['id'] == 'test':
			logging.debug('got test packet')
			self.stack.put(data['item'])
	
	def setsocket(self, sock):
		self.socket = sock

class Server(threading.Thread):
	def __init__(self, inq, outq, closed):
		self.host = ''
		self.port = 50007
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
		
		self.exit = False
		threading.Thread.__init__(self)
	
	def setup(self):
		logging.debug('Startup Initiated')
		self.send = Send(self.response, self.socklock, self.inq, self.connected, self.running)
		self.receive = Receive(self.response, self.socklock, self.outq, self.connected, self.disconnected, self.running)
		self.keepalive = KeepAlive(self.socklock, self.connected, self.inq, self.running)
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
		print 'exiting'
		self.send.exit = True
		self.receive.exit = True
		self.keepalive.exit = True
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
	def __init__(self, inq, outq, closed):
		self.host = '127.0.0.1'
		self.port = 50007
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
		self.receive = Receive(self.response, self.socklock, self.outq, self.connected, self.disconnected, self.running)
		self.send.setsocket(self.socket)
		self.receive.setsocket(self.socket)
		self.keepalive = KeepAlive(self.socklock, self.connected, self.inq, self.running)
		self.send.start()
		self.receive.start()
		self.keepalive.start()
		logging.debug('Setup Finished')
		
	def shutdown(self):
		logging.debug('Sutting Down')
		self.send.exit = True
		self.receive.exit = True
		self.keepalive.exit = True
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
	def __init__(self, socklock, connected, inq, running):
		self.socklock = socklock
		self.connected = connected
		self.exit = False
		self.packet = pickle.dumps({'id':'keepalive'})
		self.running = running
		self.inq = inq
		threading.Thread.__init__(self)
	def run(self):
		self.running.acquire()
		logging.debug('aquired semaphore kepalive')
		while not self.exit:	
			self.connected.wait(5)
			if self.connected.isSet():
				self.inq.put(self.packet)
		logging.debug('Keepalive exiting')
		self.running.release()
			
			
			
			
			
		
					
		
	
	
		
	