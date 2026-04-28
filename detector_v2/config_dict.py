import json

class DetectorConfig:
    config : dict = None
    file_name : str = "UNKNOWN"

    ENTRY_DICT_NAME                 = "name"
    ENTRY_DICT_MINIMUM              = "min"
    ENTRY_DICT_MAXIMUM              = "max"
    ENTRY_DICT_TYPE                 = "type"
    ENTRY_DICT_DEFAULT              = "default"

    #########################################################################
    DETECTOR_TRIGGER_THRESHOLD      = {ENTRY_DICT_NAME      :   "thresh",
                                       ENTRY_DICT_MINIMUM   :   0.0,
                                       ENTRY_DICT_TYPE      :   float,
                                       ENTRY_DICT_DEFAULT   :   100000.0}
    #########################################################################
    DETECTOR_RECORD_BEFORE_SECONDS  = {ENTRY_DICT_NAME      :   "pre",
                                       ENTRY_DICT_MINIMUM   :   0.0,
                                       ENTRY_DICT_TYPE      :   float,
                                       ENTRY_DICT_DEFAULT   :   1.0}
    #########################################################################
    DETECTOR_RECORD_AFTER_SECONDS   = {ENTRY_DICT_NAME      :   "post",
                                       ENTRY_DICT_MINIMUM   :   0.5,
                                       ENTRY_DICT_TYPE      :   float,
                                       ENTRY_DICT_DEFAULT   :   1.0}
    #########################################################################
    DETECTOR_SAVE_RESOLUTION_X      = {ENTRY_DICT_NAME      :   "res_x",
                                       ENTRY_DICT_TYPE      :   int,
                                       ENTRY_DICT_DEFAULT   :   320,
                                       ENTRY_DICT_MINIMUM   :   32,
                                       ENTRY_DICT_MAXIMUM   :   3200}
    #########################################################################
    DETECTOR_SAVE_RESOLUTION_Y      = {ENTRY_DICT_NAME      :   "res_y",
                                       ENTRY_DICT_TYPE      :   int,
                                       ENTRY_DICT_DEFAULT   :   240,
                                       ENTRY_DICT_MINIMUM   :   24,
                                       ENTRY_DICT_MAXIMUM   :   2400}
    #########################################################################
    DETECTOR_FRAMES_PER_SECOND      = {ENTRY_DICT_NAME      :   "fps",
                                       ENTRY_DICT_MINIMUM   :   1,
                                       ENTRY_DICT_MAXIMUM   :   144,
                                       ENTRY_DICT_TYPE      :   int,
                                       ENTRY_DICT_DEFAULT   :   20}
    #########################################################################
    DETECTOR_RECORD_SAMPLE_RATE     = {ENTRY_DICT_NAME      :   "sample_rate",
                                       ENTRY_DICT_MINIMUM   :   1000,
                                       ENTRY_DICT_MAXIMUM   :   100000,
                                       ENTRY_DICT_TYPE      :   int,
                                       ENTRY_DICT_DEFAULT   :   44100}
    #########################################################################
    DETECTOR_RECORD_BLOCK_LENGTH    = {ENTRY_DICT_NAME      :   "audio_block_size",
                                       ENTRY_DICT_MINIMUM   :   0.01,
                                       ENTRY_DICT_MAXIMUM   :   10.0,
                                       ENTRY_DICT_TYPE      :   float,
                                       ENTRY_DICT_DEFAULT   :   0.1}
    #########################################################################
    DETECTOR_INTERPRETATION_MODULO  = {ENTRY_DICT_NAME      :   "mod",
                                       ENTRY_DICT_MINIMUM   :   1,
                                       ENTRY_DICT_MAXIMUM   :   1000,
                                       ENTRY_DICT_TYPE      :   int,
                                       ENTRY_DICT_DEFAULT   :   3}
    #########################################################################
    DETECTOR_AUDIO_MODULO           = {ENTRY_DICT_NAME      :   "amod",
                                       ENTRY_DICT_MINIMUM   :   1,
                                       ENTRY_DICT_MAXIMUM   :   1000,
                                       ENTRY_DICT_TYPE      :   int,
                                       ENTRY_DICT_DEFAULT   :   3}
    #########################################################################
    DETECTOR_DIFF_AUDIO_MOD         = {ENTRY_DICT_NAME      :   "amod_diff",
                                       ENTRY_DICT_TYPE      :   bool,
                                       ENTRY_DICT_DEFAULT   :   False}
    #########################################################################
    DETECTOR_IN_DEBUG               = {ENTRY_DICT_NAME      :   "in_debug",
                                       ENTRY_DICT_TYPE      :   bool,
                                       ENTRY_DICT_DEFAULT   :   False}
    #########################################################################
    DETECTOR_DEBUG_UPDATE_FREQ      = {ENTRY_DICT_NAME      :   "debug_update_freq",
                                       ENTRY_DICT_MINIMUM   :   0.1,
                                       ENTRY_DICT_TYPE      :   float,
                                       ENTRY_DICT_DEFAULT   :   10.0}
    #########################################################################
    DETECTOR_CONFIG_REFRESH_RATE    = {ENTRY_DICT_NAME      :   "config_refresh_rate",
                                       ENTRY_DICT_MINIMUM   :   1,
                                       ENTRY_DICT_MAXIMUM   :   1000000,
                                       ENTRY_DICT_TYPE      :   int,
                                       ENTRY_DICT_DEFAULT   :   100}
    #########################################################################
    DETECTOR_HEARTBEAT_RATE         = {ENTRY_DICT_NAME      :   "heartbeat_rate",
                                       ENTRY_DICT_MINIMUM   :   0.1,
                                       ENTRY_DICT_MAXIMUM   :   3600.0,
                                       ENTRY_DICT_TYPE      :   float,
                                       ENTRY_DICT_DEFAULT   :   1.0}
    #########################################################################
    ALL_CONFIG_VARS = [
        DETECTOR_TRIGGER_THRESHOLD,     DETECTOR_RECORD_BEFORE_SECONDS,     DETECTOR_RECORD_AFTER_SECONDS,
        DETECTOR_SAVE_RESOLUTION_X,     DETECTOR_SAVE_RESOLUTION_Y,         DETECTOR_FRAMES_PER_SECOND,
        DETECTOR_RECORD_SAMPLE_RATE,    DETECTOR_RECORD_BLOCK_LENGTH,       DETECTOR_INTERPRETATION_MODULO, 
        DETECTOR_AUDIO_MODULO,          DETECTOR_DIFF_AUDIO_MOD,            DETECTOR_IN_DEBUG,
        DETECTOR_DEBUG_UPDATE_FREQ,     DETECTOR_CONFIG_REFRESH_RATE,       DETECTOR_HEARTBEAT_RATE
    ]

    def __init__(self, file_name : str):
        self.file_name = file_name
        try:
            with open(self.file_name, "r") as json_file:
                self.config = json.load(json_file)
        except:
            print("Failed to read from JSON. Using all default values.")
            self.config = dict()
        _ = self.to_defaults_if_dne()
        _ = self.remove_unknowns_from_config()

    def to_defaults_if_dne(self):
        for entry in self.ALL_CONFIG_VARS:
            if self.ENTRY_DICT_NAME in entry and \
               self.ENTRY_DICT_DEFAULT in entry and \
               entry[self.ENTRY_DICT_NAME] not in self.config:
                self.config[entry[self.ENTRY_DICT_NAME]] = entry[self.ENTRY_DICT_DEFAULT]
        return True

    def to_defaults(self):
        self.config = dict()
        self.to_defaults_if_dne()
        return True

    def remove_unknowns_from_config(self):
        valid_names = [entry[self.ENTRY_DICT_NAME] for entry in self.ALL_CONFIG_VARS \
                       if self.ENTRY_DICT_NAME in entry]
        keys = list(self.config.keys())
        for entry in keys:
            if entry not in valid_names and entry in self.config:
                print(f"Invalid entry {entry} with value {self.config.pop(entry)} detected. Removing...")
        return True

    def update_entry(self, entry_id, entry_value):
        # Phase 1: sanity checks. Does the configuration even exist, is the configuration actually
        #   the type we expect it to be (a dictionary), and does the entry exist in the config?
        #   If the answer to any of these are no, this request is invalid. Error and exit.
        if self.config is None:
            print("Detector configuration does not exist! How did that happen?")
            return False
        if type(self.config) != dict:
            print("Detector configuration isn't of the expected dict type. How?")
            return False
        if entry_id not in self.config:
            print("Can't update an entry not in the dictionary. Is it spelled incorrectly?")
            return False
        # Phase 2: getting the configuration settings. Find an entry in the list of possible
        #   configurable keywords that has this one. If it's not recorded, or there's more than
        #   one, there's an issue somewhere in this file and it needs to be sorted out. Otherwise,
        #   the single existing keyword is the one we're attempting to update.
        config_entry_configurations = [keyword_cfg for keyword_cfg in self.ALL_CONFIG_VARS \
                                       if self.ENTRY_DICT_NAME in keyword_cfg and keyword_cfg[self.ENTRY_DICT_NAME] == entry_id]
        if len(config_entry_configurations) < 1:
            print("Configuration entry exists in the dictionary, isn't a known configurable variable.")
            return False
        if len(config_entry_configurations) > 1:
            print("Conflicting keywords among configurable variables! Check config_dict.py or config.json")
            return False
        # Phase 3: Sanity check the target configuration keyword configuration (that's a mouthful).
        #   If there's no designated type, we can't do anything with it. This is an issue with this file,
        #   rather than a configuration problem.
        config_entry_configuration = config_entry_configurations[0]
        if self.ENTRY_DICT_TYPE not in config_entry_configuration:
            print("No type for this entry, so can't safely set it. Check config_dict.py!")
            return False
        # Phase 4: Perform the casting. This might cause an error, so catch it and report it.
        #   That will only occur if we attempt some icky transformation.
        try:
            casted_entry_value = config_entry_configuration[self.ENTRY_DICT_TYPE](entry_value)
        except ValueError:
            print("Attepted to perform an invalid cast. Your types must not be correct.")
            return False
        # Phase 5: Check maximums and minimums. If the value is outside a valid range, discard it.
        #   Also, sanity checks for types as well. In theory we should get that in the last check,
        #   but just in case.
        try:
            if self.ENTRY_DICT_MINIMUM in config_entry_configuration and \
            casted_entry_value < config_entry_configuration[self.ENTRY_DICT_MINIMUM]:
                print("Value exists in the configuration, but we can't set it that low.")
                return False
            if self.ENTRY_DICT_MAXIMUM in config_entry_configuration and \
            casted_entry_value > config_entry_configuration[self.ENTRY_DICT_MAXIMUM]:
                print("Value exists in the configuration, but we can't set it that high.")
                return False
        except:
            print("Unexpected exception when comparing entry against maximums. Likely a TypeError.")
            return False
        self.config[entry_id] = casted_entry_value
        return True

    def get_entry(self, entry_id):
        if entry_id not in self.config:
            print(f"Attempted to get {entry_id} from config, but that doesn't exist")
            return None
        return self.config[entry_id]
    
    def reset_entry(self, entry_id):
        if entry_id not in self.config:
            print(f"Attempted to reset {entry_id}, which doesn't exist in the config")
            return False
        config_entry_configurations = [keyword_cfg for keyword_cfg in self.ALL_CONFIG_VARS \
                                       if self.ENTRY_DICT_NAME in keyword_cfg and keyword_cfg[self.ENTRY_DICT_NAME] == entry_id]
        if len(config_entry_configurations) < 1:
            print("Configuration entry exists in the dictionary, isn't a known configurable variable.")
            return False
        if len(config_entry_configurations) > 1:
            print("Conflicting keywords among configurable variables! Check config_dict.py or config.json")
            return False
        config_entry_configuration = config_entry_configurations[0]
        if self.ENTRY_DICT_DEFAULT not in config_entry_configuration:
            print("Attempted to reset {entry_id}, but it has no reset value.")
            return False
        self.config[entry_id] = config_entry_configurations[0][self.ENTRY_DICT_DEFAULT]
        return True

    def export_configuration(self):
        try:
            with open(self.file_name, 'w') as jfile:
                json.dump(self.config, jfile, indent=4)
                print(f"Saved current configuration to {self.file_name}")
                return True
        except:
            print("Failed to export the JSON for some reason. Maybe the file is invalid?")
            return False
    
    def view_configuration(self):
        print(self.config)
        return True

    def get_cfg_var_name(self, var_dict):
        if self.ENTRY_DICT_NAME not in var_dict:
            print("Entry name does not exist!")
            return None
        return var_dict[self.ENTRY_DICT_NAME]