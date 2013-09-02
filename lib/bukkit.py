import urllib2
import json
import requests
import hashlib

class Craftbukkit(object):
	def __init__(self, version, path, build, md5):
		self.version = version
		self.path = path
		self.build = build
		self.md5 = md5
		
class Api(object):
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
			for chunk in r.iter_content(chunk_size=1024): 
				if chunk: # filter out keep-alive new chunks
					dled = dled + len(chunk)
					if self.progcall:
						self.progcall(float(file['size']),float(dled))
					f.write(chunk)
					f.flush()
		file = Craftbukkit(version, 'jars/' + filename, build, file['checksum_md5'])
		if self.check_md5(file):
			return file
		
	def check_md5(self, file):
		hasher = hashlib.md5()
		with open(file.path, rb) as f:
			for chunk in iter(lambda: f.read(65536), b''): 
				hasher.update(chunk)
				
		hash = hasher.hexdigest()
		if hash == file.md5:
			return True
		else:
			return False
		
		