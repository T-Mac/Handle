import uuid
import shutil
import os

#class Server(object):
	#def _init__(self,
	
	
	
	
class Package(object):
	def __init__(self, craftbukkit, name):
		self.name = name
		self.id = str(uuid.uuid4())
		self.craftbukkit = craftbukkit
		
	def setup(self):
		os.mkdir('servers/%s'%self.name)
		shutil.copy(self.craftbukkit.path, 'servers/%s/craftbukkit.jar'%self.name)