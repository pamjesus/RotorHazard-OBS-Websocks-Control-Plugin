'''OBS integration plugin'''

import logging
logger = logging.getLogger(__name__)
import Config
from eventmanager import Evt
from monotonic import monotonic
from .obs_manager import NoOBSManager, OBSManager
import gevent.monkey
import obsws_python as obs
from RHUI import UIField, UIFieldType, UIFieldSelectOption


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

        config = self._rhapi.config.get_all
        if config and not MODULE_NAME in set(config):
            ######## REGISTER MODULE #########  TOOD: move to UI
            api_config = self._rhapi.config
            api_config.register_section(MODULE_NAME)
            api_config.set(MODULE_NAME, "HOST", "localhost")
            api_config.set(MODULE_NAME, "PORT", 4455)
            api_config.set(MODULE_NAME, "PASSWORD", "YourPassword")
            api_config.set(MODULE_NAME, "ENABLED", False)  
            api_config.set(MODULE_NAME, "PRE_START", 1000) 
            api_config.set(MODULE_NAME, "FILENAME", "%CCYY-%MM-%DD_%hh-%mm-%ss_CAAR_%Class-%Heat-%Round")
            #api_config.set(MODULE_NAME, "DIRNAME", "")
            #################################
            logger.info("Module "+MODULE_NAME+"inicializado")

        config = self._rhapi.config.get_all
        if  config and MODULE_NAME in config:
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
            else:
                self.OBS = NoOBSManager()

            if 'PRE_START' in module_conf:
                t_ms = self._rhapi.config.get(section=MODULE_NAME, name='PRE_START', as_int=True)
                self.time_before_start_ms = t_ms if t_ms >=0 else 0
        
        logger.info("do_ObsInitialize_fn DONE" + ", current instance of " + type(self.OBS).__name__)


    def format_name(self, template):
        """
        Formats a name string by replacing template placeholders with race context values.
        Args:
            template (str): The template string containing placeholders such as
                %heat, %heatId, %class, %classId, and %round.
        Returns:
            str: The formatted string with placeholders replaced by actual race data.
        Placeholders:
            %heat    - Name of the current heat (empty string if no heat).
            %heatId  - ID of the current heat (0 if no heat).
            %class   - Name of the race class (or "PracticeMode" if no heat).
            %classId - ID of the race class (0 if no heat).
            %round   - Current round number.
        """
        Rhdata = self._rhapi.race._racecontext.rhdata
        heat_id = self._rhapi.race.heat
        Heat = Rhdata.get_heat(heat_id) if heat_id != 0 else None
        heat_name = Heat.name if heat_id != 0 else ""
        class_name = Rhdata.get_raceClass(Heat.class_id).name if heat_id != 0 else "PracticeMode"
        class_id =  Heat.class_id if heat_id != 0 else 0
        round_num = self._rhapi.race.round if heat_id != 0 else ""
        #print((heat_id, heat_name, class_id, class_name, round_num) )
        
        result = (
            template.replace("%heat", heat_name)
            .replace("%heatId", str(heat_id))
            .replace("%class", class_name)
            .replace("%classId", str(class_id))
            .replace("%round", str(round_num))
        )

        return result  
        

    def do_race_start(self , args=None):
        logger.info("do_race_start")
        if not self.OBS.start():
            self.emite_priority_message("OBS: Start Recording Failed")


    def do_race_stage(self, args):
        logger.info("do_race_stage")

        #prepare OBS filename, inject RH data
        self.currentFilenameFormatting = self.OBS.get_current_filename()
        filename_base = self._rhapi.config.get(MODULE_NAME, "FILENAME")  
        rh_filename =  self.format_name( filename_base )  
        self.OBS.set_filename(rh_filename)

        #wait to before start
        while (monotonic() < args['pi_starts_at_s'] - (self.time_before_start_ms/1000)):
            gevent.sleep(0.1)
        self.do_race_start()


    def do_race_stop(self, args):
        logger.info("do_race_stop")
        if not self.OBS.stop():
            self.emite_priority_message("OBS: Stop Recording Failed")
        #restore obs filename formating
        self.OBS.set_filename( self.currentFilenameFormatting )



    def setSettings(self, args):  
        config = self._rhapi.config.get_all
        
        #Initialize MODULE if Needed
        if not config[MODULE_NAME]:
            config.register_section(MODULE_NAME)
            logger.info("Module inicializado")

        #Apply setthings to RHAPI Config
        config = self._rhapi.config
        config.set(MODULE_NAME, "HOST"       , self._rhapi.db.option("obs_hostname"))
        config.set(MODULE_NAME, "PORT"       , int(self._rhapi.db.option("obs_port")) )
        config.set(MODULE_NAME, "PASSWORD"   , self._rhapi.db.option("obs_password") )
        config.set(MODULE_NAME, "ENABLED"    , ( True if str(self._rhapi.db.option("obs_enabled")) == "1" else False ) ) 
        config.set(MODULE_NAME, "PRE_START"  , int(self._rhapi.db.option("obs_pre_start")) )
        config.set(MODULE_NAME, "FILENAME"   , str(self._rhapi.db.option("obs_filename")))

        logger.info("OBS Websocks settings applied")

        if config.get(MODULE_NAME, "ENABLED") == False and isinstance(self.OBS, OBSManager):
            self.disconnectFromOBS(None)
        
        if config.get(MODULE_NAME, "ENABLED") == True and isinstance(self.OBS, NoOBSManager):
            self.do_ObsInitialize_fn(None)
            if isinstance(self.OBS, NoOBSManager):
                self.emite_priority_message("OBS: Error connecting to OBS server", True)
                logger.info("OBS: Connected to OBS server")
            else:
                logger.info("OBS: Connected to OBS server")

    def disconnectFromOBS(self, args):
        if self.OBS and isinstance(self.OBS, OBSManager):
            self.OBS.disconnect()
            self.OBS = NoOBSManager()
            logger.info("Disconnected from OBS server")
            return
        logger.info("Not connected to OBS server")
        

def initialize(rhapi):
    obs = OBS_Actions(rhapi)
    rhapi.events.on(Evt.STARTUP    , obs.do_ObsInitialize_fn  , default_args=None, priority=101, unique=True, name=MODULE_NAME)
    rhapi.events.on(Evt.RACE_STOP  , obs.do_race_stop         , default_args=None, priority=101, unique=True, name=MODULE_NAME)
    rhapi.events.on(Evt.RACE_STAGE , obs.do_race_stage        , default_args=None, priority=101, unique=True, name=MODULE_NAME)
 
    panelName = MODULE_NAME + 'options'
    rhapi.ui.register_panel( panelName, MODULE_NAME + ' Actions', 'settings', order=0)
    rhapi.fields.register_option(UIField('obs_hostname', 'OBS IP', UIFieldType.TEXT), panelName)
    rhapi.fields.register_option(UIField('obs_port', 'Port', UIFieldType.NUMBER, value=4455), panelName)
    rhapi.fields.register_option(UIField('obs_password', 'Password', UIFieldType.PASSWORD), panelName)
    rhapi.fields.register_option(UIField('obs_pre_start', 'Pre start (ms)',  UIFieldType.NUMBER, value = 0), panelName)
    rhapi.fields.register_option(UIField('obs_filename', 'Filename template (optional)', UIFieldType.TEXT), panelName)
    rhapi.fields.register_option(UIField('obs_enabled', 'Enable OBS Actions', UIFieldType.CHECKBOX), panelName)
    UIField('obs_enabled', 'Enable OBS Actions', UIFieldType.CHECKBOX, options=[UIFieldSelectOption('1', 'Enabled'), UIFieldSelectOption('0', 'Disabled')])

    # Register Buttons in the panel
    rhapi.ui.register_quickbutton(panelName, 'generate_connectin_file', 'Apply Connection Settings', obs.setSettings)
    rhapi.ui.register_quickbutton(panelName, 'connect_to_obs', 'Connect to OBS Server', obs.do_ObsInitialize_fn)
    rhapi.ui.register_quickbutton(panelName, 'disconnect_from_obs', 'Disconnect from OBS Server', obs.disconnectFromOBS)

  