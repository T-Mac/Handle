import json
import urllib2
import uuid

def checkin(id):
	try:
		result=urllib2.urlopen('http://localhost:5000/checkin?id=%s' %id).read()
		return True
	except:
		pass
	return False
	
def has_internet():
	try:
		response=urllib2.urlopen('http://74.125.134.100',timeout=5)
		return True
	except urllib2.URLError as err: pass
	return False
	
def gen_id():
	return uuid.uuid4().hex