let pc;
let mediaRecorder;
let recordedChunks = [];

async function negotiate() {
    try {
        pc.addTransceiver('video', { direction: 'recvonly' });

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        const response = await fetch('/offer', {
            body: JSON.stringify({ sdp: offer.sdp, type: offer.type }),
            headers: { "Content-Type": "application/json" },
            method: 'POST'
        });

        if (!response.ok) throw new Error('Network response was not ok');
        const answer = await response.json();
        if (!answer || !answer.sdp || !answer.type) throw new Error('Invalid answer received');

        await pc.setRemoteDescription(answer);
    } catch (e) {
        console.error('Failed to negotiate:', e);
        alert("Failed to negotiate: " + e.message);
    }
}

function start() {
    const config = {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' }  // Use a public STUN server
        ],
        iceTransportPolicy: 'all',  // Use 'all' to ensure connectivity
        sdpSemantics: 'unified-plan'
    };
    pc = new RTCPeerConnection(config);

    pc.ontrack = function (evt) {
        if (evt.track.kind === 'video') {
            const videoElement = document.getElementById('video');
            videoElement.srcObject = evt.streams[0];

            // Start recording
            startRecording(evt.streams[0]);
        }
    };

    pc.oniceconnectionstatechange = function () {
        if (pc.iceConnectionState === 'disconnected' || pc.iceConnectionState === 'failed') {
            stop();
        }
    };

    document.getElementById('start').style.display = 'none';
    negotiate();
    document.getElementById('stop').style.display = 'inline-block';
}

function stop() {
    document.getElementById('stop').style.display = 'none';
    document.getElementById('start').style.display = 'inline-block';

    if (pc) {
        pc.close();
        pc = null;
    }

    if (mediaRecorder) {
        mediaRecorder.stop();
    }

    document.getElementById('video').srcObject = null;
}

function startRecording(stream) {
    mediaRecorder = new MediaRecorder(stream);
    recordedChunks = [];

    mediaRecorder.ondataavailable = function(event) {
        if (event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };

    mediaRecorder.onstop = function() {
        const blob = new Blob(recordedChunks, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'recorded_video.webm';
        document.body.appendChild(a);
        a.click();

        URL.revokeObjectURL(url);
    };

    mediaRecorder.start();
}

window.addEventListener('beforeunload', () => {
    if (pc) {
        pc.close();
    }
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
});
