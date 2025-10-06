"""OBS integration plugin"""

import logging

logger = logging.getLogger(__name__)
import Config
from eventmanager import Evt
from monotonic import monotonic
from .obs_manager import NoOBSManager, OBSManager
import gevent.monkey
import obsws_python as obs
from RHUI import UIField, UIFieldType, UIFieldSelectOption


MODULE_NAME = "OBS_WS"


class OBS_Actions:
    START_RECORDING = "obs_start_record"  # Custom event for starting recording
    STOP_RECORDING = "obs_stop_record"  # Custom event for stopping recording

    def __init__(self, rhapi):
        self._rhapi = rhapi
        self.OBS = {}

    def emite_priority_message(self, message, interrupt=False):
        if interrupt:
            self._rhapi.ui.message_alert(message)
        else:
            self._rhapi.ui.message_alert(message)

    def disconectIfConnected(self):
        if self.OBS and isinstance(self.OBS, OBSManager):
            self.OBS.disconnect()
            self.OBS = NoOBSManager()
            logger.info("Disconnected from OBS server")
            return

    def do_ObsInitialize_fn(self, args):
        logger.info("def do_ObsInitialize_fn")
        global MODULE_NAME
        self.OBS = NoOBSManager()
        obs_enabled = self._rhapi.config.get(MODULE_NAME, "ENABLED")

        if not obs_enabled:
            logger.info("OBS Actions not enabled")
            self.OBS = NoOBSManager()
        if obs_enabled:
            module_conf = self._rhapi.config.get_all[MODULE_NAME]
            try:
                self.OBS = OBSManager(config=module_conf)
                logger.info("Connected to OBS server")
            except:
                logger.error("Error connecting to OBS server")
                self.OBS = NoOBSManager()
                self.emite_priority_message("Error conneting OBS server", True)

        logger.info(
            "do_ObsInitialize_fn DONE"
            + ", current instance of "
            + type(self.OBS).__name__
        )

    def format_name(self, template: str) -> str:
        """
        Replace placeholders in `template` with race context values.

        Supported placeholders:
            %eventName - Name of the event
            %heat      - Current heat name (or "PracticeMode" if none)
            %heatId    - ID of the current heat (0 if none)
            %class     - Race class name ("UNCLASSIFIED", "PracticeMode", or real class name)
            %classId   - Race class ID (0 if none)
            %round     - Current round number (empty if none)
        """
        rhdata = self._rhapi.race._racecontext.rhdata
        heat_id = self._rhapi.race.heat
        heat = rhdata.get_heat(heat_id) if heat_id else None

        round_num = self._rhapi.race.round if heat_id else ""
        event_name = rhdata.get_option("eventName")

        if not heat:
            heat_name, class_name, class_id = "PracticeMode", "", round_num
        else:
            heat_name = heat.display_name
            class_id = heat.class_id
            if class_id:
                class_name = rhdata.get_raceClass(class_id).name
            else:
                class_name = "UNCLASSIFIED"

        placeholders = {
            "%eventName": str(event_name),
            "%heat": heat_name,
            "%heatId": str(heat_id),
            "%class": class_name,
            "%classId": str(class_id),
            "%round": str(round_num),
        }

        for key, val in placeholders.items():
            template = template.replace(key, val)

        return template

    def do_start_recording(self, args=None):
        logger.info("do_start_recording")
        if not self.OBS.start():
            self.emite_priority_message("OBS: Start Recording Failed")

    def do_stop_recording(self, args=None):
        logger.info("do_stop_recording")
        if not self.OBS.stop():
            self.emite_priority_message("OBS: Stop Recording Failed")

    def read_time_before_start_ms(self):
        t_ms = self._rhapi.config.get(
            section=MODULE_NAME, name="PRE_START", as_int=True
        )
        return t_ms if t_ms >= 0 else 0

    def do_race_stage(self, args):
        logger.info("do_race_stage")

        # prepare OBS filename, inject RH data
        filename_template = self._rhapi.config.get(MODULE_NAME, "FILENAME")
        rh_filename = self.format_name(filename_template)
        self.OBS.set_filename(rh_filename)

        t_ms = 0
        t_ms = self.read_time_before_start_ms()

        # wait to before start
        while monotonic() < args["pi_starts_at_s"] - (t_ms / 1000):
            gevent.sleep(0.1)
        self._rhapi.events.trigger(self.START_RECORDING, None)

    def do_race_stop(self, args):
        if self.OBS:
            logger.info("do_race_stop")
            self._rhapi.events.trigger(self.STOP_RECORDING, None)
            # restore obs filename formating
            self.OBS.rollback_filename()

    def button_ConnectToOBS(self, args):
        if self.OBS and isinstance(self.OBS, OBSManager):
            logger.info("Already connected to OBS server")
            return
        elif (
            self.OBS
            and isinstance(self.OBS, NoOBSManager)
            and not self._rhapi.config.get(MODULE_NAME, "ENABLED")
        ):
            logger.info("Nothing to do, OBS Actions not enabled")
            return
        self.do_ObsInitialize_fn(None)

    def button_DisconnectFromOBS(self, args):
        if self.OBS and isinstance(self.OBS, OBSManager):
            self.OBS.disconnect()
            self.OBS = NoOBSManager()
            logger.info("Disconnected from OBS server")
        else:
            logger.info("Not connected to OBS server")
        logger.info(
            "Disconnect DONE" + ", current instance of " + type(self.OBS).__name__
        )


def initialize(rhapi):
    obs = OBS_Actions(rhapi)

    panelName = MODULE_NAME + "options"
    rhapi.config.register_section(MODULE_NAME)
    rhapi.ui.register_panel(panelName, MODULE_NAME + " Actions", "settings", order=0)

    # Register to events
    rhapi.events.on(
        Evt.STARTUP,
        obs.do_ObsInitialize_fn,
        default_args=None,
        priority=101,
        unique=True,
        name=MODULE_NAME,
    )
    rhapi.events.on(
        Evt.RACE_STOP,
        obs.do_race_stop,
        default_args=None,
        priority=101,
        unique=True,
        name=MODULE_NAME,
    )
    rhapi.events.on(
        Evt.LAPS_CLEAR,
        obs.do_race_stop,
        default_args=None,
        priority=101,
        unique=True,
        name=MODULE_NAME,
    )
    rhapi.events.on(
        Evt.RACE_STAGE,
        obs.do_race_stage,
        default_args=None,
        priority=101,
        unique=True,
        name=MODULE_NAME,
    )
    rhapi.events.on(
        obs.START_RECORDING,
        obs.do_start_recording,
        default_args=None,
        priority=101,
        unique=True,
        name=MODULE_NAME,
    )
    rhapi.events.on(
        obs.STOP_RECORDING,
        obs.do_stop_recording,
        default_args=None,
        priority=101,
        unique=True,
        name=MODULE_NAME,
    )

    # Register Buttons in the panel
    rhapi.ui.register_quickbutton(
        panelName,
        MODULE_NAME + "connect_to_obs",
        "Connect to OBS Server",
        obs.button_ConnectToOBS,
    )
    rhapi.ui.register_quickbutton(
        panelName,
        MODULE_NAME + "disconnect_from_obs",
        "Disconnect from OBS Server",
        obs.button_DisconnectFromOBS,
    )

    # Register configuration options
    rhapi.fields.register_option(
        UIField(
            "HOST",
            "OBS IP",
            UIFieldType.TEXT,
            persistent_section=MODULE_NAME,
            value="localhost",
        ),
        panelName,
    )
    rhapi.fields.register_option(
        UIField(
            "PORT",
            "Port",
            UIFieldType.NUMBER,
            persistent_section=MODULE_NAME,
            value=4455,
        ),
        panelName,
    )
    rhapi.fields.register_option(
        UIField(
            "PASSWORD",
            "Password",
            UIFieldType.PASSWORD,
            persistent_section=MODULE_NAME,
            value="YourPassword",
        ),
        panelName,
    )
    rhapi.fields.register_option(
        UIField(
            "PRE_START",
            "Pre start (ms)",
            UIFieldType.NUMBER,
            persistent_section=MODULE_NAME,
            value=1000,
        ),
        panelName,
    )
    rhapi.fields.register_option(
        UIField(
            "FILENAME",
            "Filename template (optional)",
            UIFieldType.TEXT,
            persistent_section=MODULE_NAME,
            value="%CCYY%MM%DD_%class-%heat-%round",
        ),
        panelName,
    )
    rhapi.fields.register_option(
        UIField(
            "ENABLED",
            "Enable OBS Actions",
            UIFieldType.CHECKBOX,
            persistent_section=MODULE_NAME,
            value=False,
        ),
        panelName,
    )
