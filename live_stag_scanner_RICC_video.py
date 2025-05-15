"""
Julian Kempenaers
07/05/2025

follow instructions in 'instructions.txt'
press 'esc' to close the live scanner

This code keeps track of the n most recently detected tags and colour codes them. 
This means that even if they move out of frame for a few seconds, they will still 
have the same colour when they return. 
WARNING. The number of tags detectable in a single frame is capped at the n_col that you set. 
		to add more colours, edit 'colour_palette' and increase n_cols accordingly.
		To detect an unlimited number of tags per frame, use the scanner with "no Recent Id Colour Coding" (nRICC) instead.
"""
#modifiable variables:
#--------------------------------------------------------------------
#desired number of unique colours to cycle through (max 21)
n_cols = 15

#stag libraries to be detected
stag_libraries = [17, 19]

#normalise the view to increase contrast? (sometimes makes the tag detection better, sometimes worse)
normalise_view = False

#settings. Feel free to adjust shutterus (exposure) and gain
WIDTH = 4056
HEIGHT = 3040
#shutterus = exposure. can range from 0 to 120000. Higher exposure increases brightness (better tag detection) but also increases blurriness of moving tags (worse tag detection!)
SHUTTERUS = 3000
GAIN = 0
#----------------------------------------------------------------
import cv2
import time
import numpy as np
from picamera2 import Picamera2
import sys
import select
import stag
import skimage.draw
import scipy
from datetime import datetime

colour_palette = [
    (255, 0, 0),      # red
    (0, 255, 0),      # green
    (0, 0, 255),      # blue
    (255, 255, 0),    # yellow
    (0, 255, 255),    # cyan
    (255, 0, 255),    # magenta
    (255, 128, 0),    # orange
    (128, 0, 255),    # violet
    (0, 128, 255),    # light blue
    (128, 255, 0),    # lime
    (255, 0, 128),    # pink
    (128, 128, 0),    # olive
    (0, 128, 128),    # teal
    (128, 0, 128),    # purple
    (255, 153, 51),   # apricot
    (102, 255, 102),  # light green
    (102, 102, 255),  # periwinkle
    (255, 102, 178),  # rose
    (255, 204, 0),    # gold
    (0, 204, 153),    # turquoise
    (153, 51, 255)    # amethyst
]

def runCameraAcquisition(colour_palette, WIDTH, HEIGHT):
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
	
	recentIDs = [] #empty list wehre IDs of last n detected markers will be stored
	id_to_colour = {} 
	available_colours = colour_palette.copy()
	
	fourcc = cv2.VideoWriter_fourcc(*'XVID') #mp4 codec
	videoname = datetime.now().strftime("stag_video%Y%m%d_%H%M%S.avi")
	out=cv2.VideoWriter(videoname, fourcc, 2, (WIDTH, HEIGHT), isColor=True)

	while True:
		#capture a new frame
		yuv = picam2.capture_array("main")
		grey = yuv[:HEIGHT, :WIDTH]
		
		img, render, corners, ids, recentIDs, available_colours = detect_markers_and_assign_colours(grey, recentIDs, available_colours)
		render = apply_overlay(img, render, corners, ids, recentIDs)				
		
		out.write(render)
		#check for 's' to stop recording
		if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
			user_input = sys.stdin.readline().strip()
			if user_input.lower() == 's':
				print("Stopping video recording...")
				break
	#clean up when finished
	print("camera stopped, closing live stream")
	out.release()
	cv2.destroyAllWindows()
	
def detect_markers_and_assign_colours(grey, recentIDs, available_colours):
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
	temp_hold = []
	new_ids = []
	for k, libraryHD in enumerate(stag_libraries): #iterate over the desired stag libraries
		(corners, ids, rejected_corners) = stag.detectMarkers(img, libraryHD) 
		frame_corners.extend(corners)
		frame_ids.extend((libraryHD)*1000+ids) #create a unique marker (combination of library & tag id
	for marker_id in frame_ids: #first check for presence of each marker in the recentIDs list
		found = False
		#if the marker_id is present in the LEFT column of recentIDs
		for row in recentIDs:
			if row[0] == marker_id: #search through recentIDs and compare to the detected marker_IDs. 
				temp_hold.append(row.copy()) #duplicate the row into temp_hold
				recentIDs.remove(row) #then remove the row from recentID
				found= True
				break #once it's found we can stop searching in recentIDs
		if not found: #if the current ID wasn't found in recentIDs
			new_ids.append([marker_id]) #store it in 'new_ids' for now. 
	total_rows = len(recentIDs) + len(temp_hold) + len(new_ids)
	if total_rows > n_cols:
		x = total_rows -n_cols
		for row in recentIDs[-x:]: #for the last x rows in recentIDs
			available_colours.append(row[1]) #return the colours to available_colours pool
		recentIDs = recentIDs[:-x] #remove the last x rows from recentIDs.
	#assign colours to new IDs. 
	if new_ids:
		for i in range(len(new_ids)):
			if available_colours:
				new_ids[i].append(available_colours.pop())
			else:
				print('Number of tags detected exceeds the number of unique colours. Please change the variable "n_col" in the live_stag_scanner_RICC.py code')
	#add temp_hold and new_ids to the top of recentIDs
	recentIDs = temp_hold + new_ids + recentIDs
	
			
	return img, render, frame_corners, frame_ids, recentIDs, available_colours
		
	
def apply_overlay(img, render, corners, ids, recentIDs):		
	for i, marker in enumerate(corners):
		marker = marker[0] #extract marker corners   
		marker_id = ids[i]
		color = next((row[1] for row in recentIDs if row[0] == marker_id), None)
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
	print("Recording in progress. Type 's' and press Enter in this terminal to stop.")
	runCameraAcquisition(colour_palette, WIDTH, HEIGHT)

	
