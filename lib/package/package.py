import lib.msg.pipeline as pipeline
import logging
import constructFilters
import yaml
module_logger = logging.getLogger(__name__)

class Package(yaml.YAMLObject):
	yaml_tag = '!Package'
	def __init__(self, cb_version, channel, plugins):
		self.cb_version = cb_version
		self.channel = channel
		#self.id = str(uuid.uuid4())
		self.craftbukkit = None
		self.plugins = plugins
		self.pkg_version = None

	def __repr__(self):
		return "%s(cb_version=%r, channel=%r, craftbukkit=%r, plugins=%r, pkg_version=%r)"%(
			self.__class__.__name__,
			self.cb_version, 
			self.channel, 
			self.craftbukkit,
			self.plugins,
			self.pkg_version)

class Craftbukkit(yaml.YAMLObject):
	yaml_tag = '!Craftbukkit'
	def __init__(self, version, path, md5, url):
		self.version = version
		self.path = path
		self.md5 = md5
		self.url = url
	def __repr__(self):
		return "%s(version=%r, path=%r, md5=%r, url=%r)"%(self.__class__.__name__, self.version, self.path, self.md5, self.url)
		
class Plugin(object):
	yaml_tag = '!Plugin'
	def __init__(self, path, plugin, md5):
		self.path = path
		self.plugin = plugin
		self.md5 = md5
		
	def __repr__(self):
		return "%s(path=%r, plugin=%r, md5=%r)"%(self.__class__.__name__, self.path, self.plugin, self.md5)

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
		self.packages = []

	def load(self, package = 'all'):
		if package == 'all':
			pass
			