from datetime import datetime
import platform
import threading
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
import cv2
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.utils import CustomVideoTrack

app = FastAPI()

relay = None
webcam = None
pcs = set()
write_video_thread = None
video_capture = None
stop_event = threading.Event()

# rtsp_url = "rtsp://admin:admin@192.168.0.19:8081/h264_pcm.sdp"  # or "rtsp://admin:admin@192.168.0.19:8081/h264_ulaw.sdp"
rtsp_url = "rtsp://admin:admin@192.168.50.46:8081/h264_pcm.sdp"
play_from = "data_input/xenang_cut2.mp4"

def write_video(ip_camera, stop_event):
    global video_capture
    video_capture = cv2.VideoCapture(ip_camera)

    frame_width = int(video_capture.get(3))
    frame_height = int(video_capture.get(4))
    size = (frame_width, frame_height)
    fps_video = int(video_capture.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"video_{timestamp}.mp4"
    result_in = cv2.VideoWriter(f'data_input/{filename}', fourcc, fps_video, size)

    while not stop_event.is_set() and video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            break
        
        result_in.write(frame)
        # cv2.imshow("frame", frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    video_capture.release()
    result_in.release()
    cv2.destroyAllWindows()
    print("Video recording stopped")

def create_local_tracks(play_from=None, decode=True, buffer_size="64000"):
    global relay, webcam
    options = {
        "framerate": "30",
        "video_size": "640x360",
        "rtsp_transport": "tcp",  # Use TCP transport to reduce packet loss
        "buffer_size": buffer_size  # Adjustable buffer size
    }
    
    if play_from:
        player = MediaPlayer(play_from, decode=decode, options=options)
        return player.video
    else:
        if platform.system() == "Darwin":
            webcam = MediaPlayer("default:none", format="avfoundation", options=options)
        elif platform.system() == "Windows":
            webcam = MediaPlayer(rtsp_url, format="rtsp", options=options)
        else:
            webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
        relay = MediaRelay()
        return relay.subscribe(webcam.video)

@app.post("/offer")
async def handle_offer(request: Request):
    # global write_video_thread, stop_event
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState in ["failed", "closed", "disconnected"]:
            print("Connection closed, stopping video recording.")
            await pc.close()
            pcs.discard(pc)
            if webcam and webcam.video:
                webcam.video.stop()
            stop_event.set()  # Signal the write_video thread to stop
            print("stop_event set.")

    buffer_size = "64000"  # Start with a moderate buffer size for local network
    video = create_local_tracks(play_from=play_from, decode=True, buffer_size=buffer_size)
    
    if video:
        process_video = CustomVideoTrack(video)
        pc.addTrack(process_video)

        # Start the video writing thread
        # stop_event = threading.Event()  # Create a new stop_event for the new session
        # write_video_thread = threading.Thread(target=write_video, args=(rtsp_url, stop_event))
        # write_video_thread.start()

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return JSONResponse({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
