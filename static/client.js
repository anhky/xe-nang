let pc;
let mediaRecorder1;
let mediaRecorder2;
let recordedChunks1 = [];
let recordedChunks2 = [];

async function negotiate() {
    try {
        pc.addTransceiver('video', { direction: 'recvonly' });
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

    let videoTracks = 0;
    pc.ontrack = function (evt) {
        if (evt.track.kind === 'video') {
            if (videoTracks === 0) {
                console.log(evt.track)
                const videoElement1 = document.getElementById('video_1');
                videoElement1.srcObject = new MediaStream([evt.track]);
                startRecording(evt.streams[0], 1);
                videoTracks++;
            } else if (videoTracks === 1) {
                const videoElement2 = document.getElementById('video_2');
                console.log(evt.track)
                videoElement2.srcObject = new MediaStream([evt.track]);
                startRecording(evt.streams[0], 2);
                videoTracks++;
            }
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

    if (mediaRecorder1) {
        mediaRecorder1.stop();
    }
    if (mediaRecorder2) {
        mediaRecorder2.stop();
    }

    document.getElementById('video_1').srcObject = null;
    document.getElementById('video_2').srcObject = null;
}

function startRecording(stream, index) {
    const mediaRecorder = new MediaRecorder(stream);
    let recordedChunks = [];

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
        a.download = `recorded_video${index}.webm`;
        document.body.appendChild(a);
        a.click();

        URL.revokeObjectURL(url);
    };

    mediaRecorder.start();

    if (index === 1) {
        mediaRecorder1 = mediaRecorder;
        recordedChunks1 = recordedChunks;
    } else if (index === 2) {
        mediaRecorder2 = mediaRecorder;
        recordedChunks2 = recordedChunks;
    }
}

window.addEventListener('beforeunload', () => {
    if (pc) {
        pc.close();
    }
    if (mediaRecorder1 && mediaRecorder1.state !== 'inactive') {
        mediaRecorder1.stop();
    }
    if (mediaRecorder2 && mediaRecorder2.state !== 'inactive') {
        mediaRecorder2.stop();
    }
});
