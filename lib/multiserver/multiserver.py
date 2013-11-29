#import msg
import shutil
import os
import lib.msg.pipeline as pipeline
import deployFilters
from lib.package import package
import yaml
import createFilters


class Server(yaml.YAMLObject):
	yaml_tag = '!Server'
	def __init__(self, package, name, config='default'):
		self.package = package
		self.name = name
		self.path = 'servers/%s'%name
		self.deployed = False
		self.config = config
		self.running = False
	
	def __repr__(self):
		return "%s(package=%r, name=%r, path=%r, deployed=%r, config=%r)"%(
			self.__class__.__name__,
			self.package,
			self.name,
			self.path,
			self.deployed,
			self.config)
			
class ServerController(object):
	def __init__(self):
		self.deploy_pipe = pipeline.Pipeline()
		self.deploy_pipe.Register(deployFilters.PkgVerifyFilter())
		self.deploy_pipe.Register(deployFilters.FileDeployFilter())
		self.deploy_pipe.Register(deployFilters.FileCheckFilter())
		self.deploy_pipe.Register(deployFilters.ConfigDeployFilter())
		self.deploy_pipe.Register(deployFilters.SetStartCmdFilter())
		self.deploy_pipe.Register(deployFilters.SetDeployedFilter())
		#make sure SetDeployedFilter is LAST
		
	def Deploy(self, server):
		msg = self.deploy_pipe.Execute(server)
		return msg
		
	def Start(self, server):
		if server.deployed:
			server.process = subprocess.Popen(server.startcmd, 
												shell=False, 
												cwd='servers/%s/'%server.name, 
												stdin = subprocess.PIPE, 
												stdout = subprocess.PIPE, 
												stderr = subprocess.STDOUT)
			server.running = True
		else:
			msg = self.Deploy(server)
			self.Start(msg)
			
		return server
		
	def Stop(self, server):
		if server.running:
			server.process.stdin.write('stop\n')
			server.running = False
		return server
		
class ServerHandler(object):
	def __init__(self):
		self.servers = {}
		self.create_pipeline = pipeline.Pipeline()
		self.create_pipeline.Register(createFilters.PkgCreateFilter())
		self.create_pipeline.Register(createFilters.ServerCreateFilter())
		self.Controller = ServerController()
		
	def load(self):
		try:
			with open('servers.yml', 'r') as file:
				for server in yaml.load_all(file):
					self.servers[server.name] = server
		except IOError:
			pass
	
	def save(self):
		with open('servers.yml', 'a') as file:
			yaml.dump_all(self.servers.values(), file)
			
	def create(self, server, package = 'default'):
		server = self.create_pipeline.Execute((server, package))
		self.servers[server.name] = server
		self.Controller.Deploy(server)
		return server
		