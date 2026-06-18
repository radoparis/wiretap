import SwiftUI

/// The list of recorded sessions (06_UI_SPEC "Recent sessions").
struct SessionListView: View {
    @EnvironmentObject private var store: SessionStore

    var body: some View {
        Group {
            if store.sessions.isEmpty {
                ContentUnavailableView(
                    "No recordings yet",
                    systemImage: "tray",
                    description: Text("Start your first recording.")
                )
            } else {
                List(store.sessions, selection: Binding(
                    get: { store.selectedSessionID },
                    set: { id in if let id { Task { await store.selectSession(id) } } }
                )) { session in
                    SessionRow(session: session).tag(session.id)
                }
                .listStyle(.sidebar)
            }
        }
        .frame(maxHeight: .infinity)
    }
}

private struct SessionRow: View {
    let session: Session

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(session.title).font(.body).lineLimit(1)
            HStack(spacing: 6) {
                Text(session.createdAt.prefix(19).replacingOccurrences(of: "T", with: " "))
                Text("·")
                Text(session.formattedDuration)
            }
            .font(.caption)
            .foregroundStyle(.secondary)
            HStack(spacing: 6) {
                StatusBadge(status: session.status)
                if session.isTranscribed {
                    Label("Transcript", systemImage: "doc.text")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(.vertical, 2)
    }
}

private struct StatusBadge: View {
    let status: String

    var body: some View {
        Text(status)
            .font(.caption2.weight(.medium))
            .padding(.horizontal, 6)
            .padding(.vertical, 1)
            .background(color.opacity(0.2), in: Capsule())
            .foregroundStyle(color)
    }

    private var color: Color {
        switch status {
        case "transcribed": return .green
        case "recording", "transcribing": return .orange
        case "failed": return .red
        default: return .secondary
        }
    }
}
