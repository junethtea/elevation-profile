# Elevation Profile ⛰️📈 (Standard Version)

![QGIS Version](https://img.shields.io/badge/QGIS-3.16%20%7C%204.x-589632?logo=qgis)
![Version](https://img.shields.io/badge/version-1.9.3-blue)
![License](https://img.shields.io/badge/license-GPL--2.0--or--later-green)

*"Sebaik-baiknya Manusia adalah yang bermanfaat bagi sesama"*

## 📖 Overview
**Elevation Profile** is a high-precision 2D terrain profiling tool built for QGIS. Designed specifically to bridge the gap between Geographic Information Systems (GIS) and Telecommunication Network Planning & Optimization (NPO) workflows. 

This **Standard Version** allows engineers and GIS professionals to instantly visualize terrain cross-sections directly against actual local DEM raster data, without the need to load heavy RF planning software. Now fully refactored for maximum stability, featuring a pure single-row layout optimized for both **QGIS 3.x** and the upcoming **QGIS 4.x**.

## ✨ Standard Features
* **Offline DEM Support:** Seamlessly generate elevation profiles from local Raster files (e.g., DEMNAS, SRTM, AW3D30).
* **Interactive Line Drawing:** Draw a path on the map with **real-time live tooltips** displaying Azimuth and Distance. Instantly view the elevation cross-section.
* **Dynamic Terrain Smoothing (Sigma):** Adjust DEM smoothing on the fly to filter noise and spikes from raw terrain sources.
* **Interactive Tracking:** Hover over the generated profile chart to instantly see the exact distance and elevation mapped back to the map canvas via an interactive crosshair marker.
* **QGIS 4.x Ready:** Fully compatible with PyQt6 while seamlessly maintaining backward compatibility with older QGIS 3.x (PyQt5) versions.
* **High-Res Export:** Save your analysis as PNG images or scalable SVG vectors for sharp, professional technical reporting.

---

## 🔒 PRO Features (Upgrade Required)
Take your RF Site Audit and Network Planning to the next level! Upgrading to the **Pro Version** unlocks:
* **📡 Advanced LoS Viewer:** Perform Microwave and Radio Link planning with interactive Tx/Rx tower heights, Earth bulge calculations, dynamic K-Factor presets, and 60% Fresnel Zone clearance visualization complete with smart critical obstacle detection.
* **🌐 Online DEM APIs:** Access free global Online APIs (Open-Meteo 90m & OpenTopoData 30m SRTM) without needing to download local raster files.
* **👥 Population Metrics:** Load demographic raster data to overlay a 1D population density profile directly onto the elevation chart and automatically estimate the total population within a corridor.
* **🌗 Dual Theme UI:** Instantly toggle between Dark Mode and an elegant Ivory Light Mode.
* **🎁 SPECIAL BONUS:** Get the **Embed Legend Pro** plugin for FREE with your upgrade!

**Get the Pro Version here / Dapatkan Versi Pro disini:**
* 🌐 **Global:** [Download via Gumroad](https://jujunet.gumroad.com/l/dssdip)
* 🇮🇩 **Indonesia:** [Download via Lynk.id](https://lynk.id/kangjun/55xnn81vz9rg)

---

## 🚀 How to Use (Standard Version)
1. **Load Data:** Ensure your local DEM/Raster layer is loaded in QGIS and selected in the dropdown menu. (Click the **↻** button to refresh the list).
2. **Draw Line (📈):** Click the "📈 Line" button, then click on the map to trace your path (Left-click to add points). Watch the live tooltips for Distance and Azimuth. **Right-click** to finish and generate the profile.
3. **Adjust Smoothing:** Change the "Smooth" value to filter out terrain noise (0 = Raw, 3 = DEMNAS, 5 = AW3D30, 20 = Smooth/SRTM).
4. **Export:** Click the "💾 Export" button to save your profile as a PNG or SVG file.

## 📸 Screenshots

## 📥 Recommended Data Sources
* **Global Data:** [JAXA ALOS World 3D (30m)](https://earth.jaxa.jp/en/)
* **Indonesia Local Data:** [DEMNAS - Badan Informasi Geospasial (8m)](https://tanahair.indonesia.go.id/demnas/)

## ☕ Support & Donate
If this free standard tool saves you hours of work or helps your daily optimization tasks, consider supporting its continuous development!
* **Global:** [Buy me a coffee! ☕](https://buymeacoffee.com/juneth)
* **Indonesia:** [Donate via Saweria](https://saweria.co/juneth)
* **Via PayPal:** [paypal.me/junjunan81](https://paypal.me/junjunan81)

---
> *"Sebaik-baiknya Manusia adalah yang bermanfaat bagi sesama"*

---
<div align="center">
  <sub>by <b>Jujun Junaedi</b> | © 2024 - 2026</sub>
</div>