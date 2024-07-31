from datetime import datetime
import platform
import threading
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
import cv2
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.utils import CombinedVideoTrack, CustomVideoTrack

app = FastAPI()

webcam_1 = None
webcam_2 = None
pcs = set()
write_video_1_thread = None
write_video_2_thread = None
video_capture = None
stop_event = threading.Event()

# rtsp_url = "rtsp://admin:admin@192.168.0.19:8081/h264_pcm.sdp"  # or "rtsp://admin:admin@192.168.0.19:8081/h264_ulaw.sdp"
rtsp_url1 = "rtsp://admin:admin@192.168.50.46:8081/h264_pcm.sdp"
rtsp_url2 = "rtsp://admin:admin@192.168.50.46:8081/h264_pcm.sdp"
play_from1 = "data_input/xenang_cut2.mp4"
play_from2 = "data_input/xenang_cut2.mp4"

def write_video(ip_camera, stop_event, label):
    video_capture = cv2.VideoCapture(ip_camera)

    frame_width = int(video_capture.get(3))
    frame_height = int(video_capture.get(4))
    size = (frame_width, frame_height)
    fps_video = int(video_capture.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"video_{timestamp}_{label}.mp4"
    result_in = cv2.VideoWriter(f'data_input/{filename}', fourcc, fps_video, size)

    while not stop_event.is_set() and video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            break
        result_in.write(frame)
        # cv2.imshow(f"frame_{label}", frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    video_capture.release()
    result_in.release()
    cv2.destroyAllWindows()
    print(f"Video recording stopped for {label}")

async def test_create_local_tracks(buffer_size="64000"):
    global webcam_1, webcam_2
    options = {
        "framerate": "30",
        "video_size": "640x360",
        "rtsp_transport": "tcp",  # Use TCP transport to reduce packet loss
        "buffer_size": buffer_size  # Adjustable buffer size
    }

    player1 = MediaPlayer(play_from1, decode=True, options=options)
    player2 = MediaPlayer(play_from2, decode=True, options=options)
    return player1.video, player2.video

async def create_local_tracks(buffer_size="64000"):
    global webcam_1, webcam_2
    options = {
        "framerate": "30",
        "video_size": "640x360",
        "rtsp_transport": "tcp",  # Use TCP transport to reduce packet loss
        "buffer_size": buffer_size  # Adjustable buffer size
    }

    if platform.system() == "Darwin":
        webcam_1 = MediaPlayer("default:none", format="avfoundation", options=options)
        webcam_2 = MediaPlayer("default:none", format="avfoundation", options=options)
    elif platform.system() == "Windows":
        webcam_1 = MediaPlayer(rtsp_url1, format="rtsp", options=options)
        webcam_2 = MediaPlayer(rtsp_url2, format="rtsp", options=options)
    else:
        webcam_1 = MediaPlayer("/dev/video0", format="v4l2", options=options)
        webcam_2 = MediaPlayer("/dev/video_1", format="v4l2", options=options)

    relay1 = MediaRelay()
    relay2 = MediaRelay()
    return relay1.subscribe(webcam_1.video), relay2.subscribe(webcam_2.video)

@app.post("/offer")
async def handle_offer(request: Request):
    global write_video_1_thread, write_video_2_thread, stop_event
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
            if webcam_1 and webcam_1.video:
                webcam_1.video.stop()
            if webcam_2 and webcam_2.video:
                webcam_2.video.stop()
            stop_event.set()  # Signal the write_video thread to stop
            print("stop_event set.")

    buffer_size = "64000"  # Start with a moderate buffer size for local network
    video_1, video_2 = await create_local_tracks(buffer_size=buffer_size)

    stop_event = threading.Event()  # Create a new stop_event for the new session

    if video_1:
        process_video_1 = CustomVideoTrack(video_1, "track_1")
        pc.addTrack(process_video_1)
        
        write_video_1_thread = threading.Thread(target=write_video, args=(rtsp_url1, stop_event, "track_1"))
        write_video_1_thread.start()
    
    if video_2:
        process_video_2 = CustomVideoTrack(video_2, "track_2")
        pc.addTrack(process_video_2)

        write_video_2_thread = threading.Thread(target=write_video, args=(rtsp_url2, stop_event, "track_2"))
        write_video_2_thread.start()
    

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return JSONResponse({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})

