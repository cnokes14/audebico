from config_dict    import DetectorConfig
from command_center import CommandCenter
from video_record   import VideoRecord
from audio_record   import AudioRecord
from time           import sleep, time
from queue          import Queue

if __name__ == "__main__":
    detector_config             = DetectorConfig("config.json")
    command_center              = CommandCenter(detector_config)
    video_interpretation_queue  = Queue(maxsize=4)
    audio_interpretation_queue  = Queue(maxsize=4)
    video_storage_queue         = Queue(maxsize=4096)
    audio_storage_queue         = Queue(maxsize=1024)

    video_record = VideoRecord(video_interpretation_queue,
                               video_storage_queue,
                               detector_config)
    audio_record = AudioRecord(audio_interpretation_queue,
                               audio_storage_queue,
                               detector_config)

    idx = 0
    in_debug_dict_key       = detector_config.get_cfg_var_name(detector_config.DETECTOR_IN_DEBUG)
    debug_refresh_dict_key  = detector_config.get_cfg_var_name(detector_config.DETECTOR_DEBUG_UPDATE_FREQ)
    cfg_refresh_dict_key    = detector_config.get_cfg_var_name(detector_config.DETECTOR_CONFIG_REFRESH_RATE)
    sleep_time_dict_key     = detector_config.get_cfg_var_name(detector_config.DETECTOR_HEARTBEAT_RATE)
    in_debug                = detector_config.get_entry(in_debug_dict_key)
    debug_refresh_rate      = detector_config.get_entry(debug_refresh_dict_key)
    cfg_refresh_rate        = detector_config.get_entry(cfg_refresh_dict_key)
    sleep_time              = detector_config.get_entry(sleep_time_dict_key)
    t_last_debug            = time() - debug_refresh_rate
    while True:
        # First and foremost, if the command center wants us to exit, we kill everything
        #   and leave ASAP. The threads themselves will handle all the cleanup.
        if command_center.check_exit():
            video_record.stop()
            command_center.stop()
            audio_record.stop()
            break
        # If we're continuing to run, we need to make sure all the threads are still up.
        #   Boot them back up if they don't already exist. This is also how we startup
        #   the threads for the first time.
        if not video_record.alive():
            video_record.start()
        if not command_center.alive():
            command_center.start()
        if not audio_record.alive():
            audio_record.start()
        if in_debug and time() - t_last_debug > debug_refresh_rate:
            t_last_debug = time()
            print("\n-----VIEWING DEBUG INFORMATION-----\n")
            video_record.print_debug()
            print("\n-----END DEBUG INFORMATION-----\n")
        # Update our local configuration, if necessary.
        if idx % cfg_refresh_rate == cfg_refresh_rate - 1:
            in_debug                = detector_config.get_entry(in_debug_dict_key)
            debug_refresh_rate      = detector_config.get_entry(debug_refresh_dict_key)
            cfg_refresh_rate        = detector_config.get_entry(cfg_refresh_dict_key)
            sleep_time              = detector_config.get_entry(sleep_time_dict_key)
        # Another successful loop iteration.
        idx += 1
        # Sleep to allow other threads with more work to have more time. We can lower this
        #   to make threads boot up more quickly after failing, and to make the program
        #   exit faster if that's requested.
        sleep(sleep_time)