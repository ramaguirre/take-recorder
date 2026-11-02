# Run Take Recorder on this PC: http://localhost:8000, takes saved in a real folder.
# Change the folder with:  .\serve.ps1 -Root "D:\Music\Takes"
param([string]$Root = "$env:USERPROFILE\Videos\TakeRecorder", [int]$Port = 8000)
Start-Process "http://localhost:$Port"
python "$PSScriptRoot\take_server.py" --root $Root --port $Port
