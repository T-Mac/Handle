import threading
import Queue
import lib.server as server
import lib.gui as gui
import lib.network3 as network
import lib.schedule as schedule
import logging
from lib.task import Task
from lib.network3 import NetworkCommand
from lib.network3 import Packet
from lib.schedule import SchedCommand, Event
import time
import os.path
import os
import lib.daemon
import lib.apiconnect as api
from lib.apiconnect import ApiCmd, ApiObj

LOGLVL = logging.INFO	#<----------------------------------------- LOGGING LEVEL------------------------------------

class NotImplemented(Exception):
	pass

class Handle(threading.Thread):
	def __init__(self):
		#config logger
		self.loglvl = LOGLVL	
		if not self.loglvl == logging.DEBUG:
			self.logfile = 'handle.log'
		else:
			self.logfile = 'server.log'
		logging.basicConfig(level=self.loglvl, filename=self.logfile, format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.log = logging.getLogger('HANDLE')
		
		#create task q
		self.tasks = Queue.Queue(maxsize=0)
		

		#create database
		self.database = server.Database(self.tasks)
		self.database.loadconfig()
		self.database.create_default_events()
		
		#create sever controller
		self.server = server.Bukkit(self.database, self) 
		
		#create networking
		self.network = network.Network(self.tasks)
		
		#create schedule
		self.schedule = schedule.Schedule(self.tasks)

		#create api connection
		self.api = api.Api(self.tasks)
		
		#create backup
		self.backup = server.Backup(self.tasks)
		
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
					Task.NET_UPPKG:self.__net_uppkg,
					Task.SRV_START:self.__srv_start,
					Task.SRV_STOP:self.__srv_stop,
					Task.SRV_RESTART:self.__srv_restart,
					Task.SRV_INPUT:self.__srv_input,
					Task.CLT_UPDATE:self.__clt_update,
					Task.SCH_ADD:self.__sch_add,
					Task.SCH_REMOVE:self.__sch_remove,
					Task.SCH_UPDATE:self.__sch_update,
					Task.API_REGISTER:self.__api_register,
					Task.API_REMOVE:self.__api_remove,
					Task.API_GET:self.__api_get,
					Task.API_UPDATE:self.__api_update,
					Task.API_CONNECT:self.__api_connect,
					Task.ON_CONNECT:self.__on_connect,
					Task.SRV_BACKUP:self.__srv_backup,
					}
		#set alive flag
		self.alive = threading.Event()
		self.alive.set()
		

		self.pid = os.getpid()
		open("handle.pid", "w").write(str(self.pid))
		threading.Thread.__init__( self )
		
	def run(self):
		self.network.start()
		self.schedule.start()
		self.api.start()
		self.backup.start()
		while self.alive.isSet():
			try:
				task = self.tasks.get(True, 0.1)
				self.log.debug('Got Task: ' + task.stype[task.type])
				self.handlers[task.type](task)
			except Queue.Empty:
				pass
			except KeyError:
				self.log.error('UKNOWN TASK: %s - %s'%(task.type, task.stype[task.type]))
	
	def addtask(self, task):
		self.tasks.put(task)
		
	def __hdl_command(self, task):
		self.interpret(task.data)
		
	def __hdl_exit(self, task):
		if self.server.running:
			self.api.join()
			pack = Packet(Packet.LINEUP,'[HANDLE] Api Connection Closed')
			self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
			self.server.stopserver()
			time.sleep(1)
			pack = Packet(Packet.LINEUP,'[HANDLE] Server Closed')
			self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
		self.log.debug('Sent closed message')
		time.sleep(1)
		self.schedule.join()
		pack = Packet(Packet.LINEUP,'[HANDLE] Schedule Stopped')
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
		self.backup.join()
		pack = Packet(Packet.LINEUP,'[HANDLE] Backup Stopped')
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
		time.sleep(1)
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.EXIT, ('127.0.0.1',int(self.database.config['Handle']['port']) )))
		self.log.debug('Closed Networking')
		time.sleep(1)
		self.log.debug('Calling Network.join()')
		self.network.join()
		self.log.debug('Network COMPLETELY closed')
		self.log.info('Handle Closed')
		os.remove('handle.pid')
		self.alive.clear()
		
	def __hdl_update(self, task):
		raise NotImplemented()
		
	def __hdl_checkup(self, task):
		raise NotImplemented()
		
	def __net_job(self, task):
		raise NotImplemented()
		
	def __net_screen(self, task):
		ups = []
		ups.append(('screen',self.database.data['screen']))
		pack = Packet(Packet.UPDATE, ups)
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND, pack))
		self.log.debug('[H] Update Added to Q')
		
	def __net_version(self, task):
		raise NotImplemented()
		
	def __net_lineup(self, task):
		if self.database.data['screen'] == None:
			self.database.data['screen'] = []
		if len(self.database.data['screen']) == 100:
			self.database.data['screen'].pop(0)
		encodeds = task.data.encode('hex_codec')
		self.database.data['screen'].append(encodeds)
		pack = Packet(Packet.LINEUP,task.data)
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
		self.log.debug(':[H]Packet added to Q')		
	
	def __net_uppkg(self, task):
		raise NotImplemented()
	
	def __srv_start(self, task):
		if not self.server.running:
			self.log.info('Starting Server')
			self.tasks.put(Task(Task.NET_LINEUP, '[HANDLE] Starting Server...'))
			self.server.startserver()
			self.tasks.put(Task(Task.SCH_ADD, (Task(Task.API_CONNECT), 1) ))
		else:	
			self.tasks.put(Task(Task.NET_LINEUP, '[HANDLE] The server is already running'))

		
	def __srv_stop(self, task):
		if self.server.running:
			self.log.info('Stopping Server')
			self.api.cmd_q.put(ApiCmd(ApiCmd.DISCONNECT))
			self.server.stopserver()
		else:
			self.tasks.put(Task(Task.NET_LINEUP, '[HANDLE] The server is already stopped'))
		
	def __srv_restart(self, task):
		if self.server.running:
			self.log.info('Restarting Server')
			self.api.cmd_q.put(ApiCmd(ApiCmd.DISCONNECT))
			self.server.stopserver()
			self.tasks.put(Task(Task.SCH_ADD, (Task(Task.SRV_START), 10) ))
			self.tasks.put(Task(Task.NET_LINEUP, '[HANDLE] Server Stopped - Waiting 10 secs.....'))
		else:	
			self.tasks.put(Task(Task.NET_LINEUP, "[HANDLE] The server isn't running"))
		
	def __srv_input(self, task):
		self.server.input(task.data)	
		
	def __srv_backup(self, task):
		task.data = self.database.config
		self.backup.cmd_q.put(task)
		self.log.debug('[H] Added Backup to Q')
		self.log.info('Backup Started')
		
	def __clt_update(self, task):
		pack = Packet(Packet.UPDATE,[task.data])
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
		self.log.debug('[H] Sent Update: %s - %s'% (task.data[0][0], str(task.data[0][1])))
		
	def __sch_add(self, task):
		self.schedule.cmd_q.put(SchedCommand(SchedCommand.ADD, task.data))
		self.log.debug('[H] Task addded to Schedule Q')
	
	def __sch_remove(self, task):
		self.schedule.cmd_q.put(SchedCommand(SchedCommand.REMOVE, task.data))
		
	def __sch_update(self, task):
		self.schedule.cmd_q.put(SchedCommand(SchedCommand.UPDATE))
		
	def __api_register(self, task):
		self.api.cmd_q.put(ApiCmd(ApiCmd.REGISTER, task.data))
		self.log.debug('[H] Api Register:  %s Added  to Q' % task.data.method)
		
	def __api_remove(self, task):
		self.api.cmd_q.put(ApiCmd(ApiCmd.REMOVE, task.data))
		self.log.debug('[H]	Api Remove: %s Added to Q' % task.data.method)
		
	def __api_get(self,task):
		self.api.cmd_q.put(ApiCmd(ApiCmd.Get, task.data))
		self.log.debug('[H]	Api Get: %s Added to Q' % task.data.method)
		
	def __api_update(self, task):
		self.api.cmd_q.put(ApiCmd(ApiCmd.UPDATE, task.data))
		self.log.debug('[H]	Api Update: %s Added to Q' % task.data.method)		
	
	def __api_connect(self, task):
		dict = self.database.config['JSON_API']
		params = (dict['host'], dict['port'], dict['user'], dict['pass'], dict['salt'])
		self.api.cmd_q.put(ApiCmd(ApiCmd.CONNECT, params))
		self.log.debug('[H] Api Connect Added to Q')
		
	def __on_connect(self, task):
		self.log.debug('ON_CONNECT RECEIVED')
		self.log.info('Client Connected')
		pack = Packet(Packet.UPDATE, [('handlev',self.database.config['Handle']['version'])])
		
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND, pack))
		if self.database.data['screen'] == None:
			self.database.data['screen'] = []
		if len(self.database.data['screen']) == 100:
			self.database.data['screen'].pop(0)
			
		s = '[HANDLE] Connected to Handle ver. %s' % self.database.config['Handle']['version']
		encodeds = s.encode('hex_codec')
		if not self.database.data['screen'][len(self.database.data['screen'])-1] == encodeds:
			self.database.data['screen'].append(encodeds)
		pack = Packet(Packet.UPDATE,[('screen',self.database.data['screen'])])
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))

		pack = Packet(Packet.UPDATE,[('events',self.schedule.visible_events)])
		self.network.cmd_q.put(NetworkCommand(NetworkCommand.SEND,pack))
		self.tasks.put(Task(Task.SCH_ADD,(Task(Task.SCH_UPDATE), 30, True)))
		self.api.cmd_q.put(ApiCmd(ApiCmd.RECONNECT))
		
	def interpret(self, command):
		if command == 'start':
			self.tasks.put(Task(Task.SRV_START))
		elif command == 'stop':
			self.tasks.put(Task(Task.SRV_STOP))
		elif command == 'restart':
			self.tasks.put(Task(Task.SRV_RESTART))
		elif command == 'exit':
			self.tasks.put(Task(Task.HDL_EXIT))
		elif command == 'help':
			self.tasks.put(Task(Task.NET_LINEUP,'===============================Handle Commands==============================='))
			self.tasks.put(Task(Task.NET_LINEUP,'[HANDLE] start                                               start the server'))
			self.tasks.put(Task(Task.NET_LINEUP,'[HANDLE] stop                                                 stop the server'))
			self.tasks.put(Task(Task.NET_LINEUP,'[HANDLE] restart                                           restart the server'))
			self.tasks.put(Task(Task.NET_LINEUP,'[HANDLE] exit                                stop the server and close Handle'))
			self.tasks.put(Task(Task.NET_LINEUP,'[HANDLE] close                      close the client but leave Handle running'))
			self.tasks.put(Task(Task.NET_LINEUP,'[HANDLE] Use the Left/Right Keys to change sidebar tabs'))
			self.tasks.put(Task(Task.SRV_INPUT, 'help'))
			
		elif command == 'serve_welcome_packet':
			self.tasks.put(Task(Task.NET_LINEUP,'Connected to Handle ver. %s' %self.database.config['Handle']['version']))
		elif command[:10] == 'test_event':
			self.tasks.put(Task(Task.SCH_ADD, (Task(Task.NET_LINEUP, '%s' % command[11:]), 5)))
			self.tasks.put(Task(Task.NET_LINEUP, 'added test task'))
			
		elif command[:11] == 'test_method':
			ao = ApiObj(command[12:], 30)
			self.tasks.put(Task(Task.API_REGISTER, ao))
			self.tasks.put(Task(Task.API_UPDATE, ao))
			self.tasks.put(Task(Task.NET_LINEUP, 'added test method'))
			
		elif command == 'backup':
			self.tasks.put(Task(Task.SRV_BACKUP))
			
		else:
			self.tasks.put(Task(Task.SRV_INPUT, command))
	

				
				
class Client(object):
	def __init__(self):
		#threading.Thread.__init__(self)
		#create task q
		self.tasks = Queue.Queue(maxsize=0)
		print str(self)
		#create database
		self.database = server.Database(self.tasks)
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
				Task.CLT_CLOSE:self.__clt_close,
				Task.NET_SCREEN:self.__clt_updates,
				}
		
		#define alive flag
		self.alive = threading.Event()
		self.alive.set()
		self.loglvl = LOGLVL		#<---------------------------- LOGGING LEVEL
		#setup logging
		if not self.loglvl == logging.DEBUG:
			self.logfile = 'handle.log'
		else:
			self.logfile = 'client.log'
		logging.basicConfig(level=LOGLVL, filename=self.logfile, format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
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
		
		return None
	def addtask(self, task):
		self.tasks.put(task)
		
	def __clt_updates(self, task):
		self.gui.update(task.data)
			
		
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
		return None

	
	def __clt_close(self, task):
		self.log.debug('Disconnecting......')
		self.log.info('Client Closing')
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
		client.run()
	else:
		lib.daemon.createDaemon()
		srv= Handle()
		srv.start()