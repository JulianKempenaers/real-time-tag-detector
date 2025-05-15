"""
Julian Kempenaers
07/05/2025

follow instructions in 'instructions.txt'
press 'esc' to close the live scanner
"""
#-----------------------------------------------------------------------------
#Modifiable variables
#stag libraries to be detected
stag_libraries = [17, 19]

#to zoom in or out on the video view (it zooms in on the top left corner)
#4x zoom = 4056x3040 
#2x zoom = 2028x1520
#1x zoom = 1014x760
display_width = 2028
display_height = 1520

#normalise the view to increase contrast? (sometimes makes the tag detection better, sometimes worse)
normalise_view = True

#settings. Feel free to adjust shutterus (exposure) and gain
WIDTH = 4056
HEIGHT = 3040
#shutterus = exposure. can range from 0 to 120000. Higher exposure increases brightness (better tag detection) but also increases blurriness of moving tags (worse tag detection!)
SHUTTERUS = 3000
GAIN = 0
#------------------------------------------------------------------------------------------
import cv2
import time
import numpy as np
from picamera2 import Picamera2
import sys
import select
import stag
import skimage.draw
import scipy

def runCameraAcquisition(display_width, display_height):
	"""
	Run the camera acquisition loop and process frames with overlay.
	"""
	FORMAT = 'YUV420'
	picam2 = Picamera2()
	config = picam2.create_still_configuration({
		'format': FORMAT, 'size': (WIDTH, HEIGHT)
	})
	picam2.configure(config)
	picam2.set_controls({"ExposureTime": SHUTTERUS, "AnalogueGain": GAIN})
	
	picam2.start()
	time.sleep(2)#camera warmup time
	
	
	while True:
		#capture a new frame
		yuv = picam2.capture_array("main")
		grey = yuv[:HEIGHT, :WIDTH]
		
		img, render, corners, ids = detect_markers(grey)
		render = apply_overlay(img, render, corners, ids)				
		resized_render = cv2.resize(render, (display_width, display_height))
		
		cv2.namedWindow('Live Stream', cv2.WND_PROP_FULLSCREEN) #create livestream window
		cv2.setWindowProperty('Live Stream', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) #set the window fullscreen
		cv2.imshow('Live Stream', resized_render)		
		#check for 'esc' to stop recording
		key = cv2.waitKey(1) & 0xFF
		
		if key == 27:
			print("Stopping frame capture...")
			break	
	#clean up when finished
	print("camera stopped, closing live stream")
	cv2.destroyAllWindows()
	
def detect_markers(grey):
	if normalise_view:
		# normalize to 0-255 and convert to uint8
		grey_8bit = cv2.convertScaleAbs(grey, alpha=(255.0 / grey.max()))
	else:
		#grey_8bit = (grey >> 2).astype(np.uint8)#without normalising
		grey_8bit = grey.astype(np.uint8)
	img = 255 - grey_8bit #invert image for qr detection
	render = np.repeat(grey_8bit.copy()[:,:,np.newaxis], 3, axis = 2) #reshapes image array to add a new axis: convert from grayscale to 3D array with 3 identical channels (simulating RGB)
	frame_corners = []
	frame_ids = []
	for k, libraryHD in enumerate(stag_libraries): #iterate over the 17 and 19 stag libraries
		(corners, ids, rejected_corners) = stag.detectMarkers(img, libraryHD) 
		frame_corners.extend(corners)
		frame_ids.extend((libraryHD)*1000+ids) #create a unique marker (combination of library & tag id)	
			
	return img, render, frame_corners, frame_ids
		
	
def apply_overlay(img, render, corners, ids):		
	for i, marker in enumerate(corners):
		marker = marker[0] #extract marker corners   
		marker_id = ids[i]
		color = (0, 0, 255)
		assert marker.ndim == 2 #make marker data 2D
		#add boxes to mask
		single_marker_mask = np.zeros_like(render[:, :, 0], dtype = np.bool_) #initiate mask for this marker
		rr, cc = skimage.draw.polygon_perimeter(marker[:, 1], marker[:, 0], render.shape[:2]) #get row and column coordinates of the ROI 
		single_marker_mask[rr, cc] = True #set coordinate pixel as 'true' in the mask
		single_marker_mask = scipy.ndimage.binary_dilation(single_marker_mask, iterations=4) #dilate the mask to make the ROI bigger
		render[single_marker_mask, :] = color  
		
		# Draw ID text
		#compute center
		center_x = 	int(np.mean(marker[:, 0]))-400
		center_y = int(np.mean(marker[:, 1])) -10  
		height, width = render.shape[:2]
		#check if the text falls within image bounds
		if center_x-40 < 0 or center_x >= width or center_y-25 < 0 or center_y >= height:
			
			center_x = int(np.mean(marker[:, 0])) +60
			center_y = int(np.mean(marker[:, 1])) +50    
		cv2.putText(render, str(marker_id[0]), (center_x, center_y), cv2.FONT_HERSHEY_SIMPLEX, 3, color, 6)	
	return render
	
if __name__ == '__main__':
	#Start the camera acquisition process
	runCameraAcquisition(display_width, display_height)
	
