from lib.package import package
import lib.package.constructFilters as constructFilters
import pytest
import logging
LOGLVL = logging.DEBUG
logging.basicConfig(level=LOGLVL, format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class Whitelist(logging.Filter):
    def __init__(self, *whitelist):
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)
for handler in logging.root.handlers:
	handler.addFilter(Whitelist('lib.package'))
	
@pytest.fixture(scope='module')
def mockpkg():
	return package.Package('latest', 'dev', {'jsonapi':True})
	
@pytest.fixture()
def mockinvoke():
	return ('latest', 'rb', {'jsonapi':True})
	
@pytest.fixture(scope='module')
def pkgConstruct():
	return package.Package_Constructor()
	#MockCB = package.Craftbukkit
	
@pytest.fixture(scope='module')
def pkgHandler():
	return package.Package_Handler()
	
class Test_Package:
	def test_plugin_version_finder(self, mockpkg):
		PluginVersionFilter = constructFilters.PluginVersionFilter()
		PVIProcessFilter = constructFilters.PVIProcessFilter()
		msg = PluginVersionFilter.Execute(mockpkg)
		assert hasattr(msg, 'PVI') == True
		msg = PVIProcessFilter.Execute(msg)
		assert hasattr(msg, 'PVI')
		assert hasattr(msg, 'pkg_version')
		
	def test_CBVersionFilter(self, mockpkg):
		pkg = mockpkg
		pkg.cb_version = '1.6.4'
		filter = constructFilters.CBVersionFilter()
		msg = filter.Execute(pkg)
		assert hasattr(msg, 'download')
		assert isinstance(msg.craftbukkit, package.Craftbukkit)
		mockpkg = msg
		
	def test_CBDownloadFilter(self, mockpkg, download):
		filter = constructFilters.CBDownloadFilter()
		mockpkg.download = download
		msg = filter.Execute(mockpkg)
		assert not hasattr(msg, 'download')
		assert isinstance(msg.craftbukkit, package.Craftbukkit)
		assert not msg.craftbukkit.path == None
		
	def test_PluginDownloadFilter(self, mockpkg):
		filter = constructFilters.PluginDlFilter()
		msg = filter.Execute(mockpkg)
		for plugin, object in msg.plugins.iteritems():
			assert isinstance(object, package.Plugin)
			
	def test_PackageConstructor(self, pkgConstruct, mockinvoke):
		pkg = pkgConstruct.Construct(mockinvoke[0], mockinvoke[1], mockinvoke[2])
		assert hasattr(pkg, 'pkg_version')
		assert hasattr(pkg, 'plugins')
		for plugin, obj in pkg.plugins.iteritems():
			assert isinstance(plugin, basestring)
			assert isinstance(obj, package.Plugin)
		assert isinstance(pkg.craftbukkit, package.Craftbukkit)
		assert hasattr(pkg, 'channel')
		
	def test_PackageHandler(self, pkgHandler):
		pkg = pkgHandler.get('default')
		assert isinstance(pkg, package.Package)
		
		
		