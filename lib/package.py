import msg.pipeline as pipeline
import requests
import hashlib
from path import path
import logging
from bs4 import BeautifulSoup
import time
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
		
		self.pipeline.Register(PluginVersionFilter())
		self.pipeline.Register(PVIProcessFilter())
		self.pipeline.Register(CBVersionFilter())
		self.pipeline.Register(CBDownloadFilter(self.progcall))
		self.pipeline.Register(PluginDlFilter(self.progcall))
		
	def Construct(self, cb_version = 'latest', channel = 'rb', plugins = {}):
		msg = Package(cb_version, channel, plugins)
		module_logger.info('Created Package - cb: %s - ch: %s - pl: %s'%(cb_version, channel, str(plugins)))
		pkg = self.Invoke(msg)
		return pkg
		
	def Invoke(self, msg):
		package = self.pipeline.Execute(msg)
		return package
		
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
		for item in version_list:
			if not item[0].find(msg.cb_version) == -1:
				version = item
				module_logger.debug('Found version match: %s'%version[0])
				break
		match = FolderApi.check_for_existing(version[0].replace('.',''), version[1]['checksum_md5'])
		if match:
			msg.craftbukkit = Craftbukkit(version[0], match, version[1]['checksum_md5'], version[1]['url'])
			msg.download = False
		else:
			msg.craftbukkit = Craftbukkit(version[0], None, version[1]['checksum_md5'], version[1]['url'])
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
			existing = FolderApi.check_for_existing(file, deets[1])
			module_logger.debug('Check Returned: %s' %str(existing))
			if not existing == False:
				module_logger.debug('Match Found: %s'%existing)
				msg.plugins[plugin] = Plugin(existing, plugin, deets[1])
			else:
				module_logger.debug('Downloading: %s'%plugin)
				filename = 'jars/%s.jar'%(file)
				FolderApi.dl_file(deets[0], filename, self.callback)
				if FolderApi.check_md5(filename, deets[1]):
					msg.plugins[plugin] = Plugin(filename, plugin, deets[1])
					module_logger.debug('Finished downloading %s'%plugin)
		return msg
			
class Dev_Bukkit(object):
	@staticmethod
	def get_versions(name):
		filter = ['even', 'odd']
		r = requests.get('http://dev.bukkit.org/bukkit-plugins/' + name + '/files')
		soup = BeautifulSoup(r.text)
		rough_list = soup.find_all('tr',class_=filter)
		parsed = Dev_Bukkit.create_version_list(rough_list)
		return parsed
		
	@staticmethod	
	def create_version_list(rough_list):
		version_list = []
		for item in rough_list:
			file_url = item.find(class_='col-file').contents[0]['href'][16:]
			compat_versions = []
			for version in item.find(class_='comma-separated-list').contents:
				compat_versions.append(str(version.string).replace('CB ',''))
			version_list.append((file_url,compat_versions))
		return version_list
	
	@staticmethod
	def find_compat(plugin, cb_version):
		version_list = Dev_Bukkit.get_versions(plugin)
		for entry in version_list:
			for version in entry[1]:
				#print 'CB: %s - %s :VER'%(cb_version,version)
				if cb_version == version:
					deets = Dev_Bukkit.get_download_details(entry[0])
					return deets
		return False
	
	@staticmethod
	def get_download_details(url):
		r = requests.get('http://dev.bukkit.org/bukkit-plugins/' + url)
		soup = BeautifulSoup(r.text)
		rough = soup.dl.find_all('dd')
		url = rough[2].contents[0]['href']
		md5 = str(rough[4].contents[0])
		plugin = str(rough[2].contents[0].string)
		return (url, md5, plugin)
		
class Dl_Bukkit(object):
	@staticmethod
	def get_cb_versions(channel = 'dev'):
		versions = []
		response = requests.get('http://dl.bukkit.org/api/1.0/downloads/projects/craftbukkit/artifacts/%s?_accept=application/json'%(channel))
		for item in response.json()['results']:
			versions.append((item['version'], item['file']))
		return versions
		
		
class FolderApi(object):
	@staticmethod
	def check_for_existing(pattern, md5):
		dir = path('jars')
		matches = dir.glob('*'+pattern+'*')
		for file in matches:
			if FolderApi.check_md5(str(file), md5):
				module_logger.debug('Match Fodund: %s'%str(file))
				return str(file)
		return False
	@staticmethod			
	def check_md5(path, md5):
		hasher = hashlib.md5()
		module_logger.debug('Starting Hash Check for %s with %s'%(path, md5))
		with open(path, 'rb') as f:
			for chunk in iter(lambda: f.read(65536), b''): 
				hasher.update(chunk)
				
		hash = hasher.hexdigest()
		if hash == md5:
			module_logger.debug('Hash Check -PASSED-')
			return True
		else:
			module_logger.debug('Hash Check -FAILED-')
			return False
			
	@staticmethod
	def dl_file(url, filename, callback=None):
		module_logger.info('Starting download of URL: %s'%url)
		start = time.time()
		r = requests.get(url, stream = True)
		with open(filename, 'wb') as f:
			dled = 0
			for chunk in r.iter_content(chunk_size=3072): 
				if chunk: # filter out keep-alive new chunks
					dled = dled + len(chunk)
					if callback:
						callback(float(r.headers['content-length']),float(dled))
					f.write(chunk)
					f.flush()
		stop = time.time()
		module_logger.info('Download Finished in %s secs'%str(int(stop-start)))
		return filename
	
	@staticmethod
	def convert_ver_to_float(ver, whole = False):
		x = ver.replace('.','').replace('-','')
		version = float(x[:3])
		x = x[3:]
		if not x.find('R') == -1:
			x = x.replace('R','')
			version = version + (float(x)*0.01)
		if whole:
			version = int(version * 100)
		module_logger.debug('Converted %s to %s'%(ver, str(version)))
		return version
	
	@staticmethod
	def expand_float_to_ver(ver):
		x = str(int(ver))
		version = ''
		for number in x:
			version = version + number + '.'
		version = version[:-1]
		if len(str(ver)) > 5:
			version = version + '-R' + str(ver)[-2:-1] + '.' + str(ver)[-1:]
		return version