# Start FinAlly in Docker. Idempotent; pass -Build to force a rebuild.
param([switch]$Build)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$image = "finally"
$container = "finally"

docker image inspect $image *> $null
if ($Build -or $LASTEXITCODE -ne 0) {
    docker build -t $image .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

docker rm -f $container *> $null

$envArgs = @()
if (Test-Path ".env") { $envArgs = @("--env-file", ".env") }

docker run -d --name $container -p 8000:8000 -v finally-data:/app/db @envArgs $image | Out-Null

Write-Host "FinAlly is running at http://localhost:8000"
Start-Process "http://localhost:8000"
