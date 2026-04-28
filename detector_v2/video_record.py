from config_dict    import DetectorConfig
from queue          import Queue
from threading      import Thread
from cv2            import VideoCapture
from time           import time

class VideoRecord:
    interpretation_queue    : Queue             = None
    storage_queue           : Queue             = None
    config                  : DetectorConfig    = None
    enabled                 : bool              = False
    thread                  : Thread            = None
    fps                     : int               = 1

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

    def print_debug(self):
        print(f"VideoRecord via video_record.py\n\tEstimated {self.fps} FPS")

    def run_recording(self):
        camera : VideoCapture = VideoCapture(0)
        if camera is None or not camera.isOpened():
            print("Failed to open the camera. Need to restart the recording thread.")
            return
        idx = 0
        modulo_dict_key             = self.config.get_cfg_var_name(self.config.DETECTOR_INTERPRETATION_MODULO)
        cfg_refresh_dict_key        = self.config.get_cfg_var_name(self.config.DETECTOR_CONFIG_REFRESH_RATE)
        interpretation_frame_modulo = self.config.get_entry(modulo_dict_key)
        cfg_refresh_rate            = self.config.get_entry(cfg_refresh_dict_key)
        t_start = time()
        while self.enabled:
            image_time = time()
            image_ok, image = camera.read()
            if not image_ok:
                print("Image is not okay. Closing the camera and exiting this thread.")
                camera.release()
                return
            image_struct = [image_time, image]
            VideoRecord.force_push(image_struct, self.storage_queue)
            if idx % interpretation_frame_modulo == interpretation_frame_modulo - 1:
                VideoRecord.force_push(image_struct, self.interpretation_queue)
            idx+=1
            # Now that our iteration is done, we can safely refresh our configuration values.
            if idx % cfg_refresh_rate == cfg_refresh_rate - 1:
                interpretation_frame_modulo = self.config.get_entry(modulo_dict_key)
                cfg_refresh_rate            = self.config.get_entry(cfg_refresh_dict_key)
                self.fps                    = idx / (image_time - t_start)