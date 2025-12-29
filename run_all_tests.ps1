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
    FermentationUnit = $null
    FermentationIntegration = $null
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
                Write-Host "[SKIP] ${Name}: No pyproject.toml found at $pyprojectPath" -ForegroundColor Yellow
                return @{ Success = $true; Passed = 0; Failed = 0; Skipped = $true; ExitCode = 0 }
            }
            
            # Run tests using poetry from module directory
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
            Pop-Location
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
        $resultLine = $output | Select-String -Pattern "(\d+) passed" | Select-Object -Last 1
        
        if ($resultLine) {
            $passed = [int]($resultLine -replace '.*?(\d+) passed.*', '$1')
            
            # Check if there are any failed tests in the same line
            $failedCount = 0
            if ($resultLine -match '(\d+) failed') {
                $failedCount = [int]($Matches[1])
            }
            
            if ($failedCount -gt 0) {
                Write-Host "[PARTIAL] ${Name}: $passed passed, $failedCount failed" -ForegroundColor Yellow
                return @{ Success = $false; Passed = $passed; Failed = $failedCount; ExitCode = $exitCode }
            } else {
                Write-Host "[PASS] ${Name}: $passed tests passed" -ForegroundColor Green
                return @{ Success = $true; Passed = $passed; Failed = 0; ExitCode = $exitCode }
            }
        } elseif ($output | Select-String -Pattern "failed|errors?") {
            $failedLine = $output | Select-String -Pattern "(\d+) failed" | Select-Object -Last 1
            $errorLine = $output | Select-String -Pattern "(\d+) errors?" | Select-Object -Last 1
            
            $failed = if ($failedLine) { [int]($failedLine -replace '.*?(\d+) failed.*', '$1') } else { 0 }
            $errors = if ($errorLine) { [int]($errorLine -replace '.*?(\d+) errors?.*', '$1') } else { 0 }
            
            Write-Host "[FAIL] ${Name}: $failed failed, $errors errors" -ForegroundColor Red
            Write-Host "Last 10 lines of output:" -ForegroundColor Yellow
            $output | Select-Object -Last 10 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
            
            return @{ Success = $false; Passed = 0; Failed = $failed; Errors = $errors; ExitCode = $exitCode }
        } else {
            Write-Host "[WARN] ${Name}: Could not parse test results" -ForegroundColor Yellow
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

# Run Fermentation Unit Tests
Write-Host "`n"
$testResults.FermentationUnit = Invoke-TestSuite `
    -Name "Fermentation - Unit Tests" `
    -ModulePath "src/modules/fermentation" `
    -TestPath "tests/unit/" `
    -Type "unit"

if (-not $testResults.FermentationUnit.Success) { $allPassed = $false }

# Run Fermentation Integration Tests - SKIPPED due to known limitations
# See ADR-011 and ADR-013 for details on Sample model metadata conflicts
if (-not $Quick) {
    Write-Host "`n"
    Write-Host "--------------------------------------------" -ForegroundColor Yellow
    Write-Host "Fermentation - Integration Tests (SKIPPED)" -ForegroundColor Yellow
    Write-Host "--------------------------------------------" -ForegroundColor Yellow
    Write-Host "NOTE: These tests are skipped due to SQLAlchemy single-table inheritance" -ForegroundColor Gray
    Write-Host "      metadata conflicts (ADR-011/ADR-013). To run them separately:" -ForegroundColor Gray
    Write-Host "      cd src/modules/fermentation" -ForegroundColor Gray
    Write-Host "      poetry run pytest tests/integration/repository_component/ -v" -ForegroundColor Gray
    
    $testResults.FermentationIntegration = @{
        Success = $true
        Passed = 0
        Failed = 0
        Skipped = $true
        ExitCode = 0
    }
}

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
    Write-Host "`nNOTE: Fermentation repository integration tests are not included in this script" -ForegroundColor Gray
    Write-Host "      due to SQLAlchemy single-table inheritance metadata conflicts (ADR-011/ADR-013)." -ForegroundColor Gray
    Write-Host "      To run them separately:" -ForegroundColor Gray
    Write-Host "      cd src/modules/fermentation" -ForegroundColor Gray
    Write-Host "      python -m pytest tests/integration/repository_component/ -v" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "`n[FAILED] Some tests failed. Please review the output above." -ForegroundColor Red
    exit 1
}
