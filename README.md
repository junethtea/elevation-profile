# Elevation Profile ⛰️📈

![QGIS Version](https://img.shields.io/badge/QGIS-3.16%20%7C%204.x-589632?logo=qgis)
![Version](https://img.shields.io/badge/version-1.9.1-blue)
![License](https://img.shields.io/badge/license-GPL--2.0--or--later-green)

*"Sebaik-baiknya Manusia adalah yang bermanfaat bagi sesama"*

## 📖 Overview
**Elevation Profile** is a high-precision 2D terrain profiling tool built for QGIS. Designed specifically to bridge the gap between Geographic Information Systems (GIS) and Telecommunication Network Planning & Optimization (NPO) workflows. 

It allows engineers and GIS professionals to instantly visualize Line of Sight (LoS) and terrain cross-sections directly against actual DEM data or Free Online APIs, without the need to load heavy RF planning software. Now fully refactored and optimized for both **QGIS 3.x** and the upcoming **QGIS 4.x**.

## ✨ Key Features
* **Offline & Online DEM Support:** Seamlessly switch between local offline Raster files or free global Online APIs (Open-Meteo 90m & OpenTopoData 30m SRTM) without requiring any API keys.
* **Dual Theme UI (☀️/🌙):** Instantly toggle between Dark Mode and an elegant Ivory Light Mode for optimal viewing during outdoor field work or late-night planning.
* **Interactive Line Drawing:** Draw a path on the map with **real-time live tooltips** displaying Azimuth and Distance. Instantly view the elevation cross-section to verify Line of Sight (LoS).
* **QGIS 4.x Ready:** Fully compatible with PyQt6 while seamlessly maintaining backward compatibility with older QGIS 3.x (PyQt5) versions.
* **Dynamic Terrain Smoothing (Sigma):** Adjust DEM smoothing on the fly to reduce noise and spikes from raw terrain sources (e.g., AW3D30, DEMNAS, SRTM).
* **Interactive Tracking:** Hover over the generated profile chart to instantly see the exact distance and elevation mapped back to the map canvas via an interactive crosshair marker.
* **High-Res Export:** Save your analysis as PNG images or scalable SVG vectors for sharp, professional technical reporting.

## 🚀 How to Use
1. **Select Source:** Choose your data source from the "Source" dropdown (Offline DEM, Open-Meteo, or OpenTopoData).
2. **Load Data (Offline Mode):** If using Offline DEM, ensure your Raster layer is loaded and selected in the secondary dropdown. (Click the **↻** button to refresh the list).
3. **Draw Line (📈):** Click the "📈 Line" button, then click on the map to trace your path (Left-click to add points). Watch the live tooltips for Distance and Azimuth. **Right-click** to finish and generate the profile.
4. **Adjust Smoothing:** Change the "Smooth" value to filter out terrain noise (0 = Raw, 3 = DEMNAS, 5 = AW3D30, 20 = Smooth/SRTM).
5. **Toggle Theme:** Click the ☀️/🌙 icon to switch between Light and Dark interface modes.
6. **Export:** Click the "💾 Export" button to save your profile as a PNG or SVG file.

## ⚠️ Important Disclaimer (Online DEM)
* **Server Stability & Limitations:** Both Open-Meteo and OpenTopoData are public APIs. They have rate limits and no guaranteed uptime. You may occasionally experience slow responses or timeouts depending on global server traffic.
* **Auto-Block / Rate Limiting:** If you draw consecutive long profile lines rapidly, your IP address might be temporarily blocked by the API server to prevent spam. If you encounter a connection error, please wait before trying again.
* **Professional Recommendation:** Online APIs perform interpolation which might not perfectly reflect raw terrain anomalies. For highly critical engineering tasks (e.g., Telecom RF Coverage, precise Line-of-Sight planning), it is strongly recommended to use the **Offline DEM (Raster)** mode with verified local datasets.

## 📸 Screenshots
<img width="646" height="468" alt="1" src="https://github.com/user-attachments/assets/e6d5cc09-4b93-4778-94f9-cb87cc57a9bd" />

<img width="448" height="356" alt="Help-Guide" src="https://github.com/user-attachments/assets/658b9812-8fe6-4489-be57-e176923e4344" />

## 📥 Recommended Data Sources
* **Global Data:** [JAXA ALOS World 3D (30m)](https://earth.jaxa.jp/en/)
* **Indonesia Local Data:** [DEMNAS - Badan Informasi Geospasial (8m)](https://tanahair.indonesia.go.id/demnas/)

## ☕ Support & Donate
If this tool saves you hours of work or helps your daily optimization tasks, consider supporting the development!
* **Global:** [Buy me a coffee! ☕](https://buymeacoffee.com/juneth)
* **Indonesia:** [Donate via Saweria](https://saweria.co/juneth)

---
*May this tool be a continuous charity (amal jariah), especially for my beloved late parents. 🤲*
