import React from 'react';
import './App.css';
import io, {Socket} from "socket.io-client";

type AppProps = {};
type AppState = {};

class App extends React.Component<AppProps, AppState> {
  private d_videoRef:React.LegacyRef<HTMLVideoElement> = React.createRef();
  private d_remoteVideoRef:React.LegacyRef<HTMLVideoElement> = React.createRef();
  private d_webRTCProxy?: WebRTCProxy;
  constructor(props: AppProps) {
    super(props);
  }
  public render() {
    return (
      <div>
        <h1>WebRTC Screen Sharing</h1>
        <h3>Local sharing</h3>
        <p>Hidden</p>
        <video ref={this.d_videoRef} hidden={true} autoPlay={true} playsInline={true} controls={true} muted={true}>
        </video>
        <br />
        <button onClick={this.onBeginClick.bind(this)}>Begin</button>
        <h3>Remote sharing</h3>
        <video ref={this.d_remoteVideoRef} autoPlay={true} playsInline={true} controls={true} muted={true}>
        </video>
      </div>
    )
  }

  private async onBeginClick() {
    try {
      const videoStream = await getVideoStream();
      console.log("Got videoStream:", videoStream);
      // @ts-ignore
      this.d_videoRef.current.srcObject = videoStream;
      this.d_webRTCProxy = new WebRTCProxy({
        videoStream,
        remoteVideoStreamCallback: (stream: any) => {
          // @ts-ignore
          this.d_remoteVideoRef.current.srcObject = stream;
        }
      });
    }
    catch (error) {
      console.error("Failed to get video stream:" + error.message, error);
    }
  }
}

async function getVideoStream() {
  if ("getDisplayMedia" in navigator.mediaDevices) {
    // @ts-ignore
    return navigator.mediaDevices.getDisplayMedia({ video: true });
  }
  else if ("getDisplayMedia" in navigator) {
    // @ts-ignore
    return navigator.getDisplayMedia({ video: true })
  }
  else {
    throw new Error("getDisplayMedia not present");
  }
}

class WebRTCProxy {

private d_socket = io("localhost:4000", {
  transports: [ 'websocket' ]
});
private d_peerConnection: RTCPeerConnection;
private d_videoStream: any;
private d_remoteVideoStreamCallback: Function;
private d_isInitiator = false;
constructor({
  videoStream,
  remoteVideoStreamCallback
}: {
  videoStream: any,
  remoteVideoStreamCallback: Function,
}) {
  console.log("Got socket:", this.d_socket);
  this.d_videoStream = videoStream;
  this.d_remoteVideoStreamCallback = remoteVideoStreamCallback;

  this.d_peerConnection = new RTCPeerConnection();
  this.onVideoStream();
}

private onVideoStream() {
    this.setupPeerConnection(this.d_socket, this.d_peerConnection);
    // @ts-ignore
    this.d_peerConnection.addStream(this.d_videoStream);
    this.setupSocket(this.d_socket, this.d_peerConnection);
    const room = "foo";
    this.d_socket.emit('create or join', room);
    this.d_socket.emit('ready');
}

private setupPeerConnection(socket: Socket, pc: RTCPeerConnection) {
    pc.onicecandidate = (event) => {
        if (event.candidate && event.candidate.candidate) {
            console.log("Sent candidate:", event.candidate);
            socket.emit("candidate", {
                type: 'candidate',
                label: event.candidate.sdpMLineIndex,
                id: event.candidate.sdpMid,
                candidate: JSON.stringify(event.candidate.candidate),
            });
        }
    };
    // @ts-ignore
    pc.onaddstream = (event) => {
        console.log("Dropping remote stream:", event.stream);
        this.d_remoteVideoStreamCallback(event.stream);
    }
    // @ts-ignore
    pc.onremovestream = (event) => {
        console.log("Remote stream removed:", event);

    };
    pc.oniceconnectionstatechange = () => {
        console.log(pc.iceConnectionState);
    }
}

private setupSocket(socket:Socket, pc:RTCPeerConnection) {
    socket.on('created', (room) => {
        console.log("Created room:", room);
        this.d_isInitiator = true;
    });
    socket.on('join', (room) => {
        console.log("A peer has joined our room:", room);
        if (this.d_isInitiator) {
          pc.createOffer()
          .then(offer => {
            pc.setLocalDescription(offer);
            socket.emit("offer", offer);
          });
        }
    });
    socket.on('joined', (room) => {
        console.log("We have joined room:", room);
    });
    socket.on('ready', () => {
        console.log("Received ready");
    });
    socket.on('isinitiator', (data) => {
        this.d_isInitiator = true;
    });
    socket.on('offer', (data) => {
        console.log('Got offer:', data);
        pc.setRemoteDescription(new RTCSessionDescription(data));
        pc.createAnswer()
        .then(answer => {
            pc.setLocalDescription(answer);
            console.log("Emitting answer:", answer);
            socket.emit('answer', answer);
        });
    });
    socket.on('answer', (data) => {
        pc.setRemoteDescription(new RTCSessionDescription(data))
    })
    socket.on('candidate', (message) => {
        console.log("Adding remote candidate", message);
        const candidate = new RTCIceCandidate({
            sdpMLineIndex: message.label,
            candidate: message.candidate,
        });
        pc.addIceCandidate(candidate);
    });
}

}
export default App;
