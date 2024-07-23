from datetime import datetime
import json
from aiortc import MediaStreamTrack
from av import VideoFrame
import cv2
import torch

from app.yolov8 import draw_detection, process_frame, draw_lines_if_needed
latest_detected_objects = {}

class CustomVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track):
        super().__init__()
        self.track = track
        self.frame_count = 0
    
    def check_write_data(self):
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}.mp4"
        self.input = cv2.VideoWriter(f'data_input/{filename}', cv2.VideoWriter_fourcc(*'mp4v'), 30, (1280, 720))
        self.out = cv2.VideoWriter(f'data_output/{filename}', cv2.VideoWriter_fourcc(*'mp4v'), 30, (1280, 720))
        # Pre-check if CUDA is available once
        self.is_cuda = torch.cuda.is_available()
        self.position = (30, 80)

    def write_text(self, img):
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(img, f"{current_time}-{self.is_cuda}", self.position, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    async def recv(self):
        global latest_detected_objects
        frame = await self.track.recv()

        try:
            img = frame.to_ndarray(format="bgr24")
            # Process every 3rd frame to reduce processing load
            if self.frame_count % 3 == 0:
                img, detected_objects = process_frame(img)
                latest_detected_objects = detected_objects
            else:
                draw_lines_if_needed(img, latest_detected_objects)
                if "block_thang" in latest_detected_objects:
                    draw_detection(img, latest_detected_objects["block_thang"], "block_thang", 0, img.shape[1] // 3, (0, 0, 255))
                if "pallet" in latest_detected_objects:
                    draw_detection(img, latest_detected_objects["pallet"], "pallet", 0, img.shape[1] // 3, (0, 255, 0))
                if "block" in latest_detected_objects:
                    draw_detection(img, latest_detected_objects["block"], "block", 0, img.shape[1] // 3, (0, 255, 0))
            
            # Convert processed image back to VideoFrame
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            self.frame_count += 1
            return new_frame
        except Exception as e:
            print(f"Failed to process frame: {e}")
            return frame
