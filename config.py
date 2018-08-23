import os

from ConfigParser import SafeConfigParser

containing_dir = os.path.abspath(os.path.dirname(__file__))
cfg_file = SafeConfigParser()
path_to_cfg = os.path.join(containing_dir, 'config.cfg')
cfg_file.read(path_to_cfg)


class ConfigSection(object):
    def __init__(self, section, keys):
        for key in keys:
            setattr(self, key, cfg_file.get(section, key))


reddit = ConfigSection('reddit', ('username',
                                  'password',
                                  'app_key',
                                  'app_secret',
                                  'subreddit'))

heatware = ConfigSection('heatware', ('link_id',
                                      'reply',
                                      'regex'))
