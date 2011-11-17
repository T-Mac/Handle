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
		
		
		threading.Thread.__init__( self )
		
	def run(self):
		while not self.exit:
			self.tasks.get(True,5)
			
		
		
	def addtask(self, task)
		self.tasks.put(task)
	