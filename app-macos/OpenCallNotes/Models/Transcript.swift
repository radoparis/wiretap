import Foundation

/// A single timestamped transcript segment.
struct TranscriptSegment: Codable, Identifiable, Hashable {
    let id: Int
    let start: Double
    let end: Double
    let text: String
    let speaker: String?

    /// `mm:ss` start timestamp for display.
    var startTimestamp: String {
        let total = Int(start)
        return String(format: "%02d:%02d", total / 60, total % 60)
    }
}

/// A full transcript, mirroring the worker's `transcript.json`.
struct Transcript: Codable, Hashable {
    let language: String
    let model: String
    let durationSeconds: Double
    let text: String
    let segments: [TranscriptSegment]

    enum CodingKeys: String, CodingKey {
        case language
        case model
        case durationSeconds = "duration_seconds"
        case text
        case segments
    }
}
