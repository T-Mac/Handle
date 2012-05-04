import threading
import Queue
import lib.server as server
import lib.gui as gui
import lib.network3 as network
import logging
from lib.task import Task
from lib.network3 import NetworkCommand
from lib.network3 import Packet
import time
import os.path
import os
import lib.daemon

class NotImplemented(Exception):
	pass

class Handle(threading.Thread):
	def __init__(self):
		#create task q
		self.tasks = Queue.Queue(maxsize=0)
		

		#create database
		self.database = server.Database()
		self.database.loadconfig()
		
		#create sever controller
		self.server = server.Bukkit(self.database, self)
		
		#create networking
		self.network = network.Network(self.tasks)
		#put startup tasks
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SERVE,('',int(self.database.config['Handle']['port']))))
		#define task handlers
		self.handlers = {
					Task.HDL_COMMAND:self.__hdl_command,
					Task.HDL_EXIT:self.__hdl_exit,
					Task.HDL_UPDATE:self.__hdl_update,
					Task.HDL_CHECKUP:self.__hdl_checkup,
					Task.NET_JOB:self.__net_job,
					Task.NET_SCREEN:self.__net_screen,
					Task.NET_VERSION:self.__net_version,
					Task.NET_LINEUP:self.__net_lineup,
					Task.SRV_START:self.__srv_start,
					Task.SRV_STOP:self.__srv_stop,
					Task.SRV_RESTART:self.__srv_restart,
					Task.SRV_INPUT:self.__srv_input,
					}
		#set alive flag
		self.alive = threading.Event()
		self.alive.set()
		
		#config logger
		self.loglvl = logging.DEBUG		#<-------- LOGGING LEVEL
		logging.basicConfig(level=self.loglvl, filename='server.log', format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.log = logging.getLogger('HANDLE')
		self.pid = os.getpid()
		open("handle.pid", "w").write(str(self.pid))
		threading.Thread.__init__( self )
		
	def run(self):
		self.network.start()
		while self.alive.isSet():
			try:
				task = self.tasks.get(True, 0.1)
				self.log.debug('Got Task: ' + task.stype[task.type])
				self.handlers[task.type](task)
			except Queue.Empty:
				pass
	
	def addtask(self, task):
		self.tasks.put(task)
		
	def __hdl_command(self, task):
		self.interpret(task.data)
		
	def __hdl_exit(self, task):
		if self.server.running:
			self.server.stopserver()
			time.sleep(1)
		pack = Packet(Packet.LINEUP,'[HANDLE] Server Closed')
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
		self.log.debug('Sent closed message')
		time.sleep(1)
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.EXIT, ('127.0.0.1',int(self.database.config['Handle']['port']) )))
		self.log.debug('Closed Networking')
		time.sleep(1)
		self.log.debug('Calling Network.join()')
		self.network.join()
		self.log.debug('Network COMPLETELY closed')
		os.remove('handle.pid')
		self.alive.clear()
		
	def __hdl_update(self, task):
		raise NotImplemented()
		
	def __hdl_checkup(self, task):
		raise NotImplemented()
		
	def __net_job(self, task):
		raise NotImplemented()
		
	def __net_screen(self, task):
		raise NotImplemented()
		
	def __net_version(self, task):
		raise NotImplemented()
		
	def __net_lineup(self, task):
		pack = Packet(Packet.LINEUP,task.data)
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
		self.log.debug(':[H]Packet added to Q')		
		
	def __srv_start(self, task):
		self.log.debug(':[H]Starting Server')
		self.server.startserver()
				
	def __srv_stop(self, task):
		self.log.debug(':[H]Stopping Server')
		self.server.stopserver()
		
	def __srv_restart(self, task):
		raise NotImplemented()
		
	def __srv_input(self, task):
		self.server.input(task.data)	
	
	def interpret(self, command):
		if command == 'start':
			self.tasks.put(Task(Task.SRV_START))
		elif command == 'stop':
			self.tasks.put(Task(Task.SRV_STOP))
		elif command == 'exit':
			self.tasks.put(Task(Task.HDL_EXIT))
	

				
				
class Client(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		#create task q
		self.tasks = Queue.Queue(maxsize=0)
		print str(self)
		#create database
		self.database = server.Database()
		self.database.loadconfig()
		
		#create networking
		self.network = network.Network(self.tasks)
		
		#put startup tasks
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.CONNECT,('127.0.0.1',int(self.database.config['Handle']['port']))))
		
		#create gui
		self.gui = gui.Gui(self)
		#define task handlers
		self.handlers = {
				Task.CLT_UPDATE:self.__clt_updates,
				Task.CLT_INPUT:self.__clt_input,
				Task.CLT_LINEUP:self.__clt_lineup,
				Task.CLT_EXIT:self.__clt_exit,
				Task.CLT_CLOSE:self.__clt_close
				}
		
		#define alive flag
		self.alive = threading.Event()
		self.alive.set()
		self.loglvl = logging.DEBUG
		#setup logging
		logging.basicConfig(level=self.loglvl, filename='client.log', format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.log = logging.getLogger('CLIENT')
		

		
	def run(self):
		self.network.start()
		self.gui.initscreen()
		while self.alive.isSet():
			try:
				task = self.tasks.get(True, 0.1)
				self.log.debug('Got Task: ' + task.stype[task.type])
				self.handlers[task.type](task)
			
			except Queue.Empty:
				pass
		
	
	def addtask(self, task):
		self.tasks.put(task)
		
	def __clt_updates(self, task):
		raise NotImplemented()
		
	def __clt_input(self, task):
		if task.data == 'close':
			self.tasks.put(Task(Task.CLT_CLOSE))
		else:
			pack = Packet(Packet.INPUT,task.data)
			self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
			self.log.debug(':[H]Sent Command: ' + task.data)
		
	def __clt_lineup(self, task):
		self.gui.addline(task.data)
		self.log.debug(':[H]Line Update: ' + task.data)
	
	def __clt_exit(self, task):
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.STOP))
		time.sleep(1)
		self.log.debug('Calling Network.join()')
		self.network.join()
		self.log.debug('Network COMPLETELY closed')
		self.gui.exit()
		self.alive.clear()
	
	def __clt_close(self, task):
		self.log.debug('Disconnecting......')
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.DISCONN))
		self.log.debug('Disconnected!	Stopping Network')	
		time.sleep(1)
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.STOP))
		self.log.debug('Calling Network.join()')
		self.network.join()
		self.log.debug('Network COMPLETELY closed')
		self.gui.exit()
		self.alive.clear()
		
if __name__ == "__main__":
	if os.path.exists('./handle.pid'):
		client = Client()
		client.start()
	else:
		lib.daemon.createDaemon()
		srv= Handle()
		srv.start()