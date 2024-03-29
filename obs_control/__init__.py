'''OBS integration plugin'''

import logging
logger = logging.getLogger(__name__)
import Config
from eventmanager import Evt
from monotonic import monotonic
from .obs_manager import NoOBSManager, OBSManager
import gevent.monkey
import obsws_python as obs
import RHAPI

OBS = {}
RH_API : RHAPI = None
MODULE_NAME = 'OBS_WS'
time_before_start_ms = 0


def emite_priority_message(message, interrupt = False):
    ''' Emits message to clients '''
    RH_API.emit_priority_message(message, interrupt)


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
    global RH_API
    RH_API = kwargs['RHAPI'] 
    if 'Events' in kwargs:
        kwargs['Events'].on(Evt.STARTUP, 'ObsInitialize', do_ObsInitialize_fn, {}, 101 )
        kwargs['Events'].on(Evt.RACE_STOP, 'ObsRaceStop', do_race_stop, {}, 101 )
        kwargs['Events'].on(Evt.RACE_STAGE, 'ObsRaceStage', do_race_stage, {}, 101 )
