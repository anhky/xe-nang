var pc = null;

function negotiate() {
  pc.addTransceiver("video", { direction: "recvonly" });
  pc.addTransceiver("audio", { direction: "recvonly" });

  return pc
    .createOffer()
    .then((offer) => {
      return pc.setLocalDescription(offer);
    })
    // .then(() => {
    //   // wait for ICE gathering to complete
    //   return new Promise((resolve) => {
    //     if (pc.iceGatheringState === "complete") {
    //       resolve();
    //     } else {
    //       const checkState = () => {
    //         if (pc.iceGatheringState === "complete") {
    //           pc.removeEventListener("icegatheringstatechange", checkState);
    //           resolve();
    //         }
    //       };
    //       pc.addEventListener("icegatheringstatechange", checkState);
    //     }
    //   });
    // })
    .then(() => {
      var offer = pc.localDescription;
      return fetch("/offer", {
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
  pc = new RTCPeerConnection(config);
  pc.ontrack = function (evt) {
    if (evt.track.kind == "video") {
      document.getElementById("video").srcObject = evt.streams[0];
    } else {
      document.getElementById("audio").srcObject = evt.streams[0];
    }
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
