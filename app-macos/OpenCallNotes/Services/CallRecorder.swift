import AVFoundation
import Foundation
import ScreenCaptureKit

/// Records a call as two tracks: the microphone ("Me") via AVAudioEngine and the
/// system/call audio ("Them") via ScreenCaptureKit. Each track is written as a
/// 16 kHz mono 16-bit WAV — the format the worker's Whisper path expects.
///
/// NOTE: authored without a Mac to compile on. ScreenCaptureKit audio capture and
/// the format conversion are exactly the things that need on-device iteration; see
/// docs/dev-guide.md. System-audio capture requires the Screen Recording permission
/// (System Settings → Privacy & Security → Screen Recording).
@available(macOS 13.0, *)
final class CallRecorder: NSObject, SCStreamOutput, SCStreamDelegate {
    enum RecorderError: LocalizedError {
        case noDisplay
        case engineFailed(String)
        var errorDescription: String? {
            switch self {
            case .noDisplay: return "No display available for system-audio capture."
            case let .engineFailed(message): return message
            }
        }
    }

    private let engine = AVAudioEngine()
    private var micWriter: AudioTrackWriter?
    private var systemWriter: AudioTrackWriter?
    private var stream: SCStream?
    private let sampleQueue = DispatchQueue(label: "org.opencallnotes.callrecorder.scaudio")

    /// Start capturing the mic to `micURL` and system audio to `systemURL`.
    func start(micURL: URL, systemURL: URL) async throws {
        micWriter = try AudioTrackWriter(url: micURL)
        systemWriter = try AudioTrackWriter(url: systemURL)

        try startMicrophone()
        try await startSystemAudio()
    }

    func stop() async {
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        if let stream {
            try? await stream.stopCapture()
        }
        stream = nil
        micWriter?.close()
        systemWriter?.close()
        micWriter = nil
        systemWriter = nil
    }

    // MARK: Microphone (AVAudioEngine)

    private func startMicrophone() throws {
        let input = engine.inputNode
        let format = input.outputFormat(forBus: 0)
        input.installTap(onBus: 0, bufferSize: 4096, format: format) { [weak self] buffer, _ in
            self?.micWriter?.append(buffer)
        }
        engine.prepare()
        do {
            try engine.start()
        } catch {
            throw RecorderError.engineFailed("Microphone capture failed: \(error.localizedDescription)")
        }
    }

    // MARK: System audio (ScreenCaptureKit)

    private func startSystemAudio() async throws {
        let content = try await SCShareableContent.excludingDesktopWindows(
            false, onScreenWindowsOnly: true
        )
        guard let display = content.displays.first else { throw RecorderError.noDisplay }

        let filter = SCContentFilter(display: display, excludingWindows: [])
        let config = SCStreamConfiguration()
        config.capturesAudio = true
        config.sampleRate = 48_000
        config.channelCount = 2
        // We only want audio; keep the video path minimal.
        config.width = 2
        config.height = 2
        config.minimumFrameInterval = CMTime(value: 1, timescale: 1)

        let stream = SCStream(filter: filter, configuration: config, delegate: self)
        try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: sampleQueue)
        try await stream.startCapture()
        self.stream = stream
    }

    func stream(
        _ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType
    ) {
        guard type == .audio, sampleBuffer.isValid,
              let formatDesc = CMSampleBufferGetFormatDescription(sampleBuffer),
              let format = AVAudioFormat(cmAudioFormatDescription: formatDesc) else { return }

        let frames = AVAudioFrameCount(CMSampleBufferGetNumSamples(sampleBuffer))
        guard frames > 0,
              let pcm = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frames) else { return }
        pcm.frameLength = frames
        let status = CMSampleBufferCopyPCMDataIntoAudioBufferList(
            sampleBuffer, at: 0, frameCount: Int32(frames), into: pcm.mutableAudioBufferList
        )
        guard status == noErr else { return }
        systemWriter?.append(pcm)
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        NSLog("CallRecorder system-audio stream stopped: \(error.localizedDescription)")
    }
}
