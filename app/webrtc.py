from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from av import VideoFrame

import cv2
# from fastapi.responses import JSONResponse

# from app.utils import CustomVideoTrack
from app.yolov8 import process_frame
import torch 
from datetime import datetime

relay = None
webcam = None
pcs = set()

class VideoTransformTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track):
        super().__init__()  # Initialize base class
        self.track = track
        self.frame_count = 0
    
    async def recv(self):
        try:
            frame = await self.track.recv()
            img = frame.to_ndarray(format="bgr24")
            if self.frame_count % 5 == 0:
                img = process_frame(img)
                self.processed_frame = img
            else:
                img = self.processed_frame
            self.frame_count += 1
            # code show hinh ảnh tại localhost orin
            # is_cuda = torch.cuda.is_available()
            # now = datetime.now()
            # current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            # position = (30, 80)
            # cv2.putText(img, f"{current_time}-{is_cuda}", position, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # cv2.imshow("Received Video", img)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     cv2.destroyAllWindows()
            #     for pc in pcs:  # Đóng tất cả các kết nối
            #         await pc.close()
            #     pcs.clear()
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
        except Exception as e:
            print("e", e)
    
async def handle_offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState in ["failed", "disconnected", "closed"]:
            cv2.destroyAllWindows()
            pcs.discard(pc)
            await pc.close()
    
    @pc.on("track")
    def on_track(track):
        print("Track received with kind:", track.kind)
        if track.readyState == "live":
            if track.kind == "video":
                print("Xin caho")
                pc.addTrack(VideoTransformTrack(track))
        else:
            print("Track is not live.")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
