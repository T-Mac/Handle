import socket
import pickle
import threading
import Queue
import select
import ctypes
import os

_PACKETQ = Queue.Queue(maxsize=0)
global _CONNECTED
global _MODE
global _DISCONNECT
_DISCONNECT = threading.Event()
_CONNECTED = False
_NETLOCK = threading.Lock()
_NETREADY = threading.Event()
class network:
	
	def __init__(self, queue):
		packets = {}
		packets[0x00] = ''
		packets[0x01] = 'item'
		packets[0x02] = 'command'
		packets[0x03] = 'item'
		packets[0x03a] = 'jobs'
		packets[0x03b] = 'screen'
		packets[0x03c] = 'version'
		packets[0x03d] = 'line,updatable'
		self.lockp = 'lock requested'
		self.releasep = 'lock released'
		self.acknow = 'lock achknowledged'
		self.packets = packets
		self.queue = queue
		self.locking = False
		self.locked = threading.Event()
	
	def check(self, packet):
		items = self.packets[packet['id']].split(',')
		if packet['id'] != 0x00:
			for item in items:
				if not item in packet:
					raise KeyError('Malformed packet! obj -' + str(item) + "- doesn't exist")
		if packet['id'] == 0x03:
			numlet = {1:0x03a, 2:0x03b, 3:0x03c, 4:0x03d}
			items = self.packets[numlet[int(packet['item'])]].split(',')
			for item in items:
				if not item in packet:
					raise KeyError('Malformed packet! obj -' + str(item) + "- doesn't exist")
		return packet
	
	def pack(self, data):
		self.check(data)
		packet = pickle.dumps(data)
		#packet = data
		if _CONNECTED == True:
			_PACKETQ.put_nowait(packet)
			
	def unpack(self, data):
		packet = pickle.loads(data)
		#packet = data
		self.check(packet)
		self.queue.put_nowait(packet)
	#def acquire(self):
	#	_NETLOCK.acquire()
	#	x = False
	#	while not x:
	#	self.queue.put_nowait(self.lockp)
	#	x = self.locked.wait(5)
	#	if x == True or x == None:
	#		x 
	
	#def release(self):
	
	#def lock(self, packet):
	#	if packet == self.lockp and self.locking == False:
	#		_NETLOCK.acquire()
			
	
class send(threading.Thread):
	def __init__(self, sock):
		self.sock = sock
		self.queue = _PACKETQ
		self.ping = pickle.dumps({'id':0x00})
		if _MODE == 'client':
			self.timeout = 30
		else:
			self.timeout = None

		threading.Thread.__init__ ( self )

	def run(self):
		while _CONNECTED:
			try:
				packet = self.queue.get(True,self.timeout)
			except Queue.Empty:
				if _MODE == 'client':
					self.queue.put(self.ping)
			else:
				#print 'sending'
				#print 'Connected: ' + str(_CONNECTED)
				_NETLOCK.acquire()
				self.sock.send('isready')
				#print 'asking if ready'
				_NETLOCK.release()
				_NETREADY.wait()
				_NETREADY.clear()
				_NETLOCK.acquire()
				#print 'event set'
				self.sock.send(packet)
				_NETLOCK.release()
	def ready(self):
		self.sock.send('ready')
			
class recv(threading.Thread):
	def __init__(self, network, sock):
		self.lockp = 'lock requested'
		self.releasep = 'lock released'
		self.acknow = 'lock achknowledged'
		self.sock = sock
		self.network = network
		self.timeout = 60
		global _CONNECTED
		threading.Thread.__init__ ( self )
		
	def run(self):
		while _CONNECTED == True:
			#print 'waiting for packets'
			x = select.select((self.sock,),(),(),self.timeout)
			if len(x[0]) == 0:
				if _MODE == 'server':
					#print 'timed out'
					_DISCONNECT.set()
					global _CONNECTED
					_CONNECTED = False
			else:
				#print 'recieving'
				_NETLOCK.acquire()
				data = self.sock.recv(4096)
				if data == 'isready':
					self.sock.send('ready')
					#print 'Ready to Receive'
					data = self.sock.recv(4096)
					self.network.unpack(data)
				elif data == 'ready':
					#print 'setting flag'
					_NETREADY.set()

				_NETLOCK.release()
				
class comm(threading.Thread):
	def __init__(self, queue, mode):
		global _MODE
		_MODE = mode
		self.network = network(queue)
		self.pack = self.network.pack
		self.mode = mode
		self.PORT = 50007              # Arbitrary non-privileged port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if mode == 'server':
			self.HOST = ''                 # Symbolic name meaning all available interfaces
		elif mode == 'client':
			self.HOST = '127.0.0.1'			
		
		threading.Thread.__init__ ( self )

	def run(self):

		global _CONNECTED
		
		if self.mode == 'server':
			self.sock.bind((self.HOST, self.PORT))
			while True:
				#print 'Waiting for clients'
				self.sock.listen(1)
				conn, addr = self.sock.accept()
				#print 'Connected'

				_CONNECTED = True
				send(conn).start()
				self.recv = recv(self.network, conn)
				self.recv.start()
				_DISCONNECT.wait()
				#print 'Disconnected'
		elif self.mode == 'client':
			#print 'Connecting'
			self.sock.connect((self.HOST, self.PORT))
			#print 'Connected'
			_CONNECTED = True
			self.recv = recv(self.network, self.sock)
			send(self.sock).start()
			self.recv.start()
			_DISCONNECT.wait()
			#self.recv.block()
		
		
