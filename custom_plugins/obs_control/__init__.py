'''OBS integration plugin'''

import logging
logger = logging.getLogger(__name__)
import Config
from eventmanager import Evt
from monotonic import monotonic
from .obs_manager import NoOBSManager, OBSManager
import gevent.monkey
import obsws_python as obs


MODULE_NAME = 'OBS_WS'


class OBS_Actions():
    def __init__(self, rhapi):
        self._rhapi = rhapi
        self.OBS = {}
        self.time_before_start_ms = 0
        

    def emite_priority_message(self, message, interrupt = False):
        if interrupt:
            self._rhapi.ui.message_alert(message)
        else:
            self._rhapi.ui.message_alert(message)


    def do_ObsInitialize_fn(self, args):
        logger.info("def do_ObsInitialize_fn" )
        global MODULE_NAME
        self.OBS = NoOBSManager()

        ######### REGISTER MODULE #########  TOOD: move to UI
        config = self._rhapi.config
        config.register_section(MODULE_NAME)
        config.set(MODULE_NAME, "HOST", "localhost")
        config.set(MODULE_NAME, "PORT", 4455)
        config.set(MODULE_NAME, "PASSWORD", "YourPassword")
        config.set(MODULE_NAME, "ENABLED", True)  
        config.set(MODULE_NAME, "PRE_START", 2000)  
       
        config = self._rhapi.config.get_all

        if  config[MODULE_NAME]:
            module_conf = config[MODULE_NAME] 
            if      'HOST' in module_conf      \
                and 'PORT' in module_conf      \
                and 'PASSWORD' in module_conf  \
                and 'ENABLED' in module_conf   \
                and module_conf['ENABLED'] == True:
                try:
                    self.OBS = OBSManager(config=module_conf)
                except:
                    logger.error("OBS: Error connecting to OBS server")
                    self.OBS = NoOBSManager()
                    self.emite_priority_message('Error conneting OBS server', True)
            if 'PRE_START' in module_conf:
                self.time_before_start_ms = module_conf['PRE_START'] 
        logger.info("do_ObsInitialize_fn DONE" )


    def do_race_start(self , args=None):
        logger.info("do_race_start")
        if not self.OBS.start():
            self.emite_priority_message("OBS: Start Recording Failed")


    def do_race_stage(self, args):
        logger.info("do_race_stage")
        #wait to before start
        while (monotonic() < args['pi_starts_at_s'] - (self.time_before_start_ms/1000)):
            gevent.sleep(0.1)
        self.do_race_start()


    def do_race_stop(self, args):
        logger.info("do_race_stop")
        if not self.OBS.stop():
            self.emite_priority_message("OBS: Stop Recording Failed")


def initialize(rhapi):
    obs = OBS_Actions(rhapi)
    rhapi.events.on(Evt.STARTUP    , obs.do_ObsInitialize_fn  , default_args=None, priority=101, unique=True, name=MODULE_NAME)
    rhapi.events.on(Evt.RACE_STOP  , obs.do_race_stop         , default_args=None, priority=101, unique=True, name=MODULE_NAME)
    rhapi.events.on(Evt.RACE_STAGE , obs.do_race_stage        , default_args=None, priority=101, unique=True, name=MODULE_NAME)

