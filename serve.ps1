# Run Take Recorder on this PC: http://localhost:8000, takes saved in a real folder.
# The folder is chosen in the app (📁 Change folder…) and remembered.
# To force one for this run:  .\serve.ps1 -Root "D:\Music\Takes"
param([string]$Root = "", [int]$Port = 8000)
Start-Process "http://localhost:$Port"
$rootArg = if ($Root) { @("--root", $Root) } else { @() }
python "$PSScriptRoot\take_server.py" --port $Port @rootArg
