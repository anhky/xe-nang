var pc = null;

async function negotiate() {
    var config = {
        sdpSemantics: "unified-plan",
    };

    pc = new RTCPeerConnection(config);

    // var stream = await navigator.mediaDevices.getUserMedia({
    //     video: {
    //         width: { min: 1024, ideal: 1280, max: 1920 },
    //         height: { min: 576, ideal: 720, max: 1080 },
    //     }
    // });
    var stream = await navigator.mediaDevices.getUserMedia({
      video: {
          width: { exact: 640 },
          height: { exact: 480 }
      }
  });
    stream.getTracks().forEach(track => pc.addTrack(track, stream));

    var videoElement = document.getElementById('video');
    videoElement.srcObject = stream;
    videoElement.muted = true; // Tắt âm thanh trên thẻ video
    
    pc.onicecandidate = event => {
        if (event.candidate === null) {
            fetch('/offer', {
                method: 'POST',
                body: JSON.stringify({
                    sdp: pc.localDescription.sdp,
                    type: pc.localDescription.type
                }),
                headers: {
                    'Content-Type': 'application/json'
                }
            }).then(response => response.json())
              .then(answer => pc.setRemoteDescription(new RTCSessionDescription(answer)));
        }
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
}

function start() {
    negotiate();
    document.getElementById('start').style.display = 'none';
    document.getElementById('stop').style.display = 'inline';
}

function stop() {
    pc.close();
    pc = null;

    document.getElementById('start').style.display = 'inline';
    document.getElementById('stop').style.display = 'none';
    document.getElementById('video').srcObject.getTracks().forEach(track => track.stop());
}

document.getElementById('start').addEventListener('click', start);
document.getElementById('stop').addEventListener('click', stop);
