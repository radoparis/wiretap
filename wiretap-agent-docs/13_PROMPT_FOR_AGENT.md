# Prompt for Autonomous Coding Agent

You are implementing OpenCallNotes, an open-source local-first macOS app for recording conversations and producing local transcripts without paid APIs.

You must work autonomously.

Do not ask the user preference questions. Make decisions using the included docs.

Primary goal: ship a working MVP with UI.

Read these files first:
1. `00_AGENT_MISSION.md`
2. `01_PRODUCT_SPEC.md`
3. `02_ARCHITECTURE.md`
4. `07_IMPLEMENTATION_PLAN.md`
5. `08_TASKS_FOR_AGENT.md`
6. `10_DECISION_POLICY.md`

Implement in this order:
1. Repo bootstrap.
2. Python worker device listing.
3. Python worker recording.
4. Python worker transcription.
5. Exporters.
6. SwiftUI UI.
7. End-to-end test.
8. README polish.

Rules:
- If there are multiple implementation options, choose the simplest working one.
- Record decisions in `DECISIONS.md`.
- Do not introduce paid APIs.
- Do not introduce cloud upload.
- Do not block on perfect packaging.
- Do not skip UI.
- Do not implement live transcription before record-then-transcribe works.

Definition of Done:
A user can launch the app, record audio, stop recording, transcribe locally, view transcript, and export it.

