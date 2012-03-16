import threading
import Queue
import lib.server as server
import lib.gui as gui
import lib.network2 as network
import logging

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
		self.comp['bukkit'] = server.Bukkit(self.comp['database'], self)
		#create Networking
		self.comp['network'] = network.Network('server', self.tasks, int(self.comp['database'].config['Handle']['port']))
	
	def parsetask(self, task):
		if task['id'] == 'network.lineup':
			self.comp['network'].send({'id':'clientup', 'item':'line', 'data':task['data']})
		elif task['id'] == 'handle.command':
			self.parsecommand(task['data'])
		elif task['id'] == 'server.start':
			self.comp['bukkit'].startserver()
		elif task['id'] == 'server.stop':
			self.comp['bukkit'].stopserver()
		elif task['id'] == 'server.input':
			self.comp['bukkit'].input(task['data'])
		
			
	def start(self):
		self.comp['network'].start()
		Base.start( self )

	def parsecommand(self, command):
		if command == 'start':
			self.addtask({'id':'server.start'})
		elif command == 'stop':
			self.addtask({'id':'server.stop'})
		elif command == 'help':
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] Command	Description'})
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] start		Start the server'})
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] stop		Stop the server'})
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] restart	Restart the Server'})
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] exit		Stop the server and close Handle'})
			self.addtask({'id':'server.input', 'data':'help'})
		else:
			self.addtask({'id':'server.input', 'data':command})


class Client(Base):
	def __init__(self):
		Base.__init__( self )
		self.comp['network']= network.Network('client', self.tasks, int(self.comp['database'].config['Handle']['port']))
		self.comp['gui'] = gui.Gui(self)
		logging.basicConfig(level=logging.DEBUG, filename='client.log', format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.log = logging.getLogger('MainClient')
		
	def parsetask(self, task):
		if task['id'] == 'client.command': 
			self.comp['network'].send({'id':'input', 'data':task['data']})
		if task['id'] == 'client.lineup':
			self.log.debug('line update - ' + task['data'])
			self.comp['gui'].addline(task['data'])
			
	def start(self):
		self.comp['network'].start()
		Base.start( self )

	
	
	
	
	
	
