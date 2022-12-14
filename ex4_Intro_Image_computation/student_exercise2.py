# code partially adapted from https://pypi.org/project/pupil-apriltags/
# and https://pyimagesearch.com/2020/11/02/apriltag-with-python/
from djitellopy import Tello
import cv2
import time
import numpy as np

import cv2
from matplotlib import pyplot as plt
from pupil_apriltags import Detector

# NOTE THAT THE 3D POSE OF TAGS IS WRT THE CAMERA FRAME!

############ params ############
width = 640  # WIDTH OF THE IMAGE
height = 480  # HEIGHT OF THE IMAGE

# intrinsic calibration
cx = width / 2.0
cy = height / 2.0
fx = 600
fy = 600
intrinsics = ([fx, fy, cx, cy])
K = np.array([[fx, 0.0, cx],
              [0.0, fy, cy],
              [0.0, 0.0, 1.0]])

# tag size (m)
tag_size = 0.165
###############################

# CONNECT TO TELLO
tello = Tello()
tello.connect(False)
time.sleep(1)
tello.for_back_velocity = 0 # forward and backward velocity
tello.left_right_velocity = 0 # left and right velocity
tello.up_down_velocity = 0 # up and down velocity
tello.yaw_velocity = 0 # yaw angular velocity
tello.speed = 0

tello.streamon()
########################

# initialize detector
at_detector = Detector(families='tag36h11',
                   nthreads=1,
                   quad_decimate=1.0,
                   quad_sigma=0.0,
                   refine_edges=1,
                   decode_sharpening=0.25,
                   debug=0)

def get_point_below_tag(T_camera_tag, meters_below, K):
    """
    given a 4x4 transform FROM the tag TO the camera,
    compute the 3D location of a point meters_below the tag
    and return the 2D location of that point in the image frame.
    """
    # get inverse transform
    T_tag_camera = np.linalg.inv(T_camera_tag)
    # find 3D location of point below the tag
    T_tag_camera[1,3] -= meters_below
    # convert back to being wrt the camera frame
    T_camera_tag = np.linalg.inv(T_tag_camera)
    
    ###### TODO fill in here ##########
    # compute the 2D location of the target point in the image plane
    # hint: T_camera_tag[0:3,3:] is the 3D point of the target wrt the camera
    # hint: don't forget to return a 2D point and not a 3D point
    # px = T_camera_tag[0:3,3:]/T_camera_tag[0:3,3:][2]
    x_img = K@T_camera_tag[0:3,3:]
    x_img = x_img/x_img[2]
    x_img = x_img[0:2, :]
    px = int(x_img[0][0])
    py = int(x_img[1][0])
    print(px, py)
    return (px, py)
    
    ##################################

def track_tags(img):
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    tags = at_detector.detect(img_gray, estimate_tag_pose=True,
                              camera_params=intrinsics, tag_size=tag_size)
    print("number of tags detected:", len(tags))
    
    # loop over the AprilTag detection results
    for tag in tags:
        print("tag id:", tag.tag_id)
    	# extract the bounding box (x, y)-coordinates for the AprilTag
    	# and convert each of the (x, y)-coordinate pairs to integers
        (ptA, ptB, ptC, ptD) = tag.corners
        ptB = (int(ptB[0]), int(ptB[1]))
        ptC = (int(ptC[0]), int(ptC[1]))
        ptD = (int(ptD[0]), int(ptD[1]))
        ptA = (int(ptA[0]), int(ptA[1]))
    	# draw the bounding box of the AprilTag detection
        cv2.line(img, ptA, ptB, (0, 255, 0), 2)
        cv2.line(img, ptB, ptC, (0, 255, 0), 2)
        cv2.line(img, ptC, ptD, (0, 255, 0), 2)
        cv2.line(img, ptD, ptA, (0, 255, 0), 2)
    	# draw the center (x, y)-coordinates of the AprilTag
        (cX, cY) = (int(tag.center[0]), int(tag.center[1]))
        cv2.circle(img, (cX, cY), 5, (0, 0, 255), -1)
    	# draw the tag family on the image
        tagFamily = tag.tag_family.decode("utf-8")
        cv2.putText(img, tagFamily, (ptA[0], ptA[1] - 15),
    		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        print("[INFO] tag family: {}".format(tagFamily))
        print("t: ", tag.pose_t)
        
        ##### Detect point set distance below tag #####
        # construct 4x4 transform matrix of the tags location wrt the camera frame
        T_camera_tag = np.zeros((4,4))
        T_camera_tag[3,3] = 1.0
        T_camera_tag[0:3,3:] = tag.pose_t
        T_camera_tag[0:3,0:3] = tag.pose_R
        
        ###### TODO fill in here ##########
        point_below = get_point_below_tag(T_camera_tag, below_meters, K=K)
        
        # # Draw line from tag center to (px,py) on img. Hint, use cv2.line
        cv2.line(img, point_below, (cX, cY), (255, 0, 0) , 3)
        ###################################
        #get_point_below_tag(T_camera_tag, meters_below = 0.5, K = K)
        
        cv2.imshow("drone cam", img)
        key = cv2.waitKey(50)

while True:
    # GET THE IMAGE FROM TELLO
    frame_read = tello.get_frame_read()
    myFrame = frame_read.frame
    img = cv2.resize(myFrame, (width, height))
    track_tags(img)