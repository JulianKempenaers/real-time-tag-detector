"""
Julian Kempenaers
07/05/2025

follow instructions in 'instructions.txt'
press 'esc' to close the live scanner

This code keeps track of the n most recently detected tags and colour codes them. 
This means that even if they move out of frame for a few seconds, they will still 
have the same colour when they return. 
WARNING. The number of tags detectable in a single frame is capped at the n_col that you set. 
		to add more colours, edit 'colour_palette' edit the limit for n_cols in STag_GUI.py
		To detect an unlimited number of tags per frame, simply set it to '1', resulting in no colour coding at all. 
"""
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
import threading
from datetime import datetime
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from STag_GUI import STag_GUI
from STag_GUI import load_settings


def launch_settings_gui():
	root = ttk.Window(themename="solar")  # or try other themes like "darkly", "cyborg", "minty"
	app = STag_GUI(root)
	root.mainloop()
	return app.started

# Run the GUI
if not launch_settings_gui(): #because launch_settings_gui returns False if 'start' wasn't pressed
	print("User closed the GUI without pressing Start. Exiting.")
	sys.exit(0)  # Clean exit

# After it closes, load settings and continue
settings = load_settings()  # assuming you import this too from STag_GUI

stag_libraries = settings["stag_libraries"]
normalise_view = settings["normalise_view"]
SHUTTERUS = settings["SHUTTERUS"]
GAIN = settings["GAIN"]
input_resolution_factor = settings["input_resolution_factor"]
output_zoom = settings["output_zoom"]
save_video = settings["save_video"]
colour_coding = settings["colour_coding"]
n_cols = settings["n_cols"]
filename_addon = settings["filename_addon"]


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
def camera_capture_loop(picam2, output_holder, width, height, display_width, display_height, crop_x, crop_y):
	while True:
		yuv = picam2.capture_array("main")
		grey = yuv[crop_y:crop_y + display_height, crop_x:crop_x + display_width] #cropping the image to the display height/width
		output_holder[0] = grey

def runCameraAcquisitionDual(colour_palette, input_resolution_factor, output_zoom):
	WIDTH = 1014*input_resolution_factor
	HEIGHT = 760*input_resolution_factor
	display_width = int(WIDTH/output_zoom)
	display_height = int(HEIGHT/output_zoom)
	crop_x = (WIDTH - display_width) // 2
	crop_y = (HEIGHT - display_height) // 2
	FORMAT = 'YUV420'

	# Init both cameras
	picam1 = Picamera2(0)
	config1 = picam1.create_still_configuration({'format': FORMAT, 'size': (WIDTH, HEIGHT)})
	picam1.configure(config1)
	picam1.set_controls({"ExposureTime": SHUTTERUS, "AnalogueGain": GAIN})

	picam2 = Picamera2(1)
	config2 = picam2.create_still_configuration({'format': FORMAT, 'size': (WIDTH, HEIGHT)})
	picam2.configure(config2)
	picam2.set_controls({"ExposureTime": SHUTTERUS, "AnalogueGain": GAIN})

	# Start both cameras
	picam1.start()
	picam2.start()
	time.sleep(2)

	# Hold frames from threads
	frame1_holder = [None]
	frame2_holder = [None]

	# Start threads to continuously update frames
	t1 = threading.Thread(target=camera_capture_loop, args=(picam1, frame1_holder, WIDTH, HEIGHT, display_width, display_height, crop_x, crop_y))
	t2 = threading.Thread(target=camera_capture_loop, args=(picam2, frame2_holder, WIDTH, HEIGHT, display_width, display_height, crop_x, crop_y))
	t1.daemon = True
	t2.daemon = True
	t1.start()
	t2.start()

	recentIDs = []
	available_colours = colour_palette.copy()
	recentIDs_lock = threading.Lock()
	
	if save_video:
		output_dir = "output_videos"
		os.makedirs(output_dir, exist_ok=True)
		videoname = os.path.join(output_dir, datetime.now().strftime(f"stag_video%Y%m%d_%H%M%S_{filename_addon}.mp4"))
		fourcc = cv2.VideoWriter_fourcc(*'mp4v') #mp4 codec
		out=cv2.VideoWriter(videoname, fourcc, 5, (WIDTH, HEIGHT), isColor=True)

	while True:
		if frame1_holder[0] is None or frame2_holder[0] is None:
			continue  # wait until both frames are ready

		grey1 = frame1_holder[0]
		grey2 = frame2_holder[0]

		# Process first frame
		with recentIDs_lock:
			img1, render1, corners1, ids1, recentIDs, available_colours = detect_markers_and_assign_colours(
			grey1, recentIDs, available_colours, display_width, display_height)

		render1 = apply_overlay(img1, render1, corners1, ids1, recentIDs)
		resized1 = cv2.resize(render1, (int(WIDTH*4/input_resolution_factor), int(HEIGHT*4/input_resolution_factor)), interpolation=cv2.INTER_NEAREST)


		# Process second frame
		with recentIDs_lock:
			img2, render2, corners2, ids2, recentIDs, available_colours = detect_markers_and_assign_colours(
			grey2, recentIDs, available_colours, display_width, display_height)

		render2 = apply_overlay(img2, render2, corners2, ids2, recentIDs)
		resized2 = cv2.resize(render2, (int(WIDTH*4/input_resolution_factor), int(HEIGHT*4/input_resolution_factor)), interpolation=cv2.INTER_NEAREST)


		# Combine both images side by side
		combined = np.hstack((resized1, resized2))
		
		#create recentID text bar
		if colour_coding:
			text_bar = add_recentID_bar(recentIDs, combined)
			combined = np.vstack((combined, text_bar))

		# Display
		cv2.namedWindow('Dual Camera Live Stream - PRESS ESC TO EXIT', cv2.WND_PROP_FULLSCREEN)
		cv2.setWindowProperty('Dual Camera Live Stream - PRESS ESC TO EXIT', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
		cv2.putText(combined, "Press ESC to exit", (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
		cv2.imshow('Dual Camera Live Stream - PRESS ESC TO EXIT', combined)
		if save_video:
			frame_to_write = pad_to_size(combined, WIDTH, HEIGHT)
			out.write(frame_to_write)

		# Exit on ESC
		if cv2.waitKey(1) & 0xFF == 27:
			print("Stopping dual camera stream...")
			break
	if save_video:
		out.release()
	cv2.destroyAllWindows()
	

	
def runCameraAcquisition(colour_palette, input_resolution_factor, output_zoom):
	"""
	Run the camera acquisition loop and process frames with overlay.
	"""
	WIDTH = 1014*input_resolution_factor
	HEIGHT = 760*input_resolution_factor
	display_width = int(WIDTH/output_zoom)
	display_height = int(HEIGHT/output_zoom)
	crop_y = (HEIGHT - display_height) // 2
	crop_x = (WIDTH - display_width) // 2
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
	
	if save_video:
		output_dir = "output_videos"
		os.makedirs(output_dir, exist_ok=True)
		videoname = os.path.join(output_dir, datetime.now().strftime(f"stag_video%Y%m%d_%H%M%S_{filename_addon}.mp4"))
		fourcc = cv2.VideoWriter_fourcc(*'mp4v') #mp4 codec
		out=cv2.VideoWriter(videoname, fourcc, 5, (WIDTH, HEIGHT), isColor=True)
	while True:
		#capture a new frame
		yuv = picam2.capture_array("main")
		grey = yuv[crop_y:crop_y + display_height, crop_x:crop_x + display_width] #cropping the image to the display height/width

		img, render, corners, ids, recentIDs, available_colours = detect_markers_and_assign_colours(grey, recentIDs, available_colours, display_width, display_height)
		render = apply_overlay(img, render, corners, ids, recentIDs)				
		resized_render = cv2.resize(render, (int(WIDTH*4/input_resolution_factor), int(HEIGHT*4/input_resolution_factor)), interpolation=cv2.INTER_NEAREST)
		
		#create recentID text bar
		if colour_coding:
			text_bar = add_recentID_bar(recentIDs, resized_render)
			resized_render = np.vstack((resized_render, text_bar))
		
		cv2.namedWindow('Live Stream - PRESS ESC TO EXIT', cv2.WND_PROP_FULLSCREEN) #create livestream window
		cv2.setWindowProperty('Live Stream - PRESS ESC TO EXIT', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) #set the window fullscreen
		cv2.putText(resized_render, "Press ESC to exit", (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
		cv2.imshow('Live Stream - PRESS ESC TO EXIT', resized_render)		
		if save_video:
			frame_to_write = pad_to_size(resized_render, WIDTH, HEIGHT)
			out.write(frame_to_write)
		#check for 'esc' to stop recording
		key = cv2.waitKey(1) & 0xFF
		
		if key == 27:
			print("Stopping frame capture...")
			break	
	#clean up when finished
	print("camera stopped, closing live stream")
	if save_video:
		out.release()
	cv2.destroyAllWindows()
	

	
def detect_markers_and_assign_colours(grey, recentIDs, available_colours, display_width, display_height):
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
	if colour_coding:
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
		if colour_coding:
			color = next((row[1] for row in recentIDs if row[0] == marker_id), None)
		else:
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
		center_x = 	int(np.mean(marker[:, 0]))
		center_y = int(np.mean(marker[:, 1]))  
		height, width = render.shape[:2]
		#check if the text falls within image bounds
		if center_x-75 < 0 :
			text_x = center_x+30
		else:
			text_x = 	center_x-75
		if center_y-35 < 0 :
			text_y = center_y+50
		else:
			text_y = center_y -20
		cv2.putText(render, str(marker_id[0]), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5*input_resolution_factor, color, int(round(1*input_resolution_factor)))	
	return render

def add_recentID_bar(recentIDs, combined):
	bar_height = 200
	text_bar = np.ones((bar_height, combined.shape[1], 3), dtype=np.uint8) * 255  # white background
	font = cv2.FONT_HERSHEY_SIMPLEX
	font_scale = 5
	thickness = 4
	x = 10  # Starting X position
	y = 180  # Y position (baseline of text)

	for marker_id, color in recentIDs:
		text = str(marker_id)

		# Draw text
		cv2.putText(text_bar, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

		# Estimate text size and advance x position
		(text_width, _), _ = cv2.getTextSize(text, font, font_scale, thickness)
		x += text_width + 20  # Add some spacing after each ID
	return text_bar
	
def pad_to_size(image, target_width, target_height, pad_color=(0, 0, 0)):
	img_h, img_w = image.shape[:2]
	aspect_ratio = img_w / img_h
	target_ratio = target_width / target_height

	# Resize while preserving aspect ratio
	if aspect_ratio > target_ratio:
		new_w = target_width
		new_h = int(target_width / aspect_ratio)
	else:
		new_h = target_height
		new_w = int(target_height * aspect_ratio)

	resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

	# Compute padding amounts
	top = (target_height - new_h) // 2
	bottom = target_height - new_h - top
	left = (target_width - new_w) // 2
	right = target_width - new_w - left

	# Pad with color
	padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=pad_color)
	return padded


if __name__ == '__main__':
	import sys
	import traceback
	from picamera2.encoders import Quality
	import traceback
	
	def is_camera_usable(index):
		try:
			test_width=1014
			test_height= 760
			cam = Picamera2(index)
			config = cam.create_still_configuration({'format': 'YUV420', 'size': (1014, 760)})
			cam.configure(config)
			cam.start()
			time.sleep(0.5)
			cam.stop()
			cam.close()
			return True
		except Exception as e:
			print(f"Camera {index} failed: {e}")
			return False

	try:
		usable_cameras = [i for i in range(2) if is_camera_usable(i)]
		if not usable_cameras:
			print("No usable cameras detected. Exiting.")
			sys.exit(1)
		elif len(usable_cameras) == 1:
			print("One usable camera detected. Running single-camera mode.")
			runCameraAcquisition(colour_palette, input_resolution_factor, output_zoom)
		elif len(usable_cameras) >= 2:
			print("Two usable cameras detected. Running dual-camera mode.")
			runCameraAcquisitionDual(colour_palette, input_resolution_factor, output_zoom)

	except Exception:
		print("Unhandled exception occurred:")
		traceback.print_exc()
		sys.exit(1)
