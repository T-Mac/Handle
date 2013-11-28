import pytest
import tests.pipeobj as pipeobj
import lib.msg.pipeline as pipeline

@pytest.fixture()
def filter():
	return pipeobj.SimpleFilter()
	

@pytest.fixture()
def pipe(filter):
	p = pipeline.Pipeline()
	p.filters = []
	p.Register(filter)
	return p
	
@pytest.fixture()
def pipeWaspect(pipe):
	pipe.addGlobalAspect(pipeobj.SimpleAspect)
	return pipe
@pytest.fixture()	
def pipeW2Aspects(pipe):
	pipe.addGlobalAspect(pipeobj.SimpleAspect)
	filter2 = pipeobj.SimpleFilter()
	pipe.Register(filter2)
	pipe.addFilterAspect(pipeobj.SimpleAspect)
	return pipe
def test_PipeAndFilter(pipe):
	msg = pipe.Execute(0)
	assert not msg == 0
	
def test_Aspects(pipeWaspect):
	msg = pipeWaspect.Execute(0)
	assert not msg == 0
	
def test_2Aspects(pipeW2Aspects):
	msg = pipeW2Aspects.Execute(0)
	assert not msg == 0

def test_retry():
	p = pipeline.Pipeline()
	f = pipeobj.RetryFilter()
	p.Register(f)
	p.addFilterAspect(pipeobj.RetryAspect)
	msg = pipeobj.TestMsg()
	p.Execute(msg)