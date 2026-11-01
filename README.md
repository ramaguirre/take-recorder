# Take Recorder

Hands-free recorder for musical takes. Recording starts when you play and stops on silence.
After each take you get a few seconds to throw it away with a gesture; otherwise it's kept.

App: https://ramaguirre.github.io/take-recorder/ (installable on Android from Chrome: ⋮ → Install app)

## Controls

| Gesture | Keys / pedal | Action |
|---|---|---|
| 👍 hold | → PgDn Enter | Mark last take ★ best (`_best` in the file name) |
| 👎 hold | ← PgUp Del | Discard last take · while recording, hold 1.5 s to cancel |
| ✋ hold 1 s | P | Pause / resume listening |

## Storage

Each session is a folder named with its start time (`YYYYMMDD_HHMMSS`) in the app's private
storage. **📂 Library** lists the sessions, where you can play, share, download or delete takes.
On desktop you can instead pick a real folder with **Choose folder…**.

## Run locally (PC)

```powershell
.\serve.ps1     # http://localhost:8000
```

Single file app: `index.html`. `sw.js` + `manifest.webmanifest` make it installable/offline.
