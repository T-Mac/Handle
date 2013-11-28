import logging
module_logger = logging.getLogger(__name__)
import hashlib
import path
import os
import shutil
import lib.config
import shlex
from lib.api.Folder import FolderApi
import os.path

class PkgVerifyFilter(object):
	def Execute(self, msg):
		pkg = msg.package
		module_logger.debug('Checking Craftbukkit')
		if FolderApi.check_md5(pkg.craftbukkit.path, pkg.craftbukkit.md5):
			module_logger.debug('Craftbukkit Check PASSED - Checking Plugins')
			passed = True
			for name, plugin in pkg.plugins.iteritems():
				module_logger.debug('Checking %s'%name)
				if not FolderApi.check_md5(plugin.path, plugin.md5):
					module_logger.debug('%s Hash Check FAILED'%name)
					passed = False
					msg.error = 'PkgVerify -FAILED- %s Check Failed'%name
				else:
					module_logger.debug('%s Hash Check PASSED'%name)
			if not passed:
				msg.StopProcessing = True
		else:
			module_logger.debug('CraftBukkit Check FAILED')
			msg.StopProcessing = True
			msg.error = 'PkgVerify -FAILED- Craftbukkit Check Failed'
		return msg
					


class FileDeployFilter(object):
	def Execute(self, msg):
		module_logger.debug('Running Deploy Filter')
		DeployApi.Deploy(msg)
		return msg
		
class FileCheckFilter(object):
	def Execute(self, msg):
		if FolderApi.check_md5('servers/%s/craftbukkit.jar'%msg.name, msg.package.craftbukkit.md5):
			passed = True
			for name, plugin in msg.package.plugins.iteritems():
				if not FolderApi.check_md5('servers/%s/plugins/%s.jar'%(msg.name, name), plugin.md5):
					passed = False
			if passed:
				return msg
			else:
				msg.StopProcessing = True
				msg.error = 'FileCheck -FAILED-'
				return msg
				
class ConfigDeployFilter(object):
	def Execute(self, msg):
		module_logger.debug('Deploying Config')
		DeployApi.DeployConfig(msg)
		config = lib.config.load_server_config(section='settings', keys=['maxheap','startheap'])
		msg.maxheap = config['maxheap']
		msg.startheap = config['startheap']
		return msg
		
class SetDeployedFilter(object):
	def Execute(self, msg):
		msg.deployed = True
		return msg
		
class SetStartCmdFilter(object):
	def Execute(self, msg):
		startcmd = 'java -Xmx %s -Xms %s -jar %s'%(msg.startheap, msg.maxheap, 'servers/%s/craftbukkit.jar'%msg.name)
		msg.startcmd = shlex.split(startcmd)
		return msg
		
		
class DeployApi(object):
	@staticmethod
	def Deploy(server):
		if not DeployApi.CheckForExisting(server.name):
			module_logger.debug('No deploy found Creating...')
			os.mkdir('servers/%s'%server.name)
			module_logger.debug('Copying %s to craftbukkit.jar'%server.package.craftbukkit.path)
			shutil.copyfile(server.package.craftbukkit.path,  'servers/%s/craftbukkit.jar'%server.name)
			os.mkdir('servers/%s/plugins'%server.name)
			for name, plugin in server.package.plugins.iteritems():
				module_logger.debug('Copying Plugin: %s'%name)
				shutil.copyfile(plugin.path, 'servers/%s/plugins/%s'%(server.name, name+'.jar'))
		else:
			module_logger.debug('Existing Deploy Found, Updating...')
			DeployApi.UpdateExistingDeploy(server)
	@staticmethod
	def CheckForExisting(name):
		if os.path.exists('servers'):
			if 'servers/'+name in path.path('servers/').dirs():
				return True
			else:
				return False
		else:
			os.mkdir('servers')
			return False
		
	@staticmethod
	def UpdateExistingDeploy(server):
		if not FolderApi.check_md5('servers/%s/craftbukkit.jar'%server.name, server.package.craftbukkit.md5):
			module_logger.debug('Craftbukkit check -FAILED- Copying: %s'%server.package.craftbukkit.path)
			try:
				os.remove('servers/%s/craftbukkit.jar'%server.name)
			except OSError:
				pass
			shutil.copyfile(server.package.craftbukkit.path, 'servers/%s/craftbukkit.jar'%server.name)
		for name, plugin in server.package.plugins.iteritems():
			if not FolderApi.check_md5('servers/%s/plugins/%s.jar'%(server.name, name), plugin.md5):
				module_logger.debug('Check: %s -FAILED- Copying: %s'%(name, plugin.path))
				try:
					os.remove('servers/%s/plugins/%s.jar'%(server.name, name))
				except OSError:
					pass
				shutil.copyfile(plugin.path, 'servers/%s/plugins/%s.jar'%(server.name, name))

	@staticmethod
	def gen_md5(path):
		hasher = hashlib.md5()
		try:
			with open(path, 'r') as f:
				for chunk in iter(lambda: f.read(65536), b''): 
					hasher.update(chunk)
		except IOError:
			module_logger.debug('Hash Gen -FAILED- NO FILE PRESENT')
			return False
			
		hash =  hasher.hexdigest()
		module_logger.debug('Generated Hash: %s for %s'%(hash, path))
		return hash
		
	@staticmethod
	def DeployConfig(server):
		files = path.path('config/%s/'%server.config).walkfiles()
		header = len(str(path.path('config/%s/'%server.config)))
		configfiles = {}
		for file in files:
			md5 = DeployApi.gen_md5(str(file))
			key = file[header:]
			configfiles[key] = md5
			
		for file, md5 in configfiles.iteritems():
			if not FolderApi.check_md5('servers/%s/%s'%(server.name, file), md5):
				try:
					os.remove('servers/%s/%s'%(server.name, file))
				except OSError:
					pass
				try:
					shutil.copyfile('config/%s/%s'%(server.config, file), 'servers/%s/%s'%(server.name, file))
				except IOError:
					folder = file[:file.rfind('/')]
					folder = 'servers/%s/%s'%(server.name,folder)
					os.makedirs(folder)
					shutil.copyfile('config/%s/%s'%(server.config, file), 'servers/%s/%s'%(server.name, file))
			
			
			