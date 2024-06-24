from datetime import datetime
import json
from aiortc import MediaStreamTrack
from av import VideoFrame
import cv2
import torch

from app.yolov8 import process_frame

class CustomVideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track, filename):
        super().__init__()
        self.track = track
        self.log_filename = f'data/log_{filename}.json'  # Log file
        self.frame_count = 0
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}.mp4"
        self.input = cv2.VideoWriter(f'data_input/{filename}', cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))
        self.out = cv2.VideoWriter(f'data_output/{filename}', cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))
        

    async def recv(self):
        frame = await self.track.recv()
        self.frame_count += 1
        
        try:
            img = frame.to_ndarray(format="bgr24")
            # self.input.write(img)
            # print(img.shape)
            is_cuda = torch.cuda.is_available()
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            position = (30, 80)
            cv2.putText(img, f"{current_time}-{is_cuda}", position, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            if self.frame_count % 5:
                img = process_frame(img)
            # self.out.write(img)
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base

            return frame
        except Exception as e:
            print(f"Failed to process frame: {e}")
            return frame
    