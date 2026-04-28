import cv2

# Create a VideoCapture object, 0 specifies the default camera
# Use 1 or higher for external cameras
cap = cv2.VideoCapture(0)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, [160,120], fx=0, fy=0, interpolation=cv2.INTER_LINEAR)

    # Apply Sobel operator
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)  # Horizontal edges
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)  # Vertical edges

    # Compute gradient magnitude
    gradient_magnitude = cv2.magnitude(sobelx, sobely)
    
    # Convert to uint8
    gradient_magnitude = cv2.convertScaleAbs(gradient_magnitude)
    _, gradient_magnitude = cv2.threshold(gradient_magnitude, 128, 255, cv2.THRESH_BINARY)

    # Display the resulting frame
    cv2.imshow('Webcam Feed', gradient_magnitude)

    # Press 'q' on the keyboard to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture and destroy windows
cap.release()
cv2.destroyAllWindows()