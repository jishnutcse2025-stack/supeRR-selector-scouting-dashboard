# 🏰 SupeRR Selector Season 2 — Interactive Cricket Scouting Dashboard

Official interactive scouting portal for **SupeRR Selector Season 2 — Round 1 Challenge: "Identify the Most Reliable Players Under Pressure"**.

Built for the **Rajasthan Royals Scouting & Analytics Division** using **Streamlit** and **Plotly**.

---

## 📖 Overview

This dashboard translates over **185,000 legal deliveries** and **853 IPL & T20I matches (2022–2026)** into an interactive, real-time scouting portal. Rather than relying on static reports or generic tournament averages, the portal evaluates player reliability under pre-delivery situational pressure (Score $\ge$ 65.0), incorporating:
- **Innings 2 Chase Pressure:** Required run rate escalation, wickets lost, balls remaining, and dead-rubber tapering.
- **Innings 1 Setting Pressure:** Early collapse shocks ($\ge 2$ wickets in Powerplay, $\ge 3$ wickets before over 10) and death-overs acceleration.
- **Empirical Bayes Shrinkage ($k=100$):** Stabilizes small-sample outliers.
- **Context-Adjusted Expected Par:** Isolates Run Value Above Expected (RVAE) and Run Saved Above Expected (RSAE).

---

## 🚀 Quickstart: Running Locally

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Activate the Virtual Environment
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows Command Prompt
.\.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Requirements
```bash
pip install -r requirements-dashboard.txt
```

### 4. Launch the Dashboard
```bash
streamlit run dashboard.py
```
The dashboard will open automatically in your browser at `http://localhost:8501`.

---

## 🌐 Deploying to Streamlit Community Cloud

Deploying this scouting portal to **Streamlit Community Cloud** takes under 2 minutes:

1. **Push to GitHub:**
   Ensure your repository includes:
   - `dashboard.py` (Main entrypoint)
   - `dashboard_utils.py` (Caching & visual helpers)
   - `requirements-dashboard.txt` (or rename to `requirements.txt`)
   - `outputs/` folder containing all precalculated CSVs, publication charts, and PDF report.

2. **Connect Streamlit Cloud:**
   - Log into [share.streamlit.io](https://share.streamlit.io).
   - Click **"New App"** and link your GitHub repository.
   - Set **Main file path** to `dashboard.py`.
   - In Advanced Settings, ensure Python 3.10+ is selected.

3. **Deploy:**
   Click **"Deploy!"** — Streamlit Cloud will install dependencies and serve the portal at your public URL.

---

## 🧭 Dashboard Architecture & The 9 Pages

| Page | Key Features & Analytical Capabilities |
| :--- | :--- |
| **1. 📊 Executive Overview** | High-level KPIs (853 matches, 185k legal balls, 51.8k HP balls), Top 5 Batters & Bowlers quick podium, pressure distribution curve, key scouting intelligence. |
| **2. 🏏 Top 10 Batters** | Interactive PPI leaderboard (#1 Naman Dhir to #10 Dhruv Jurel), horizontal Plotly rankings bar chart, Δ SR vs sample size bubble chart, tactical player profiles. |
| **3. 🎯 Top 10 Bowlers** | Interactive PPI leaderboard (#1 Abrar Ahmed to #10 Mitchell Santner), horizontal Plotly rankings bar chart, Δ Econ vs RSAE containment scatter plot, tactical bowler profiles. |
| **4. 🔍 Complete Player Database** | Search, filter, and inspect all 232 qualified players (96 batters, 136 bowlers) with dynamic sliders for HP balls and PPI score, plus instant CSV export. |
| **5. 👤 Individual Player Profiles** | Deep-dive diagnostic for every qualified player with an interactive **5-Axis Radar Chart** against tournament medians, baseline vs pressure comparison table, and featured signature match callout. |
| **6. ⚡ Pressure Analysis** | The physics of leverage: Powerplay, Middle, and Death par comparison, publication-grade baseline vs pressure scatter plots, and PPI component contribution weights. |
| **7. 🏆 Match Case Studies** | 20 signature match situations extracted from actual deliveries (Jos Buttler 74 off 34 vs KKR, Jasprit Bumrah 3/1 in 2 overs vs KKR, Naman Dhir 62 off 28 vs LSG). |
| **8. 📐 Methodology & Validation** | Complete mathematical architecture (Innings 1 & 2 formulas, dead-rubber taper, Bayes shrinkage), sensitivity analysis (thresholds 60/65/70), and **10/10 automated validation suite audit**. |
| **9. 📥 Reports & Downloads** | Direct one-click download buttons for the 11-page publication-grade PDF report, Markdown document, and all certified analytics CSV outputs. |

---

## 🎨 Design System

The portal adheres to the official **Rajasthan Royals** brand palette:
- **Background:** Deep Navy & Midnight Charcoal (`#0A0F1D`, `#151E33`)
- **Primary Accent:** Royals Pink (`#D91E5B`, `#FF2E93`)
- **Secondary Accent:** Royal Blue (`#1E88E5`, `#60A5FA`)
- **Trophy & Honors Accent:** Gold (`#F59E0B`)
- **Typography:** Crisp, modern typography with responsive card containers and custom CSS badges.

---

## 🛡️ Data Quality & Audit Integrity

- **10/10 Validation Checks Passed:** Sum of batter runs (261,119) and bowling runs (270,826) reconciles to 0.0 error.
- **Strict Bowling Attribution:** 9,905 bowler wickets strictly exclude run-outs and retired outs.
- **Zero Mock / Placeholder Data:** 100% of data points originate from the official competition dataset.
