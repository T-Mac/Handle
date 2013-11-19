import requests

class Dl_Bukkit(object):
	@staticmethod
	def get_cb_versions(channel = 'dev'):
		versions = []
		response = requests.get('http://dl.bukkit.org/api/1.0/downloads/projects/craftbukkit/artifacts/%s?_accept=application/json'%(channel))
		for item in response.json()['results']:
			versions.append((item['version'], item['file']))
		return versions