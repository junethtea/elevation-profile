# Elevation Profile ⛰️📈

![QGIS Version](https://img.shields.io/badge/QGIS-3.16%20%7C%204.x-589632?logo=qgis)
![Version](https://img.shields.io/badge/version-1.9.0-blue)
![License](https://img.shields.io/badge/license-GPL--2.0--or--later-green)

*"Sebaik-baiknya Manusia adalah yang bermanfaat bagi sesama"*

## 📖 Overview
**Elevation Profile** is a high-precision 2D terrain profiling tool built for QGIS. Designed specifically to bridge the gap between Geographic Information Systems (GIS) and Telecommunication Network Planning & Optimization (NPO) workflows. 

It allows engineers and GIS professionals to instantly visualize Line of Sight (LoS) and terrain cross-sections directly against actual DEM data, without the need to load heavy RF planning software. Now fully refactored and optimized for both **QGIS 3.x** and the upcoming **QGIS 4.x**.

## ✨ Key Features
* **High-Precision 2D Profiling:** Generate highly accurate 2D terrain profiles along a user-drawn path using QGIS native ellipsoid distance calculations.
* **QGIS 4.x Ready:** Fully compatible with PyQt6 while seamlessly maintaining backward compatibility with older QGIS 3.x (PyQt5) versions.
* **Dynamic Terrain Smoothing (Sigma):** Adjust DEM smoothing on the fly to reduce noise and spikes from raw terrain sources (e.g., AW3D30, DEMNAS, SRTM).
* **Interactive Tracking:** Hover over the generated profile chart to instantly see the exact distance and elevation mapped back to the map canvas via an interactive crosshair marker.
* **High-Res Export:** Save your analysis as PNG images or scalable SVG vectors for sharp, professional technical reporting.

## 🚀 How to Use
1. **Load Data:** Ensure you have a Raster/DEM layer loaded in your QGIS project.
2. **Select DEM:** Choose your Raster layer from the plugin's "DEM" dropdown menu. (Click the **↻** button to refresh the list if you just added a new layer).
3. **Draw Line (📈):** Click the "📈 Line" button, then click on the map to trace your path (Left-click to add points). **Right-click** to finish and generate the profile.
4. **Adjust Smoothing:** Change the "Smooth" value to filter out terrain noise (0 = Raw, 3 = DEMNAS, 5 = AW3D30, 20 = Smooth/SRTM).
5. **Export:** Click the "💾 Export" button to save your profile as a PNG or SVG file.

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
