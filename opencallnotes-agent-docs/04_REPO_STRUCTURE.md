# Repository Structure

```text
opencallnotes/
  README.md
  LICENSE
  DECISIONS.md
  docs/
    architecture.md
    user-guide.md
    dev-guide.md
    privacy.md
  app-macos/
    OpenCallNotes.xcodeproj
    OpenCallNotes/
      App.swift
      ContentView.swift
      Views/
      Models/
      Services/
        WorkerClient.swift
        SessionStore.swift
  worker/
    pyproject.toml
    src/opencallnotes_worker/
      __init__.py
      cli.py
      audio.py
      transcribe.py
      sessions.py
      export.py
      devices.py
    tests/
  scripts/
    bootstrap.sh
    run-worker.sh
    run-app-dev.sh
```

## Rule
Keep UI and worker decoupled. The Swift app should communicate with the worker via command-line JSON initially.

