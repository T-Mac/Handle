import sys
import lib.package as package
import logging
logger = logging.getLogger('')

def callback(size, done):
	print '%s %s/%s'%(str((done/size)*100)[:3], str(done), str(size))


PC = package.Package_Constructor(callback)
pkg = PC.Construct('latest', 'dev', {'jsonapi':True, 'punishwarnand':True})
print 'Test Finished'