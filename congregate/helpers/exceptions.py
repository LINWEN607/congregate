class ConfigurationException(Exception):
    def __init__(self, failed_config):
        Exception.__init__(self,"Incorrect configuration found in {}".format(failed_config)) 
