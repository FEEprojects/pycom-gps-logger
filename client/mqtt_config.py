"""
    Basic config parser for details of an MQTT stream
    @author Philip Basford
"""

from configobj import ConfigObj

class MqttConfig(object):
    """
        Basic config for listening to an MQTT stream
    """
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
        except KeyError:
            raise ConfigError("Invalid configuration given, missing a required option")
        except ValueError:
            raise ConfigError("Number expected but string given")

class ConfigError(Exception):
    """
        Exception for use if the config file does not contain the required items
    """
    pass

