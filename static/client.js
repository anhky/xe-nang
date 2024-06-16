var pc = null;
var dataChannel = null;

function negotiate() {
  pc.addTransceiver("video", { direction: "recvonly" });
  pc.addTransceiver("audio", { direction: "recvonly" });

  dataChannel = pc.createDataChannel("chat", { ordered: true });

  dataChannel.onopen = function () {
    console.log("DataChannel is open");
  };
  dataChannel.onerror = function (error) {
    console.error("DataChannel Error:", error);
  };

  return pc
    .createOffer()
    .then((offer) => {
      return pc.setLocalDescription(offer);
    })
    .then(() => {
      // wait for ICE gathering to complete
      return new Promise((resolve) => {
        if (pc.iceGatheringState === "complete") {
          resolve();
        } else {
          const checkState = () => {
            if (pc.iceGatheringState === "complete") {
              pc.removeEventListener("icegatheringstatechange", checkState);
              resolve();
            }
          };
          pc.addEventListener("icegatheringstatechange", checkState);
        }
      });
    })
    .then(() => {
      var offer = pc.localDescription;
      // return fetch("https://vectorinfotech.io/offer", {  // Sử dụng HTTPS và domain của bạn
      return fetch("/offer", {  // Sử dụng HTTPS và domain của bạn
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
    })
    .then((response) => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then((answer) => {
      if (!answer || !answer.sdp || !answer.type) {
        throw new Error('Invalid answer received');
      }
      return pc.setRemoteDescription(answer);
    })
    .catch((e) => {
      console.error('Failed to negotiate:', e);
      alert("Failed to negotiate: " + e.message);
    });
}

function start() {
  var config = {
    sdpSemantics: "unified-plan"
  };
  // iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }]  // Sử dụng STUN server
  pc = new RTCPeerConnection(config);
  pc.ontrack = function (evt) {
    if (evt.track.kind == "video") {
      document.getElementById("video").srcObject = evt.streams[0];
    } else {
      document.getElementById("audio").srcObject = evt.streams[0];
    }
  };

  // Setup Data Channel
  pc.ondatachannel = function (event) {
    dataChannel = event.channel;
    dataChannel.onopen = function () {
      console.log("Data Channel is open");
    };
    dataChannel.onmessage = function (event) {
      // Parsing the incoming data
      let parseData = JSON.parse(event.data);
      console.log("Received message:", parseData);

      // Object keys corresponding to the elements in the HTML
      const statusKeys = ["Moving", "Moving Slowly", "Stationary", "Detected"];

      // Initially set all counts to zero
      statusKeys.forEach(key => {
        let element = document.getElementById(key.replace(" ", "").toLowerCase());
        if (element) {
          element.innerText = '0';
        }
      });

      // Check each key in the received data and update the count
      if (parseData.object_counts) {
        statusKeys.forEach(key => {
          let elementId = key.replace(" ", "").toLowerCase();
          let element = document.getElementById(elementId);
          if (element && key in parseData.object_counts) {
            element.innerText = parseData.object_counts[key];
          }
        });
      }

      // Update the timestamp
      let timeElement = document.getElementById("time");
      if (timeElement) {
        timeElement.innerText = parseData.timestamp;
      }
    };
  };

  document.getElementById("start").style.display = "none";
  negotiate();
  document.getElementById("stop").style.display = "inline-block";
}

function stop() {
  document.getElementById("stop").style.display = "none";
  document.getElementById("start").style.display = "inline-block";

  // close peer connection
  setTimeout(() => {
    if (pc) {
      pc.close();
      pc = null;
    }
  }, 500);
}
