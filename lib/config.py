import yaml

def load_server_config(config = 'default' , section = None, keys=[]):
	with open('config/%s/handle.yml'%config, 'r') as configfile:
		file = yaml.load(configfile)
		values = {}
		if keys and section:
			for key in keys:
				values[key] = file[section][key]
		if section and not keys:
			values = file[section]
		if not section and not keys:
			values = file
		return values
		
		
		