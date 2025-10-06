import logging
import obsws_python as obs

logger = logging.getLogger(__name__)


class NoOBSManager:
    def __init__(self):
        pass

    def isEnabled(self):
        return False

    def start(self):
        return True

    def stop(self):
        return True

    def set_filename(self, fmt):
        return True

    def rollback_filename(self):
        return True


class OBSManager:
    rc = None
    config = {}
    obs_version = None
    obs_web_socket_version = None
    obs_filename_base = None

    def __init__(self, config):
        self.config = config
        self.connect()

    def connect(self):
        try:
            logger.info("OBS: (Re)connecting...")
            self.rc = obs.ReqClient(
                host=self.config["HOST"],
                port=self.config["PORT"],
                password=self.config["PASSWORD"],
                timeout=5,
            )
            version_info = self.rc.get_version()
            self.obs_version = version_info.obs_version
            self.obs_web_socket_version = version_info.obs_web_socket_version
            self.obs_filename_base = self._get_current_filename()
            logger.info(
                f"OBS: Connected to configured instance. Obs-websocket Version: {self.obs_web_socket_version}, OBS Studio Version: {self.obs_version}"
            )
        except Exception as e:
            logger.error("OBS: Error connecting to configured instance")
            logger.error(e)

    def disconnect(self):
        try:
            self.rc.disconnect()
        except:
            logger.error("OBS: Error disconnecting from configured instance")

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
            if self.rc is None:
                return True

            RStatus = self.rc.get_record_status()  # retuns GetRecordStatusDataclass
            if RStatus.output_active is True:
                self.rc.stop_record()
                logger.info("OBS: Recording Stoppped")
        except:
            self.connect()
            try:
                RStatus = self.rc.get_record_status()  # retuns GetRecordStatusDataclass
                if RStatus.output_active is True:
                    self.rc.stop_record()
                    logger.info("OBS: Recording Stoppped")
            except:
                logger.error("OBS: Stop Recording Failed")
                return False
        return True

    def _apply_filename(self, fmt):
        try:
            self.rc.set_profile_parameter("Output", "FilenameFormatting", fmt)
        except:
            self.connect()
            try:
                self.rc.set_profile_parameter("Output", "FilenameFormatting", fmt)
            except:
                return False
        return True

    def set_filename(self, fmt):
        if self._apply_filename(fmt):
            logger.info("OBS: Filename formatting set to" + fmt)
            return True
        else:
            logger.error("OBS: Setting Filename formatting Failed")
            return False

    def rollback_filename(self):
        file_name = self.obs_filename_base
        if self._apply_filename(file_name):
            logger.info("OBS: Filename formatting rolled back to " + file_name)
            return True
        else:
            logger.error("OBS: Rolling back Filename formatting Failed")
            return False

    def _get_current_filename(self):
        try:
            # Saves the OLD formating
            resp = self.rc.get_profile_parameter("Output", "FilenameFormatting")
            currentFilenameFormatting = resp.parameter_value
            return currentFilenameFormatting
        except:
            logger.error("OBS: Getting Filename formatting Failed")
            return "%CCYY%MM%DD"  # OBS default
        return ""
