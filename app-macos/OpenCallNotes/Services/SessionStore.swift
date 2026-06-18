import AppKit
import Foundation

/// Observable application state. Bridges the SwiftUI views to the worker.
@MainActor
final class SessionStore: ObservableObject {
    @Published var devices: [Device] = []
    @Published var sessions: [Session] = []
    @Published var selectedSessionID: String?
    @Published var detail: SessionDetail?

    @Published var isRecording = false
    @Published var recordingSessionID: String?
    @Published var recordingStartDate: Date?

    @Published var isBusy = false
    @Published var statusMessage: String?
    @Published var errorMessage: String?

    let preferences: Preferences
    private let worker: WorkerClient

    init(preferences: Preferences) {
        self.preferences = preferences
        self.worker = WorkerClient(preferences: preferences)
    }

    // MARK: Loading

    func refreshDevices() async {
        await guarded("Listing devices") {
            self.devices = try await self.worker.listDevices()
        }
    }

    func refreshSessions() async {
        await guarded("Loading sessions") {
            self.sessions = try await self.worker.listSessions()
        }
    }

    func selectSession(_ id: String) async {
        selectedSessionID = id
        detail = nil
        await guarded("Opening session") {
            self.detail = try await self.worker.getSession(id)
        }
    }

    // MARK: Recording

    func startRecording(deviceID: String, title: String, language: String, model: String) async {
        let cleanTitle = title.trimmingCharacters(in: .whitespacesAndNewlines)
        await guarded("Starting recording") {
            let result = try await self.worker.startRecording(
                deviceId: deviceID,
                title: cleanTitle.isEmpty ? "Untitled" : cleanTitle,
                language: language,
                model: model
            )
            self.isRecording = true
            self.recordingSessionID = result.sessionId
            self.recordingStartDate = Date()
        }
        await refreshSessions()
    }

    func stopRecording() async {
        guard let id = recordingSessionID else { return }
        await guarded("Stopping recording") {
            _ = try await self.worker.stopRecording(sessionId: id)
            self.isRecording = false
            self.recordingSessionID = nil
            self.recordingStartDate = nil
        }
        await refreshSessions()
        await selectSession(id)
    }

    // MARK: Transcription / export

    func transcribeSelected() async {
        guard let id = selectedSessionID else { return }
        await guarded("Transcribing (this can take a while)") {
            _ = try await self.worker.transcribe(
                sessionId: id,
                model: self.preferences.defaultModel,
                language: self.preferences.defaultLanguage
            )
            self.detail = try await self.worker.getSession(id)
        }
        await refreshSessions()
    }

    func exportSelected(format: String) async {
        guard let id = selectedSessionID else { return }
        await guarded("Exporting \(format.uppercased())") {
            let result = try await self.worker.export(sessionId: id, format: format)
            self.statusMessage = "Exported \(format.uppercased())"
            NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: result.path)])
        }
    }

    func openRecordingsFolder() {
        let url = preferences.resolvedRecordingsURL
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        NSWorkspace.shared.open(url)
    }

    // MARK: Helpers

    private func guarded(_ message: String, _ work: @escaping () async throws -> Void) async {
        isBusy = true
        statusMessage = message
        errorMessage = nil
        defer { isBusy = false }
        do {
            try await work()
            statusMessage = nil
        } catch let error as WorkerError {
            errorMessage = "\(message) failed: \(error.message)"
            statusMessage = nil
        } catch {
            errorMessage = "\(message) failed: \(error.localizedDescription)"
            statusMessage = nil
        }
    }
}
