let pc;

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
    const config = { sdpSemantics: 'unified-plan' };
    pc = new RTCPeerConnection(config);

    pc.ontrack = function (evt) {
        if (evt.track.kind === 'video') {
            document.getElementById('video').srcObject = evt.streams[0];
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

    document.getElementById('video').srcObject = null;
}

window.addEventListener('beforeunload', () => {
    if (pc) {
        pc.close();
    }
});
