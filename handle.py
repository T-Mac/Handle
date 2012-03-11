import threading
import Queue
import lib.server as server

class Handle(Base):
	def __init__(self):
		Base.__init__( self )
		#create instance of bukkit controller
		self.comp['bukkit'] = server.Bukkit(self.comp['database'])
		#create Networking
		self.comp['network'] = network.Network('server', self.tasks, self.comp['database'].config['Handle']['port'])
	
	def parsetask(self, task)
		if task['id'] == 'network.lineup':
			self.comp['network'].send({'id':'clientup', 'item':'lineup', 'data':task['data']})
		if task['id'] == 'handle.command':
			self.parsecommand(task['data'])
		if task['id'] == 'server.start':
			self.comp['bukkit'].startserver()
		if task['id'] == 'server.stop':
			self.comp['bukkit'].stopserver()
			
	def start(self):
		self.comp['network'].start()
		Base.start( self )

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

class Base(threading.Thread):
	def __init__(self):
		self.comp = {}
		self.tasks = Queue.Queue(maxsize = 0)
		self.exit = False
		self.comp['database'] = server.Database()
		self.comp['database'].loadconfig()
		
		threading.Thread.__init__( self )
	
	def run(self):
		while not self.exit:
			task = self.tasks.get(True,5)
			self.parsetask(task)

	def addtask(self, task)
		self.tasks.put(task)
		
	def parsetask(self, task)
		return False
	
	
	
	
	
	
