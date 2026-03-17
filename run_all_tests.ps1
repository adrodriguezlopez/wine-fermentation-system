#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs all unit and integration tests for the wine fermentation system.

.DESCRIPTION
    This script runs all tests across all modules with proper reporting.
    Uses Poetry to run tests in each module's independent virtual environment (ADR-028).
    Exit code 0 indicates all tests passed, non-zero indicates failures.
    
    Requirements:
    - Poetry installed and available in PATH
    - Each module has poetry.lock and dependencies installed (poetry install)
    - Modules: fermentation, winery, fruit_origin

.EXAMPLE
    .\run_all_tests.ps1
    Runs all tests with full reporting

.EXAMPLE
    .\run_all_tests.ps1 -Quick
    Runs only unit tests for faster feedback
    
.EXAMPLE
    .\run_all_tests.ps1 -Verbose
    Runs all tests with detailed output
#>

param(
    [switch]$Quick,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$startTime = Get-Date

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Wine Fermentation System - Test Suite" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Started: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host ""

$testResults = @{
    SharedTestingUnit = $null
    SharedErrorHandlingUnit = $null
    SharedAuthUnit = $null
    SharedAuthIntegration = $null
    WineryUnit = $null
    WineryIntegration = $null
    FruitOriginUnit = $null
    FruitOriginIntegration = $null
    FruitOriginAPI = $null
    FermentationComplete = $null
    AnalysisEngineUnit = $null
    AnalysisEngineIntegration = $null
    ProtocolMigrationIntegration = $null
    ProtocolUnit = $null
}

$allPassed = $true

# Helper function to run tests using Poetry
function Invoke-TestSuite {
    param(
        [string]$Name,
        [string]$ModulePath,
        [string]$TestPath,
        [string]$Type = "unit",
        [switch]$UsePoetry = $true
    )
    
    Write-Host "--------------------------------------------" -ForegroundColor Yellow
    Write-Host "Running: $Name" -ForegroundColor Yellow
    Write-Host "--------------------------------------------" -ForegroundColor Yellow
    
    try {
        if ($UsePoetry) {
            # Check if pyproject.toml exists
            $pyprojectPath = Join-Path $ModulePath "pyproject.toml"
            if (-not (Test-Path $pyprojectPath)) {
                Write-Host "[SKIP] ${Name}: No pyproject.toml found at $ModulePath" -ForegroundColor Yellow
                return @{ Success = $true; Passed = 0; Failed = 0; Skipped = $true; ExitCode = 0 }
            }
            
            # Run tests using poetry from module directory
            try {
                Push-Location $ModulePath
                $testArgs = @(
                    "run",
                    "pytest",
                    $TestPath,
                    "-q",
                    "--tb=line"
                )
                
                if ($Verbose) {
                    $testArgs[2] = "-v"
                }
                
                $output = & poetry @testArgs 2>&1
                $exitCode = $LASTEXITCODE
            } finally {
                Pop-Location
            }
        } else {
            # Run tests using python directly (for shared modules without Poetry)
            try {
                $pythonExe = (Get-Command python -ErrorAction Stop).Source
            } catch {
                Write-Host "[SKIP] ${Name}: Python not found" -ForegroundColor Yellow
                return @{ Success = $true; Passed = 0; Failed = 0; Skipped = $true; ExitCode = 0 }
            }
            
            $testArgs = @(
                "-m", "pytest",
                $TestPath,
                "-q",
                "--tb=line"
            )
            
            if ($Verbose) {
                $testArgs[3] = "-v"
            }
            
            $output = & $pythonExe @testArgs 2>&1
            $exitCode = $LASTEXITCODE
        }
        
        # Check for pytest not installed
        if ($output -match "No module named pytest") {
            Write-Host "[SKIP] ${Name}: pytest not installed" -ForegroundColor Yellow
            return @{ Success = $true; Passed = 0; Failed = 0; Skipped = $true; ExitCode = 0 }
        }
        
        # Parse output for test results (flexible regex for both verbose and quiet modes)
        # Filter to get only pytest summary line (lines with "passed", "failed", "error" at end)
        # Matches both "===== 23 passed in 0.43s =====" and "23 passed in 0.43s"
        $summaryLine = $output | Select-String -Pattern "(\d+)\s+(passed|failed|error)" | Select-Object -Last 1
        
        if ($summaryLine) {
            $summaryText = $summaryLine.ToString()
            
            # Extract passed count
            $passed = 0
            if ($summaryText -match '(\d+)\s+passed') {
                $passed = [int]($Matches[1])
            }
            
            # Extract failed count
            $failed = 0
            if ($summaryText -match '(\d+)\s+failed') {
                $failed = [int]($Matches[1])
            }
            
            # Extract error count
            $errors = 0
            if ($summaryText -match '(\d+)\s+errors?') {
                $errors = [int]($Matches[1])
            }
            
            if ($failed -gt 0 -or $errors -gt 0) {
                Write-Host "[FAIL] ${Name}: $passed passed, $failed failed, $errors errors" -ForegroundColor Red
                Write-Host "Last 10 lines of output:" -ForegroundColor Yellow
                $output | Select-Object -Last 10 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
                return @{ Success = $false; Passed = $passed; Failed = $failed; Errors = $errors; ExitCode = $exitCode }
            } elseif ($passed -gt 0) {
                Write-Host "[PASS] ${Name}: $passed tests passed" -ForegroundColor Green
                return @{ Success = $true; Passed = $passed; Failed = 0; ExitCode = $exitCode }
            } else {
                Write-Host "[WARN] ${Name}: Could not parse test count" -ForegroundColor Yellow
                return @{ Success = $false; Passed = 0; Failed = 0; ExitCode = $exitCode }
            }
        } else {
            Write-Host "[WARN] ${Name}: Could not find pytest summary line" -ForegroundColor Yellow
            return @{ Success = $false; Passed = 0; Failed = 0; ExitCode = $exitCode }
        }
    } catch {
        # Check if the error is about pytest not being installed
        if ($_.Exception.Message -match "No module named pytest") {
            Write-Host "[SKIP] ${Name}: pytest not installed" -ForegroundColor Yellow
            return @{ Success = $true; Passed = 0; Failed = 0; Skipped = $true; ExitCode = 0 }
        }
        
        Write-Host "[FAIL] ${Name}: Exception occurred" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        return @{ Success = $false; Passed = 0; Failed = 0; ExitCode = 1 }
    }
}

# ADR-028 Phase 4: Shared module now uses Poetry for independent environment

# Run Shared Testing Unit Tests
Write-Host "`n" 
$testResults.SharedTestingUnit = Invoke-TestSuite `
    -Name "Shared Testing - Unit Tests" `
    -ModulePath "src/shared" `
    -TestPath "testing/tests/" `
    -Type "unit"

if (-not $testResults.SharedTestingUnit.Success) { $allPassed = $false }

# Run Shared Error Handling Unit Tests (ADR-026)
Write-Host "`n"
$testResults.SharedErrorHandlingUnit = Invoke-TestSuite `
    -Name "Shared Error Handling - Unit Tests" `
    -ModulePath "src/shared" `
    -TestPath "../../tests/shared/test_error_handling.py" `
    -Type "unit"

if (-not $testResults.SharedErrorHandlingUnit.Success) { $allPassed = $false }

# Run Shared Auth Unit Tests
Write-Host "`n"
$testResults.SharedAuthUnit = Invoke-TestSuite `
    -Name "Shared Auth - Unit Tests" `
    -ModulePath "src/shared" `
    -TestPath "auth/tests/unit/" `
    -Type "unit"

if (-not $testResults.SharedAuthUnit.Success) { $allPassed = $false }

# Run Shared Auth Integration Tests
if (-not $Quick) {
    Write-Host "`n"
    $testResults.SharedAuthIntegration = Invoke-TestSuite `
        -Name "Shared Auth - Integration Tests" `
        -ModulePath "src/shared/auth" `
        -TestPath "tests/integration/" `
        -Type "integration"
    
    if (-not $testResults.SharedAuthIntegration.Success) { $allPassed = $false }
}

# ADR-028: Module tests now use Poetry for independent environments

# Run Winery Unit Tests
Write-Host "`n"
$testResults.WineryUnit = Invoke-TestSuite `
    -Name "Winery - Unit Tests" `
    -ModulePath "src/modules/winery" `
    -TestPath "tests/unit/" `
    -Type "unit"

if (-not $testResults.WineryUnit.Success) { $allPassed = $false }

# Run Winery Integration Tests
if (-not $Quick) {
    Write-Host "`n"
    $testResults.WineryIntegration = Invoke-TestSuite `
        -Name "Winery - Integration Tests" `
        -ModulePath "src/modules/winery" `
        -TestPath "tests/integration/" `
        -Type "integration"
    
    if (-not $testResults.WineryIntegration.Success) { $allPassed = $false }
}

# Run Fruit Origin Unit Tests
Write-Host "`n" 
$testResults.FruitOriginUnit = Invoke-TestSuite `
    -Name "Fruit Origin - Unit Tests" `
    -ModulePath "src/modules/fruit_origin" `
    -TestPath "tests/unit/" `
    -Type "unit"

if (-not $testResults.FruitOriginUnit.Success) { $allPassed = $false }

# Run Fruit Origin Integration Tests
if (-not $Quick) {
    Write-Host "`n"
    $testResults.FruitOriginIntegration = Invoke-TestSuite `
        -Name "Fruit Origin - Integration Tests" `
        -ModulePath "src/modules/fruit_origin" `
        -TestPath "tests/integration/" `
        -Type "integration"
    
    if (-not $testResults.FruitOriginIntegration.Success) { $allPassed = $false }
}

# Run Fruit Origin API Tests
if (-not $Quick) {
    Write-Host "`n"
    $testResults.FruitOriginAPI = Invoke-TestSuite `
        -Name "Fruit Origin - API Tests" `
        -ModulePath "src/modules/fruit_origin" `
        -TestPath "tests/api/" `
        -Type "api"
    
    if (-not $testResults.FruitOriginAPI.Success) { $allPassed = $false }
}

# Run Fermentation Module Tests (all unit, integration, and API tests)
Write-Host "`n"
Write-Host "--------------------------------------------" -ForegroundColor Yellow
Write-Host "Running: Fermentation Module - Complete Test Suite" -ForegroundColor Yellow
Write-Host "--------------------------------------------" -ForegroundColor Yellow

try {
    Push-Location "src/modules/fermentation"
    $output = & poetry run pytest tests/unit/ tests/integration/repository_component/ tests/integration/test_etl_integration.py tests/integration/api_component/ tests/api/ --ignore=tests/unit/api_security/ -q --tb=line 2>&1
    $exitCode = $LASTEXITCODE
    Pop-Location
} catch {
    Write-Host "[FAIL] Fermentation Tests: Exception occurred" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $testResults.FermentationComplete = @{ Success = $false; Passed = 0; Failed = 0; ExitCode = 1 }
    $allPassed = $false
}

if ($exitCode -eq 0) {
    $summaryLine = $output | Select-String -Pattern "(\d+)\s+passed" | Select-Object -Last 1
    if ($summaryLine) {
        $summaryText = $summaryLine.ToString()
        $passed = 0
        if ($summaryText -match '(\d+)\s+passed') { $passed = [int]($Matches[1]) }
        Write-Host "[PASS] Fermentation Module - Complete Test Suite: $passed tests passed" -ForegroundColor Green
        $testResults.FermentationComplete = @{ Success = $true; Passed = $passed; Failed = 0; ExitCode = 0 }
    }
} else {
    $summaryLine = $output | Select-String -Pattern "(\d+)\s+(passed|failed|error)" | Select-Object -Last 1
    if ($summaryLine) {
        $summaryText = $summaryLine.ToString()
        $passed = 0
        $failed = 0
        if ($summaryText -match '(\d+)\s+passed') { $passed = [int]($Matches[1]) }
        if ($summaryText -match '(\d+)\s+failed') { $failed = [int]($Matches[1]) }
        Write-Host "[FAIL] Fermentation Module - Complete Test Suite: $passed passed, $failed failed" -ForegroundColor Red
        $output | Select-Object -Last 10 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
        $testResults.FermentationComplete = @{ Success = $false; Passed = $passed; Failed = $failed; ExitCode = 1 }
        $allPassed = $false
    }
}

# Run Analysis Engine Unit Tests
Write-Host "`n"
Write-Host "--------------------------------------------" -ForegroundColor Yellow
Write-Host "Running: Analysis Engine - Unit Tests" -ForegroundColor Yellow
Write-Host "--------------------------------------------" -ForegroundColor Yellow

try {
    Push-Location "src/modules/analysis_engine"
    $output = & poetry run pytest "../../../tests/unit/modules/analysis_engine/" -q --tb=line 2>&1
    $exitCode = $LASTEXITCODE
    Pop-Location
} catch {
    Write-Host "[FAIL] Analysis Engine Unit Tests: Exception occurred" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $testResults.AnalysisEngineUnit = @{ Success = $false; Passed = 0; Failed = 0; ExitCode = 1 }
    $allPassed = $false
}

if ($exitCode -eq 0) {
    $summaryLine = $output | Select-String -Pattern "(\d+)\s+passed" | Select-Object -Last 1
    if ($summaryLine) {
        $summaryText = $summaryLine.ToString()
        $passed = 0
        if ($summaryText -match '(\d+)\s+passed') { $passed = [int]($Matches[1]) }
        Write-Host "[PASS] Analysis Engine - Unit Tests: $passed tests passed" -ForegroundColor Green
        $testResults.AnalysisEngineUnit = @{ Success = $true; Passed = $passed; Failed = 0; ExitCode = 0 }
    } else {
        Write-Host "[WARN] Analysis Engine Unit Tests: Could not parse test count" -ForegroundColor Yellow
        $testResults.AnalysisEngineUnit = @{ Success = $false; Passed = 0; Failed = 0; ExitCode = 1 }
        $allPassed = $false
    }
} else {
    $summaryLine = $output | Select-String -Pattern "(\d+)\s+(passed|failed|error)" | Select-Object -Last 1
    if ($summaryLine) {
        $summaryText = $summaryLine.ToString()
        $passed = 0
        $failed = 0
        if ($summaryText -match '(\d+)\s+passed') { $passed = [int]($Matches[1]) }
        if ($summaryText -match '(\d+)\s+failed') { $failed = [int]($Matches[1]) }
        Write-Host "[FAIL] Analysis Engine - Unit Tests: $passed passed, $failed failed" -ForegroundColor Red
        $output | Select-Object -Last 10 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
        $testResults.AnalysisEngineUnit = @{ Success = $false; Passed = $passed; Failed = $failed; ExitCode = 1 }
        $allPassed = $false
    }
}

# Run Analysis Engine Integration Tests
# Requires PostgreSQL test DB at localhost:5433. Skips gracefully if not available.
Write-Host "`n"
Write-Host "--------------------------------------------" -ForegroundColor Yellow
Write-Host "Running: Analysis Engine - Integration Tests" -ForegroundColor Yellow
Write-Host "--------------------------------------------" -ForegroundColor Yellow

$dbAvailable = $false
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connectTask = $tcpClient.ConnectAsync("localhost", 5433)
    $dbAvailable = $connectTask.Wait(2000) -and $tcpClient.Connected
    $tcpClient.Close()
} catch {
    $dbAvailable = $false
}

if (-not $dbAvailable) {
    Write-Host "[SKIP] Analysis Engine - Integration Tests: PostgreSQL not available at localhost:5433" -ForegroundColor Yellow
    $testResults.AnalysisEngineIntegration = @{ Success = $true; Passed = 0; Failed = 0; Skipped = $true; ExitCode = 0 }
} else {
    try {
        Push-Location "src/modules/analysis_engine"
        $output = & poetry run pytest "../../../tests/integration/modules/analysis_engine/repositories/" -q --tb=line 2>&1
        $exitCode = $LASTEXITCODE
        Pop-Location
    } catch {
        Write-Host "[FAIL] Analysis Engine Integration Tests: Exception occurred" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        $testResults.AnalysisEngineIntegration = @{ Success = $false; Passed = 0; Failed = 0; ExitCode = 1 }
        $allPassed = $false
    }

    if ($exitCode -eq 0) {
        $summaryLine = $output | Select-String -Pattern "(\d+)\s+passed" | Select-Object -Last 1
        if ($summaryLine) {
            $summaryText = $summaryLine.ToString()
            $passed = 0
            if ($summaryText -match '(\d+)\s+passed') { $passed = [int]($Matches[1]) }
            Write-Host "[PASS] Analysis Engine - Integration Tests: $passed tests passed" -ForegroundColor Green
            $testResults.AnalysisEngineIntegration = @{ Success = $true; Passed = $passed; Failed = 0; ExitCode = 0 }
        }
    } else {
        $summaryLine = $output | Select-String -Pattern "(\d+)\s+(passed|failed|error)" | Select-Object -Last 1
        if ($summaryLine) {
            $summaryText = $summaryLine.ToString()
            $passed = 0; $failed = 0
            if ($summaryText -match '(\d+)\s+passed') { $passed = [int]($Matches[1]) }
            if ($summaryText -match '(\d+)\s+failed') { $failed = [int]($Matches[1]) }
            Write-Host "[FAIL] Analysis Engine - Integration Tests: $passed passed, $failed failed" -ForegroundColor Red
            $output | Select-Object -Last 10 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
            $testResults.AnalysisEngineIntegration = @{ Success = $false; Passed = $passed; Failed = $failed; ExitCode = 1 }
            $allPassed = $false
        }
    }
}

# Run Protocol Migration Integration Tests (migrations 001-003)
# Requires PostgreSQL at localhost:5433 with alembic upgrade head applied.
# Skips gracefully if DB is not available.
Write-Host "`n"
Write-Host "--------------------------------------------" -ForegroundColor Yellow
Write-Host "Running: Protocol Migrations - Integration Tests (001-003)" -ForegroundColor Yellow
Write-Host "--------------------------------------------" -ForegroundColor Yellow

if (-not $dbAvailable) {
    Write-Host "[SKIP] Protocol Migrations - Integration Tests: PostgreSQL not available at localhost:5433" -ForegroundColor Yellow
    $testResults.ProtocolMigrationIntegration = @{ Success = $true; Passed = 0; Failed = 0; Skipped = $true; ExitCode = 0 }
} else {
    try {
        Push-Location "src/modules/fermentation"
        $output = & poetry run pytest "../../../tests/integration/modules/protocol_migrations/" -q --tb=line 2>&1
        $exitCode = $LASTEXITCODE
        Pop-Location
    } catch {
        Write-Host "[FAIL] Protocol Migration Integration Tests: Exception occurred" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        $testResults.ProtocolMigrationIntegration = @{ Success = $false; Passed = 0; Failed = 0; ExitCode = 1 }
        $allPassed = $false
    }

    if ($exitCode -eq 0) {
        $summaryLine = $output | Select-String -Pattern "(\d+)\s+passed" | Select-Object -Last 1
        if ($summaryLine) {
            $summaryText = $summaryLine.ToString()
            $passed = 0
            if ($summaryText -match '(\d+)\s+passed') { $passed = [int]($Matches[1]) }
            Write-Host "[PASS] Protocol Migrations - Integration Tests: $passed tests passed" -ForegroundColor Green
            $testResults.ProtocolMigrationIntegration = @{ Success = $true; Passed = $passed; Failed = 0; ExitCode = 0 }
        }
    } else {
        $summaryLine = $output | Select-String -Pattern "(\d+)\s+(passed|failed|error)" | Select-Object -Last 1
        if ($summaryLine) {
            $summaryText = $summaryLine.ToString()
            $passed = 0; $failed = 0
            if ($summaryText -match '(\d+)\s+passed') { $passed = [int]($Matches[1]) }
            if ($summaryText -match '(\d+)\s+failed') { $failed = [int]($Matches[1]) }
            Write-Host "[FAIL] Protocol Migrations - Integration Tests: $passed passed, $failed failed" -ForegroundColor Red
            $output | Select-Object -Last 10 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
            $testResults.ProtocolMigrationIntegration = @{ Success = $false; Passed = $passed; Failed = $failed; ExitCode = 1 }
            $allPassed = $false
        }
    }
}

# Run Protocol (ADR-035) Unit Tests (enums + repositories)
Write-Host "`n"
Write-Host "--------------------------------------------" -ForegroundColor Yellow
Write-Host "Running: Protocol (ADR-035) - Unit Tests" -ForegroundColor Yellow
Write-Host "--------------------------------------------" -ForegroundColor Yellow

try {
    Push-Location "src/modules/fermentation"
    $output = & poetry run pytest tests/unit/test_protocol_enums.py tests/unit/test_protocol_repositories.py -q --tb=line 2>&1
    $exitCode = $LASTEXITCODE
    Pop-Location
} catch {
    Write-Host "[FAIL] Protocol Unit Tests: Exception occurred" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    $testResults.ProtocolUnit = @{ Success = $false; Passed = 0; Failed = 0; ExitCode = 1 }
    $allPassed = $false
}

if ($exitCode -eq 0) {
    $summaryLine = $output | Select-String -Pattern "(\d+)\s+passed" | Select-Object -Last 1
    if ($summaryLine) {
        $summaryText = $summaryLine.ToString()
        $passed = 0
        if ($summaryText -match '(\d+)\s+passed') {
            $passed = [int]($Matches[1])
        }
        Write-Host "[PASS] Protocol (ADR-035) - Unit Tests: $passed tests passed" -ForegroundColor Green
        $testResults.ProtocolUnit = @{ Success = $true; Passed = $passed; Failed = 0; ExitCode = 0 }
    } else {
        Write-Host "[WARN] Protocol Unit Tests: Could not parse test count" -ForegroundColor Yellow
        $testResults.ProtocolUnit = @{ Success = $false; Passed = 0; Failed = 0; ExitCode = 1 }
        $allPassed = $false
    }
} else {
    $summaryLine = $output | Select-String -Pattern "(\d+)\s+(passed|failed|error)" | Select-Object -Last 1
    if ($summaryLine) {
        $summaryText = $summaryLine.ToString()
        $passed = 0
        if ($summaryText -match '(\d+)\s+passed') { $passed = [int]($Matches[1]) }
        $failed = 0
        if ($summaryText -match '(\d+)\s+failed') { $failed = [int]($Matches[1]) }
        Write-Host "[FAIL] Protocol (ADR-035) - Unit Tests: $passed passed, $failed failed" -ForegroundColor Red
        $output | Select-Object -Last 10 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
        $testResults.ProtocolUnit = @{ Success = $false; Passed = $passed; Failed = $failed; ExitCode = 1 }
        $allPassed = $false
    }
}

# Run Fermentation Complete Test Suite (see FermentationComplete section below)

# Summary
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$totalPassed = 0
$totalFailed = 0

foreach ($key in $testResults.Keys) {
    $result = $testResults[$key]
    if ($result -ne $null) {
        if ($result.Skipped) {
            Write-Host "[SKIP] ${key}: skipped (environment not configured)" -ForegroundColor Yellow
        } else {
            $totalPassed += $result.Passed
            $totalFailed += $result.Failed
            
            $icon = if ($result.Success) { "[PASS]" } else { "[FAIL]" }
            $color = if ($result.Success) { "Green" } else { "Red" }
            Write-Host "$icon ${key}: $($result.Passed) passed, $($result.Failed) failed" -ForegroundColor $color
        }
    }
}

Write-Host "--------------------------------------------" -ForegroundColor Cyan
Write-Host "Total: $totalPassed passed, $totalFailed failed" -ForegroundColor $(if ($allPassed) { "Green" } else { "Red" })
Write-Host "Duration: $($duration.TotalSeconds.ToString('F2'))s" -ForegroundColor Gray
Write-Host "Completed: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan

if ($allPassed) {
    Write-Host "`n[SUCCESS] All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n[FAILED] Some tests failed. Please review the output above." -ForegroundColor Red
    exit 1
}
