import threading
import Queue
import logging
import MinecraftApi
from task import Task
from urllib2 import URLError
import select

class Api(threading.Thread):
	def __init__(self, reply_q, cmd_q = Queue.Queue(maxsize = 0)):
		self.reply_q = reply_q
		self.cmd_q = cmd_q
		self.apiobjs = []
		self.streamobjs = []
		self.api = None
		self.log = logging.getLogger('API')
		self.alive = threading.Event()
		self.alive.set()
		self.connected = threading.Event()
		
		self.handlers = {
			ApiCmd.REGISTER:self.__register,
			ApiCmd.REMOVE:self.__remove,
			ApiCmd.GET:self.__get_data,
			ApiCmd.UPDATE:self.__update_data,
			ApiCmd.CONNECT:self.__connect,
			ApiCmd.SETUP:self.__setup,
			ApiCmd.DISCONNECT:self.__disconnect,
			ApiCmd.RECONNECT:self.__reconnect,
			ApiCmd.STREAM:self.__stream,
			}
		
		threading.Thread.__init__(self)
	def run(self):
		while self.alive.isSet():
			try:
				cmd = self.cmd_q.get(True, 0.1)
				self.log.debug('Got Task: %s' % cmd.stype[cmd.type])
				self.handlers[cmd.type](cmd)
				
			except Queue.Empty:
				pass
		
	def __register(self, cmd):
		self.apiobjs.append(cmd.data)
		tskreg = Task(Task.API_UPDATE, cmd.data)
		tsk = Task(Task.SCH_ADD, (tskreg, cmd.data.delay, cmd.data.repeat))
		self.reply_q.put(tsk)
		self.cmd_q.put(ApiCmd(ApiCmd.UPDATE, cmd.data))
		self.log.debug('Registered Method: %s - Delay: %s' % (cmd.data.method, str(cmd.data.delay)) )

	def __remove(self, cmd):
		self.apiobjs.remove(cmd.data)
		self.log.debug('Removed Method: %s' % cmd.data.method)
		
	def __get_data(self, cmd):
		if self.connected.isSet():
			self.api.getMethod(cmd.data.method)
		
	def __update_data(self, cmd):
		if self.connected.isSet():
			#method = self.api.getMethod(cmd.data.method)
			#if not method == None:
			try:
				data = self.api.call(cmd.data.method)
				cmd.data.data = data
				#self.reply_q.put(Task(Task.NET_LINEUP, str(data)))
				self.reply_q.put(Task(Task.CLT_UPDATE, (cmd.data.name, cmd.data.data)))
				self.log.debug('Updated: %s - %s' % (cmd.data.name, str(data)))
			except Exception:
				self.log.debug('Error calling %s'%cmd.data.method)
				self.cmd_q.put(ApiCmd(ApiCmd.UPDATE, cmd.data))
			#else:
			#	self.log.debug('getMethod returned None')
	
	def __connect(self, cmd):
		#self.log.debug('MinecraftApi.MinecraftJsonApi(host = %s, port = %s, username = %s, password = %s, salt = %s)'%cmd.data)
		try:
			self.api = MinecraftApi.MinecraftJsonApi(host = cmd.data[0], port = int(cmd.data[1]), username = cmd.data[2], password = cmd.data[3], salt = cmd.data[4])
			self.connected.set()
			self.log.debug('Api Connected to Server')
			self.cmd_q.put(ApiCmd(ApiCmd.SETUP))
		except URLError:
			tsk = Task(Task.API_CONNECT)
			self.reply_q.put(Task(Task.SCH_ADD, (tsk, 5)))
			self.log.debug('Api Connection Failed: Rescheduled')
			
	def __disconnect(self, cmd):
		self.connected.clear()
		self.log.debug('Api Disconnected from server')
		self.reply_q.put(Task(Task.SCH_REMOVE, Task.API_UPDATE))
		
	def __setup(self, cmd):
		self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('getServerVersion', 600, 'bukkitv')))
		self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('getPlayerLimit', 600, 'plimit')))
		#self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('getPlayerCount', 10, 'pcount')))
		self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('getBukkitVersion', 600, 'serverv')))
		self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('system.getDiskSize', 0, 'maxdsk')))
		self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('system.getDiskUsage', 600, 'useddsk')))
		self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('system.getJavaMemoryTotal', 600, 'maxmem')))
		self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('system.getJavaMemoryUsage', 30, 'usemem')))
		self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('getServerPort', 600, 'port')))
		self.cmd_q.put(ApiCmd(ApiCmd.REGISTER, ApiObj('getPlugins', 10, 'plugins')))
		self.cmd_q.put(ApiCmd(ApiCmd.STREAM, 'connections'))
		
	def __reconnect(self, cmd):
		self.log.debug('Got Reconnect Command')
		for item in self.apiobjs:
			self.cmd_q.put(ApiCmd(ApiCmd.UPDATE,item))
			self.log.debug('Add Update for %s'%item.method)
	
	def __stream(self, cmd):
		self.log.debug('Creating Stream API Connection for %s'%cmd.data)
		obj = StreamObj(cmd.data, self.alive, self.reply_q, self.api)
		obj.connect()
		obj.start()
		
	def join(self):
		self.alive.clear()
		threading.Thread.join(self)
		
		
class ApiObj(object):
	def __init__(self, method, delay, name= None):
		self.method = method
		self.delay = delay
		if not delay == 0:
			self.repeat = True
		else:
			self.repeat = False
		self.data = None	
		self.name = name
		
class StreamObj(threading.Thread):
	def __init__(self, type, alive, reply_q, api):
		self.type = type
		self.alive = alive
		self.reply_q = reply_q
		self.stream = None
		self.log = logging.getLogger('Stream API: %s'%self.type)
		self.api = api
		threading.Thread.__init__(self)
		
	def run(self):
		while self.alive.isSet():
			x = select.select((self.stream,),(),(), 0.1)
			if not len(x[0]) == 0:
				packet = self.stream.readjson()
				self.log.debug('Got Packet')
				if self.type == 'connections':
					self.reply_q.put(Task(Task.CLT_UPDATE,('players',{'name':packet['success']['player'], 'action':packet['success']['action'], 'time':packet['success']['time']})))
	def connect(self):
		
		self.stream = self.api.subscribe(self.type)
		if self.stream:
			return True
		else:
			return False

	
class ApiCmd(object):
	
	'''
		REGISTER	ApiObj
		REMOVE		ApiObj
		GET			ApiObj
		UPDATE		ApiObj
		CONNECT		None
		SETUP		None
		DISCONNECT	None
		RECONNECT	None
		STREAM		type
	'''
	
	REGISTER, REMOVE, GET, UPDATE, CONNECT, SETUP, DISCONNECT, RECONNECT, STREAM = range(9)
	
	stype = {
		0:'REGISTER',
		1:'REMOVE',
		2:'GET',
		3:'UPDATE',
		4:'CONNECT',
		5:'SETUP',
		6:'DISCONNECT',
		7:'RECONNECT',
		8:'STREAM',
		}
	
	def __init__(self, type, data = None):
		self.type = type
		self.data = data
		self.types = self.stype[type]