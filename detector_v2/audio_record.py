from config_dict    import DetectorConfig
from queue          import Queue
from threading      import Thread
from time           import time
from sounddevice    import rec, wait
from numpy          import concatenate

class AudioRecord:
    interpretation_queue    : Queue             = None
    storage_queue           : Queue             = None
    config                  : DetectorConfig    = None
    enabled                 : bool              = False
    thread                  : Thread            = None

    def __init__(self, 
                 interpretation_queue : Queue, 
                 storage_queue : Queue,
                 config : DetectorConfig):
        self.interpretation_queue = interpretation_queue
        self.storage_queue = storage_queue
        self.config = config

    def start(self):
        self.enabled = True
        self.thread = Thread(target=self.run_recording)
        self.thread.start()

    def stop(self):
        if self.thread is None:
            print("Attempted to kill a video recording thread that doesn't exist.")
            return False
        self.enabled = False
        self.thread.join()
        return True
    
    def restart(self):
        self.stop()
        self.start()

    def alive(self):
        return self.thread is not None and self.thread.is_alive()
    
    def force_push(element, queue : Queue):
        if queue is None:
            print("Cannot push to a NoneType queue!")
            return False
        if queue.full():
            _ = queue.get()
        queue.put(element)
        return True

    def run_recording(self):
        # The index defines what loop we're in. Used for periodic refresh and posting.
        idx = 0
        # These keys are all used to read from the configuration. The names are constant.
        modulo_dict_key      = self.config.get_cfg_var_name(self.config.DETECTOR_INTERPRETATION_MODULO)
        use_amod_dict_key    = self.config.get_cfg_var_name(self.config.DETECTOR_DIFF_AUDIO_MOD)
        amod_dict_key        = self.config.get_cfg_var_name(self.config.DETECTOR_AUDIO_MODULO)
        sample_rate_dict_key = self.config.get_cfg_var_name(self.config.DETECTOR_RECORD_SAMPLE_RATE)
        block_size_dict_key  = self.config.get_cfg_var_name(self.config.DETECTOR_RECORD_BLOCK_LENGTH)
        cfg_refresh_dict_key = self.config.get_cfg_var_name(self.config.DETECTOR_CONFIG_REFRESH_RATE)
        # Find what the values of the elements are during startup. These may change eventually.
        interpretation_audio_modulo = self.config.get_entry(modulo_dict_key) \
                                                    if not self.config.get_entry(use_amod_dict_key) \
                                                    else self.config.get_entry(amod_dict_key)
        sample_rate          = self.config.get_entry(sample_rate_dict_key)
        block_size           = self.config.get_entry(block_size_dict_key)
        cfg_refresh_rate     = self.config.get_entry(cfg_refresh_dict_key)
        # The larger audio block that gets passed to the interpretation thread.
        interpretation_audio_struct = None
        # Now, run the loop until requested to exit.
        while self.enabled:
            audio_time  = time()
            audio       = rec(int(block_size * sample_rate), samplerate=sample_rate, 
                                channels=1, dtype='float32')
            wait()
            audio_struct = [audio_time, audio]
            if interpretation_audio_struct is None:
                interpretation_audio_struct = audio_struct
            else:
                interpretation_audio_struct[1] = concatenate([interpretation_audio_struct[1], audio], axis=0)
            AudioRecord.force_push(audio_struct, self.storage_queue)
            if idx % interpretation_audio_modulo == interpretation_audio_modulo - 1:
                AudioRecord.force_push(interpretation_audio_struct, self.interpretation_queue)
                interpretation_audio_struct = None
            idx+=1
            # Now that our iteration is done, we can safely update configuration values.
            if idx % cfg_refresh_rate == cfg_refresh_rate - 1:
                interpretation_audio_modulo = self.config.get_entry(modulo_dict_key) \
                                                    if not self.config.get_entry(use_amod_dict_key) \
                                                    else self.config.get_entry(amod_dict_key)
                sample_rate                 = self.config.get_entry(sample_rate_dict_key)
                block_size                  = self.config.get_entry(block_size_dict_key)
                cfg_refresh_rate            = self.config.get_entry(cfg_refresh_dict_key)