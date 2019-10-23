import configparser
import sys, os


# Append the directory in which this file exists to the
# path of the configuration file

TEST_CONFIGURATION_FILE=os.path.join(os.path.dirname(os.path.abspath(__file__)),"configuration.txt")


class TestConfig:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(TEST_CONFIGURATION_FILE)



    def get(self,section,configName)->str:
        try:
            ret_val=self.config[section][configName]	
        except: # if the key is not found return None
            ret_val=None
        return ret_val




