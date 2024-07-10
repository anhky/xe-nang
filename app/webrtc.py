import platform
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
from fastapi.responses import JSONResponse

from app.utils import CustomVideoTrack

relay = None
webcam = None
pcs = set()

def create_local_tracks(play_from, decode):
    global relay, webcam
    options = {"framerate": "30", "video_size": "640x360"}

    if play_from:
        player = MediaPlayer(play_from, decode=decode, options=options)
        return player.audio, player.video
    else:
        if relay is None:
            if platform.system() == "Darwin":
                webcam = MediaPlayer("default:none", format="avfoundation", options=options)
            elif platform.system() == "Windows":
                # webcam = MediaPlayer("video=Integrated Webcam", format="dshow", options=options)
                webcam = MediaPlayer("rtsp://admin:admin@192.168.0.19:8081/h264_pcm.sdp", format="rtsp", options=options)
            else:
                webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
            relay = MediaRelay()
        return relay.subscribe(webcam.video)

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

    # Use the appropriate video source
    play_from = None
    decode = True
    video = create_local_tracks(play_from=play_from, decode=decode)
    
    # if video:
    process_video = CustomVideoTrack(video)
    pc.addTrack(process_video)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return JSONResponse({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})

# webcam = MediaPlayer("rtsp://admin:admin@192.168.0.19:8081/h264_pcm.sdp", format="rtsp", options=options)
           