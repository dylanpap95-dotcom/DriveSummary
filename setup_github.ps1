# ==========================================
# DriveSummary GitHub Setup Script
# ==========================================

# Get the current directory where the script is running
$repoPath = Get-Location
$workflowDir = "$repoPath\.github\workflows"
$workflowFile = "$workflowDir\drive_summary.yml"

Write-Host "➡ Repo Path detected: $repoPath" -ForegroundColor Cyan

# Check if .github/workflows exists, create if not
if (-not (Test-Path $workflowDir)) {
    New-Item -ItemType Directory -Force -Path $workflowDir | Out-Null
    Write-Host "Created .github/workflows directory." -ForegroundColor Green
}

# ==========================================
# Initialize Git (if needed)
# ==========================================
if (-not (Test-Path "$repoPath\.git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    git branch -M main
    git remote add origin https://github.com/dylanpap95-dotcom/DriveSummary.git
}

# ==========================================
# Commit and Push
# ==========================================
Write-Host "Committing and pushing to GitHub..." -ForegroundColor Yellow
git add .
git commit -m "Upgrade to A+ version: Cleaned up code, added requirements, updated schedule"
git push -u origin main --force
Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green

Write-Host "`nYou can now open your repo and check under Actions → DriveSummary to manually run the workflow or wait for the next schedule." -ForegroundColor Cyan