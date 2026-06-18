import SwiftUI

/// Session detail: metadata, transcribe/export actions, transcript viewer
/// (06_UI_SPEC "Session detail").
struct SessionDetailView: View {
    @EnvironmentObject private var store: SessionStore
    let detail: SessionDetail

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                header
                Divider()
                actions
                Divider()
                transcriptSection
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .navigationTitle(detail.title)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(detail.title).font(.title2.bold())
            Label(detail.createdAt, systemImage: "calendar")
            Label("\(detail.session.formattedDuration) · \(detail.status)",
                  systemImage: "clock")
            Label("\(detail.audioFile)", systemImage: "waveform")
                .foregroundStyle(.secondary)
        }
        .font(.callout)
        .labelStyle(.titleAndIcon)
    }

    private var actions: some View {
        HStack {
            Button {
                Task { await store.transcribeSelected() }
            } label: {
                Label(detail.transcriptAvailable ? "Re-transcribe" : "Transcribe",
                      systemImage: "text.bubble")
            }
            .buttonStyle(.borderedProminent)
            .disabled(store.isBusy || detail.status == "recording")

            Spacer()

            ForEach(["txt", "md", "srt", "json"], id: \.self) { format in
                Button(format.uppercased()) {
                    Task { await store.exportSelected(format: format) }
                }
                .disabled(!detail.transcriptAvailable || store.isBusy)
            }
        }
    }

    @ViewBuilder private var transcriptSection: some View {
        if let transcript = detail.transcript {
            VStack(alignment: .leading, spacing: 10) {
                Text("Transcript").font(.headline)
                Text("Language: \(transcript.language) · Model: \(shortModel(transcript.model))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                ForEach(transcript.segments) { segment in
                    HStack(alignment: .top, spacing: 10) {
                        Text(segment.startTimestamp)
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(.secondary)
                            .frame(width: 48, alignment: .leading)
                        Text(segment.text).textSelection(.enabled)
                    }
                }
                if transcript.segments.isEmpty {
                    Text(transcript.text).textSelection(.enabled)
                }
            }
        } else {
            ContentUnavailableView(
                "No transcript yet",
                systemImage: "doc.text.magnifyingglass",
                description: Text("Click Transcribe to generate one on-device.")
            )
        }
    }

    private func shortModel(_ id: String) -> String {
        id.split(separator: "/").last.map(String.init) ?? id
    }
}
