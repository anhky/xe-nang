import os
import random
import cv2
import numpy as np
import torch
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import logging

# Disable logging
logging.getLogger('ultralytics').setLevel(logging.ERROR)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Path to the trained model weights
model_path = "./models/m_merge_new_det_N.pt"
start_img_path = "./data/start.jpg"
pending_img_path = "./data/pending.png"

# Load YOLO model
model = YOLO(model_path)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
names = model.model.names
colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

# Initialize DeepSort tracker
def initialize_tracker():
    return DeepSort(max_age=30)

tracker = initialize_tracker()
prev_block_detected = False

# Define the class names you are interested in
class_names_of_interest = ["pallet", "block", "block_thang"]

def draw_bracketed_bounding_box(image, top_left, bottom_right, label, color=(255, 0, 0), box_color=(255, 0, 0), text_color=(255, 255, 255), full_box=True):
    top_right = (bottom_right[0], top_left[1])
    bottom_left = (top_left[0], bottom_right[1])

    bracket_length = 30  # Length of the bracket lines
    thickness = 5       # Thickness of the lines

    if full_box:
        # Draw full brackets at the corners of the bounding box
        cv2.line(image, top_left, (top_left[0] + bracket_length, top_left[1]), color, thickness)
        cv2.line(image, top_left, (top_left[0], top_left[1] + bracket_length), color, thickness)
        cv2.line(image, top_right, (top_right[0] - bracket_length, top_right[1]), color, thickness)
        cv2.line(image, top_right, (top_right[0], top_right[1] + bracket_length), color, thickness)
        cv2.line(image, bottom_left, (bottom_left[0] + bracket_length, bottom_left[1]), color, thickness)
        cv2.line(image, bottom_left, (bottom_left[0], bottom_left[1] - bracket_length), color, thickness)
        cv2.line(image, bottom_right, (bottom_right[0] - bracket_length, bottom_right[1]), color, thickness)
        cv2.line(image, bottom_right, (bottom_right[0], bottom_right[1] - bracket_length), color, thickness)
    else:
        # Draw partial brackets for half top left and bottom right
        cv2.line(image, top_left, (top_left[0] + bracket_length, top_left[1]), color, thickness)
        cv2.line(image, top_left, (top_left[0], top_left[1] + bracket_length), color, thickness)
        cv2.line(image, bottom_right, (bottom_right[0] - bracket_length, bottom_right[1]), color, thickness)
        cv2.line(image, bottom_right, (bottom_right[0], bottom_right[1] - bracket_length), color, thickness)

    box_width, box_height = 200, 40
    label_box_top_left = (bottom_right[0] + 10, top_left[1])
    label_box_bottom_right = (label_box_top_left[0] + box_width, label_box_top_left[1] + box_height)

    # Draw label box
    # cv2.rectangle(image, label_box_top_left, label_box_bottom_right, box_color, cv2.FILLED)
    # cv2.putText(image, label, (label_box_top_left[0] + 5, label_box_top_left[1] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)

def draw_detection(frame, ltrb, class_name, conf, track_id, crop_x, color=(0, 0, 255), box_color=(0, 0, 255), text_color=(255, 255, 255)):
    x1, y1, x2, y2 = map(int, ltrb)
    x1 += crop_x
    x2 += crop_x
    if conf is not None:
        label = f"{class_name} {conf:.2f} ID: {track_id}"
        if class_name == "block_thang":
            draw_bracketed_bounding_box(frame, (x1, y1), (x2, y2), label, (0, 0, 255), box_color, text_color, full_box=True)
        else:
            draw_bracketed_bounding_box(frame, (x1, y1), (x2, y2), label, (0, 255, 0), box_color, text_color, full_box=False)

def draw_lines(frame, pallet, block, block_thang, crop_x):
    pallet_x1, pallet_y1 = int(pallet[0]) + crop_x, int(pallet[1])
    block_thang_x1 = int(block_thang[0]) + crop_x
    block_thang_y1 = int(block_thang[1])
    block_thang_x2 = int(block_thang[2]) + crop_x
    block_thang_y2 = int(block_thang[3])
    block_y1 = int(block[1])

    if block_thang_y1 < pallet_y1 < block_thang_y2:
        cv2.line(frame, (pallet_x1, pallet_y1), (block_thang_x2, pallet_y1), (0, 0, 255), 2)
        cv2.putText(frame, "start alignment", (pallet_x1 + (block_thang_x2 - pallet_x1) // 2, pallet_y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Load the start image
        start_img = cv2.imread(start_img_path)
        start_img = cv2.resize(start_img, (frame.shape[1] // 10, frame.shape[0] // 10))  # Resize to fit in the corner
        
        # Extract the dimensions of the start image
        start_h, start_w, _ = start_img.shape

        # Overlay the start image onto the frame
        frame[0:start_h, 0:start_w] = start_img

        # Convert the start image to the same color space as the frame
        start_img_hsv = cv2.cvtColor(start_img, cv2.COLOR_BGR2HSV)
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Calculate the mean color of the start image
        mean_color = cv2.mean(start_img_hsv)[:3]

        # Adjust the hue, saturation, and value of the frame
        frame_hsv[..., 0] = mean_color[0]
        frame_hsv[..., 1] = mean_color[1]
        frame_hsv[..., 2] = frame_hsv[..., 2] * (mean_color[2] / 255.0)

        # Convert back to BGR color space
        frame = cv2.cvtColor(frame_hsv, cv2.COLOR_HSV2BGR)
    else:
        # Load the pending image
        pending_img = cv2.imread(pending_img_path)
        pending_img = cv2.resize(pending_img, (frame.shape[1] // 10, frame.shape[0] // 10))  # Resize to fit in the corner
        
        # Extract the dimensions of the pending image
        pending_h, pending_w, _ = pending_img.shape

        # Overlay the pending image onto the frame
        frame[0:pending_h, 0:pending_w] = pending_img
    

def process_frame(frame):
    global tracker, prev_block_detected

    height, width, _ = frame.shape
    crop_x = width // 3
    cropped_frame = frame[:, crop_x:]

    results = model(cropped_frame)
    block_detected = False
    detect = []
    detected_objects = {}

    for result in results:
        for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
            class_id = int(cls)
            if conf > 0.8 and class_id != 2:
                class_name = model.names[class_id]
                if class_name in class_names_of_interest:
                    x1, y1, x2, y2 = map(int, box)
                    detect.append([[x1, y1, x2 - x1, y2 - y1], conf, class_id])
                if class_name == "block_thang":
                    block_detected = True

    if block_detected:
        try:
            tracks = tracker.update_tracks(detect, frame=cropped_frame)
            for track in tracks:
                if not track.is_confirmed():
                    continue
                track_id = track.track_id
                ltrb = track.to_ltrb()
                class_id = track.get_det_class()
                class_name = model.names[class_id]
                conf = track.get_det_conf()
                if class_name in class_names_of_interest:
                    detected_objects[class_name] = ltrb
                
                draw_detection(frame, ltrb, class_name, conf, track_id, crop_x)
        except Exception as e:
            print("Error:", e)
    else:
        if prev_block_detected:
            tracker = initialize_tracker()
    
    if "pallet" in detected_objects and "block" in detected_objects and "block_thang" in detected_objects:
        draw_lines(frame, detected_objects["pallet"], detected_objects["block"], detected_objects["block_thang"], crop_x)
    
    prev_block_detected = block_detected

    return frame

# Additional optimizations can include:
# - Reducing the resolution of the input frames if high resolution is not necessary
# - Skipping frames for detection and tracking if real-time processing is not critical
# - Optimizing model loading and using mixed precision if supported by the hardware and model

