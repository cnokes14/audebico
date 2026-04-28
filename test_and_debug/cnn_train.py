import cv2
import glob
import time
import random
import torch
import pandas
import matplotlib.pyplot as plt

class BirdData(torch.utils.data.Dataset):
    def __init__(self, csv_file, root_dir, transform=None):
        self.landmarks_frame = pandas.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform

    def __len__(self):
        return len(self.landmarks_frame)
    
    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        img_name = self.root_dir + self.landmarks_frame.iloc[idx, 0]
        image = cv2.imread(img_name, cv2.IMREAD_GRAYSCALE)
        is_bird = float(self.landmarks_frame.iloc[idx, 1])
        data = {'image':image, 'is_bird':is_bird}
        if self.transform:
            data = self.transform(data)
        return data

class BirdCNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        # Input: 1 channel, 160x120 images
        # Layer 1: Conv2d (input=1, output=16, kernel=5) -> MaxPool2d (kernel=2)
        self.conv1 = torch.nn.Conv2d(in_channels=1, out_channels=16, kernel_size=5, stride=1, padding=2)
        self.pool = torch.nn.MaxPool2d(kernel_size=2, stride=2)
        
        # After one pooling layer, image size is 160/2 * 120/2 = 80*60
        # Layer 2: Conv2d (input=16, output=32, kernel=5) -> MaxPool2d (kernel=2)
        self.conv2 = torch.nn.Conv2d(in_channels=16, out_channels=32, kernel_size=5, stride=1, padding=2)
        
        # After two pooling layers, image size is 80/2 * 60/2 = 40*30
        # The number of features going into the fully connected layer is 32 * 40 * 30
        self.fc1 = torch.nn.Linear(32 * 40 * 30, 512)
        self.fc2 = torch.nn.Linear(512, 1)
        self.sigmoid = torch.nn.Sigmoid()
    
    def forward(self, x):
        # Convolutional and pooling layers with ReLU activation
        x = self.pool(torch.nn.functional.relu(self.conv1(x)))
        x = self.pool(torch.nn.functional.relu(self.conv2(x)))
        
        # Flatten the output for the fully connected layers
        x = x.view(-1, 32 * 40 * 30) # Use .view or torch.flatten

        # Fully connected layers with ReLU activation
        x = torch.nn.functional.relu(self.fc1(x))
        x = self.fc2(x)
        x = self.sigmoid(x) # Output between 0 and 1
        return x

def display_bird_dataset(dataset : BirdData):
    for i, sample in enumerate(dataset):
        print(i, sample['image'].shape, sample['is_bird'])
        cv2.imshow("tmp", sample['image'])
        cv2.waitKey(0)

if False:
    dataset = BirdData(csv_file="data.csv", root_dir="")
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=1,
                            shuffle=True, num_workers=0)
    birdy = BirdCNN()
    criterion = torch.nn.BCELoss()
    optimizer = torch.optim.SGD(birdy.parameters(), lr=0.001, momentum=0.9)

    for epoch in range(2):  # loop over the dataset multiple times
        running_loss = 0.0
        for i, data in enumerate(dataloader, 0):
            # get the inputs; data is a list of [inputs, labels]
            inputs = data["image"].float() / 255.0
            labels = data["is_bird"].float()

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            outputs = birdy(inputs)
            loss = criterion(outputs[0].float(), labels)
            loss.backward()
            optimizer.step()

            # print statistics
            running_loss += loss.item()
            if i % 200 == 199:    # print every 200 mini-batches
                print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 200:.3f}')
                running_loss = 0.0
            # if i > 100:
            #     break
    print('Finished Training')

# Create a VideoCapture object, 0 specifies the default camera
# Use 1 or higher for external cameras
cap = cv2.VideoCapture(0)
# Bird video, from the RIT Birding Discord.
#cap = cv2.VideoCapture("Videos/rit_birding_vid0.mp4")
# Bird video, from Cornell Bird Lab's bird feeding videos
#cap = cv2.VideoCapture("Videos/cornell_birdfeeder.mp4")

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
    # if motion > 100000:
    #     motion = 100000
    # if motion > 50000:
    #     print(f"Motion detected! {motion}")
    #     # print(birdy(torch.stack([torch.from_numpy(frame)]).float() / 255.0), "with sum", motion)
    
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