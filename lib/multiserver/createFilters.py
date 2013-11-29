from lib.package import package
import multiserver

class PkgCreateFilter(object):
	def __init__(self):
		self.Package_Handler = package.Package_Handler()
		
	def Execute(self, msg):
		pkg = self.Package_Handler.get(msg[1])
		return (msg[0],pkg)
		
class ServerCreateFilter(object):
	def Execute(self, msg):
		server = multiserver.Server(msg[1], msg[0])
		return server