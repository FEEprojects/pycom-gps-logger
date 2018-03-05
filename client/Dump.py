#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created 10/2017
@author pjb
"""
import json
import logging
from optparse import OptionParser, OptionGroup

from pymongo import MongoClient
from position_config import PositionLoggerConfig

DEFAULT_TARGET = "positions.json"
DEFAULT_CONFIG = "position-config.ini"
DEFAULT_LOG_LEVEL = logging.INFO
CONFIG = None
DB = None
DB_CLIENT = None

class PositionLogDump(object):

    def __init__(self, log_level, config_file):
        self.logger = logging.getLogger()
        self.logger.setLevel(log_level)
        config = PositionLoggerConfig(config_file)
        self.db_server = config.db_server
        self.db_port = config.db_port
        self.db_database = config.db_database
        self.db_collection = config.db_collection
        self.db_client = None
        self.db = None
        self.collection = None
        self.logger.info("DB Server: " + self.db_server)
        self.logger.info("DB Port: " + str(self.db_port))
        self.logger.info("DB Database: " + str(self.db_database))
        self.logger.info("DB Collection: " + str(self.db_collection))



    def connect(self):
        self.db_client = MongoClient(self.db_server, self.db_port)
        self.db = self.db_client[self.db_database]
        self.collection = self.db[self.db_collection]

    def dump(self, filename):
        self.logger.info("Filename: " + filename)
        self.connect()
        new_data = []
        positions = self.collection.find()
        for pos in positions:
            p = {}
            p["lat"] = pos["lat"]
            p["lon"] = pos["lon"]
            p["hdop"] = pos["hdop"]
            p["alt"] = pos["alt"]
            p["timestamp"] = pos["timestamp"]
            p["gateways"] = []
            for gw in pos["gateways"]:
                n_gw = {}
                n_gw["GatewayId"] = "lora_" + gw["gw_id"].split("-")[1]
                n_gw["Rssi"] = gw["rssi"]
                n_gw["Snr"] = gw["snr"]
                try:
                    n_gw["AntennaId"] = gw["antenna"]
                except KeyError:    #antenna ID not stored
                    n_gw["AntennaId"] = 0 #Default to antenna ID 0
                try:
                    n_gw["fine_timestamp"] = gw["fine_timestamp"]
                except:
                    n_gw["fine_timestamp"] = None
                try:
                    n_gw["timestamp"] = gw["timestamp"]
                except:
                    n_gw["timestamp"] = None
                p["gateways"].append(n_gw)
            new_data.append(p)
        f = open(filename, "w")
        f.write(json.dumps(new_data, default=str))
        f.close()
        self.logger.info("Dumped %d records", len(new_data))

if __name__ == "__main__":
    PARSER = OptionParser()
    LOG_LEVEL = DEFAULT_LOG_LEVEL
    logging.basicConfig(format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    LOG_GROUP = OptionGroup(
        PARSER, "Verbosity Options",
        "Options to change the level of output")
    LOG_GROUP.add_option(
        "-q", "--quiet", action="store_true",
        dest="quiet", default=False,
        help="Supress all but critical errors")
    LOG_GROUP.add_option(
        "-v", "--verbose", action="store_true",
        dest="verbose", default=False,
        help="Print all information available")
    PARSER.add_option_group(LOG_GROUP)
    PARSER.add_option(
        "-c", "--config", action="store",
        type="string", dest="config_file",
        help="Configuration file description options needed")
    PARSER.add_option(
        "-f", "--filename", action="store",
        type="string", dest="target_file",
        help="Dump destination file")
    (OPTIONS, ARGS) = PARSER.parse_args()
    if OPTIONS.quiet:
        LOG_LEVEL = logging.CRITICAL
    elif OPTIONS.verbose:
        LOG_LEVEL = logging.DEBUG
    if OPTIONS.config_file is None:
        CONFIG_FILE = DEFAULT_CONFIG
    else:
        CONFIG_FILE = OPTIONS.config_file
    if OPTIONS.target_file is None:
        TARGET_FILE = DEFAULT_TARGET
    else:
        TARGET_FILE = OPTIONS.target_file
    DUMPER = PositionLogDump(LOG_LEVEL, CONFIG_FILE)
    DUMPER.dump(TARGET_FILE)

