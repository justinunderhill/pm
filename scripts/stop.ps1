$ErrorActionPreference = "Stop"

$containerName = "pm-mvp"
$existing = docker ps -a --filter "name=^/$containerName$" --format "{{.Names}}"
if ($LASTEXITCODE -ne 0) {
  throw "Unable to query Docker containers."
}

if ($existing -eq $containerName) {
  docker rm -f $containerName | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to remove container '$containerName'."
  }
  Write-Host "Container '$containerName' stopped and removed."
} else {
  Write-Host "Container '$containerName' is not running."
}
