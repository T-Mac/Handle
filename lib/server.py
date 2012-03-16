import ConfigParser
import shlex
from select import select
import subprocess
import os
import threading
import logging

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
		self.running = False
		self.bukkit.stdin.write('stop\n')
		self.serverout.exit = True
		os.write(self.pipe_write, 'exit')
		

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
	def loadconfig(self):
		self.config = {}
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		sections = configfile.sections()
		for section in sections:
			options = configfile.options(section)
			internal = {}
			for option in options:
				internal[option] = configfile.get(section,option)
			self.config[section] = internal
		self.config['Handle']['original_path'] = os.getcwd()

class ServerOut(threading.Thread):
	def __init__(self, Handle):
			self.handle = Handle
			self.exit = False
			threading.Thread.__init__(self)

	def run(self):
		while not self.exit:
		
			output = self.handle.comp['bukkit'].output()
			if not output == 0x00:
				self.handle.addtask({'id':'network.lineup', 'data':output})

