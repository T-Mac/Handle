import urllib2
import json
import requests
import hashlib
from bs4 import BeautifulSoup

class Craftbukkit(object):
	def __init__(self, version, path, build, md5):
		self.version = version
		self.path = path
		self.build = build
		self.md5 = md5
		
class Plugin(object):
	def __init__(self, path, plugin, md5):
		self.path = path
		self.plugin = plugin
		self.md5 = md5
		
class Dl_Bukkit(object):
	def __init__(self, dl_path='temp', progress_callback=None):
		self.path = dl_path
		self.progcall = progress_callback
		
	def get_latest(self, project, channel):
		response = requests.get('http://dl.bukkit.org/api/1.0/downloads/projects/%s/view/latest-%s?_accept=application/json'%(project,channel))
		return (response.json()['version'], response.json()['file'], response.json()['build_number'])
		
	def dl_latest(self, project, channel):
		version, file, build  = self.get_latest(project, channel)
		r = requests.get('http://dl.bukkit.org' + file['url'], stream = True)
		filename = 'jars/craftbukkit-%s.jar'%version.replace('.','')
		#print 'Downloading %s bytes to %s'%(str(file['size']), filename),
		with open(filename, 'wb') as f:
			dled = 0
			for chunk in r.iter_content(chunk_size=2048): 
				if chunk: # filter out keep-alive new chunks
					dled = dled + len(chunk)
					if self.progcall:
						self.progcall(float(file['size']),float(dled))
					f.write(chunk)
					f.flush()
		file = Craftbukkit(version, filename, build, file['checksum_md5'])
		if self.check_md5(file):
			return file
		
	def check_md5(self, file):
		hasher = hashlib.md5()
		with open(file.path, 'rb') as f:
			for chunk in iter(lambda: f.read(65536), b''): 
				hasher.update(chunk)
				
		hash = hasher.hexdigest()
		if hash == file.md5:
			return True
		else:
			return False
		
class Dev_Bukkit(object):
	def __init__(self, path='temp', progress_callback = None):
		self.path = path
		self.prog_call  = progress_callback
		self.base_path = 'http://dev.bukkit.org/bukkit-plugins/'
		
	def get_versions(self, name):
		filter = ['even', 'odd']
		r = requests.get(self.base_path+name+'/files')
		soup = BeautifulSoup(r.text)
		rough_list = soup.find_all('tr',class_=filter)
		parsed = self.create_version_list(rough_list)
		return parsed
		
	def create_version_list(self, rough_list):
		version_list = []
		for item in rough_list:
			file_url = item.find(class_='col-file').contents[0]['href'][16:]
			compat_versions = []
			for version in item.find(class_='comma-separated-list').contents:
				compat_versions.append(str(version.string).replace('CB ',''))
			version_list.append((file_url,compat_versions))
		return version_list
		
	def find_compat(self, cb_version, version_list):
		for entry in version_list:
			for version in entry[1]:
				#print 'CB: %s - %s :VER'%(cb_version,version)
				if cb_version == version:
					return entry
		return False
		
	def get_download_details(self, dl_page):
		r = requests.get(self.base_path + dl_page)
		soup = BeautifulSoup(r.text)
		rough = soup.dl.find_all('dd')
		url = rough[2].contents[0]['href']
		md5 = str(rough[4].contents[0])
		plugin = str(rough[2].contents[0].string)
		return (url, md5, plugin)
		
	def dl_file(self, url):
		deets = self.get_download_details(url)
		filename = 'jars/%s.jar'%url[url.find('-')+1:-1].replace('-','')
		r = requests.get(deets[0], stream = True)
		with open(filename, 'wb') as file:
			dled = 0
			for chunk in r.iter_content(chunk_size=2048): 
				if chunk: # filter out keep-alive new chunks
					dled = dled + len(chunk)
					#if self.prog_call:
					#	self.prog_call(float(file['size']),float(dled))
					file.write(chunk)
					file.flush()
		file = Plugin(filename, deets[2], deets[1])
		if self.check_md5(file):
			return file

		
					
	def check_md5(self, file):
		hasher = hashlib.md5()
		with open(file.path, 'rb') as f:
			for chunk in iter(lambda: f.read(65536), b''): 
				hasher.update(chunk)
				
		hash = hasher.hexdigest()
		if hash == file.md5:
			return True
		else:
			return False 