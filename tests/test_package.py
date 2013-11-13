import lib.package as package
import pytest

@pytest.fixture(scope='module')
def mockpkg():
	return package.Package('latest', 'dev', {'jsonapi':True})
	
#MockCB = package.Craftbukkit(
	
class TestClass:
	def test_plugin_version_finder(self, mockpkg):
		PluginVersionFilter = package.PluginVersionFilter()
		PVIProcessFilter = package.PVIProcessFilter()
		msg = PluginVersionFilter.Execute(mockpkg)
		assert hasattr(msg, 'PVI') == True
		msg = PVIProcessFilter.Execute(msg)
		assert not hasattr(msg, 'PVI')
		assert hasattr(msg, 'pkg_version')
		
	def test_CBVersionFilter(self, mockpkg):
		pkg = mockpkg
		pkg.cb_version = '1.6.4'
		filter = package.CBVersionFilter()
		msg = filter.Execute(pkg)
		assert hasattr(msg, 'download')
		assert isinstance(msg.craftbukkit, package.Craftbukkit)
		mockpkg = msg
		
	def test_CBDownloadFilter(self, mockpkg, download):
		filter = package.CBDownloadFilter()
		mockpkg.download = download
		msg = filter.Execute(mockpkg)
		assert not hasattr(msg, 'download')
		assert isinstance(msg.craftbukkit, package.Craftbukkit)
		assert not msg.craftbukkit.path == None
		
	def test_PluginDownloadFilter(self, mockpkg):
		filter = package.PluginDlFilter()
		msg = filter.Execute(mockpkg)
		for plugin, object in msg.plugins.iteritems():
			assert isinstance(object, package.Plugin)