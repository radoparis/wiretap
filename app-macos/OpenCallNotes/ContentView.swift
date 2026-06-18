import SwiftUI

/// Two-column layout: recording controls + session library on the left, the
/// selected session's detail on the right (06_UI_SPEC).
struct ContentView: View {
    @EnvironmentObject private var store: SessionStore

    var body: some View {
        NavigationSplitView {
            VStack(spacing: 0) {
                RecordingPanel()
                Divider()
                SessionListView()
            }
            .frame(minWidth: 320)
        } detail: {
            if let detail = store.detail {
                SessionDetailView(detail: detail)
            } else {
                ContentUnavailableView(
                    "Select a recording",
                    systemImage: "waveform",
                    description: Text("Pick a session from the list, or start a new recording.")
                )
            }
        }
        .overlay(alignment: .bottom) { statusBar }
        .privacyFooter()
        .alert(
            "Worker error",
            isPresented: Binding(
                get: { store.errorMessage != nil },
                set: { if !$0 { store.errorMessage = nil } }
            ),
            presenting: store.errorMessage
        ) { _ in
            Button("Retry") { Task { await store.refreshDevices(); await store.refreshSessions() } }
            Button("OK", role: .cancel) {}
        } message: { message in
            Text(message + "\n\nCheck the Worker path in Settings (⌘,). For a source "
                + "checkout, point it at scripts/run-worker.sh.")
        }
    }

    @ViewBuilder private var statusBar: some View {
        if let error = store.errorMessage {
            Label(error, systemImage: "exclamationmark.triangle.fill")
                .padding(8)
                .background(.red.opacity(0.15), in: RoundedRectangle(cornerRadius: 8))
                .padding()
        } else if store.isBusy, let message = store.statusMessage {
            HStack(spacing: 8) {
                ProgressView().controlSize(.small)
                Text(message)
            }
            .padding(8)
            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8))
            .padding()
        }
    }
}

private struct PrivacyFooter: ViewModifier {
    func body(content: Content) -> some View {
        content.safeAreaInset(edge: .bottom) {
            Text("OpenCallNotes records audio locally on your Mac. Make sure you have the "
                + "right to record under the laws and rules that apply to you.")
                .font(.caption2)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 6)
                .background(.bar)
        }
    }
}

extension View {
    func privacyFooter() -> some View { modifier(PrivacyFooter()) }
}
