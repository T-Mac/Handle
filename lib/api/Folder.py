import hashlib
import time
from path import path
import requests
import logging
import os.path
import os
module_logger = logging.getLogger(__name__)

class FolderApi(object):
	@staticmethod
	def check_for_existing(folder, pattern, md5):
		dir = path(folder)
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
		try:
			with open(path, 'rb') as f:
				for chunk in iter(lambda: f.read(65536), b''): 
					hasher.update(chunk)
		except IOError:
			module_logger.debug('Hash Check -FAILED- NO FILE PRESENT')
			return False
				
		hash = hasher.hexdigest()
		if hash == md5:
			module_logger.debug('Hash Check -PASSED-')
			return True
		else:
			module_logger.debug('Hash Check -FAILED-')
			return False
			
	@staticmethod
	def dl_file(url, filename, callback=None):
		if not os.path.exists('jars'):
			os.mkdir('jars')
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
	def convert_ver_to_float(ver, whole = False, rough = False):
		x = ver.replace('.','').replace('-','')
		if not x.find('R') == -1:
			version = float(x[:x.find('R')] )
			if not rough:
				version = version + (float(x[x.find('R')+1:]) * 0.01)
		else:
			version = float(x)
		if whole:
			version = int(version)
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