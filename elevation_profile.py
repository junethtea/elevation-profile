#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------
#  ELEVATION PROFILE TOOLS
# --------------------------------------------------------------------------
#  PLUGIN NAME : Elevation Profile
#  DESCRIPTION : High-Precision Terrain Profiling Tool for QGIS
#  AUTHOR      : Jujun Junaedi
#  EMAIL       : jujun.junaedi@outlook.com
#  VERSION     : 1.9.0
#  COPYRIGHT   : (c) 2023 by Jujun Junaedi
#  LICENSE     : GPL-2.0-or-later
#  MOTTO       : "Sebaik-baiknya Manusia adalah yang bermanfaat bagi sesama"
# --------------------------------------------------------------------------

"""
LICENSE AGREEMENT:
This program is free software; you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free Software Foundation.
To support the developer and ensure you have the latest stable version, 
please download directly from the Official QGIS Repository.
"""

import os
import numpy as np
import traceback

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
from matplotlib import cm 

# Matplotlib backend resolution
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from qgis.core import (
    QgsProject, QgsMapLayerType, QgsDistanceArea, 
    QgsPointXY, QgsGeometry, QgsCoordinateTransform, 
    QgsWkbTypes
)
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.utils import iface

from qgis.PyQt.QtGui import QIcon, QColor, QFont
from qgis.PyQt.QtWidgets import (
    QAction, QDockWidget, QVBoxLayout, 
    QWidget, QComboBox, QLabel, QHBoxLayout, 
    QSizePolicy, QToolButton, QDialog, 
    QSpinBox, QMessageBox, QTextBrowser,
    QMenu, QFileDialog, QApplication
)
from qgis.PyQt.QtCore import Qt, pyqtSignal

# PyQt enum compatibility mapping (PyQt6 -> PyQt5 fallback)
try:
    QT_LEFT_BUTTON = Qt.MouseButton.LeftButton
    QT_RIGHT_BUTTON = Qt.MouseButton.RightButton
    QT_BOTTOM_DOCK = Qt.DockWidgetArea.BottomDockWidgetArea
    QT_TOP_DOCK = Qt.DockWidgetArea.TopDockWidgetArea
    QT_RICH_TEXT = Qt.TextFormat.RichText
    POLICY_EXPANDING = QSizePolicy.Policy.Expanding
    POLICY_FIXED = QSizePolicy.Policy.Fixed
    MSG_INFO = QMessageBox.Icon.Information
    MSG_OK = QMessageBox.StandardButton.Ok
    TOOLBUTTON_INSTANT_POPUP = QToolButton.ToolButtonPopupMode.InstantPopup
except AttributeError:
    QT_LEFT_BUTTON = Qt.LeftButton
    QT_RIGHT_BUTTON = Qt.RightButton
    QT_BOTTOM_DOCK = Qt.BottomDockWidgetArea
    QT_TOP_DOCK = Qt.TopDockWidgetArea
    QT_RICH_TEXT = Qt.RichText
    POLICY_EXPANDING = QSizePolicy.Expanding
    POLICY_FIXED = QSizePolicy.Fixed
    MSG_INFO = QMessageBox.Information
    MSG_OK = QMessageBox.Ok
    TOOLBUTTON_INSTANT_POPUP = QToolButton.InstantPopup


class ProfileMapTool(QgsMapTool):
    line_finished = pyqtSignal(object) 
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.points = []
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubber_band.setColor(QColor(231, 76, 60, 150))
        self.rubber_band.setWidth(2)

    def canvasPressEvent(self, event):
        try:
            if event.button() == QT_LEFT_BUTTON:
                pt = self.toMapCoordinates(event.pos())
                self.points.append(pt)
                self.rubber_band.addPoint(pt)
            elif event.button() == QT_RIGHT_BUTTON:
                if len(self.points) >= 2:
                    geom = QgsGeometry.fromPolylineXY(self.points)
                    self.line_finished.emit(geom)
                    self.points = []
                    self.rubber_band.reset(QgsWkbTypes.LineGeometry)
        except Exception:
            pass

    def canvasMoveEvent(self, event):
        if len(self.points) > 0:
            pt = self.toMapCoordinates(event.pos())
            self.rubber_band.reset(QgsWkbTypes.LineGeometry)
            for p in self.points:
                self.rubber_band.addPoint(p)
            self.rubber_band.addPoint(pt)


class ElevationDockWidget(QDockWidget):
    draw_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    closing = pyqtSignal() 
    
    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)

    def __init__(self, parent=None):
        super().__init__("Elevation Profile v1.9.0 | ©Jujun.J", parent)    
        self.setAllowedAreas(QT_BOTTOM_DOCK | QT_TOP_DOCK)
        
        self.main_widget = QWidget()
        self.main_widget.setStyleSheet("background-color: #2b2b2b; color: #dfe6e9;")
        
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.create_toolbar()
        self.create_chart()
        self.setWidget(self.main_widget)
        
        self.x_data_km = None
        self.y_data = None
        self.geom = None
        self.xf = None
        self.marker_arrow = None
        self.cursor_line = None
        self.cursor_text = None
        self.max_dist_km = 0
        
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def create_toolbar(self):
        v_lay = QVBoxLayout()
        v_lay.setContentsMargins(5, 5, 5, 2)
        v_lay.setSpacing(3)
        
        h_lay1 = QHBoxLayout()
        h_lay2 = QHBoxLayout()
        h_lay1.setSpacing(5)
        h_lay2.setSpacing(5)
        
        combo_style = "QComboBox { background: #3b3b3b; color: #dfe6e9; border: 1px solid #555; border-radius: 2px; padding: 2px; font-size: 7.5pt; }"
        spin_style = "QSpinBox { background: #3b3b3b; color: #dfe6e9; border: 1px solid #555; border-radius: 2px; padding: 2px; font-size: 7.5pt; }"
        flat_btn_style = """
            QToolButton { background: #333; color: #dfe6e9; border: 1px solid #555; border-radius: 2px; padding: 3px 8px; font-size: 7.5pt; font-weight: bold; }
            QToolButton:hover { background: #555; color: white; border: 1px solid #00cec9; }
        """
        lbl_style = "color: #b2bec3; font-size: 7.5pt; font-weight: bold;"

        lbl_dem = QLabel("DEM:")
        lbl_dem.setStyleSheet(lbl_style)
        
        self.combo = QComboBox()
        self.combo.setStyleSheet(combo_style)
        self.combo.setMinimumWidth(160)
        self.combo.setSizePolicy(POLICY_EXPANDING, POLICY_FIXED)

        self.btn_refresh = QToolButton()
        self.btn_refresh.setText("↻")
        self.btn_refresh.setStyleSheet(flat_btn_style)
        self.btn_refresh.clicked.connect(lambda: self.refresh_clicked.emit())

        self.btn_help = QToolButton()
        self.btn_help.setText("?")
        self.btn_help.setStyleSheet(flat_btn_style)
        self.btn_help.clicked.connect(self.show_help)

        self.btn_about = QToolButton()
        self.btn_about.setText("i")
        self.btn_about.setStyleSheet(flat_btn_style)
        self.btn_about.clicked.connect(self.show_about_dialog)

        widgets_row1 = [lbl_dem, self.combo, self.btn_refresh, self.btn_help, self.btn_about]
        
        for w in widgets_row1:
            h_lay1.addWidget(w)
            
        h_lay1.addStretch() 

        self.btn_draw = QToolButton()
        self.btn_draw.setText("📈 Line")
        self.btn_draw.setStyleSheet(flat_btn_style)
        self.btn_draw.clicked.connect(lambda: self.draw_clicked.emit())

        lbl_sigma = QLabel("Smooth:")
        lbl_sigma.setStyleSheet(lbl_style)
        
        self.spin_sigma = QSpinBox()
        self.spin_sigma.setRange(0, 50)
        self.spin_sigma.setValue(5)
        self.spin_sigma.setStyleSheet(spin_style)
        self.spin_sigma.setFixedWidth(40)

        self.btn_export = QToolButton()
        self.btn_export.setText("💾 Export")
        self.btn_export.setPopupMode(TOOLBUTTON_INSTANT_POPUP)
        self.btn_export.setStyleSheet(flat_btn_style)
        
        export_menu = QMenu(self.btn_export)
        export_menu.addAction("Save as PNG Image (.png)", lambda: self.handle_export("png"))
        export_menu.addAction("Save as SVG Vector (.svg)", lambda: self.handle_export("svg"))
        self.btn_export.setMenu(export_menu)

        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("color: #00cec9; font-size: 7.5pt; margin-left: 15px;")
        
        widgets_row2 = [self.btn_draw, lbl_sigma, self.spin_sigma, self.btn_export]
        
        for w in widgets_row2:
            h_lay2.addWidget(w)
            
        h_lay2.addWidget(self.lbl_info) 
        h_lay2.addStretch()

        v_lay.addLayout(h_lay1)
        v_lay.addLayout(h_lay2)
        self.layout.addLayout(v_lay)

    def show_about_dialog(self):
        msg = QMessageBox(self.iface.mainWindow() if hasattr(self, 'iface') else None)
        msg.setWindowTitle("About")
        msg.setIcon(MSG_INFO)
        msg.setTextFormat(QT_RICH_TEXT)
        
        text = (
            "<h3>Elevation Profile</h3>"
            "<b>Version:</b> 1.9.0<br>"
            "<b>Author:</b> Jujun Junaedi<br><br>"
            "<b>☕ Support & Donate:</b><br>"
            "If this tool saves you hours of work, consider buying me a coffee!<br><br>"
            "<table width='100%'><tr><td align='center'>"
            "<a href='https://saweria.co/juneth' style='text-decoration: none;'>"
            "<table bgcolor='#FFDD00' cellpadding='10' cellspacing='0' border='0' style='border-radius: 5px; border: 1px solid #000000; margin-bottom: 5px; width: 220px;'>"
            "<tr><td align='center' style='color: black; font-weight: bold; font-family: sans-serif; font-size: 14px;'>"
            "&nbsp;☕ Donate via Saweria&nbsp;"
            "</td></tr></table></a>"
            "<br>"
            "<a href='https://buymeacoffee.com/juneth' style='text-decoration: none;'>"
            "<table bgcolor='#FFDD00' cellpadding='10' cellspacing='0' border='0' style='border-radius: 5px; border: 1px solid #000000; width: 220px;'>"
            "<tr><td align='center' style='color: black; font-weight: bold; font-family: sans-serif; font-size: 14px;'>"
            "&nbsp;☕ Buy me a coffee!&nbsp;"
            "</td></tr></table></a>"
            "</td></tr></table><br>"
            "<div style='background-color: #e8f4f8; padding: 10px; border-radius: 5px; text-align: center; color: #2d98da; border: 1px solid #bdc3c7;'>"
            "<b>💡 PRO TIP FOR SHARING 💡</b><br>"
            "<span style='font-size: 11px;'>"
            "To ensure your colleagues get the latest version without bugs, please share the <b>Official QGIS Plugin Link</b> or <b>GitHub Link</b> instead of raw ZIP files.<br><br>"
            "<i>Biar rekan kerjamu selalu dapat versi terbaru yang bebas error, yuk biasakan share link resmi QGIS/GitHub, bukan bagi-bagi file ZIP mentahan 😉</i>"
            "</span>"
            "</div><br>"
            "<hr>"
            "<p align='center' style='color: #636e72; font-size: 11px;'>"
            "<i>\"May this tool be a continuous charity (amal jariah),<br>especially for my beloved late parents. 🤲\"</i>"
            "</p>"
        )
        msg.setText(text)
        msg.setStandardButtons(MSG_OK)
        
        if hasattr(msg, 'exec'):
            msg.exec()
        else:
            msg.exec_()

    def show_help(self):
        dialog = QDialog(iface.mainWindow())
        dialog.setWindowTitle("Elevation Profile - Help & Guide")
        dialog.resize(600, 450)
        
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        
        html_content = """
        <style>
            h3 { color: #2980b9; margin-bottom: 5px; border-bottom: 1px solid #ddd; }
            h4 { color: #e67e22; margin-top: 15px; margin-bottom: 5px; }
            li { margin-bottom: 5px; }
            a { color: #2980b9; text-decoration: none; font-weight: bold; }
        </style>
        
        <h3>📖 User Guide (English)</h3>
        <ul>
            <li><b>Select DEM:</b> Choose your Raster/DEM layer.</li>
            <li><b>Refresh (↻):</b> Updates layer list if you added new data.</li>
            <li><b>Draw Line (📈):</b> Click on map to trace path. <b>Right-click</b> to finish.</li>
            <li><b>Smooth:</b> Adjust Sigma to reduce noise. <br><i>(0=Raw, 3=DEMNAS, 5=AW3D30, 20=Smooth/SRTM)</i>.</li>
        </ul>

        <h3>📖 Panduan Pengguna (Indonesia)</h3>
        <ul>
            <li><b>Pilih DEM:</b> Pilih layer elevasi dari daftar.</li>
            <li><b>Refresh (↻):</b> Update daftar jika layer baru belum muncul.</li>
            <li><b>Gambar Garis (📈):</b> Klik di peta buat jalur. <b>Klik kanan</b> selesai.</li>
            <li><b>Smooth:</b> Atur kehalusan grafik. <br><i>(0=Asli, 3=DEMNAS, 5=AW3D30, 20=Halus/SRTM)</i>.</li>
        </ul>

        <hr>
        <h3>🌍 Data Sources (Download Links)</h3>
        <h4>1. Global Data (Worldwide)</h4>
        <p><b>JAXA ALOS World 3D (30m):</b> <a href="https://www.eorc.jaxa.jp/ALOS/en/aw3d30/registration.htm">🌐 https://earth.jaxa.jp/en/</a></p>

        <h4>2. Indonesia Local Data (High Res)</h4>
        <p><b>DEMNAS - BIG (8m):</b> <a href="https://tanahair.indonesia.go.id/portal-web/unduh">🇮🇩 https://tanahair.indonesia.go.id/demnas/</a></p>
        """
        browser.setHtml(html_content)
        layout.addWidget(browser)
        
        if hasattr(dialog, 'exec'):
            dialog.exec()
        else:
            dialog.exec_()

    def create_chart(self):
        self.figure = Figure(figsize=(10, 3), dpi=100)
        self.figure.patch.set_facecolor('#2b2b2b')
        
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors="#dfe6e9", labelsize=7)
        
        for spine in ['top', 'right']:
            self.ax.spines[spine].set_visible(False)
            
        for spine in ['bottom', 'left']:
            self.ax.spines[spine].set_color("#636e72")
            
        self.figure.subplots_adjust(left=0.06, right=0.96, top=0.92, bottom=0.28)

    def init_marker(self):
        if self.marker_arrow:
            self.marker_arrow.reset(QgsWkbTypes.PolygonGeometry)
            
        self.marker_arrow = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.marker_arrow.setColor(QColor(255, 0, 0, 230))
        self.marker_arrow.setStrokeColor(QColor(255, 255, 255, 255))
        self.marker_arrow.setWidth(1)
        self.marker_arrow.hide()

    def update_raster(self):
        self.combo.clear()
        r_layers = [l.name() for l in QgsProject.instance().mapLayers().values() if l.type() == QgsMapLayerType.RasterLayer]
        self.combo.addItems(r_layers)
        
        if not r_layers:
            self.combo.addItem("No Raster")

    def handle_export(self, ext):
        if self.x_data_km is None:
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, "Export", f"Profile.{ext}", f"Files (*.{ext})")
        if filename: 
            self.figure.savefig(filename, facecolor=self.figure.get_facecolor(), dpi=300, format=ext)

    def update_summary(self, y_smooth, dist_km):
        if len(y_smooth) == 0:
            self.lbl_info.setText("")
            return
            
        mn = np.min(y_smooth)
        mx = np.max(y_smooth)
        av = np.mean(y_smooth)
        
        self.lbl_info.setText(f"Dist: {dist_km:.2f} km   |   Elev: Min {mn:.0f} m / Avg {av:.0f} m / Max {mx:.0f} m")

    def plot_data(self, x_meters, y, dist_meters, geom, xf):
        self.x_data_km = x_meters / 1000.0
        self.y_data = y
        self.max_dist_km = dist_meters / 1000.0
        self.geom = geom
        self.xf = xf
        
        self.ax.clear()
        self.cursor_line = None
        self.cursor_text = None
        self.update_summary(y, self.max_dist_km)
        
        self.ax.fill_between(self.x_data_km, y, color="#e67e22", alpha=0.3)
        self.ax.plot(self.x_data_km, y, color="#ff9f43", linewidth=1.2)
        
        self.ax.set_facecolor("#2b2b2b")
        self.ax.set_xlabel("Distance (Km)", fontsize=7, color="#dfe6e9")
        self.ax.set_ylabel("Elevation (m)", fontsize=7, color="#dfe6e9")
        self.ax.grid(True, linestyle=':', linewidth=0.5, alpha=0.15, color="white")
        self.ax.tick_params(colors="#dfe6e9", labelsize=7)
        
        for spine in ['top', 'right']:
            self.ax.spines[spine].set_visible(False)
            
        for spine in ['bottom', 'left']:
            self.ax.spines[spine].set_color("#636e72")
        
        if self.max_dist_km <= 0:
            self.max_dist_km = 0.001
            
        self.ax.set_xlim(0, self.max_dist_km)
        
        if len(y) > 0:
            mn = np.min(y)
            mx = np.max(y)
            pad = (mx - mn) * 0.1 if (mx - mn) > 1 else 1
            self.ax.set_ylim(mn - pad, mx + pad)
            
        self.canvas.draw()

    def on_mouse_move(self, event):
        if event.inaxes != self.ax or self.x_data_km is None:
            if self.cursor_line:
                self.cursor_line.set_visible(False)
            if self.cursor_text:
                self.cursor_text.set_visible(False)
            if self.marker_arrow:
                self.marker_arrow.hide()
            self.canvas.draw_idle()
            return
            
        idx = (np.abs(self.x_data_km - event.xdata)).argmin()
        x_snap = self.x_data_km[idx]
        y_snap = self.y_data[idx]
        ylim_min = self.ax.get_ylim()[0]
        
        if self.cursor_line is None or self.cursor_line not in self.ax.lines:
            self.cursor_line, = self.ax.plot([x_snap, x_snap], [ylim_min, y_snap], color='#00cec9', linestyle='--', linewidth=1, zorder=100)
        else:
            self.cursor_line.set_data([x_snap, x_snap], [ylim_min, y_snap])
            self.cursor_line.set_visible(True)
            
        txt = f"Dist : {x_snap:.2f} Km\nHeight : {y_snap:.0f} m"
        
        if self.cursor_text is None or self.cursor_text not in self.ax.texts:
            bbox_props = dict(boxstyle='round,pad=0.3', facecolor='#2d3436', alpha=0.9, edgecolor='#00cec9')
            self.cursor_text = self.ax.text(x_snap, y_snap, txt, fontsize=7, color='#00cec9', bbox=bbox_props, ha='center', va='bottom', zorder=100)
        else:
            self.cursor_text.set_text(txt)
            self.cursor_text.set_position((x_snap, y_snap))
            self.cursor_text.set_visible(True)
            
        if self.geom:
            ratio = x_snap / self.max_dist_km if self.max_dist_km > 0 else 0
            pt_can = self.xf.transform(self.geom.interpolate(ratio * self.geom.length()).asPoint())
            
            if not self.marker_arrow:
                self.init_marker()
                
            S = 15 * iface.mapCanvas().mapUnitsPerPixel()
            poly = [[
                QgsPointXY(pt_can.x(), pt_can.y()), 
                QgsPointXY(pt_can.x() - (S * 0.6), pt_can.y() + (S * 1.5)), 
                QgsPointXY(pt_can.x(), pt_can.y() + (S * 1.0)), 
                QgsPointXY(pt_can.x() + (S * 0.6), pt_can.y() + (S * 1.5))
            ]]
            
            self.marker_arrow.setToGeometry(QgsGeometry.fromPolygonXY(poly), None)
            self.marker_arrow.show()
            
        self.canvas.draw_idle()


class ElevationProfile:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.dock = None
        self.line = QgsRubberBand(iface.mapCanvas(), QgsWkbTypes.LineGeometry)
        self.line.setColor(QColor(255, 255, 0, 180))
        self.line.setWidth(3)

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.act = QAction(QIcon(icon_path), "Elevation Profile", self.iface.mainWindow())
        self.act.triggered.connect(self.run)
        
        self.iface.addRasterToolBarIcon(self.act)
        self.iface.addPluginToMenu("&Elevation Profile", self.act)

    def unload(self):
        self.clean_up_canvas()
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            
        self.iface.removeRasterToolBarIcon(self.act)
        self.iface.removePluginMenu("&Elevation Profile", self.act)

    def clean_up_canvas(self):
        try:
            self.line.hide()
        except Exception:
            pass
            
        if self.dock and self.dock.marker_arrow:
            try:
                self.dock.marker_arrow.hide()
            except Exception:
                pass
                
        try:
            self.iface.mapCanvas().unsetMapTool(self.tool)
        except Exception:
            pass

    def run(self):
        if not self.dock:
            self.dock = ElevationDockWidget(self.iface.mainWindow())
            self.dock.init_marker()
            self.dock.iface = self.iface
            self.iface.addDockWidget(QT_BOTTOM_DOCK, self.dock)
            
            self.dock.draw_clicked.connect(self.start_draw)
            self.dock.refresh_clicked.connect(self.dock.update_raster)
            self.dock.closing.connect(self.clean_up_canvas)
            
        self.dock.show()
        self.dock.update_raster()
        self.update_calc()

    def start_draw(self):
        self.line.hide()
        self.tool = ProfileMapTool(self.iface.mapCanvas())
        self.tool.line_finished.connect(self.finish_draw)
        self.iface.mapCanvas().setMapTool(self.tool)

    def finish_draw(self, geom):
        try:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.line.setToGeometry(geom, None)
            self.line.show()
            self.calc_profile(geom)
        except Exception:
            pass

    def update_calc(self):
        lyr = self.iface.activeLayer()
        if lyr and lyr.type() == QgsMapLayerType.VectorLayer and lyr.selectedFeatures():
            self.line.hide()
            self.calc_profile(lyr.selectedFeatures()[0].geometry())

    def calc_profile(self, geom):
        try:
            r_name = self.dock.combo.currentText()
            if not r_name or r_name == "No Raster":
                return
                
            rst = QgsProject.instance().mapLayersByName(r_name)[0]
            d_calc = QgsDistanceArea()
            crs_dest = self.iface.mapCanvas().mapSettings().destinationCrs()
            
            d_calc.setSourceCrs(crs_dest, QgsProject.instance().transformContext())
            ellps = QgsProject.instance().ellipsoid()
            
            if not ellps or ellps.upper() == 'NONE':
                d_calc.setEllipsoid('WGS84')
            else:
                d_calc.setEllipsoid(ellps)
            
            real_dist_meters = d_calc.measureLength(geom)
            geom_rst = QgsGeometry(geom)
            geom_rst.transform(QgsCoordinateTransform(crs_dest, rst.crs(), QgsProject.instance()))
            
            x = np.linspace(0, real_dist_meters, 1500)
            y = []
            prov = rst.dataProvider()
            
            for d in np.linspace(0, geom_rst.length(), 1500):
                val, res = prov.sample(geom_rst.interpolate(d).asPoint(), 1)
                y.append(val if res and val > -10000 else (y[-1] if y else 0))
            
            sigma = self.dock.spin_sigma.value()
            if len(y) > 50 and sigma > 0:
                radius = int(4 * sigma + 0.5)
                kernel = np.exp(-0.5 * (np.arange(-radius, radius + 1) / sigma) ** 2)
                kernel /= kernel.sum()
                
                y_sm = np.convolve(y, kernel, mode='same')
                y_sm[:radius] = y[:radius]
                y_sm[-radius:] = y[-radius:]
                y = y_sm
            
            xf = QgsCoordinateTransform(crs_dest, crs_dest, QgsProject.instance())
            self.dock.plot_data(x, y, real_dist_meters, geom, xf)
            
        except Exception:
            pass