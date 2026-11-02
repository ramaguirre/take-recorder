# vendor/ffmpeg

Unmodified copy of `@ffmpeg/ffmpeg@0.12.10` `dist/esm/` (MIT, https://github.com/ffmpegwasm/ffmpeg.wasm).

It is served from the app's own origin because browsers refuse to start a Web Worker from
another origin. The large core (`@ffmpeg/core@0.12.6`, ~32 MB wasm) is fetched from jsDelivr
at first use and cached by `sw.js`.
