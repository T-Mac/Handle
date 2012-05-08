import Queue
import socket
import select
import threading
import pickle
import logging
import os
from task import Task
import inspect
import time

class Network(threading.Thread):
	def __init__(self, reply_q, cmd_q = Queue.Queue(maxsize=0)):
		self.cmd_q = cmd_q
		self.reply_q = reply_q
		self.alive = threading.Event()
		self.alive.set()
		self.loglvl = logging.DEBUG # <------- Logging Level
		self.IO_cmd_q = Queue.Queue(maxsize=0)
		self.IO = IO(self.IO_cmd_q, self.cmd_q)
		self.Parse = Parse(cmd_q, reply_q)
		self.handlers = {
					NetworkCommand.CONNECT: self.__handle_connect,
					NetworkCommand.SERVE: self.__handle_serve,
					NetworkCommand.STOP: self.__handle_stop,
					NetworkCommand.SEND: self.__handle_send,
					NetworkCommand.RECEIVE: self.__handle_receive,
					NetworkCommand.DISCONN: self.__handle_disconn,
					NetworkCommand.CLOSED: self.__handle_closed,
					NetworkCommand.EXIT: self.__handle_exit,
					NetworkCommand.TASK: self.__handle_task
					
				}
		self.log = logging.getLogger('NETWORK')
		self.ready_to_exit = threading.Event()
		threading.Thread.__init__( self )
		
	def run(self):
		self.IO.start()
		while self.alive.isSet():
			try:
				cmd = self.cmd_q.get(True, 0.1)
				if cmd.type == 3 or cmd.type == 4:
					part = cmd.data.stype[cmd.data.type] + ' : ' + str(cmd.data.data)
				else:
					part = cmd.data
				self.log.debug('Got Command! ' + str(cmd.stype[cmd.type]) + ' : ' + str(part))
				self.handlers[cmd.type](cmd)
			except Queue.Empty as e:
				continue
	def __handle_connect(self, cmd):
		self.IO_cmd_q.put(cmd)
		
	def __handle_serve(self, cmd):	
		self.IO_cmd_q.put(cmd)
	
	def __handle_stop(self, cmd):
		self.log.debug('STOPPING.......')
		self.IO.join()
		self.log.debug('DONE!!')
		self.ready_to_exit.set()
		
	def __handle_send(self, cmd):
		if self.IO.connected.isSet():
			self.IO_cmd_q.put(cmd)
					
	def __handle_receive(self, cmd):
		self.Parse.parse(cmd.data)
	
	def __handle_disconn(self, cmd):
		self.log.debug('GOT DISCONNECT COMMAND')
		self.IO_cmd_q.put(cmd)
		
	def __handle_closed(self, cmd):
		self.IO_cmd_q.put(cmd)
		
	def __handle_exit(self, cmd):
		if self.IO.listening.isSet():
			client = DummyClient(cmd.data[0],int(cmd.data[1]))
			client.connect()
			self.IO_cmd_q.put(NetworkCommand(NetworkCommand.DISCONN,False))
		else:
			self.IO._IO__handle_disconn(NetworkCommand(NetworkCommand.DISCONN,False))
		self.IO.join()
		self.log.debug('IO join completed')
		self.ready_to_exit.set()
		self.log.debug('Ready Flag set')
	
	def __handle_task(self,cmd):
		self.reply_q.put(cmd.data)
		
	def join(self):
		self.ready_to_exit.wait()
		self.alive.clear()
		threading.Thread.join(self)
	
	
		
	
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
		self.ready_to_exit = threading.Event()
		self.fault_count = 0
		self.sock = None
		threading.Thread.__init__( self )
		
	def run(self):
		self.log.debug('loop started')
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
		self.fault_count = 0

		
		
	def __handle_serve(self, cmd):
		self.log.debug('SERVING......')
		self.host, self.port = cmd.data
		if self.sock == None:
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
		self.fault_count = 0
		self.reply_q.put(NetworkCommand(NetworkCommand.TASK,Task(Task.ON_CONNECT)))

		
	def __handle_send(self, cmd):
		self.log.debug('Sending.....')
		if self.connected.isSet():
			packet = pickle.dumps(cmd.data.dconstruct(),pickle.HIGHEST_PROTOCOL)
			packetencode = packet.encode('hex_codec')
			if self.conn:
				self.conn.send(packetencode + '\n')
			else:
				self.sock.send(packetencode + '\n')
		self.log.debug('Sent!')
		
	def __reply_receive(self, data):
		try:
			packetdecode = data[:-1].decode('hex_codec')
		except TypeError as e:
			self.log.error('packet dump: %s' % data)

		try:
			raw = pickle.loads(packetdecode)
		except EOFError as e:
			self.log.error('EOFError')
			self.log.error('Pickled string dump: %s' % data)
			self.fault_count = self.fault_count + 1
			if self.fault_count > 25:
				self.connected.clear()
				if self.conn:
					self.conn.shutdown(socket.SHUT_RDWR)
					self.conn.close()
					self.cmd_q.put(NetworkCommand(NetworkCommand.DISCONN,True))
				
		else:
			self.fault_count = 0
			packet = Packet(raw['type'], raw['data'])
			self.reply_q.put(NetworkCommand(NetworkCommand.RECEIVE, packet))
			
		
	def join(self, timeout = None):
		self.log.debug('THIS IS JOIN METHOD BEING CALLED')
		#self.log.debug('caller name:' +  str(inspect.stack()[1][3]))
		self.ready_to_exit.wait()
		self.log.debug('ready flag set')
		self.alive.clear()
		threading.Thread.join(self, timeout)
		self.log.debug('DONE')
		return None
	
	def __handle_disconn(self, cmd):
		if self.conn:
			self.log.debug('Disconnected')
			if not self.fault_count > 25:
				packetraw = Packet(Packet.CLOSED)
				packet = pickle.dumps(packetraw.dconstruct(),pickle.HIGHEST_PROTOCOL)
				packetencode = packet.encode('hex_codec')
				self.conn.send( packetencode + '\n')
				self.log.debug('Sent Closed Packet MANUALY')
				time.sleep(1)
			self.connected.clear()
			if not self.fault_count > 25:
				self.conn.shutdown(socket.SHUT_RDWR)
				self.conn.close()
			
			if cmd.data:
				self.cmd_q.put(NetworkCommand(NetworkCommand.SERVE,(self.host, int(self.port))))
			else:
				self.sock.close()
				self.ready_to_exit.set()
		else:
			self.cmd_q.put(NetworkCommand(NetworkCommand.SEND,Packet(Packet.DISCONN,True)))
			#self.connected.clear()

			
	def __handle_closed(self, cmd):	
		self.log.debug('Closed recieved')
		self.connected.clear()
		self.sock.close()
		self.ready_to_exit.set()
		self.log.debug('Disconnected')
		self.reply_q.put(NetworkCommand(NetworkCommand.TASK,Task(Task.CLT_EXIT)))
	
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
		self.reply_q.put(Task(Task.NET_SCREEN, cmd.data))
		
	def __handle_input(self, cmd):
		self.reply_q.put(Task(Task.HDL_COMMAND, cmd.data))
	
	def __handle_test(self, cmd):
		print cmd.data
	
	def __handle_disconn(self, cmd):
		logging.debug('DISCONNECT AT PARSER')
		self.cmd_q.put(NetworkCommand(NetworkCommand.DISCONN,cmd.data))
		
	def __handle_closed(self, cmd):
		self.cmd_q.put(NetworkCommand(NetworkCommand.CLOSED))
		

		
class DummyClient(object):
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.log = logging.getLogger('DummyClient')
	def connect(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.log.debug('Connecting.....')
		self.sock.connect((self.host, self.port))
		self.log.debug('Connected')		
			
			
			
class NetworkCommand(object):	
	"""A command to the network controller.
	   Each command type has its associated data:
	   
	   CONNECT			(host, port) tuple
	   SERVE			(port)
	   STOP				None
	   SEND				(packet)
	   RECEIVE			(packet)
	   DISCONN			reconnect (t/f)
	   CLOSED
	   EXIT				(host, port) tuple
	   TASK				task for controller
	 """
	CONNECT, SERVE, STOP, SEND, RECEIVE, DISCONN, CLOSED, EXIT, TASK = range(9)
	stype = {
		0:'CONNECT',
		1:'SERVE',
		2:'STOP',
		3:'SEND',
		4:'RECEIVE',
		5:'DISCONN',
		6:'CLOSED',
		7:'EXIT',
		8:'TASK'
	}
		
	def __init__(self, type, data = None):
		self.type = type
		self.data = data
		
class Packet(object):
	"""
		LINEUP		(line)
		UPDATE		(dict)
		INPUT		(line)
		DISCONN		reconnect (t/f)
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


	
		
