# ==========================================
# DriveSummary GitHub Setup Script (Fixed)
# ==========================================

$repoPath = "C:\Users\Dylan\Desktop\Reminders\DriveSummary"
$workflowDir = "$repoPath\.github\workflows"
$workflowFile = "$workflowDir\drive_summary.yml"

Write-Host "➡ Cleaning up old GitHub workflow files..." -ForegroundColor Yellow
if (Test-Path $workflowDir) {
    Remove-Item -Recurse -Force $workflowDir
}
New-Item -ItemType Directory -Force -Path $workflowDir | Out-Null

# ==========================================
# Create new workflow YAML
# ==========================================
$workflowYML = @"
name: DriveSummary

on:
  schedule:
    - cron: '0 13 * * 1,2'   # 9 AM ET
    - cron: '0 21 * * 1,2'   # 5 PM ET
  workflow_dispatch:

jobs:
  drive_summary:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests

      - name: Run DriveSummary
        env:
          TOMTOM_API_KEY: `$\{{ secrets.TOMTOM_API_KEY \}\}
          TICKETMASTER_API_KEY: `$\{{ secrets.TICKETMASTER_API_KEY \}\}
          NTFY_TOPIC: "DriveSummary"
          SEND_NOTIFICATIONS: "1"
        run: python drive_summary_final.py
"@

$workflowYML | Set-Content -Path $workflowFile -Encoding UTF8
Write-Host "✅ Created new workflow file: $workflowFile" -ForegroundColor Green

# ==========================================
# Initialize Git (if needed)
# ==========================================
cd $repoPath
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
git commit -m "Clean setup: new DriveSummary workflow"
git push -u origin main --force
Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green

Write-Host "`nYou can now open your repo and check under Actions → DriveSummary to manually run the workflow or wait for the next schedule." -ForegroundColor Cyan