let localStream;
let remoteStream;
let peerConnection;
const configuration = {
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
};

const localVideo = document.getElementById('localVideo');
const remoteVideo = document.getElementById('remoteVideo');

document.getElementById('startCall').addEventListener('click', async function() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        localVideo.srcObject = localStream;

        peerConnection = new RTCPeerConnection(configuration);
        localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

        peerConnection.ontrack = event => remoteVideo.srcObject = event.streams[0];

        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        // Send the offer to the signaling server (to be implemented)
    } catch (error) {
        console.error('Error starting video call', error);
    }
});
