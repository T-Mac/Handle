import logging
module_logger = logging.getLogger(__name__)
from lib.api.Folder import FolderApi
from lib.api.DlBukkit import Dl_Bukkit
from lib.api.DevBukkit import Dev_Bukkit
import package

class PluginVersionFilter(object):
	def Execute(self, msg):
		module_logger.debug('Executing Plugin Version Filter')
		plugin_ver_index = {}
		for plugin, required in msg.plugins.iteritems():
			if required:
				module_logger.info('Getting version for %s'%plugin)
				ver_list = Dev_Bukkit.get_versions(plugin)
				plugin_ver_index[plugin]=ver_list
		msg.PVI = plugin_ver_index
		return msg
		
class PVIProcessFilter(object):
	def Execute(self, msg):
		module_logger.debug('Executing Plugin Vesion Index Process Filter')
		module_logger.debug('Creating version lists for comparison')
		lists = []
		for plugin, index in msg.PVI.iteritems():
			vers = []
			for item in index:
				vers.extend (item[1])
			lists.append(vers)
		module_logger.debug('Comparing lists')
		x = lists.pop()
		matches = set(x)
		for item in lists:
			matches = matches.intersection(item)
		matches = list(matches)
		module_logger.debug('Converting to float representation')
		versions = []
		for version in matches:
			versions.append(FolderApi.convert_ver_to_float(version))
		version = max(versions)
		version = FolderApi.expand_float_to_ver(version)
		module_logger.debug('Found Version: %s'%version)
		msg.pkg_version = msg.cb_version
		msg.cb_version = version		
		delattr(msg,'PVI')
		return msg
			
class CBVersionFilter(object):
	def Execute(self, msg):
		version_list = Dl_Bukkit.get_cb_versions(msg.channel)
		print version_list
		for item in version_list:
			if not item[0].find(msg.cb_version) == -1:
				version = item
				module_logger.debug('Found version match: %s'%version[0])
				break
			else:
				module_logger.debug('Version mismatch: %s - %s'%(item[0], msg.cb_version))
		match = FolderApi.check_for_existing('jars/', version[0].replace('.',''), version[1]['checksum_md5'])
		if match:
			msg.craftbukkit = package.Craftbukkit(version[0], match, version[1]['checksum_md5'], version[1]['url'])
			msg.download = False
		else:
			msg.craftbukkit = package.Craftbukkit(version[0], None, version[1]['checksum_md5'], version[1]['url'])
			msg.download = True
		return msg

class CBDownloadFilter(object):
	def __init__(self, callback = None):
		self.callback = callback
		
	def Execute(self, msg):
		if msg.download:
			url = 'http://dl.bukkit.org' + msg.craftbukkit.url
			filename = 'jars/craftbukkit-%s.jar'%msg.craftbukkit.version.replace('.','')
			module_logger.debug('Downloading %s to %s'%(url, filename))
			FolderApi.dl_file(url, filename, self.callback)
			if FolderApi.check_md5(filename, msg.craftbukkit.md5):
				msg.craftbukkit.path = filename
		delattr(msg, 'download')
		return msg
			
class PluginDlFilter(object):
	def __init__(self, callback = None):
		self.callback = callback
		
	def Execute(self, msg):
		module_logger.debug('Downloading Plugins')
		for plugin in msg.plugins:
			file = plugin+str(FolderApi.convert_ver_to_float(msg.craftbukkit.version, whole=True))
			deets = Dev_Bukkit.find_compat(plugin, msg.cb_version)
			module_logger.debug('Checking for Existing: %s'%plugin)
			existing = FolderApi.check_for_existing('jars/', file, deets[1])
			module_logger.debug('Check Returned: %s' %str(existing))
			if not existing == False:
				module_logger.debug('Match Found: %s'%existing)
				msg.plugins[plugin] = package.Plugin(existing, plugin, deets[1])
			else:
				module_logger.debug('Downloading: %s'%plugin)
				filename = 'jars/%s.jar'%(file)
				FolderApi.dl_file(deets[0], filename, self.callback)
				if FolderApi.check_md5(filename, deets[1]):
					msg.plugins[plugin] = package.Plugin(filename, plugin, deets[1])
					module_logger.debug('Finished downloading %s'%plugin)
		return msg
			