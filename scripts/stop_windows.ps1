# Stop FinAlly. The finally-data volume is kept, so the portfolio persists.
docker rm -f finally *> $null
Write-Host "FinAlly stopped. Data persists in the 'finally-data' volume."
