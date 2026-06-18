import SwiftUI

@main
struct OpenCallNotesApp: App {
    @StateObject private var preferences: Preferences
    @StateObject private var store: SessionStore

    init() {
        let prefs = Preferences()
        prefs.load()
        _preferences = StateObject(wrappedValue: prefs)
        _store = StateObject(wrappedValue: SessionStore(preferences: prefs))
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(store)
                .environmentObject(preferences)
                .frame(minWidth: 900, minHeight: 600)
                .task {
                    await store.refreshDevices()
                    await store.refreshSessions()
                }
        }
        .windowStyle(.titleBar)

        Settings {
            PreferencesView()
                .environmentObject(preferences)
        }
    }
}
