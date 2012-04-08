import Queue
import socket
import select
import threading
import pickle
import logging
import os
from task import Task
import inspect

class Network(threading.Thread):
	def __init__(self, reply_q, cmd_q = Queue.Queue(maxsize=0)):
		self.cmd_q = cmd_q
		self.reply_q = reply_q
		self.alive = threading.Event()
		self.alive.set()
		self.loglvl = logging.DEBUG # <------- Logging Level
		self.IO_cmd_q = Queue.Queue(maxsize=0)
		self.IO = IO(self.IO_cmd_q, self.cmd_q)
		self.IO.start()
		self.Parse = Parse(cmd_q, reply_q)
		self.handlers = {
					NetworkCommand.CONNECT: self.__handle_connect,
					NetworkCommand.SERVE: self.__handle_serve,
					NetworkCommand.STOP: self.__handle_stop,
					NetworkCommand.SEND: self.__handle_send,
					NetworkCommand.RECEIVE: self.__handle_receive,
					NetworkCommand.DISCONN: self.__handle_disconn,
					NetworkCommand.CLOSED: self.__handle_closed
					
				}
						
		threading.Thread.__init__( self )
		
	def run(self):
		while self.alive.isSet():
			try:
				cmd = self.cmd_q.get(True, 0.1)
				if cmd.type == 3 or cmd.type == 4:
					part = cmd.data.stype[cmd.data.type] + ' : ' + str(cmd.data.data)
				else:
					part = cmd.data
				logging.debug('Got Command! ' + str(cmd.stype[cmd.type]) + ' : ' + str(part))
				self.handlers[cmd.type](cmd)
			except Queue.Empty as e:
				continue
	def __handle_connect(self, cmd):
		self.IO_cmd_q.put(cmd)
		
	def __handle_serve(self, cmd):	
		self.IO_cmd_q.put(cmd)
	
	def __handle_stop(self, cmd):
		logging.debug('STOPPING.......')
		if self.IO.listening.isSet():
			self.IO = None
			self.alive.clear()
		else:
			self.IO.join()
			self.alive.clear()
		logging.debug('DONE!!')
		
	def __handle_send(self, cmd):
		if self.IO.connected.isSet():
			self.IO_cmd_q.put(cmd)
					
	def __handle_receive(self, cmd):
		self.Parse.parse(cmd.data)
	
	def __handle_disconn(self, cmd):
		logging.debug('GOT DISCONNECT COMMAND')
		self.IO_cmd_q.put(cmd)
		
	def __handle_closed(self, cmd):
		self.IO_cmd_q.put(cmd)
		
		
	def setlogfile(self, path):
		logging.basicConfig(level=self.loglvl, filename=path, format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	
	
	
	
		
	
class IO(threading.Thread):
	def __init__(self, cmd_q, reply_q):
		self.cmd_q = cmd_q
		self.reply_q = reply_q
		self.alive = threading.Event()
		self.alive.set()
		self.log = logging.getLogger('IO')
		self.connected = threading.Event()
		self.listening = threading.Event()
		self.handlers = {
					NetworkCommand.CONNECT: self.__handle_connect,
					NetworkCommand.SERVE: self.__handle_serve,
					NetworkCommand.SEND: self.__handle_send,
					NetworkCommand.DISCONN: self.__handle_disconn,
					NetworkCommand.CLOSED: self.__handle_closed
				}
		self.conn = None
		threading.Thread.__init__( self )
		
	def run(self):
		while self.alive.isSet():
			try:
				cmd = self.cmd_q.get(True, 0.1)
				self.log.debug('Q Returned')
				self.handlers[cmd.type](cmd)
			except Queue.Empty as e:
				#self.log.debug('Q Returned Empty')
				pass
				
			if self.connected.isSet():
				#self.log.debug('checking packets')
				if self.conn:
					x = select.select((self.conn,),(),(), 0.1)
					#self.log.debug('SERVER returned')
				else:
					x = select.select((self.sock,),(),(), 0.1)
					#self.log.debug('CLIENT returned')
				if len(x[0]) != 0:
					self.log.debug('Got Packet')
					packet = x[0][0].makefile('rwb').readline()
					self.__reply_receive(packet)
					
	def __handle_connect(self, cmd):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.log.debug('Connecting.....')
		self.sock.connect(cmd.data)
		self.connected.set()
		self.log.debug('Connected')
		
	def __handle_serve(self, cmd):
		self.log.debug('SERVING......')
		self.host, self.port = cmd.data
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.log.debug(self.host + ' : ' + str(self.port))
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(cmd.data)
		self.log.debug('Listening......')
		self.listening.set()
		self.sock.listen(0)
		self.conn, addr = self.sock.accept()
		self.log.debug('Connected')
		self.connected.set()
		self.listening.clear()
		
	def __handle_send(self, cmd):
		self.log.debug('Sending.....')
		if self.connected.isSet():
			packet = pickle.dumps(cmd.data.dconstruct(),pickle.HIGHEST_PROTOCOL)
			if self.conn:
				self.conn.send(packet + '\n')
			else:
				self.sock.send(packet + '\n')
		self.log.debug('Sent!')
		
	def __reply_receive(self, data):
		try:
			raw = pickle.loads(data)
		except EOFError as e:
			self.log.error(str(e))
		else:
			packet = Packet(raw['type'], raw['data'])
			self.reply_q.put(NetworkCommand(NetworkCommand.RECEIVE, packet))
		
	def join(self, timeout = None):
		self.log.debug('THIS IS JOIN METHOD BEING CALLED')
		self.log.debug('caller name:' +  str(inspect.stack()[1][3]))
		#self.alive.clear()
		#threading.Thread.join(self, timeout)
	
	def __handle_disconn(self, cmd):
		if self.conn:
			self.log.debug('Disconnected')
			self.conn.send(pickle.dumps(Packet(Packet.CLOSED).dconstruct()) + '\n')
			self.conn.send('random ass shit')
			self.connected.clear()
			self.conn.shutdown(socket.SHUT_RDWR)
			self.conn.close()
			self.sock.close()
			self.cmd_q.put(NetworkCommand(NetworkCommand.SERVE,(self.host, int(self.port))))
		else:
			self.cmd_q.put(NetworkCommand(NetworkCommand.SEND,Packet(Packet.DISCONN)))
			self.connected.clear()

			
	def __handle_closed(self, cmd):	
		self.connected.clear()
		self.sock.close()
		self.log.debug('Disconnected')
	
class Parse(object):
	def __init__(self, cmd_q, reply_q):
		self.reply_q = reply_q
		self.cmd_q = cmd_q
		self.handlers = {
				Packet.LINEUP: self.__handle_lineup,
				Packet.UPDATE: self.__handle_update,
				Packet.INPUT: self.__handle_input,
				Packet.TEST: self.__handle_test,
				Packet.DISCONN: self.__handle_disconn,
				Packet.CLOSED: self.__handle_closed
			}
			
	def parse(self, cmd):
		self.handlers[cmd.type](cmd)
		
	def __handle_lineup(self, cmd):
		self.reply_q.put(Task(Task.CLT_LINEUP, cmd.data))
	
	def __handle_update(self, cmd):
		self.reply_q.put(Task(Task.CLT_UPDATE, cmd.data))
		
	def __handle_input(self, cmd):
		self.reply_q.put(Task(Task.HDL.COMMAND, cmd.data))
	
	def __handle_test(self, cmd):
		print cmd.data
	
	def __handle_disconn(self, cmd):
		logging.debug('DISCONNECT AT PARSER')
		self.cmd_q.put(NetworkCommand(NetworkCommand.DISCONN))
		
	def __handle_closed(self, cmd):
		self.cmd_q.put(NetworkCommand(NetworkCommand.CLOSED))

class NetworkCommand(object):	
	"""A command to the network controller.
	   Each command type has its associated data:
	   
	   CONNECT			(host, port) tuple
	   SERVE			(port)
	   STOP				None
	   SEND				(packet)
	   RECEIVE			(packet)
	   DISCONN
	   CLOSED
	 """
	CONNECT, SERVE, STOP, SEND, RECEIVE, DISCONN, CLOSED = range(7)
	stype = {
		0:'CONNECT',
		1:'SERVE',
		2:'STOP',
		3:'SEND',
		4:'RECEIVE',
		5:'DISCONN',
		6:'CLOSED'
	}
		
	def __init__(self, type, data = None):
		self.type = type
		self.data = data
		
class Packet(object):
	"""
		LINEUP		(line)
		UPDATE		(dict)
		INPUT		(line)
		DISCONN		None
		TEST		(line)
		CLOSED		None
	"""
	LINEUP, UPDATE, INPUT, DISCONN, TEST, CLOSED = range(6)
	stype = {
		0:'LINEUP',
		1:'UPDATE',
		2:'INPUT',
		3:'DISCONN',
		4:'TEST',
		5:'CLOSED'
	}
	def __init__(self, type, data = None):
		self.type = type
		self.data = data
	
	def dconstruct(self):
		return {'type':self.type, 'data':self.data}


	
		
