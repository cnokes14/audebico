import queue
import threading
import cv2
import time
import json
import datetime
import sounddevice
import numpy
import scipy
import ffmpeg

storage_video_queue = queue.Queue(maxsize=4096)
storage_audio_queue = queue.Queue(maxsize=1024)

interpretation_video_queue = queue.Queue(maxsize=4)
interpretation_audio_queue = queue.Queue(maxsize=4)

interpretation_frame_modulo = 10
storage_end_time = -1
storage_start_time = -1
resolution_in = (320,180)
fps = 20.0
fps_margin = 0.1
time_after = 5.0
time_before = 5.0
total_thresh = 50000
running = True
audio_sample_rate = 44100
JSON_PATH = "config.json"

def audio():
    global running, audio_sample_rate, storage_audio_queue, \
        interpretation_audio_queue, interpretation_frame_modulo
    interpretation_audio = None
    idx = 0
    while running:
        adata = sounddevice.rec(int((0.1) * audio_sample_rate), samplerate=audio_sample_rate, 
                                channels=1, dtype='float32')
        sounddevice.wait()
        t_start = time.time()
        if storage_audio_queue.full():
            _ = storage_audio_queue.get()
        storage_audio_queue.put([adata, t_start])
        if interpretation_audio is None:
            interpretation_audio = adata
        else:
            interpretation_audio = numpy.concatenate((interpretation_audio, adata), axis=0)

        if idx % interpretation_frame_modulo == interpretation_frame_modulo - 1:
            if interpretation_audio_queue.full():
                _ = interpretation_audio_queue.get()
            interpretation_audio_queue.put([interpretation_audio, t_start])
            interpretation_audio = None
        idx += 1
    print("audio loop exited")

def recording():
    # Global variables for configuration and data storage.
    global running, resolution_in, storage_video_queue, interpretation_video_queue
    
    # Interloop values for later.
    idx = 0; f_isound = []

    # Look at the main camera. Maybe this should be programmable?
    cap = cv2.VideoCapture(0)

    # Uh oh! No camera, get out.
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    stime = time.time()
    while running:
        # TODO: Read in sound.
        f_iret, f_img = cap.read()
        f_sound = None
        # Something's wrong with the camera.
        if not f_iret or f_img is None:
            cap.release()
            cap = cv2.VideoCapture(0)
            continue
        
        # Resize image as needed.
        f_img = cv2.resize(f_img, resolution_in, fx=0, fy=0, interpolation=cv2.INTER_LINEAR)

        # For storage, we just need the raw image and sound for this
        #   frame. No other work needed!
        f_sdata = [f_img, f_sound, time.time()]

        # Drop the oldest entry from the storage queue if needed, and stick in the new one.
        if storage_video_queue.full():
            _ = storage_video_queue.get()
        storage_video_queue.put(f_sdata)

        # Add the new sound to the interpretation sound block.
        f_isound.append(f_sound)

        # If we've hit a certain index, we need to write to the interpretation queue.
        if idx % interpretation_frame_modulo == (interpretation_frame_modulo-1):
            # Create data for the interpretation thread. Current frame + all sound since last.
            f_idata = [f_img, f_isound.copy()]; f_isound = []
            
            # Drop the oldest entry from the queue if needed, and stick in the new one.
            if interpretation_video_queue.full():
                _ = interpretation_video_queue.get()
            interpretation_video_queue.put(f_idata)

        # Frame index up by one.
        idx += 1
        #print(f"fps:{idx / (time.time()-stime)}")
    print("recording loop exited.")

def storage():
    global running, fps, fps_margin, resolution_in, storage_end_time, storage_start_time, storage_video_queue
    was_recording = False
    fcc_codec = cv2.VideoWriter_fourcc(*'mp4v')
    f_save = None
    rec_shape = resolution_in
    fname = ""
    l_ftime = -1; l_atime = -1
    f_start_time = -1
    f_audio = None
    while running:
        t_comp = (storage_end_time == -1) or (l_ftime >= storage_end_time and l_atime >= storage_end_time)
        if t_comp and not was_recording:
            time.sleep(0.25) # Reconfigurable?
            continue
        elif t_comp and was_recording and f_save is not None:
            print(f"Ending and saving recording: {fname}")
            f_save.release()
            scipy.io.wavfile.write(f"tmp/tmp.wav", 44100, f_audio)
            video  = ffmpeg.input(f"tmp/tmp.mp4").video  # get only video channel
            audio  = ffmpeg.input(f"tmp/tmp.wav").audio  # get only audio channel
            output = ffmpeg.output(video, audio, f"recordings/{fname}.mp4", 
                                   vcodec='copy', acodec='aac', strict='experimental')
            ffmpeg.run(output)

            f_save = None
            was_recording = False
            f_start_time = -1
            f_audio = None
        elif (not t_comp) and was_recording and (f_save is not None):
            while not storage_video_queue.empty():
                # Are we done recording? We're okay to leave.
                if l_ftime >= storage_end_time:
                    break
                # Let's read the data in from the video queue.
                fdata = storage_video_queue.get()
                # Discard the video if it's too stale.
                if fdata[2] < storage_start_time:
                    continue
                # Start time of the audio! Necessary for matching.
                if f_start_time is None or f_start_time < 0:
                    f_start_time = fdata[2]
                # Sanity check - does the current frame match what we're saving?
                if fdata[0].shape[1] != rec_shape[0] or fdata[0].shape[0] != rec_shape[1]:
                    continue
                # Should we skip this frame? We are assuming that there's no way the framerate of the
                #   camera can be less than the requested framerate. TODO: remedy that assumption.
                if fdata[2] - l_ftime < (1.0 / (fps+fps_margin)):
                    continue
                # Write the individual frame.
                cv2.imshow("storage data", fdata[0])
                _ = cv2.waitKey(1)
                f_save.write(fdata[0])
                l_ftime = fdata[2]
            while not storage_audio_queue.empty():
                # Audio gathering in progress
                if l_atime >= storage_end_time:
                    break
                f_data = storage_audio_queue.get()
                # Discard the audio if it's too stale.
                if f_data[1] < storage_start_time:
                    continue
                if f_audio is None:
                    f_audio = f_data[0]
                else:
                    f_audio = numpy.concatenate((f_audio, f_data[0]))
                l_atime = f_data[1]
        else:
            print("Detected something! Started a recording...")
            rec_shape = resolution_in
            fname = f"{datetime.datetime.now().isoformat()}"
            f_save = cv2.VideoWriter(f"tmp/tmp.mp4", fcc_codec, 
                                        fps, rec_shape)
            was_recording = True
    if f_save is not None:
        print(f"Ending and saving recording: {fname}")
        f_save.release()
        scipy.io.wavfile.write(f"tmp/tmp.wav", 44100, f_audio)
        video  = ffmpeg.input(f"tmp/tmp.mp4").video  # get only video channel
        audio  = ffmpeg.input(f"tmp/tmp.wav").audio  # get only audio channel
        output = ffmpeg.output(video, audio, f"recordings/{fname}.mp4", 
                               vcodec='copy', acodec='aac', strict='experimental')
    print("storage loop exited.")

def interpretation():
    global running, storage_end_time, storage_start_time, \
            time_after, time_before, total_thresh, interpretation_video_queue, interpretation_audio_queue
    idx = 0
    pimg = None
    average_sound = [0]*64
    average_sound_sum = 0
    average_movement = [0]*64
    average_movement_sum = 0
    while running:
        if interpretation_video_queue.empty() or interpretation_audio_queue.empty():
            time.sleep(0.1)
            continue
        idata = interpretation_video_queue.get()
        adata = interpretation_audio_queue.get()

        frame = cv2.cvtColor(idata[0], cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, [160,120], fx=0, fy=0, interpolation=cv2.INTER_LINEAR)
        # Apply Sobel operator
        sobelx = cv2.Sobel(frame, cv2.CV_64F, 1, 0, ksize=3)  # Horizontal edges
        sobely = cv2.Sobel(frame, cv2.CV_64F, 0, 1, ksize=3)  # Vertical edges

        # Compute gradient magnitude
        frame_edge = cv2.magnitude(sobelx, sobely)
        
        # Convert to uint8
        frame_edge = cv2.convertScaleAbs(frame_edge)

        if pimg is not None:
            avg_frame = cv2.subtract(frame_edge, pimg)
        else:
            pimg = frame_edge
            continue

        avg_frame = cv2.bilateralFilter(avg_frame, 3, 90, 90)
        _, avg_frame = cv2.threshold(avg_frame, 64, 255, cv2.THRESH_BINARY)
        pimg = frame_edge

        # Remove these! Just for debugging.
        cv2.imshow("interpretation", idata[0])
        _ = cv2.waitKey(1)
        cv2.imshow("shrunk", frame)
        _ = cv2.waitKey(1)
        cv2.imshow("edging", avg_frame)
        _ = cv2.waitKey(1)
        cv2.imshow("edged_once", frame_edge)
        _ = cv2.waitKey(1)

        # Determine the magnitude of the motion
        motion = cv2.sumElems(avg_frame)[0]
        # Determine the magnitude of the audio
        amag = numpy.linalg.norm(numpy.abs(adata[0]))
        # Compute the differences between the current and average sound and motion.
        m_diff = max(1, motion - (sum(average_movement) / len(average_movement)))
        a_diff = max(1, amag - (sum(average_sound) / len(average_sound)))
        average_movement[idx % len(average_movement)] = motion
        average_sound[idx % len(average_sound)] = amag
        diff_mult = m_diff * a_diff
        if diff_mult > total_thresh*2:
            diff_mult = total_thresh*2
        if diff_mult > total_thresh:
            t_now = time.time()
            storage_end_time = t_now + time_after
            storage_start_time = t_now - time_before
        idx += 1
    print("interpretation loop exited.")

def command():
    global interpretation_frame_modulo, running, storage_end_time, \
            fps, time_after, resolution_in, total_thresh
    while running:
        s = input("").lower().split()
        if len(s) == 0:
            continue
        if "fps" == s[0]:
            if len(s) != 2:
                print("usage: fps <x>, x = new FPS as a float.")
                continue
            ffp = float(s[1])
            if ffp < 1.0:
                print("should be recording at at least 1 fps.")
                continue
            fps = ffp
        elif "res" == s[0]:
            if len(s) != 3:
                print("usage: res <x> <y>, x = width in pixels, y = height in pixels")
                continue
            fw = int(s[1]); fh = int(s[2])
            if fw < 1 or fh < 1:
                print("invalid image resolution")
                continue
            # Update the resolution.
            resolution_in = [fw,fh]
        elif "post" == s[0]:
            if len(s) != 2:
                print("usage: post <x>, x = seconds to record after event (float)")
                continue
            fp = float(s[1])
            if fp <= 0.0:
                print("shouldn't we record for at least a little bit?")
                continue
            time_after = fp
        elif "thresh" == s[0]:
            if len(s) != 2:
                print("usage: thresh <x>, x = new threshold as a float.")
                continue
            ft = float(s[1])
            if ft <= 0.0:
                print("shouldn't we at least make sure there's something there?")
            total_thresh = ft
        elif "exit" == s[0]:
            print("Exiting. We might not want to let this feature out of debug!")
            running = False
        elif "mod" == s[0]:
            if len(s) != 2:
                print("usage: mod <x>, x = num recorded frames per frame checked")
                continue
            ii = int(s[1])
            if ii < 1:
                print("That's not how this works.")
                continue
            interpretation_frame_modulo = ii
        elif "save" == s[0]:
            print("Updating config with current settings...")
            jdata = None
            with open(JSON_PATH, 'r') as jfile:
                jdata = json.load(jfile)
            if jdata is None:
                print("No config file found!")
            jdata["mod"] = interpretation_frame_modulo
            jdata["thresh"] = total_thresh
            jdata["post"] = time_after
            jdata["res"] = resolution_in
            jdata["fps"] = fps
            with open(JSON_PATH, 'w') as jfile:
                json.dump(jdata, jfile, indent=4)
                print(f"Saved: {jdata}")
        else:
            print("unrecognized command!")
    print("command loop exited.")

def main():
    # with open(JSON_PATH, 'r') as jfile:
    #     global interpretation_frame_modulo, \
    #         fps, time_after, resolution_in, total_thresh
    #     jdata = json.load(jfile)
    #     if jdata["mod"] is not None:
    #         interpretation_frame_modulo = jdata["mod"]
    #     if jdata["thresh"] is not None:
    #         total_thresh = jdata["thresh"]
    #     if jdata["post"] is not None:
    #         time_after = jdata["post"]
    #     if jdata["res"] is not None:
    #         resolution_in = jdata["res"]
    #     if jdata["fps"] is not None:
    #         fps = jdata["fps"]

    t_recording = threading.Thread(target=recording)
    t_storage = threading.Thread(target=storage)
    t_interpretation = threading.Thread(target=interpretation)
    t_command = threading.Thread(target=command)
    t_audio = threading.Thread(target=audio)

    t_recording.start()
    t_storage.start()
    t_interpretation.start()
    t_command.start()
    t_audio.start()

    t_recording.join()
    t_storage.join()
    t_interpretation.join()
    t_command.join()
    t_audio.join()

    print("cleanly exited!")

if __name__ == "__main__":
    main()