import lib.msg.pipeline as pipeline
import logging
import constructFilters
module_logger = logging.getLogger(__name__)

class Package(object):
	def __init__(self, cb_version, channel, plugins):
		self.cb_version = cb_version
		self.channel = channel
		#self.id = str(uuid.uuid4())
		self.craftbukkit = None
		self.plugins = plugins

class Craftbukkit(object):
	def __init__(self, version, path, md5, url):
		self.version = version
		self.path = path
		self.md5 = md5
		self.url = url
		
class Plugin(object):
	def __init__(self, path, plugin, md5):
		self.path = path
		self.plugin = plugin
		self.md5 = md5

class Package_Constructor(object):
	def __init__(self, progress_callback = None):
		self.pipeline = pipeline.Pipeline()
		self.progcall = progress_callback
		
		self.pipeline.Register(constructFilters.PluginVersionFilter())
		self.pipeline.Register(constructFilters.PVIProcessFilter())
		self.pipeline.Register(constructFilters.CBVersionFilter())
		self.pipeline.Register(constructFilters.CBDownloadFilter(self.progcall))
		self.pipeline.Register(constructFilters.PluginDlFilter(self.progcall))
		
	def Construct(self, cb_version = 'latest', channel = 'rb', plugins = {}):
		msg = Package(cb_version, channel, plugins)
		module_logger.info('Created Package - cb: %s - ch: %s - pl: %s'%(cb_version, channel, str(plugins)))
		pkg = self.Invoke(msg)
		return pkg
		
	def Invoke(self, msg):
		package = self.pipeline.Execute(msg)
		return package
		
class Package_Handler(object):
	def __init__(self):
		pass