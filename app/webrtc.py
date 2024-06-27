from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack

import cv2
# from fastapi.responses import JSONResponse

# from app.utils import CustomVideoTrack
from app.yolov8 import process_frame

relay = None
webcam = None
pcs = set()

class VideoTransformTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track):
        super().__init__()  # Initialize base class
        self.track = track

    async def recv(self):
        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")
        # img = CustomVideoTrack(img)
        img = process_frame(img)
        cv2.imshow("Received Video", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            for pc in pcs:  # Đóng tất cả các kết nối
                await pc.close()
            pcs.clear()
        return frame
    
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
                pc.addTrack(VideoTransformTrack(track))
        else:
            print("Track is not live.")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
