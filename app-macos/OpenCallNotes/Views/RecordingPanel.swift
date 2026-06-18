import SwiftUI

/// The recording controls: title, device/language/model pickers, and the big
/// Start/Stop button (06_UI_SPEC).
struct RecordingPanel: View {
    @EnvironmentObject private var store: SessionStore
    @EnvironmentObject private var preferences: Preferences

    enum RecordMode: String, CaseIterable, Identifiable {
        case me = "Just me"
        case call = "Call (mic + system)"
        var id: String { rawValue }
    }

    @State private var title: String = ""
    @State private var deviceID: String = ""
    @State private var language: String = "auto"
    @State private var model: String = Preferences.models[0]
    @State private var mode: RecordMode = .me

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("OpenCallNotes").font(.headline)
                Spacer()
                if store.isRecording {
                    Label("Recording", systemImage: "record.circle.fill")
                        .foregroundStyle(.red)
                        .labelStyle(.titleAndIcon)
                }
            }

            TextField("Session title", text: $title)
                .textFieldStyle(.roundedBorder)
                .disabled(store.isRecording)

            Picker("Mode", selection: $mode) {
                ForEach(RecordMode.allCases) { Text($0.rawValue).tag($0) }
            }
            .pickerStyle(.segmented)
            .disabled(store.isRecording)

            if mode == .me {
                Picker("Input", selection: $deviceID) {
                    if store.devices.isEmpty {
                        Text("No input devices").tag("")
                    }
                    ForEach(store.devices) { device in
                        Text("\(device.name) (\(device.inputChannels)ch)").tag(device.id)
                    }
                }
                .disabled(store.isRecording)
            } else {
                Text("Records your microphone (\"Me\") and the call's audio (\"Them\") "
                    + "as separate tracks, then labels who said what. Needs the Screen "
                    + "Recording permission (System Settings → Privacy & Security).")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Picker("Language", selection: $language) {
                ForEach(Preferences.languages, id: \.self) { Text($0.capitalized).tag($0) }
            }
            .disabled(store.isRecording)

            Picker("Model", selection: $model) {
                ForEach(Preferences.models, id: \.self) { Text(shortModel($0)).tag($0) }
            }
            .disabled(store.isRecording)

            if store.isRecording, let start = store.recordingStartDate {
                TimelineView(.periodic(from: start, by: 1)) { context in
                    Text(elapsed(from: start, to: context.date))
                        .font(.system(.title, design: .monospaced))
                        .foregroundStyle(.red)
                }
            }

            primaryButton

            Button {
                store.openRecordingsFolder()
            } label: {
                Label("Open recordings folder", systemImage: "folder")
            }
            .buttonStyle(.link)

            if store.devices.isEmpty {
                Text("No input devices. If you have a microphone, the worker may not be "
                    + "reachable — check the Worker path in Settings (⌘,). System audio "
                    + "capture additionally requires BlackHole or an aggregate device.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .onAppear(perform: applyDefaults)
        .onChange(of: store.devices) { _, devices in
            // Devices load asynchronously after the view appears; select the
            // first one once the list arrives.
            if deviceID.isEmpty || !devices.contains(where: { $0.id == deviceID }) {
                deviceID = devices.first?.id ?? ""
            }
        }
    }

    @ViewBuilder private var primaryButton: some View {
        if store.isRecording {
            Button(role: .destructive) {
                Task { await store.stopRecording() }
            } label: {
                Label("Stop Recording", systemImage: "stop.fill")
                    .frame(maxWidth: .infinity)
            }
            .controlSize(.large)
            .keyboardShortcut(.return)
        } else {
            Button {
                Task {
                    if mode == .call {
                        await store.startCallRecording(
                            title: title, language: language, model: model
                        )
                    } else {
                        await store.startRecording(
                            deviceID: deviceID, title: title, language: language, model: model
                        )
                    }
                }
            } label: {
                Label(mode == .call ? "Start Call Recording" : "Start Recording",
                      systemImage: "record.circle")
                    .frame(maxWidth: .infinity)
            }
            .controlSize(.large)
            .buttonStyle(.borderedProminent)
            .disabled((mode == .me && deviceID.isEmpty) || store.isBusy)
            .keyboardShortcut(.return)
        }
    }

    private func applyDefaults() {
        language = preferences.defaultLanguage
        model = preferences.defaultModel
        if deviceID.isEmpty { deviceID = store.devices.first?.id ?? "" }
    }

    private func shortModel(_ id: String) -> String {
        id.split(separator: "/").last.map(String.init) ?? id
    }

    private func elapsed(from start: Date, to now: Date) -> String {
        let total = Int(max(0, now.timeIntervalSince(start)))
        return String(format: "%02d:%02d", total / 60, total % 60)
    }
}
