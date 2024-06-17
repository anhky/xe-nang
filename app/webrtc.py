import os
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
import platform

import cv2
from fastapi.responses import JSONResponse

from app.utils import CustomVideoTrack

filename = "2.mp4"
relay = None
webcam = None
pcs = set()

def create_local_tracks(play_from, decode):
    global relay, webcam
    # options = {"framerate": "30", "video_size": "1280x720"}
    # options = {"framerate": "30", "video_size": "1280x720", "rtbufsize": "10000000"}
    # options = {"framerate": "30", "video_size": "1280x720", "rtbufsize": "10000000", "pix_fmt": "yuv420p"}
    options = {"framerate": "30", "video_size": "960x540"}
    options = {"framerate": "30", "video_size": "640x360"}

    if play_from:
        player = MediaPlayer(play_from, decode=decode, options=options)
        return player.audio, player.video
    else:
        if relay is None:
            if platform.system() == "Darwin":
                webcam = MediaPlayer("default:none", format="avfoundation", options=options)
            elif platform.system() == "Windows":
                webcam = MediaPlayer("video=Logi C270 HD WebCam", format="dshow", options=options)
            else:
                webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
            relay = MediaRelay()
        return None, relay.subscribe(webcam.video)

async def handle_offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.iceConnectionState in ["failed", "closed", "disconnected"]:
            await pc.close()
            pcs.discard(pc)
            if webcam and webcam.video:
                webcam.video.stop()
    
    
    # play_from = f"./data/{filename}"
    play_from = None
    decode = True
    audio, video = create_local_tracks(play_from=play_from, decode=decode)
    if video:
        process_video = CustomVideoTrack(video, filename)
        pc.addTrack(process_video)
        

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
