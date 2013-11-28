def pytest_addoption(parser):
	parser.addoption('--download', action="store_true", help='Tests File downloads')
	
def pytest_generate_tests(metafunc):
	if 'download' in metafunc.fixturenames:
		if not metafunc.config.option.download:
			metafunc.parametrize('download', [False])
		else:
			metafunc.parametrize('download',[True, False])