import configparser, os
import json
from datetime import datetime
from common import Globals

class Utils:
    PARSER = None
    BASEDIR = None

    @staticmethod
    def init(basedir):
        Utils.BASEDIR = basedir
        Utils.PARSER = configparser.ConfigParser()
        Utils.PARSER.read(os.path.join(basedir, Globals.Config.CONFIG_FOLDER, Globals.Config.CONFIG_FILE_NAME))

    @staticmethod
    def getConfig(section, config):
        try:
            return Utils.PARSER.get(section, config)
        except:
            return ""
    
    @staticmethod
    def getFileLocation(section, config):
        return os.path.join(Utils.BASEDIR, Utils.getConfig(section, config))

    @staticmethod
    def load_data():
        try:
            with open(Utils.getFileLocation(Globals.Config.Sections.FILES, Globals.Config.Sections.Files.PROJECTS), 'r') as f:
                projects_data = json.load(f)
            with open(Utils.getFileLocation(Globals.Config.Sections.FILES, Globals.Config.Sections.Files.RESOURCES), 'r') as f:
                resources_data = json.load(f)
            with open(Utils.getFileLocation(Globals.Config.Sections.FILES, Globals.Config.Sections.Files.HOLIDAYS), 'r') as f:
                holidays_data = json.load(f)

            for p in projects_data['projects']:
                p['start_date'] = datetime.fromisoformat(p['start_date'])
                p['end_date'] = datetime.fromisoformat(p['end_date'])
                for phase in p['phases']:
                    phase['from'] = datetime.fromisoformat(phase['from'])
                    phase['to'] = datetime.fromisoformat(phase['to'])

            for r in resources_data['resources']:
                if 'availability' in r and r['availability']:
                    availability = {
                        datetime.strptime(date, '%Y-%m-%d'): status
                        for date, status in r['availability'].items()
                    }
                    r['availability'] = availability
                else:
                    r['availability'] = {}

            for h in holidays_data['holidays']:
                h['date'] = datetime.strptime(h['date'], '%Y-%m-%d')

            return projects_data, resources_data, holidays_data

        except FileNotFoundError as e:
            print(f"Error loading data: {e}")
            return None, None, None
