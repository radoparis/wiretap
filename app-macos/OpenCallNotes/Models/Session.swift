import Foundation

/// Session metadata, mirroring the worker's `session.json` / `sessions` output.
struct Session: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let createdAt: String
    let durationSeconds: Double
    let audioFile: String
    let language: String
    let model: String
    let status: String

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case createdAt = "created_at"
        case durationSeconds = "duration_seconds"
        case audioFile = "audio_file"
        case language
        case model
        case status
    }

    var isTranscribed: Bool { status == "transcribed" }
    var isRecording: Bool { status == "recording" }

    /// Human-friendly duration, e.g. `42:05`.
    var formattedDuration: String {
        let total = Int(durationSeconds.rounded())
        return String(format: "%02d:%02d", total / 60, total % 60)
    }
}

struct SessionList: Codable {
    let sessions: [Session]
}

/// `sessions get` adds the transcript (when available) to the session fields.
struct SessionDetail: Codable {
    let id: String
    let title: String
    let createdAt: String
    let durationSeconds: Double
    let audioFile: String
    let language: String
    let model: String
    let status: String
    let transcriptAvailable: Bool
    let transcript: Transcript?

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case createdAt = "created_at"
        case durationSeconds = "duration_seconds"
        case audioFile = "audio_file"
        case language
        case model
        case status
        case transcriptAvailable = "transcript_available"
        case transcript
    }

    var session: Session {
        Session(
            id: id, title: title, createdAt: createdAt, durationSeconds: durationSeconds,
            audioFile: audioFile, language: language, model: model, status: status
        )
    }
}
