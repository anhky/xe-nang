import os
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay
import platform

import cv2
from fastapi.responses import JSONResponse

from app.utils import CustomVideoTrack

filename = "2.mp4"
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
        cv2.imshow("Received Video", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            for pc in pcs:  # Đóng tất cả các kết nối
                await pc.close()
            pcs.clear()
        return frame
    
# def create_local_tracks(play_from, decode):
#     global relay, webcam
#     # options = {"framerate": "30", "video_size": "1280x720"}
#     # options = {"framerate": "30", "video_size": "1280x720", "rtbufsize": "10000000"}
#     # options = {"framerate": "30", "video_size": "1280x720", "rtbufsize": "10000000", "pix_fmt": "yuv420p"}
#     options = {"framerate": "30", "video_size": "960x540"}
#     options = {"framerate": "30", "video_size": "640x360"}

#     if play_from:
#         player = MediaPlayer(play_from, decode=decode, options=options)
#         return player.audio, player.video
#     else:
#         if relay is None:
#             if platform.system() == "Darwin":
#                 webcam = MediaPlayer("default:none", format="avfoundation", options=options)
#             elif platform.system() == "Windows":
#                 webcam = MediaPlayer("video=Logi C270 HD WebCam", format="dshow", options=options)
#             else:
#                 webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
#             relay = MediaRelay()
#         return None, relay.subscribe(webcam.video)

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
        
    # play_from = f"./data/{filename}"
    # play_from = None
    # decode = True
    # audio, video = create_local_tracks(play_from=play_from, decode=decode)
    # if video:
    #     process_video = CustomVideoTrack(video, filename)
    #     pc.addTrack(process_video)
        

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
