<#
.SYNOPSIS
    Deploy the Wine Fermentation System to a target environment.

.DESCRIPTION
    Builds Docker images, runs Alembic migrations (via the migrate service),
    and starts all services. Supports dev / test / staging / prod.

.PARAMETER Env
    Target environment: dev | test | staging | prod
    Default: dev

.PARAMETER Action
    up      - Build images and start all services (default)
    down    - Stop and remove containers (keeps volumes)
    destroy - Stop, remove containers AND volumes (⚠ deletes DB data)
    migrate - Run migrations only, then stop the migrate container
    logs    - Tail logs for all services (Ctrl+C to stop)
    ps      - Show running containers
    build   - Build images only, do not start

.PARAMETER Service
    Optional: restrict the action to a single service name
    (e.g. fermentation, winery, db)

.PARAMETER NoBuild
    Skip the --build flag on 'up'. Use cached images.

.EXAMPLE
    .\deploy.ps1                          # dev up (default)
    .\deploy.ps1 -Env staging            # staging up
    .\deploy.ps1 -Env prod -Action up    # production up
    .\deploy.ps1 -Env dev -Action logs   # tail dev logs
    .\deploy.ps1 -Env dev -Action down   # stop dev stack
    .\deploy.ps1 -Env prod -Action migrate  # run migrations only
    .\deploy.ps1 -Env dev -NoBuild       # start without rebuilding images
    .\deploy.ps1 -Env dev -Action logs -Service fermentation  # tail one service
#>

[CmdletBinding()]
param (
    [ValidateSet("dev", "test", "staging", "prod")]
    [string]$Env = "dev",

    [ValidateSet("up", "down", "destroy", "migrate", "logs", "ps", "build")]
    [string]$Action = "up",

    [string]$Service = "",

    [switch]$NoBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# Helpers
# =============================================================================

function Write-Header([string]$msg) {
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step([string]$msg) {
    Write-Host "  --> $msg" -ForegroundColor Yellow
}

function Write-Success([string]$msg) {
    Write-Host "  [OK] $msg" -ForegroundColor Green
}

function Write-Fail([string]$msg) {
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
}

# =============================================================================
# Resolve paths
# =============================================================================

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$EnvFile     = Join-Path $Root ".env.$Env"
$ComposeBase = Join-Path $Root "docker-compose.yml"
$ComposeEnv  = Join-Path $Root "docker-compose.$Env.yml"

# =============================================================================
# Pre-flight checks
# =============================================================================

Write-Header "Wine Fermentation System — Deploy [$Env] / [$Action]"

# Verify .env file exists
if (-not (Test-Path $EnvFile)) {
    Write-Fail "Missing environment file: $EnvFile"
    Write-Host ""
    Write-Host "  Create it from the template:" -ForegroundColor White
    Write-Host "    Copy-Item .env.example $EnvFile" -ForegroundColor White
    Write-Host "  Then fill in real values." -ForegroundColor White
    exit 1
}
Write-Step "Using env file : $EnvFile"

# Verify compose override exists
if (-not (Test-Path $ComposeEnv)) {
    Write-Fail "Missing compose override: $ComposeEnv"
    exit 1
}
Write-Step "Compose files  : docker-compose.yml + docker-compose.$Env.yml"

# Verify Docker is running
try {
    docker info *> $null
} catch {
    Write-Fail "Docker is not running. Please start Docker Desktop."
    exit 1
}
Write-Success "Docker is running"

# Warn on CHANGE_ME secrets (non-dev envs)
if ($Env -ne "dev") {
    $EnvContent = Get-Content $EnvFile -Raw
    if ($EnvContent -match "CHANGE_ME") {
        Write-Host ""
        Write-Host "  [WARN] .env.$Env still contains CHANGE_ME placeholders." -ForegroundColor Red
        Write-Host "         Replace all CHANGE_ME values before deploying to $Env." -ForegroundColor Red
        if ($Env -eq "prod") {
            Write-Host ""
            Write-Host "  Aborting production deploy with placeholder secrets." -ForegroundColor Red
            exit 1
        }
        Write-Host ""
    }
}

# =============================================================================
# Build the base docker compose command
# =============================================================================

$ComposeCmd = "docker compose -f `"$ComposeBase`" -f `"$ComposeEnv`" --env-file `"$EnvFile`""

# =============================================================================
# Execute the requested action
# =============================================================================

switch ($Action) {

    "build" {
        Write-Step "Building images..."
        Invoke-Expression "$ComposeCmd build $Service"
        Write-Success "Images built"
    }

    "up" {
        $BuildFlag = if ($NoBuild) { "" } else { "--build" }

        Write-Step "Starting stack (migrations run automatically via 'migrate' service)..."
        Invoke-Expression "$ComposeCmd up $BuildFlag --detach $Service"

        if ($LASTEXITCODE -ne 0) {
            Write-Fail "docker compose up failed (exit $LASTEXITCODE)"
            exit $LASTEXITCODE
        }

        Write-Host ""
        Write-Success "Stack is up!"
        Write-Host ""
        Write-Host "  Services:" -ForegroundColor White

        # Parse host ports from env file for display
        $PortFermentation = (Get-Content $EnvFile | Where-Object { $_ -match "^FERMENTATION_HOST_PORT=" }) -replace ".*=", ""
        $PortWinery       = (Get-Content $EnvFile | Where-Object { $_ -match "^WINERY_HOST_PORT=" })       -replace ".*=", ""
        $PortDb           = (Get-Content $EnvFile | Where-Object { $_ -match "^POSTGRES_HOST_PORT=" })      -replace ".*=", ""

        if ($PortFermentation) { Write-Host "    Fermentation API : http://localhost:$PortFermentation" -ForegroundColor Green }
        if ($PortWinery)       { Write-Host "    Winery API       : http://localhost:$PortWinery"       -ForegroundColor Green }
        if ($PortDb)           { Write-Host "    PostgreSQL       : localhost:$PortDb"                  -ForegroundColor Green }

        Write-Host ""
        Write-Host "  Docs:" -ForegroundColor White
        if ($PortFermentation) { Write-Host "    http://localhost:$PortFermentation/docs" -ForegroundColor Cyan }
        if ($PortWinery)       { Write-Host "    http://localhost:$PortWinery/docs"       -ForegroundColor Cyan }
        Write-Host ""
        Write-Host "  Tail logs : .\deploy.ps1 -Env $Env -Action logs" -ForegroundColor DarkGray
        Write-Host "  Stop      : .\deploy.ps1 -Env $Env -Action down" -ForegroundColor DarkGray
    }

    "migrate" {
        Write-Step "Running Alembic migrations only..."
        Invoke-Expression "$ComposeCmd run --rm migrate"

        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Migration failed (exit $LASTEXITCODE)"
            exit $LASTEXITCODE
        }
        Write-Success "Migrations complete"
    }

    "down" {
        Write-Step "Stopping and removing containers (volumes preserved)..."
        Invoke-Expression "$ComposeCmd down $Service"
        Write-Success "Stack stopped"
    }

    "destroy" {
        Write-Host ""
        Write-Host "  [WARNING] This will DELETE all containers AND database volumes." -ForegroundColor Red
        $Confirm = Read-Host "  Type 'yes' to confirm"
        if ($Confirm -ne "yes") {
            Write-Host "  Cancelled." -ForegroundColor Yellow
            exit 0
        }
        Write-Step "Destroying stack and volumes..."
        Invoke-Expression "$ComposeCmd down --volumes $Service"
        Write-Success "Stack and volumes destroyed"
    }

    "logs" {
        Write-Step "Tailing logs (Ctrl+C to stop)..."
        Invoke-Expression "$ComposeCmd logs --follow --tail=100 $Service"
    }

    "ps" {
        Invoke-Expression "$ComposeCmd ps"
    }
}
