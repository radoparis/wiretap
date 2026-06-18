import Foundation

/// Live transcription progress, mirroring the worker's `transcribe.progress` file.
struct TranscribeProgress: Decodable {
    let fraction: Double
    let processedSeconds: Double
    let totalSeconds: Double

    enum CodingKeys: String, CodingKey {
        case fraction
        case processedSeconds = "processed_seconds"
        case totalSeconds = "total_seconds"
    }
}
