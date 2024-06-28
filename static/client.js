var pc = null;

async function negotiate() {
    var config = {
        sdpSemantics: "unified-plan",
    };

    pc = new RTCPeerConnection(config);

    // Lấy và thêm luồng video từ thiết bị người dùng
    var stream = await navigator.mediaDevices.getUserMedia({
        video: {
            width: { exact: 640 },
            height: { exact: 480 },
            frameRate: {
                ideal: 30, // Giá trị fps lý tưởng
                min: 15,   // Giá trị fps thấp nhất
                max: 30    // Giá trị fps cao nhất
              }
        }
    });
    stream.getTracks().forEach(track => pc.addTrack(track, stream));

    // Thiết lập luồng video truyền từ thiết bị người dùng
    var localVideoElement = document.getElementById('localVideo');
    localVideoElement.srcObject = stream;
    localVideoElement.muted = true; // Tắt âm thanh trên thẻ video

    // Đăng ký nhận luồng video từ peer
    pc.ontrack = function(event) {
        if (event.track.kind === 'video') {
            var remoteVideoElement = document.getElementById('remoteVideo');
            remoteVideoElement.srcObject = event.streams[0];
        }
    };

    // Xử lý ứng viên ICE và đàm phán kết nối
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
    if (pc) {
        pc.close();
        pc = null;

        var localVideoElement = document.getElementById('localVideo');
        if (localVideoElement.srcObject) {
            localVideoElement.srcObject.getTracks().forEach(track => track.stop());
            localVideoElement.srcObject = null;
        }

        var remoteVideoElement = document.getElementById('remoteVideo');
        if (remoteVideoElement.srcObject) {
            remoteVideoElement.srcObject.getTracks().forEach(track => track.stop());
            remoteVideoElement.srcObject = null;
        }

        document.getElementById('start').style.display = 'inline';
        document.getElementById('stop').style.display = 'none';
    }
}

document.getElementById('start').addEventListener('click', start);
document.getElementById('stop').addEventListener('click', stop);
