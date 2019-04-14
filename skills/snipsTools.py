import configparser
import io
import json
import re

ENCODING_FORMAT = "utf-8"

class SnipsConfigParser(configparser.ConfigParser):
    def to_dict(self):
        return {
            section: {
                option_name : option for option_name, option in self.items(section)
            } for section in self.sections()
        }

    @staticmethod
    def read_configuration_file(configuration_file):
        try:
            with io.open(configuration_file, encoding=ENCODING_FORMAT) as f:
                conf_parser = SnipsConfigParser()
                conf_parser.readfp(f)
                return conf_parser.to_dict()
        except (IOError, ConfigParser.Error) as e:
            print(e)
            return dict()

    @staticmethod
    def write_configuration_file(configuration_file, data):
        conf_parser = SnipsConfigParser()
        for key in data.keys():
            conf_parser.add_section(key)
            for inner_key in data[key].keys():
                conf_parser.set(key, inner_key, data[key][inner_key])
        try:
            with open(configuration_file, 'w') as f:
                conf_parser.write(f)
        except (IOError, configparser.Error) as e:
            print(e)
            return False

class SnipsI18n(object):
    __dic = {}

    __path = None
    __locale = None

    def __init__(self, path, locale = 'en_US'):
        self.__path = path
        self.__locale = locale
        self.__load_dictionary()

    def __load_dictionary(self):
        dir = '{}/{}.json'.format(self.__path, self.__locale)
        try:
            with open(dir, 'r', encoding=ENCODING_FORMAT) as f:
                self.__dic = json.loads(f.read())
        except IOError as e:
            print (e)

    def get(self, raw_key, parameters = {}):
        keys = raw_key.split('.')
        temp = self.__dic

        for key in keys:
            temp = temp.get(key, 'null')

        if not parameters or temp == 'null':
            return temp
        else:
            for key in parameters:
                pattern = '(\{){2}(\s)*(' + key +'){1}(\s)*(\}){2}'
                temp = re.sub(pattern, str(parameters[key]), temp)
            return temp