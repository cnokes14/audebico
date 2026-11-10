import cv2
import time
import matplotlib.pyplot as plt

# Create a VideoCapture object, 0 specifies the default camera
# Use 1 or higher for external cameras
cap = cv2.VideoCapture(0)

# What was the last image we looked at?
pimg = None

# Check if the camera opened successfully
if not cap.isOpened():
    print("Cannot open camera")
    exit()

t = time.time()

plt.ion() 
fig, ax = plt.subplots()
img_idx = 0
img_idxs = []
img_sums = []
img_unfiltered_sums = []
line, = plt.plot(img_idxs, img_sums, label="High-Pass Filtered Movement")
line_uf, = plt.plot(img_idxs, img_unfiltered_sums, label="Unfiltered Movement")
plt.legend()
running = [0.0]*32
rsum = 0.0
while True:
    # Capture frame-by-frame
    ret, frame_color = cap.read()
    if(time.time() - t < 0.1):
        continue
    t = time.time()
    time.sleep(0.1)

    frame = cv2.cvtColor(frame_color, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, [160,120], fx=0, fy=0, interpolation=cv2.INTER_LINEAR)

    # Apply Sobel operator
    sobelx = cv2.Sobel(frame, cv2.CV_64F, 1, 0, ksize=3)  # Horizontal edges
    sobely = cv2.Sobel(frame, cv2.CV_64F, 0, 1, ksize=3)  # Vertical edges

    # Compute gradient magnitude
    gradient_magnitude = cv2.magnitude(sobelx, sobely)
    
    # Convert to uint8
    gradient_magnitude = cv2.convertScaleAbs(gradient_magnitude)

    if pimg is not None:
        disp_img = cv2.subtract(gradient_magnitude, pimg)
    else:
        disp_img = gradient_magnitude
    disp_img = cv2.bilateralFilter(disp_img, 3, 90, 90)
    _, disp_img = cv2.threshold(disp_img, 64, 255, cv2.THRESH_BINARY)
    pimg = gradient_magnitude

    motion = cv2.sumElems(disp_img)[0]
    
    #disp_img = cv2.resize(disp_img, [640,480], fx=0, fy=0, interpolation=cv2.INTER_LINEAR)
    disp_img = cv2.resize(disp_img, [320,240], fx=0, fy=0, interpolation=cv2.INTER_LINEAR)
    gradient_magnitude = cv2.resize(gradient_magnitude, [320,240], fx=0, fy=0, interpolation=cv2.INTER_LINEAR)
    frame_color = cv2.resize(frame_color, [320,240], fx=0, fy=0, interpolation=cv2.INTER_LINEAR)    

    # Display the resulting frame
    cv2.imshow('Webcam Feed Edge', disp_img)
    cv2.imshow('Webcam Feed Gradient', gradient_magnitude)
    cv2.imshow('Webcam Feed Raw', frame_color)

    if img_idx > 0:
        img_idxs.append(img_idx)
        img_unfiltered_sums.append(motion / (1.5*48960.0))
        if (motion - (rsum / len(running))) >= 0.0:
            # 255*160*120 = 4,896,000 -- this is the maximum possible change.
            img_sums.append((motion - (rsum / len(running))) / 48960.0)
        else:
            img_sums.append(0.0)
        rsum -= running[img_idx % len(running)]
        running[img_idx % len(running)] = motion
        rsum += motion
    img_idx += 1
    if len(img_idxs) >= 100:
        img_idxs = img_idxs[len(img_idxs)-100:len(img_idxs)]
        img_sums = img_sums[len(img_sums)-100:len(img_sums)]
        img_unfiltered_sums = img_unfiltered_sums[len(img_unfiltered_sums)-100:len(img_unfiltered_sums)]

    # Update the line data
    line.set_data(img_idxs, img_sums)
    line_uf.set_data(img_idxs, img_unfiltered_sums)
    
    # Rescale the view for new data
    ax.relim() 
    ax.autoscale_view(True,True,True) 

    # Redraw the figure and process events
    plt.draw()
    plt.xlabel("Frame # (at 20fps)")
    plt.ylabel("Movement Detected")
    plt.pause(0.01)

    # Press 'q' on the keyboard to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture and destroy windows
cap.release()
cv2.destroyAllWindows()
