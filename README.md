# Take Recorder

Hands-free recorder for musical takes. Recording starts when you play and stops on silence.
After each take you get a few seconds to throw it away with a gesture; otherwise it's kept,
with its silent tail trimmed off.

App: https://ramaguirre.github.io/take-recorder/ (installable on Android from Chrome: ⋮ → Install app)

## Controls

| Gesture | Keys / pedal | Action |
|---|---|---|
| 👍 hold | → PgDn Enter | Mark last take ★ best (`_best` in the file name) |
| 👎 hold | ← PgUp Del | Discard last take · while recording, hold 1.5 s to cancel |
| ✋ hold 1 s | P | Pause / resume listening |

## Library

**📂 Library** lists every session (a folder named with its start time, `YYYYMMDD_HHMMSS`) with a
waveform under each take. Tap a take or its waveform to play it and trim the start and end;
share, download or delete from the same list.

Trimming uses ffmpeg (wasm) without re-encoding: the end is exact, the start lands on the
nearest earlier keyframe (recordings have one every second). The ffmpeg core (~32 MB) is
downloaded on first use and cached.

## Where takes are saved

| How you open the app | Takes go to | See them |
|---|---|---|
| PC, `.\serve.ps1` | a real folder you choose with **📁 Change folder…** (remembered; default `%USERPROFILE%\Videos\TakeRecorder`) | **🗂 Open in Explorer** |
| PC, the GitHub Pages link | a folder you pick with **Choose folder…** (remembered), else app storage | the picked folder |
| Phone | the app's private storage, not visible in the Files app | Library: ⤴ share, ⬇ copy to Downloads |

A web page cannot open Explorer, show a folder picker that returns a full path, or learn a
folder's location; the PC helper (`take_server.py`, Python stdlib only) does all three, and
remembers the folder in `%APPDATA%\TakeRecorder\config.json`.

## Run locally (PC)

```powershell
.\serve.ps1                                # http://localhost:8000
.\serve.ps1 -Root "D:\Music\Takes"         # force a folder for this run
```

Files: `index.html` (the whole app), `take_server.py` (PC helper), `sw.js` + `manifest.webmanifest`
(installable/offline), `vendor/ffmpeg/` (ffmpeg.wasm wrapper, MIT).
