$session_dir = "C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project\.superpowers\brainstorm\forge-vn-session"
If (!(Test-Path $session_dir)) {
    New-Item -ItemType Directory -Path (Join-Path $session_dir "state"), (Join-Path $session_dir "content") -Force
}
$env:BRAINSTORM_DIR = $session_dir
$env:BRAINSTORM_HOST = "127.0.0.1"
$env:BRAINSTORM_URL_HOST = "localhost"
node "C:\Users\bahma\.gemini\extensions\superpowers\skills\brainstorming\scripts\server.cjs"
