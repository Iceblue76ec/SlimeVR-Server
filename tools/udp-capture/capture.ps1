param(
    [string]$Interface,
    [ValidateRange(1, 65535)][int]$Port = 6969,
    [string]$Output = (Join-Path (Get-Location) ("slime-udp-{0}.pcapng" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))),
    [string]$Dumpcap = "$env:ProgramFiles\Wireshark\dumpcap.exe"
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Dumpcap -PathType Leaf)) {
    throw "dumpcap.exe not found at '$Dumpcap'. Install Wireshark with Npcap or pass -Dumpcap."
}
if (-not $Interface) {
    & $Dumpcap -D
    if ($LASTEXITCODE -ne 0) { throw 'Unable to list capture interfaces.' }
    Write-Host 'Run again with -Interface set to the number for the tracker network adapter.'
    exit 0
}
if (Test-Path -LiteralPath $Output) { throw "Output already exists: $Output" }
Write-Host "Capturing UDP destination port $Port on interface $Interface to $Output. Press Ctrl+C to stop."
& $Dumpcap -i $Interface -f "udp dst port $Port" -s 0 -w $Output
if ($LASTEXITCODE -ne 0) { throw "dumpcap exited with code $LASTEXITCODE; inspect the output above." }
