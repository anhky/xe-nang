from datetime import datetime
import json
from aiortc import MediaStreamTrack
from av import VideoFrame
import cv2

from app.yolov8 import process_frame

class CustomVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track, filename):
        super().__init__()
        self.track = track
        self.frame_count = 0
        self.object_counts = None
        self.center_points = {}
        self.running_boats = {}
        self.out = cv2.VideoWriter(f'data/out_{filename}', cv2.VideoWriter_fourcc(*'mp4v'), 30, (1280, 720))
        self.set_trackid_moving = set()
        self.set_trackid_stationary = set()
        self.set_trackid_slow = set()
        self.movement_logs = {}
        self.log_filename = f'data/log_{filename}.json'  # Log file

    async def recv(self):
        frame = await self.track.recv()
        self.frame_count += 1

        try:
            img = frame.to_ndarray(format="bgr24")
            img = cv2.resize(img, (1280, 720))
            img = process_frame(img)

            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base

            self.out.write(img)
            
            return new_frame
        except Exception as e:
            print(f"Failed to process frame: {e}")
            return frame
    