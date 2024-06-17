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
        self.log_filename = f'data/log_{filename}.json'  # Log file
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}.mp4"
        self.input = cv2.VideoWriter(f'data_input/{filename}', cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))
        self.out = cv2.VideoWriter(f'data_output/{filename}', cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))

    async def recv(self):
        frame = await self.track.recv()
        try:
            img = frame.to_ndarray(format="bgr24")
            self.input.write(img)
            print(img.shape)
            img = process_frame(img)
            self.out.write(img)
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base

            
            
            return frame
        except Exception as e:
            print(f"Failed to process frame: {e}")
            return frame
    