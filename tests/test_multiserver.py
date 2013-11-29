import pytest
from lib.package import package
import lib.multiserver.deployFilters as deployFilters
from lib.multiserver import multiserver

@pytest.fixture(scope='class')
def pkg():
	plugin = package.Plugin('jars/jsonapi16421.jar', 'jsonapi', '55d7846250ab3a0f21288d247771dc7a')
	cb = package.Craftbukkit('1.6.4','jars/craftbukkit-164-R21.jar', '915125d249bada999aeff867abf8a6ad','/downloads/craftbukkit/get/02391_1.6.4-R2.1/craftbukkit-dev.jar')
	pkg = package.Package('1.6.4-R2.1', 'dev', {'jsonapi':plugin})
	pkg.craftbukkit = cb
	pkg.pkg_version = 'latest'
	return pkg
	
@pytest.fixture(scope='class')
def server(pkg):
	srv = multiserver.Server(pkg, 'test2%s'%pkg.cb_version.replace('.',''))
	return srv
	
@pytest.fixture(scope='class')
def handler():
	return multiserver.ServerHandler()
class Test_MultiServer(object):
	def test_PkgVerifyFilter(self, server):
		filter = deployFilters.PkgVerifyFilter()
		msg = filter.Execute(server)
		if hasattr(msg, 'StopProcessing'):
			assert msg.StopProcessing == True
			assert hasattr(msg, 'error')
			print msg.error
			
	def test_FileDeployFilter(self, server):
		filter = deployFilters.FileDeployFilter()
		msg = filter.Execute(server)
		#assert not hasattr(msg, 'StopProcessing')
		
	def test_FileCheckFilter(self, server):
		filter = deployFilters.FileCheckFilter()
		msg = filter.Execute(server)
		assert isinstance(msg, multiserver.Server)
		
	def test_ConfigDeployFilter(self, server):
		filter = deployFilters.ConfigDeployFilter()
		msg = filter.Execute(server)
		assert isinstance(msg, multiserver.Server)
		assert hasattr(msg, 'maxheap')
		assert hasattr(msg, 'startheap')
		
	def test_SetStartCmdFilter(self, server):
		filter = deployFilters.SetStartCmdFilter()
		msg = filter.Execute(server)
		assert hasattr(msg, 'startcmd')
			
	def test_SetDeployedFilter(self, server):
		filter = deployFilters.SetDeployedFilter()
		msg = filter.Execute(server)
		assert hasattr(msg, 'deployed')
		if hasattr(msg, 'deployed'):
			assert msg.deployed == True
			
class TestPipeline(object):
	def test_DeployPipeline(self, server):
		controller = multiserver.ServerController()
		msg = controller.Deploy(server)
		assert isinstance(msg, multiserver.Server)
		assert hasattr(msg, 'startcmd')
		assert hasattr(msg, 'deployed')
		if hasattr(msg, 'deployed'):
			assert msg.deployed == True
		assert hasattr(msg, 'maxheap')
		if hasattr(msg, 'maxheap'):
			assert isinstance(msg.maxheap, basestring)
		assert hasattr(msg, 'startheap')
		if hasattr(msg, 'startheap'):
			assert isinstance(msg.startheap, basestring)
			
class Test_Handler(object):
	def test_Server_Handler(self, handler):
		server = handler.create('test')
		assert isinstance(server, multiserver.Server)
		assert isinstance(server.package, package.Package)
		assert isinstance(server.package.craftbukkit, package.Craftbukkit)
		for plugin in server.package.plugins.values():
			assert isinstance(plugin, package.Plugin)