import ConfigParser
import shlex
from select import select
import subprocess
import os
import threading
import logging
from task import Task
import Queue
import time
import shutil

class Bukkit:
	def __init__(self, database, handle=None):
		self.database = database
		if self.database.config['Handle']['path_to_bukkit'][-1:] != '/':
			path = self.database.config['Handle']['path_to_bukkit'] + '/craftbukkit.jar'
		else:
			path = self.database.config['Handle']['path_to_bukkit'] + 'craftbukkit.jar'
		startcmd = 'java -Xmx' + str(self.database.config['Handle']['start_heap']) + 'M -Xms' + str(self.database.config['Handle']['max_heap'])  + 'M -jar ' + str(path)
		self.startcmd = shlex.split(startcmd)
		self.pipe_read, self.pipe_write = os.pipe()
		self.handle = handle
		logging.basicConfig(level=logging.DEBUG, filename='server.log', format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.log = logging.getLogger('Bukkit')
		self.running = False
	def startserver(self):
		if not self.running:
			self.running = True
			if self.handle:
				self.serverout = ServerOut(self.handle)
			
			self.log.debug('ServerOut Started')
			os.chdir(self.database.config['Handle']['path_to_bukkit'])
			self.bukkit = subprocess.Popen(self.startcmd, shell=False, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
			os.chdir(self.database.config['Handle']['original_path'])
			if self.handle: 
				self.serverout.start()
		
	def stopserver(self):
		if self.running:
			self.running = False
			self.bukkit.stdin.write('stop\n')
			self.serverout.exit = True
			os.write(self.pipe_write, 'exit')
			if self.handle:
				self.handle.addtask(Task(Task.NET_LINEUP, '[HANDLE] Server Closed'))
			


	def output(self):
		x = select((self.bukkit.stdout, self.pipe_read,),(),())
		if x[0][0] == self.bukkit.stdout:
			return self.bukkit.stdout.readline()[11:-1]
		else:
			os.read(self.pipe_read, 1024)
			return 0x00
	
	def input(self,data):
		if self.running:
			self.bukkit.stdin.write(data + '\n')
		
class Database:
	def __init__(self, reply_q):
		self.data = {}
		self.data['screen'] = None
		self.reply_q = reply_q
		self.configfile = ConfigParser.RawConfigParser()
		
	def loadconfig(self):
		self.config = {}
		self.configfile.read('handle.cfg')
		sections = self.configfile.sections()
		for section in sections:
			options = self.configfile.options(section)
			internal = {}
			for option in options:
				internal[option] = self.configfile.get(section,option)
			self.config[section] = internal
		self.config['Handle']['original_path'] = os.getcwd()
		if self.config['Handle']['path_to_bukkit'][-1:] == '/':
			self.config['Handle']['path_to_bukkit'] = self.config['Handle']['path_to_bukkit'][:-1]
	
	def change(self,section,option,value):
		self.config[section][option] = value
		self.configfile.set(section,option,value)
		with open('handle.cfg', 'wb') as file:
			self.configfile.write(file)
		
	def create_default_events(self):	
		if self.config['Backup']['enabled'] == 'True':
			tsk = Task(Task.SRV_BACKUP)
			self.reply_q.put(Task(Task.SCH_ADD,(tsk, int(self.config['Backup']['interval'])*60, True, 'Auto_Backup')))
			curtime = time.time()
			runtime = curtime+int(self.config['Backup']['interval'])*60
			runtime = time.localtime(runtime)
			self.reply_q.put(Task(Task.NET_LINEUP,'[HANDLE] Server Backup at %s' % time.strftime('%H:%M:%S',runtime)))
		if self.config['Restart']['enabled'] == 'True':
			tsk = Task(Task.SRV_RESTART)
			self.reply_q.put(Task(Task.SCH_ADD,(tsk, int(self.config['Restart']['interval'])*60, True, 'Auto_Restart')))
			Restart_Gen(self.reply_q, int(self.config['Restart']['interval'])*60)
			curtime = time.time()
			runtime = curtime+int(self.config['Restart']['interval'])*60
			runtime = time.localtime(runtime)
			self.reply_q.put(Task(Task.NET_LINEUP,'[HANDLE] Server Restart at %s' % time.strftime('%H:%M:%S',runtime)))
			
def Restart_Gen(reply_q, time):
	events = []
	if time > 10:
		events.append(10)
	if time > 5:
		events.append(5)
	if time > 1:
		events.append(1)
	
	for event in events:
		tsk = Task(Task.NET_LINEUP,'Server Restart in %s min' % str(event*60))
		reply_q.put(Task(Task.SCH_ADD, (tsk, (time-event)*60)))

class ServerOut(threading.Thread):
	def __init__(self, Handle):
			self.handle = Handle
			self.exit = False
			threading.Thread.__init__(self)

	def run(self):
		while not self.exit:
		
			output = self.handle.server.output()
			if not output == 0x00:
				self.handle.addtask(Task(Task.NET_LINEUP, output))

class Backup(threading.Thread):
	def __init__(self, reply_q, cmd_q = Queue.Queue(maxsize = 0)):
		self.reply_q = reply_q
		self.cmd_q = cmd_q
		self.alive = threading.Event()
		self.alive.set()
		self.log = logging.getLogger('BACKUP')
		
		self.handlers = {
				Task.SRV_BACKUP:self.__backup
			}
		threading.Thread.__init__(self)
	def run(self):
		while self.alive.isSet():
			try:
				cmd = self.cmd_q.get(True, 0.1)
				self.handlers[cmd.type](cmd)
				
			except Queue.Empty:
				pass
				
	def __backup(self, cmd):
		self.reply_q.put(Task(Task.NET_LINEUP, '[HANDLE] Backup Started at %s'%time.strftime('%H:%M:%S')))
		backup_path = cmd.data['Handle']['path_to_bukkit'] + '/backups'
		worlds = cmd.data['Handle']['worlds'].split(',')
		world_files = []
		for world in worlds:
			world_files.append(cmd.data['Handle']['path_to_bukkit']+'/'+world)
			self.log.debug('%s added top world list'%(cmd.data['Handle']['path_to_bukkit']+'/'+world))
		self.log.debug(str(world_files))
		backup_command = ''
		x = 0
		for file in world_files:	
			shutil.copytree(file, backup_path+'/'+worlds[x])
			self.log.debug('shutil.copytree(%s, %s'%(file, backup_path+'/'+worlds[x]))
			backup_command = backup_command + (worlds[x] + ' ')
			x = x+1
		os.chdir(backup_path)
		self.log.debug('running tar: tar -cf %s.tar %s'%(time.strftime('%m_%d_%H%M'), backup_command))
		os.system('tar -cf %s.tar %s'%(time.strftime('%m_%d_%H%M'), backup_command))
		x = 0
		for file in world_files:
			shutil.rmtree(backup_path+'/'+worlds[x])
			x =x +1
		os.chdir(cmd.data['Handle']['original_path'])
		self.reply_q.put(Task(Task.NET_LINEUP, '[HANDLE] Backup Finished at %s'%time.strftime('%H:%M:%S')))
		
	def join(self):
		self.alive.clear()
		threading.Thread.join(self)