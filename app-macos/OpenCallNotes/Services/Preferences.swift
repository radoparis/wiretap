import Foundation

/// How to launch the worker subprocess (executable + fixed leading args + env).
struct LaunchConfig {
    let executablePath: String
    let leadingArgs: [String]
    let environment: [String: String]
}

/// User-configurable settings, persisted in `UserDefaults` (06_UI_SPEC Preferences).
final class Preferences: ObservableObject {
    private enum Key {
        static let workerPath = "workerPath"
        static let workerLeadingArgs = "workerLeadingArgs"
        static let recordingsFolder = "recordingsFolder"
        static let defaultLanguage = "defaultLanguage"
        static let defaultModel = "defaultModel"
    }

    static let languages = ["auto", "en", "pl", "fr", "es", "de", "it"]
    static let models = [
        "mlx-community/whisper-large-v3-turbo",
        "mlx-community/whisper-small",
        "mlx-community/whisper-tiny",
    ]

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    /// Path to the worker executable. Defaults to resolving `opencallnotes-worker`
    /// from `PATH` via `/usr/bin/env`. For dev, point this at
    /// `scripts/run-worker.sh` and clear the leading args.
    @Published var workerPath: String = "" {
        didSet { defaults.set(workerPath, forKey: Key.workerPath) }
    }

    @Published var workerLeadingArgs: String = "" {
        didSet { defaults.set(workerLeadingArgs, forKey: Key.workerLeadingArgs) }
    }

    @Published var recordingsFolder: String = "" {
        didSet { defaults.set(recordingsFolder, forKey: Key.recordingsFolder) }
    }

    @Published var defaultLanguage: String = "auto" {
        didSet { defaults.set(defaultLanguage, forKey: Key.defaultLanguage) }
    }

    @Published var defaultModel: String = Preferences.models[0] {
        didSet { defaults.set(defaultModel, forKey: Key.defaultModel) }
    }

    func load() {
        workerPath = defaults.string(forKey: Key.workerPath) ?? ""
        workerLeadingArgs = defaults.string(forKey: Key.workerLeadingArgs) ?? ""
        recordingsFolder = defaults.string(forKey: Key.recordingsFolder) ?? ""
        defaultLanguage = defaults.string(forKey: Key.defaultLanguage) ?? "auto"
        defaultModel = defaults.string(forKey: Key.defaultModel) ?? Preferences.models[0]
    }

    /// A standalone worker binary bundled inside the .app (release builds), or nil
    /// in dev builds. Lets a downloaded app run with zero configuration.
    static func bundledWorkerPath() -> String? {
        let fm = FileManager.default
        let candidates = [
            Bundle.main.resourceURL?
                .appendingPathComponent("worker", isDirectory: true)
                .appendingPathComponent("opencallnotes-worker"),
            Bundle.main.url(forResource: "opencallnotes-worker", withExtension: nil),
        ].compactMap { $0 }
        return candidates.first { fm.isExecutableFile(atPath: $0.path) }?.path
    }

    /// Resolve the effective launch configuration for the worker.
    ///
    /// Precedence: an explicit Worker path in Preferences (only if it exists) > a
    /// worker bundled in the .app > `opencallnotes-worker` resolved from PATH
    /// (dev/CLI installs). A configured path that no longer exists is ignored so a
    /// stale setting can't break a bundled app.
    var launchConfig: LaunchConfig {
        let fm = FileManager.default
        let trimmedPath = workerPath.trimmingCharacters(in: .whitespaces)
        let executable: String
        let leading: [String]
        if !trimmedPath.isEmpty, fm.isExecutableFile(atPath: trimmedPath) {
            executable = trimmedPath
            leading = workerLeadingArgs.split(separator: " ").map(String.init)
        } else if let bundled = Preferences.bundledWorkerPath() {
            executable = bundled
            leading = []
        } else {
            executable = "/usr/bin/env"
            leading = ["opencallnotes-worker"]
        }

        var env = ProcessInfo.processInfo.environment
        env["PATH"] = Preferences.augmentedPath(env["PATH"])
        let folder = recordingsFolder.trimmingCharacters(in: .whitespaces)
        if !folder.isEmpty {
            env["OPENCALLNOTES_HOME"] = folder
        }
        return LaunchConfig(executablePath: executable, leadingArgs: leading, environment: env)
    }

    /// A GUI app launched from Finder/Xcode inherits only a minimal `PATH`
    /// (`/usr/bin:/bin:/usr/sbin:/sbin`), so `opencallnotes-worker`, `uv`, and
    /// `ffmpeg` from Homebrew / uv installs are not found. Prepend the common
    /// locations so the worker (and the tools it shells out to) resolve.
    static func augmentedPath(_ existing: String?) -> String {
        let extras = [
            "/opt/homebrew/bin",            // Apple Silicon Homebrew
            "/opt/homebrew/sbin",
            "/usr/local/bin",               // Intel Homebrew
            "\(NSHomeDirectory())/.local/bin",   // uv / pipx user installs
            "\(NSHomeDirectory())/.cargo/bin",
        ]
        var seen = Set<String>()
        let current = (existing ?? "/usr/bin:/bin:/usr/sbin:/sbin").split(separator: ":").map(String.init)
        return (extras + current).filter { seen.insert($0).inserted }.joined(separator: ":")
    }

    /// The folder the worker stores recordings in (for "Open recordings folder").
    var resolvedRecordingsURL: URL {
        let folder = recordingsFolder.trimmingCharacters(in: .whitespaces)
        if !folder.isEmpty {
            return URL(fileURLWithPath: folder).appendingPathComponent("recordings")
        }
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        return appSupport.appendingPathComponent("OpenCallNotes/recordings")
    }

    /// The worker's live progress file for a session (polled during transcription).
    func progressURL(sessionID: String) -> URL {
        resolvedRecordingsURL
            .appendingPathComponent(sessionID)
            .appendingPathComponent("transcribe.progress")
    }
}
