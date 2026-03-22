$ErrorActionPreference = "Stop"

$rootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$imageName = "pm-mvp:local"
$containerName = "pm-mvp"
$envFile = Join-Path $rootDir ".env"

docker build -t $imageName $rootDir
if ($LASTEXITCODE -ne 0) {
  throw "Docker build failed."
}

$existing = docker ps -a --filter "name=^/$containerName$" --format "{{.Names}}"
if ($LASTEXITCODE -ne 0) {
  throw "Unable to query Docker containers."
}
if ($existing -eq $containerName) {
  docker rm -f $containerName | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to remove existing container '$containerName'."
  }
}

$runArgs = @("--name", $containerName, "-p", "8000:8000")
if (Test-Path $envFile) {
  $runArgs += @("--env-file", $envFile)
}

docker run -d @runArgs $imageName | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "Docker run failed."
}

Write-Host "Container '$containerName' is running at http://127.0.0.1:8000"
