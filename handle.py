import threading
import Queue
import lib.server as server
import lib.gui as gui
import lib.network2 as network

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
			try:
				task = self.tasks.get(True,5)
			except Queue.Empty:
				pass
			else:
				self.parsetask(task)

	def addtask(self, task):
		self.tasks.put(task)
		
	def parsetask(self, task):
		return False



class Handle(Base):
	def __init__(self):
		Base.__init__( self )
		#create instance of bukkit controller
		self.comp['bukkit'] = server.Bukkit(self.comp['database'])
		#create Networking
		self.comp['network'] = network.Network('server', self.tasks, int(self.comp['database'].config['Handle']['port']))
	
	def parsetask(self, task):
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
			self.addtask({'id':'server.start'})
		elif command == 'stop':
			self.addtask({'id':'server.stop'})


class Client(Base):
	def __init__(self):
			Base.__init__( self )
			self.comp['network']= network.Network('client', self.tasks, int(self.comp['database'].config['Handle']['port']))
			self.comp['gui'] = gui.Gui(self)
			
	def parsetask(self, task):
		if task['id'] == 'client.command': 
			self.comp['network'].send({'id':'input', 'data':task['data']})
		if task['id'] == 'lineup':
			self.comp['gui'].addline(task.data)
			
	def start(self):
		self.comp['network'].start()
		Base.start( self )

	
	
	
	
	
	
