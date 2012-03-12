import ConfigParser
import shlex
from select import select
import subprocess
import os
import threading

class Bukkit:
	def __init__(self, database, handle):
		self.database = database
		if self.database.config['Handle']['path_to_bukkit'][-1:] != '/':
			path = self.database.config['Handle']['path_to_bukkit'] + '/craftbukkit.jar'
		else:
			path = self.database.config['Handle']['path_to_bukkit'] + 'craftbukkit.jar'
		startcmd = 'java -Xmx' + str(self.database.config['Handle']['start_heap']) + 'M -Xms' + str(self.database.config['Handle']['max_heap'])  + 'M -jar ' + str(path)
		self.startcmd = shlex.split(startcmd)
		self.pipe_read, self.pipe_write = os.pipe()
		self.handle = handle
		
	def startserver(self):
		self.serverout = ServerOut(self.handle)
		os.chdir(self.database.config['Handle']['path_to_bukkit'])
		self.bukkit = subprocess.Popen(self.startcmd, shell=False, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
		os.chdir(self.database.config['Handle']['original_path'])
		os.write(self.pipe_write, 'exit')
		
	def stopserver(self):
		self.bukkit.stdin.write('stop\n')

	def output(self):
		select((self.bukkit.stdout, self.pipe_read,),(),())
		return self.bukkit.stdout.readline()[:-2]
	
	def input(self,data):
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
		
			output = self.handle.comp['bukkit'].server.output()
			self.handle.addtask({'id':'network.lineup', 'data':output})

