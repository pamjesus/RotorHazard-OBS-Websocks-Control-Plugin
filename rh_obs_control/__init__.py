'''OBS integration plugin'''

import logging
logger = logging.getLogger(__name__)
import Config
from eventmanager import Evt
from monotonic import monotonic
import gevent.monkey
import obsws_python as obs

OBS = {}
SOCKET_IO = None
MODULE_NAME = 'OBS_WS'
time_before_start_ms = 0

class NoOBSManager():
    def __init__(self):
        pass

    def isEnabled(self):
        return False

    def start(self):
        return True

    def stop(self):
        return True

class OBSManager():
    rc = None
    config = {} 
    
    def __init__(self, config):
        self.config=config
        self.connect()
        
    def connect(self):
        try:        
            logger.info("OBS: (Re)connecting...")
            self.rc = obs.ReqClient(host=self.config['HOST'], port=self.config['PORT'], password=self.config['PASSWORD'])        
        except:
            logger.error("OBS: Error connecting to configured instance")


    def isEnabled(self):
        return True

    def start(self):
        try:
            self.rc.start_record()
            logger.info("OBS: Recording Started")
        except:
            self.connect()          
            try:
                self.rc.start_record()
                logger.info("OBS: Recording Started")
            except:
                logger.error("OBS: Start Recording Failed")
                return False    
        return True

    def stop(self):
        try:
            self.rc.stop_record()
            logger.info("OBS: Recording Stoppped")
        except:
            self.connect()          
            try:
                self.rc.stop_record()
                logger.info("OBS: Recording Stoppped")
            except:
                logger.error("OBS: Stop Recording Failed")
                return False
        return True


def emite_priority_message(message, interrupt = False):
    ''' Emits message to clients '''
    emit_payload = {
        'message': message,
        'interrupt': interrupt
    }
    SOCKET_IO.emit('priority_message', emit_payload)


def do_ObsInitialize_fn(args):
    ''' Initialize OBS connection '''
    logger.info("def do_ObsInitialize_fn" )
    global OBS, time_before_start_ms
    OBS = NoOBSManager()
    if hasattr(Config, 'ExternalConfig') and MODULE_NAME in Config.ExternalConfig:
        module_conf = Config.ExternalConfig [MODULE_NAME] 
        if      'HOST' in module_conf      \
            and 'PORT' in module_conf      \
            and 'PASSWORD' in module_conf  \
            and 'ENABLED' in module_conf   \
            and module_conf['ENABLED'] == True:
            try:
                OBS = OBSManager(config=module_conf)
            except:
                logger.error("OBS: Error connecting to OBS server")
                OBS = NoOBSManager()
                emite_priority_message('Error conneting OBS server', True)
        if 'PRE_START' in module_conf:
            time_before_start_ms = module_conf['PRE_START'] 
    logger.info("do_ObsInitialize_fn DONE" )


def do_race_start(args):
    logger.info("do_race_start")
    if not OBS.start():
        emite_priority_message("OBS: Start Recording Failed")


def do_race_stop(args):
    logger.info("do_race_stop")
    if not OBS.stop():
        emite_priority_message("OBS: Stop Recording Failed")


def do_race_stage(args):
    logger.info("do_race_stage")
    #wait to before start
    while (monotonic() < args['pi_starts_at_s'] - (time_before_start_ms/1000)):
        gevent.sleep(0.1)
    do_race_start(args)


def initialize(**kwargs):
    global SOCKET_IO
    SOCKET_IO = kwargs['SOCKET_IO']
    if 'Events' in kwargs:
        kwargs['Events'].on(Evt.STARTUP, 'ObsInitialize', do_ObsInitialize_fn, {}, 101 )
        kwargs['Events'].on(Evt.RACE_STOP, 'ObsRaceStop', do_race_stop, {}, 101 )
        kwargs['Events'].on(Evt.RACE_STAGE, 'ObsRaceStage', do_race_stage, {}, 101 )
