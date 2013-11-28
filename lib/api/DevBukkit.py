import requests
from bs4 import BeautifulSoup
import Folder
class Dev_Bukkit(object):
	@staticmethod
	def get_versions(name):
		filter = ['even', 'odd']
		r = requests.get('http://dev.bukkit.org/bukkit-plugins/' + name + '/files')
		soup = BeautifulSoup(r.text)
		rough_list = soup.find_all('tr',class_=filter)
		parsed = Dev_Bukkit.create_version_list(rough_list)
		return parsed
		
	@staticmethod	
	def create_version_list(rough_list):
		version_list = []
		for item in rough_list:
			file_url = item.find(class_='col-file').contents[0]['href'][16:]
			compat_versions = []
			for version in item.find(class_='comma-separated-list').contents:
				compat_versions.append(str(version.string).replace('CB ',''))
			version_list.append((file_url,compat_versions))
		return version_list
	
	@staticmethod
	def find_compat(plugin, cb_version):
		version_list = Dev_Bukkit.get_versions(plugin)
		for entry in version_list:
			for version in entry[1]:
				#print 'CB: %s - %s :VER'%(cb_version,version)
				if cb_version == version:
					deets = Dev_Bukkit.get_download_details(entry[0])
					return deets
		return False
	
	@staticmethod
	def get_download_details(url):
		r = requests.get('http://dev.bukkit.org/bukkit-plugins/' + url)
		soup = BeautifulSoup(r.text)
		rough = soup.dl.find_all('dd')
		url = rough[2].contents[0]['href']
		md5 = str(rough[4].contents[0])
		plugin = str(rough[2].contents[0].string)
		return (url, md5, plugin)
	