import cv2

# Create a VideoCapture object, 0 specifies the default camera
vname = "hb_2"
#cap = cv2.VideoCapture(f"Videos/{vname}.mp4")
cap = cv2.VideoCapture("main/recordings/2026-03-16T12:25:39.751655.mp4")

# Check if the camera opened successfully
if not cap.isOpened():
    print("Cannot open camera")
    exit()

idx = 0
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    idx += 1

    #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_small = cv2.resize(frame, [160,120], fx=0, fy=0, interpolation=cv2.INTER_LINEAR)
    frame = cv2.resize(frame_small, [640,480], fx=0, fy=0, interpolation=cv2.INTER_LINEAR)

    # Display the resulting frame
    cv2.imshow('IS THIS A BIRD IN FLIGHT?', frame)

    # Press 'q' on the keyboard to exit the loop
    c = cv2.waitKey(50)
    if c == ord('q'):
        break
    elif c == ord('b'):
        cv2.imwrite(f"HAS_BIRD_IF/f{vname}_n{idx}.jpg", frame_small)
    elif c == ord('n'):
        cv2.imwrite(f"NO_BIRD_IF/f{vname}_n{idx}.jpg", frame_small)

# When everything done, release the capture and destroy windows
cap.release()
cv2.destroyAllWindows()