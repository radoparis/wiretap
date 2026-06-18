import SwiftUI

/// Preferences window (06_UI_SPEC "Preferences").
struct PreferencesView: View {
    @EnvironmentObject private var preferences: Preferences

    var body: some View {
        Form {
            Section("Worker") {
                TextField("Worker path", text: $preferences.workerPath,
                          prompt: Text("/usr/bin/env (resolves opencallnotes-worker from PATH)"))
                TextField("Worker leading args", text: $preferences.workerLeadingArgs,
                          prompt: Text("e.g. opencallnotes-worker"))
                Text("For development, point Worker path at scripts/run-worker.sh and leave "
                    + "leading args empty.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Section("Storage") {
                TextField("Recordings folder", text: $preferences.recordingsFolder,
                          prompt: Text("Default: ~/Library/Application Support/OpenCallNotes"))
            }

            Section("Defaults") {
                Picker("Default language", selection: $preferences.defaultLanguage) {
                    ForEach(Preferences.languages, id: \.self) { Text($0.capitalized).tag($0) }
                }
                Picker("Default model", selection: $preferences.defaultModel) {
                    ForEach(Preferences.models, id: \.self) {
                        Text($0.split(separator: "/").last.map(String.init) ?? $0).tag($0)
                    }
                }
            }
        }
        .formStyle(.grouped)
        .frame(width: 480, height: 360)
        .padding()
    }
}
