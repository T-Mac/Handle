#import msg
import shutil
import os
import lib.msg.pipeline as pipeline
import deployFilters

class Server(object):
	def __init__(self, package, name, config='default'):
		self.package = package
		self.name = name
		self.path = 'servers/%s'%name
		self.deployed = False
		self.config = config
		self.running = False

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
		self.pkgPipeline = pipeline.Pipeline()