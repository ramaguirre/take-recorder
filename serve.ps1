# Serve the app on http://localhost:8000 (camera, mic and folder access need localhost or https)
Start-Process "http://localhost:8000"
python -m http.server 8000 --bind 127.0.0.1 --directory $PSScriptRoot
