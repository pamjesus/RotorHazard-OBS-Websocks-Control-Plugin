import logging
import obsws_python as obs

logger = logging.getLogger(__name__)

class NoOBSManager():
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
    
    def get_current_filename(self):
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


        

    def set_filename(self, fmt):
        try:
            self.rc.set_profile_parameter("Output","FilenameFormatting", fmt)
            logger.info("OBS: Filename formatting set to "+fmt)
        except:
            self.connect()
            try:
                self.rc.set_profile_parameter("Output","FilenameFormatting", fmt)
                logger.info("OBS: Filename formatting set to "+fmt)
            except:
                logger.error("OBS: Setting Filename formatting Failed")
                return False
        return True

    def get_current_filename(self):
        try:
            #Saves the OLD formating
            resp = self.rc.get_profile_parameter("Output","FilenameFormatting")
            currentFilenameFormatting = resp.parameter_value
            return currentFilenameFormatting
        except:
            self.connect()
            try:
                resp = self.rc.get_profile_parameter("Output","FilenameFormatting")
                currentFilenameFormatting = resp.parameter_value
                return currentFilenameFormatting
            except:
                logger.error("OBS: Getting Filename formatting Failed")
                return ""
        return ""