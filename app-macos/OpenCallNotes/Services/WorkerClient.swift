import Foundation

/// A structured error returned by the worker's JSON contract (D7).
struct WorkerError: LocalizedError {
    let code: String
    let message: String
    var errorDescription: String? { message }
}

private struct ErrorEnvelope: Decodable {
    struct Inner: Decodable { let code: String; let message: String }
    let error: Inner
}

// Minimal response shapes for the worker commands the UI invokes.
struct RecordStartResult: Decodable {
    let sessionId: String
    let status: String
    enum CodingKeys: String, CodingKey { case sessionId = "session_id"; case status }
}

struct RecordStopResult: Decodable {
    let sessionId: String
    let status: String
    let durationSeconds: Double
    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"; case status; case durationSeconds = "duration_seconds"
    }
}

struct BeginCallResult: Decodable {
    let sessionId: String
    let dir: String
    let micFile: String
    let systemFile: String
    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case dir
        case micFile = "mic_file"
        case systemFile = "system_file"
    }

    var micURL: URL { URL(fileURLWithPath: dir).appendingPathComponent(micFile) }
    var systemURL: URL { URL(fileURLWithPath: dir).appendingPathComponent(systemFile) }
}

struct TranscribeResult: Decodable {
    let sessionId: String
    let status: String
    let segments: Int
    enum CodingKeys: String, CodingKey { case sessionId = "session_id"; case status; case segments }
}

struct ExportResult: Decodable {
    let sessionId: String
    let format: String
    let path: String
    enum CodingKeys: String, CodingKey { case sessionId = "session_id"; case format; case path }
}

/// Drives the Python worker as a subprocess and decodes its JSON output.
///
/// No shell is used — the executable and arguments are passed as a fixed argv,
/// so user-entered titles can never inject commands.
final class WorkerClient {
    private let preferences: Preferences

    init(preferences: Preferences) {
        self.preferences = preferences
    }

    // MARK: Commands

    func listDevices() async throws -> [Device] {
        try await run(DeviceList.self, ["devices", "--json"]).devices
    }

    func listSessions() async throws -> [Session] {
        try await run(SessionList.self, ["sessions", "list", "--json"]).sessions
    }

    func getSession(_ id: String) async throws -> SessionDetail {
        try await run(SessionDetail.self, ["sessions", "get", id, "--json"])
    }

    func startRecording(
        deviceId: String, title: String, language: String, model: String
    ) async throws -> RecordStartResult {
        try await run(RecordStartResult.self, [
            "record", "start",
            "--device-id", deviceId,
            "--title", title,
            "--language", language,
            "--model", model,
            "--json",
        ])
    }

    func stopRecording(sessionId: String) async throws -> RecordStopResult {
        try await run(RecordStopResult.self, [
            "record", "stop", "--session-id", sessionId, "--json",
        ])
    }

    func beginCall(title: String, language: String, model: String) async throws -> BeginCallResult {
        try await run(BeginCallResult.self, [
            "record", "begin-call",
            "--title", title,
            "--language", language,
            "--model", model,
            "--json",
        ])
    }

    func endCall(sessionId: String) async throws -> RecordStopResult {
        try await run(RecordStopResult.self, [
            "record", "end-call", "--session-id", sessionId, "--json",
        ])
    }

    func transcribe(sessionId: String, model: String?, language: String?) async throws
        -> TranscribeResult
    {
        var args = ["transcribe", sessionId]
        if let model { args += ["--model", model] }
        if let language { args += ["--language", language] }
        args.append("--json")
        return try await run(TranscribeResult.self, args)
    }

    @discardableResult
    func export(sessionId: String, format: String) async throws -> ExportResult {
        try await run(ExportResult.self, ["export", sessionId, "--format", format, "--json"])
    }

    // MARK: Subprocess plumbing

    private func run<T: Decodable>(_ type: T.Type, _ args: [String]) async throws -> T {
        let data = try await launch(args: args)
        let decoder = JSONDecoder()
        if let envelope = try? decoder.decode(ErrorEnvelope.self, from: data) {
            throw WorkerError(code: envelope.error.code, message: envelope.error.message)
        }
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            let raw = String(data: data, encoding: .utf8) ?? "<non-utf8 output>"
            throw WorkerError(
                code: "bad_response",
                message: "Could not parse worker output: \(raw)"
            )
        }
    }

    private func launch(args: [String]) async throws -> Data {
        let config = preferences.launchConfig
        return try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.global(qos: .userInitiated).async {
                let process = Process()
                process.executableURL = URL(fileURLWithPath: config.executablePath)
                process.arguments = config.leadingArgs + args
                process.environment = config.environment

                let stdout = Pipe()
                process.standardOutput = stdout
                process.standardError = Pipe()

                do {
                    try process.run()
                } catch {
                    continuation.resume(throwing: WorkerError(
                        code: "worker_launch_failed",
                        message: "Could not launch worker at \(config.executablePath): "
                            + error.localizedDescription
                    ))
                    return
                }
                let data = stdout.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()
                continuation.resume(returning: data)
            }
        }
    }
}
