"""
Modified 09/2017
@author pjb
"""

from configobj import ConfigObj

class PositionLoggerConfig(object):
    def __init__(self, config_file):
        try:
            config = ConfigObj(config_file)
            self.user = config["user"]
            self.password = config["pass"]
            self.server = config["server"]
            self.port = int(config["port"])
            self.keepalive = int(config["keepalive"])
            self.topic = config["topic"]
            self.qos = int(config["qos"])
            self.db_server = config["db_server"]
            self.db_port = int(config["db_port"])
            self.db_database = config["db_database"]
            self.db_collection = config["db_collection"]
        except KeyError:
            raise ConfigError("Invalid configuration given, missing a required option")
        except ValueError:
            raise ConfigError("Number expected but string given")

class ConfigError(Exception):
    """
        Exception for use if the config file does not contain the required items
    """
    pass

