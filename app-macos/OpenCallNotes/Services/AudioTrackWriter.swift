import AVFoundation
import Foundation

/// Writes a stream of `AVAudioPCMBuffer`s to a 16 kHz mono 16-bit PCM WAV,
/// resampling/downmixing from whatever format each buffer arrives in. This is the
/// format the worker's Whisper path reads (matching the v0.1 recorder).
///
/// Buffers may arrive on the mic render thread or the ScreenCaptureKit queue, so
/// appends are serialized with a lock. Each track has its own writer/file.
final class AudioTrackWriter {
    private let file: AVAudioFile
    private let targetFormat: AVAudioFormat
    private var converters: [String: AVAudioConverter] = [:]
    private let lock = NSLock()

    init(url: URL) throws {
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatLinearPCM,
            AVSampleRateKey: 16_000,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false,
        ]
        try? FileManager.default.removeItem(at: url)
        file = try AVAudioFile(forWriting: url, settings: settings)
        // AVAudioFile processes as deinterleaved float32 at the file's rate/channels.
        targetFormat = file.processingFormat
    }

    func append(_ buffer: AVAudioPCMBuffer) {
        lock.lock()
        defer { lock.unlock() }

        guard let converted = convert(buffer) else { return }
        try? file.write(from: converted)
    }

    func close() {
        lock.lock()
        defer { lock.unlock() }
        converters.removeAll()
        // AVAudioFile flushes and closes on deinit; dropping references is enough.
    }

    // MARK: Conversion

    private func convert(_ buffer: AVAudioPCMBuffer) -> AVAudioPCMBuffer? {
        if buffer.format == targetFormat { return buffer }

        let key = buffer.format.description
        let converter: AVAudioConverter
        if let existing = converters[key] {
            converter = existing
        } else {
            guard let made = AVAudioConverter(from: buffer.format, to: targetFormat) else { return nil }
            converters[key] = made
            converter = made
        }

        let ratio = targetFormat.sampleRate / buffer.format.sampleRate
        let capacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio) + 1024
        guard let output = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: capacity) else {
            return nil
        }

        var consumed = false
        var conversionError: NSError?
        let outcome = converter.convert(to: output, error: &conversionError) { _, status in
            if consumed {
                status.pointee = .noDataNow
                return nil
            }
            consumed = true
            status.pointee = .haveData
            return buffer
        }
        if outcome == .error || output.frameLength == 0 { return nil }
        return output
    }
}
