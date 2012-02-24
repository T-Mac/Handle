import threading
import Queue
import lib.server as server

class Handle(threading.Thread):
	def __init__(self):
		self.tasks = Queue.Queue(maxsize=0)
		self.comp{}
		self.exit = False
		#create Database instance
		self.comp['database'] = server.Database()
		#load config into database
		self.comp['database'].loadconfig()
		#create instance of bukkit controller
		self.comp['bukkit'] = server.Bukkit(self.comp['database'])
		#create Networking
		self.comp['network'] = network.Network('server', self.tasks, self.comp['database'].config['Handle']['port'])
		
		threading.Thread.__init__( self )
		
	def run(self):
		while not self.exit:
			task = self.tasks.get(True,5)
			self.parsetask(task)			
		
		
	def addtask(self, task)
		self.tasks.put(task)
	
	def parsetask(self, task)
		if task['id'] == 'network.lineup':
			self.comp['network'].send({'id':'clientup', 'item':'lineup', 'data':task['data']})
		if task['id'] == 'handle.command':
			self.parsecommand(task['data'])
	def start(self):
		self.comp['network'].start()

	def parsecommand(self, command):
		if command == 'start':
			self.comp['bukkit'].startserver()
		elif command == 'stop':
			self.comp['bukkit'].stopserver()


class Client(threading.Thread):
	def __init__(self):
			self.data = server.Database()
			self.data.loadconfig()
			self.tasks = Queue.Queue(maxsize=0)
			self.network = netork.Network('client', self.tasks, self.data.config['Handle']['port'])

			self.gui = 
