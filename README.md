# 🚗 DriveSummary

**Automated Commute & Weather Briefing**

A lightweight, "forever free" Python tool that sends a daily commute summary to your phone via [ntfy.sh](https://ntfy.sh). It runs automatically on GitHub Actions, so you don't need a server.

## ✨ Features (Jarvis Edition)
*   **🧠 Smart Traffic**: Compares current vs. historic traffic. If delay > 15 mins, sends a **High Priority** alert.
*   **📊 Market Data**: Live daily % change for **S&P 500** and **Bitcoin**.
*   **📰 Morning Brief**: Top 3 headlines from **NPR News**.
*   **📱 Rich Notifications**:
    *   **Action Buttons**: One-tap "Start Navigation" opens Google Maps.
    *   **Visuals**: Green/Yellow/Red status based on traffic.
    *   **Clickable Events**: Direct links to Ticketmaster events.
*   **Forever Free**: Still uses only free API tiers.

## 🚀 Setup Guide

### 1. Fork or Clone this Repo
```bash
git clone https://github.com/dylanpap95-dotcom/DriveSummary.git
cd DriveSummary
```

### 2. Get API Keys
You need two free API keys:
1.  **TomTom Maps API**: [Sign up here](https://developer.tomtom.com/) -> Get your Key.
2.  **Ticketmaster API**: [Sign up here](https://developer.ticketmaster.com/) -> Get your Key.

### 3. Configure GitHub Secrets
Go to your GitHub Repo -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

Add the following secrets:
*   `TOMTOM_API_KEY`: (Your TomTom Key)
*   `TICKETMASTER_API_KEY`: (Your Ticketmaster Key)

### 4. Custom Coordinates (Optional)
By default, the script uses coordinates for Philadelphia. To change them, add these Secrets (or Environment Variables):
*   `HOME_LAT`, `HOME_LON`
*   `WORK_LAT`, `WORK_LON`

### 5. Install ntfy App
Download the **ntfy** app on iOS or Android and subscribe to the topic `DriveSummary` (or change the topic in the code/env vars).

## 📅 Schedule
The script runs automatically on **Mon-Fri**:
*   **7:45 AM ET** (Morning Brief)
*   **5:00 PM ET** (Evening Commute)

## 🛠️ Local Usage
To run it on your own computer:
```bash
pip install -r requirements.txt
# Set your keys
$env:TOMTOM_API_KEY="your-key"
$env:TICKETMASTER_API_KEY="your-key"
python main.py
```
