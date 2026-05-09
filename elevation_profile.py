#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
#  ELEVATION PROFILE TOOLS
# --------------------------------------------------------------------------
#  PLUGIN NAME : Elevation Profile
#  DESCRIPTION : High-Precision Terrain Profiling Tool for QGIS
#  AUTHOR      : Jujun Junaedi
#  EMAIL       : jujun.junaedi@outlook.com
#  VERSION     : 1.9.3
#  COPYRIGHT   : (c) 2023-2026 by Jujun Junaedi
#  LICENSE     : GPL-2.0-or-later
# --------------------------------------------------------------------------

import os
import math
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
from matplotlib import cm 

# Matplotlib backend resolution mapping
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from qgis.core import (
    QgsProject, QgsMapLayerType, QgsDistanceArea, 
    QgsPointXY, QgsGeometry, QgsCoordinateTransform, 
    QgsWkbTypes, QgsCoordinateReferenceSystem, QgsSettings
)
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.utils import iface

from qgis.PyQt.QtGui import QIcon, QColor, QFont, QCursor
from qgis.PyQt.QtWidgets import (
    QAction, QDockWidget, QVBoxLayout, QWidget, QComboBox, 
    QLabel, QHBoxLayout, QSizePolicy, QToolButton, QDialog, 
    QSpinBox, QMessageBox, QTextBrowser, QMenu, QFileDialog, 
    QApplication, QToolTip, QLineEdit, QFrame
)
from qgis.PyQt.QtCore import Qt, pyqtSignal

# --------------------------------------------------------------------------
# PyQt6 / PyQt5 Compatibility Mapping
# --------------------------------------------------------------------------
try:
    QT_LEFT_BUTTON = Qt.MouseButton.LeftButton
    QT_RIGHT_BUTTON = Qt.MouseButton.RightButton
    QT_BOTTOM_DOCK = Qt.DockWidgetArea.BottomDockWidgetArea
    QT_TOP_DOCK = Qt.DockWidgetArea.TopDockWidgetArea
    QT_RICH_TEXT = Qt.TextFormat.RichText
    POLICY_EXPANDING = QSizePolicy.Policy.Expanding
    POLICY_FIXED = QSizePolicy.Policy.Fixed
    MSG_INFO = QMessageBox.Icon.Information
    MSG_WARNING = QMessageBox.Icon.Warning
    MSG_OK = QMessageBox.StandardButton.Ok
    TOOLBUTTON_INSTANT_POPUP = QToolButton.ToolButtonPopupMode.InstantPopup
    WAIT_CURSOR = Qt.CursorShape.WaitCursor
    QT_TRANSPARENT_MOUSE = Qt.WidgetAttribute.WA_TransparentForMouseEvents
    QT_STYLED_BACKGROUND = Qt.WidgetAttribute.WA_StyledBackground
    QFRAME_NO_FRAME = QFrame.Shape.NoFrame
    QT_ALIGN_TOP = Qt.AlignmentFlag.AlignTop
except AttributeError:
    QT_LEFT_BUTTON = Qt.LeftButton
    QT_RIGHT_BUTTON = Qt.RightButton
    QT_BOTTOM_DOCK = Qt.BottomDockWidgetArea
    QT_TOP_DOCK = Qt.TopDockWidgetArea
    QT_RICH_TEXT = Qt.RichText
    POLICY_EXPANDING = QSizePolicy.Expanding
    POLICY_FIXED = QSizePolicy.Fixed
    MSG_INFO = QMessageBox.Information
    MSG_WARNING = QMessageBox.Warning
    MSG_OK = QMessageBox.Ok
    TOOLBUTTON_INSTANT_POPUP = QToolButton.InstantPopup
    WAIT_CURSOR = Qt.WaitCursor
    QT_TRANSPARENT_MOUSE = Qt.WA_TransparentForMouseEvents
    QT_STYLED_BACKGROUND = Qt.WA_StyledBackground
    QFRAME_NO_FRAME = QFrame.NoFrame
    QT_ALIGN_TOP = Qt.AlignTop


class ProfileMapTool(QgsMapTool):
    line_finished = pyqtSignal(object) 
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.points = []
        
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubber_band.setColor(QColor(231, 76, 60, 180))
        self.rubber_band.setWidth(2)
        
        self.d_calc = QgsDistanceArea()
        self.d_calc.setSourceCrs(self.canvas.mapSettings().destinationCrs(), QgsProject.instance().transformContext())
        
        ellipsoid = QgsProject.instance().ellipsoid()
        if ellipsoid and ellipsoid.upper() != 'NONE':
            self.d_calc.setEllipsoid(ellipsoid)
        else:
            self.d_calc.setEllipsoid('WGS84')

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
                    QToolTip.hideText()
        except Exception:
            pass

    def canvasMoveEvent(self, event):
        if len(self.points) > 0:
            pt = self.toMapCoordinates(event.pos())
            self.rubber_band.reset(QgsWkbTypes.LineGeometry)
            
            for p in self.points:
                self.rubber_band.addPoint(p)
            self.rubber_band.addPoint(pt)
            
            p_start = self.points[0]
            dist_m = self.d_calc.measureLine(p_start, pt)
            bearing_rad = self.d_calc.bearing(p_start, pt)
            azimuth = (math.degrees(bearing_rad) + 360) % 360
            
            if dist_m >= 1000:
                dist_txt = f"{dist_m/1000:.2f} km"
            else:
                dist_txt = f"{dist_m:.0f} m"
                
            tooltip_txt = f"Azimuth: {azimuth:.1f}°\nDistance: {dist_txt}"
            
            font = QFont("Segoe UI", 9)
            font.setBold(True)
            QToolTip.setFont(font)
            QToolTip.showText(QCursor.pos(), tooltip_txt, self.canvas)


class ElevationDockWidget(QDockWidget):
    draw_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    closing = pyqtSignal() 
    stats_updated = pyqtSignal(dict)
    
    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)

    def __init__(self, parent=None):
        super().__init__("Elevation Profile v1.9.3 | ©Jujun.J", parent)    
        self.setAllowedAreas(QT_BOTTOM_DOCK | QT_TOP_DOCK)
        
        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.top_widget = QWidget()
        self.top_layout = QVBoxLayout(self.top_widget)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(0)
        
        self.create_toolbar()
        self.layout.addWidget(self.top_widget)

        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(0)

        # Chart Container
        self.chart_container = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_layout.addWidget(self.chart_container)
        self.layout.addLayout(self.content_layout)

        self.create_chart()
        self.setWidget(self.main_widget)
        
        # Internal State Variables
        self.x_data_km = None
        self.y_data_raw = None
        self.geom = None
        self.xf = None
        self.marker_arrow = None
        
        # Dual Crosshair Variables
        self.cursor_vline = None
        self.cursor_hline = None
        self.cursor_text = None
        
        self.max_dist_km = 0
        self.current_azimuth = 0.0
        
        self.apply_theme() # Forced Dark Mode
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def show_pro_locked_msg(self, feature_name):
        msg = QMessageBox(iface.mainWindow() if hasattr(iface, 'mainWindow') else None)
        msg.setWindowTitle("Pro Feature Locked")
        try: msg.setIcon(QMessageBox.Warning)
        except AttributeError: pass
        
        try: msg.setTextFormat(Qt.RichText)
        except AttributeError: msg.setTextFormat(Qt.TextFormat.RichText)
        
        html_text = f"""
        <div style='font-family: Arial, sans-serif;'>
        <h3 style='color: #d35400; margin-bottom: 5px;'>🔒 {feature_name} (Pro Version Only)</h3>
        <p style='color: #2c3e50; font-size: 12px;'>
        This feature is locked in the standard version. Upgrade to unlock LoS Viewer Engine, Population Density, Floating HUD, and more!<br><br>
        <i>Fitur ini hanya tersedia di versi Pro. Upgrade untuk membuka LoS Viewer, Peta Kepadatan Penduduk, dan Floating HUD!</i>
        </p>
        
        <div style='background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 10px; border-radius: 4px; margin-top: 12px; margin-bottom: 12px;'>
            <b style='font-size: 13px;'>🎁 SPECIAL BONUS / PROMO SPESIAL:</b><br>
            <span style='font-size: 12px;'>Get the <b>Embed Legend Pro</b> plugin for FREE with your upgrade!<br>
            <i>Dapatkan plugin <b>Embed Legend Pro</b> secara GRATIS untuk setiap pembelian versi Pro!</i></span>
        </div>
        
        <hr style='border: 0; border-top: 1px solid #bdc3c7; margin-bottom: 10px; margin-top: 10px;'>
        <p style='margin:0 0 5px 0; font-weight:bold; font-size: 12px;'>Get the Pro Version + Bonus here:</p>
        <ul style='margin-top: 0; font-size: 12px;'>
            <li>🌐 <a href='https://jujunet.gumroad.com/l/dssdip' style='color:#2980b9; text-decoration:none;'>Download via Gumroad (Global)</a></li>
            <li>🇮🇩 <a href='https://lynk.id/kangjun/55xnn81vz9rg' style='color:#2980b9; text-decoration:none;'>Download via Lynk.id (Indonesia)</a></li>
        </ul>
        </div>
        """
        msg.setText(html_text)
        try: msg.setStandardButtons(QMessageBox.Ok)
        except AttributeError: pass
        
        if hasattr(msg, 'exec'):
            msg.exec()
        else:
            msg.exec_()

    def check_source_lock(self, index):
        if index != 0:
            self.cmb_source.blockSignals(True)
            self.cmb_source.setCurrentIndex(0)
            self.cmb_source.blockSignals(False)
            self.show_pro_locked_msg("Online DEM (Open-Meteo & OpenTopoData)")

    def check_los_lock(self):
        self.btn_los_toggle.setChecked(False)
        self.show_pro_locked_msg("LoS Viewer & Fresnel Clearance")

    def apply_theme(self):
        # Enforce Dark Theme internally
        bg_color = "#2b2b2b"
        text_color = "#dfe6e9"
        btn_bg = "#333333"
        btn_hover = "#555555"
        border_color = "#555555"
        combo_bg = "#3b3b3b"
        info_color = "#00cec9"

        self.main_widget.setStyleSheet(f"background-color: {bg_color}; color: {text_color};")
        
        input_style = f"background: {combo_bg}; color: {text_color}; border: 1px solid {border_color}; border-radius: 2px; padding: 4px; font-size: 7pt;"
        flat_btn_style = f"""
            QToolButton {{ background: {btn_bg}; color: {text_color}; border: 1px solid {border_color}; border-radius: 2px; padding: 4px 8px; font-size: 7pt; font-weight: bold; }}
            QToolButton:hover {{ background: {btn_hover}; border: 1px solid #00cec9; }}
        """
        lbl_style = f"color: {text_color}; font-size: 7pt; font-weight: bold;"

        self.cmb_source.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.combo.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.combo_pop.setStyleSheet(f"QComboBox {{ {input_style} }}")
        self.spin_sigma.setStyleSheet(f"QSpinBox {{ {input_style} }}")
        self.input_buffer.setStyleSheet(f"QLineEdit {{ {input_style} }}")

        self.lbl_src.setStyleSheet(lbl_style)
        self.lbl_pop.setStyleSheet(lbl_style)
        self.lbl_sigma.setStyleSheet(lbl_style)
        self.lbl_info.setStyleSheet(f"color: {info_color}; font-size: 7pt; font-weight: bold; margin-left: 15px;")
        
        toolbar_buttons = [
            self.btn_refresh, self.btn_theme, self.btn_help, 
            self.btn_about, self.btn_draw, self.btn_export, self.btn_los_toggle
        ]
        
        for btn in toolbar_buttons:
            btn.setStyleSheet(flat_btn_style)

        # Plot Theme Updates
        self.figure.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        self.ax.tick_params(colors=text_color)
        
        for spine in ['bottom', 'left']:
            self.ax.spines[spine].set_color(border_color)
            
        self.canvas.draw()

    def create_toolbar(self):
        v_lay = QVBoxLayout()
        v_lay.setContentsMargins(5, 5, 5, 2)
        v_lay.setSpacing(3)
        
        h_lay1 = QHBoxLayout()
        h_lay2 = QHBoxLayout()
        h_lay1.setSpacing(5)
        h_lay2.setSpacing(5)
        
        # Source Selection
        self.lbl_src = QLabel("Source:")
        self.cmb_source = QComboBox()
        self.cmb_source.addItems([
            "📁 Offline DEM (Raster)", 
            "🌐 Open-Meteo (90m Global)", 
            "🛰️ OpenTopoData (30m SRTM)"
        ])
        self.cmb_source.currentIndexChanged.connect(self.check_source_lock)

        self.combo = QComboBox()
        self.combo.setMinimumWidth(120)
        self.combo.setSizePolicy(POLICY_EXPANDING, POLICY_FIXED)
        
        # Population Selection (Locked UI)
        self.lbl_pop = QLabel("Pop:")
        self.combo_pop = QComboBox()
        self.combo_pop.setMinimumWidth(100)
        self.combo_pop.setSizePolicy(POLICY_EXPANDING, POLICY_FIXED)
        self.combo_pop.addItem("🔒 Locked (Pro Only)")
        self.combo_pop.activated.connect(lambda: self.show_pro_locked_msg("Population Density Map"))

        # Utility Buttons
        self.btn_refresh = QToolButton()
        self.btn_refresh.setText("↻")
        self.btn_refresh.clicked.connect(lambda: self.refresh_clicked.emit())

        self.btn_theme = QToolButton()
        self.btn_theme.setText("☀️")
        self.btn_theme.clicked.connect(lambda: self.show_pro_locked_msg("Theme Switcher (Light Mode)"))

        self.btn_help = QToolButton()
        self.btn_help.setText("?")
        self.btn_help.clicked.connect(self.show_help)

        self.btn_about = QToolButton()
        self.btn_about.setText("i")
        self.btn_about.clicked.connect(self.show_about_dialog)

        # Draw & Export Controls
        self.lbl_sigma = QLabel("Smooth:")
        
        self.spin_sigma = QSpinBox()
        self.spin_sigma.setRange(0, 50)
        self.spin_sigma.setValue(5)
        self.spin_sigma.setFixedWidth(40)
        self.spin_sigma.valueChanged.connect(self.replot_current_data)
        self.spin_sigma.setToolTip("Smooth value only active for Offline DEM.")

        self.btn_draw = QToolButton()
        self.btn_draw.setText("📈 Line")
        self.btn_draw.clicked.connect(lambda: self.draw_clicked.emit())

        self.btn_export = QToolButton()
        self.btn_export.setText("💾 Export")
        self.btn_export.setPopupMode(TOOLBUTTON_INSTANT_POPUP)
        
        export_menu = QMenu(self.btn_export)
        export_menu.addAction("Save as PNG Image (.png)", lambda: self.handle_export("png"))
        export_menu.addAction("Save as SVG Vector (.svg)", lambda: self.handle_export("svg"))
        self.btn_export.setMenu(export_menu)

        self.btn_los_toggle = QToolButton()
        self.btn_los_toggle.setText("📡 LoS Viewer")
        self.btn_los_toggle.setCheckable(True)
        self.btn_los_toggle.clicked.connect(self.check_los_lock)

        self.input_buffer = QLineEdit()
        self.input_buffer.setPlaceholderText("Buffer Pop (m)")
        self.input_buffer.setText("🔒 250")
        self.input_buffer.setReadOnly(True)
        self.input_buffer.setFixedWidth(75)
        self.input_buffer.mousePressEvent = lambda e: self.show_pro_locked_msg("Population Buffer Calculation")

        self.lbl_info = QLabel("")
        self.lbl_info.setTextFormat(QT_RICH_TEXT)
        
        # Layout Assembly
        top_row_widgets = [
            self.lbl_src, self.cmb_source, self.combo, 
            self.lbl_pop, self.combo_pop, self.btn_refresh, 
            self.btn_theme, self.btn_help, self.btn_about
        ]
        for w in top_row_widgets:
            h_lay1.addWidget(w)
        h_lay1.addStretch() 

        bottom_row_widgets = [
            self.lbl_sigma, self.spin_sigma, self.btn_draw, 
            self.btn_export, self.btn_los_toggle, self.input_buffer, 
            self.lbl_info
        ]
        for w in bottom_row_widgets:
            h_lay2.addWidget(w)
        h_lay2.addStretch()

        v_lay.addLayout(h_lay1)
        v_lay.addLayout(h_lay2)
        self.top_layout.addLayout(v_lay)

    def replot_current_data(self):
        if self.x_data_km is not None and self.y_data_raw is not None:
            self.plot_data(
                self.x_data_km * 1000, 
                self.y_data_raw, 
                self.max_dist_km * 1000, 
                self.geom, 
                self.xf
            )
        
    def show_about_dialog(self):
        msg = QMessageBox(self.iface.mainWindow() if hasattr(self, 'iface') else None)
        msg.setWindowTitle("About Elevation Profile v1.9.3")
        try: msg.setIcon(QMessageBox.Information)
        except AttributeError: pass
        
        try: msg.setTextFormat(Qt.RichText)
        except AttributeError: msg.setTextFormat(Qt.TextFormat.RichText)
        
        text = (
            "<div style='font-family: Arial, sans-serif;'>"
            "<h2 style='color: #2c3e50; margin-bottom: 5px;'>Elevation Profile</h2>"
            "<p style='color: #7f8c8d; margin-top: 0px; margin-bottom: 15px;'>High-Precision 2D Terrain Profiling Tool.</p>"
            "<table style='margin-bottom: 15px;' cellpadding='3'>"
            "<tr><td width='70'><b>Version:</b></td><td>1.9.3 (Standard)</td></tr>"
            "<tr><td><b>Author:</b></td><td>Jujun Junaedi</td></tr>"
            "<tr><td><b>Contact:</b></td><td><a href='mailto:jujun.junaedi@outlook.com' style='color: #2980b9; text-decoration: none;'>jujun.junaedi@outlook.com</a></td></tr>"
            "</table>"
            "<hr style='border: 0; border-top: 1px solid #bdc3c7; margin-bottom: 15px;'>"
            "<div style='margin-bottom: 15px; margin-top: 15px;'>"
            "<p style='margin: 0 0 5px 0; font-weight: bold;'>🌟 Get the PRO Version + Free Bonus Embed Legend Pro:</p>"
            "<a href='https://jujunet.gumroad.com/l/dssdip' style='text-decoration: none;'>"
            "<span style='background-color: #ff90e8; color: black; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px; border: 1px solid #000;'>Global 👉: Buy on Gumroad</span></a>"
            "&nbsp;&nbsp;&nbsp;"
            "<a href='https://lynk.id/kangjun/55xnn81vz9rg' style='text-decoration: none;'>"
            "<span style='background-color: #000000; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px;'>Lokal 👉 : Lynk.id</span></a>"
            "</div>"
            "<hr style='border: 0; border-top: 1px dashed #bdc3c7; margin-bottom: 12px;'>"
            "<p style='margin-bottom: 10px; font-size: 11px; color: #555;'>Or support the continuous development of this standard tool:</p>"
            "<div>"
            "<a href='https://paypal.me/junjunan81' style='text-decoration: none;'>"
            "<span style='background-color: #0070ba; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px;'>Via PayPal</span></a>"
            "&nbsp;&nbsp;"
            "<a href='https://buymeacoffee.com/juneth' style='text-decoration: none;'>"
            "<span style='background-color: #f39c12; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px;'>Buy me a coffee</span></a>"
            "&nbsp;&nbsp;"
            "<a href='https://saweria.co/juneth' style='text-decoration: none;'>"
            "<span style='background-color: #2ecc71; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px;'>Saweria (IDN)</span></a>"
            "</div>"
            "<br><p style='font-size: 10px; color: #95a5a6; margin-top: 10px;'>© 2023-2026 Jujun Junaedi. All Rights Reserved.</p>"
            "</div>"
        )
        
        msg.setText(text)
        try: msg.setStandardButtons(QMessageBox.Ok)
        except AttributeError: pass
        
        if hasattr(msg, 'exec'):
            msg.exec()
        else:
            msg.exec_()

    def show_help(self):
        dialog = QDialog(iface.mainWindow())
        dialog.setWindowTitle("Help & Guide")
        dialog.resize(650, 550)
        
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        
        html_content = """
        <style>
            h3 { color: #2980b9; margin-bottom: 5px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
            h4 { color: #e67e22; margin-top: 15px; margin-bottom: 5px; }
            li { margin-bottom: 5px; }
            a { color: #2980b9; text-decoration: none; font-weight: bold; }
        </style>
        
        <h3>User Guide</h3>
        <ul>
            <li><b>1.Load Data: Ensure your local DEM/Raster layer is loaded in QGIS and selected in the dropdown menu. (Click the ↻ button to refresh the list).</li>
            <li><b>2.Draw Line (📈): Click the "📈 Line" button, then click on the map to trace your path (Left-click to add points). Watch the live tooltips for Distance and Azimuth. Right-click to finish and generate the profile.</li>
            <li><b>3.Adjust Smoothing: Change the "Smooth" value to filter out terrain noise (0 = Raw, 3 = DEMNAS, 5 = AW3D30, 20 = Smooth/SRTM).</li>
            <li><b>4.Export: Click the "💾 Export" button to save your profile as a PNG or SVG file.</li>
        </ul>
        
        <hr>
        <h3>Data Sources Recommendation</h3>
        <h4>1. Global Data (Worldwide)</h4>
        <p><b>JAXA ALOS World 3D (30m):</b> <a href="https://www.eorc.jaxa.jp/ALOS/en/aw3d30/registration.htm">https://earth.jaxa.jp/en/</a></p>

        <h4>2. Indonesia Local Data (High Res)</h4>
        <p><b>DEMNAS - BIG (8m):</b> <a href="https://tanahair.indonesia.go.id/portal-web/unduh">https://tanahair.indonesia.go.id/demnas/</a></p>
        """
        browser.setHtml(html_content)
        layout.addWidget(browser)
        
        if hasattr(dialog, 'exec'):
            dialog.exec()
        else:
            dialog.exec_()

    def create_chart(self):
        self.figure = Figure(figsize=(10, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.chart_layout.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        
        for spine in ['top', 'right']: 
            self.ax.spines[spine].set_visible(False)
            
        self.figure.subplots_adjust(left=0.06, right=0.92, top=0.92, bottom=0.28)

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
        
        r_layers = []
        seen = set()
        
        for l in QgsProject.instance().mapLayers().values():
            if l.type() == QgsMapLayerType.RasterLayer:
                dp = l.dataProvider()
                if dp and dp.name() == 'gdal':
                    name = l.name()
                    if name not in seen:
                        seen.add(name)
                        r_layers.append(name)
                        
        self.combo.addItems(r_layers)
        if not r_layers:
            self.combo.addItem("No Raster")

    def handle_export(self, ext):
        if self.x_data_km is None: 
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, "Export", f"Profile.{ext}", f"Files (*.{ext})")
        if filename: 
            self.figure.savefig(filename, facecolor=self.figure.get_facecolor(), dpi=300, format=ext)

    def apply_smoothing(self, y):
        sigma = self.spin_sigma.value()
        
        if len(y) > 10 and sigma > 0:
            y_arr = np.array(y)
            radius = int(4 * sigma + 0.5)
            max_radius = (len(y_arr) // 2) - 1
            
            if radius > max_radius: 
                radius = max_radius
                sigma = radius / 4.0 if radius > 0 else 0
                
            if radius < 1 or sigma <= 0: 
                return y
                
            kernel = np.exp(-0.5 * (np.arange(-radius, radius + 1) / sigma) ** 2)
            kernel /= kernel.sum()
            
            y_sm = np.convolve(y_arr, kernel, mode='same')
            safe_rad = min(radius, len(y_sm))
            
            if safe_rad > 0: 
                y_sm[:safe_rad] = y_arr[:safe_rad]
                y_sm[-safe_rad:] = y_arr[-safe_rad:]
                
            return y_sm.tolist() 
            
        return y

    def update_summary(self, y_smooth, dist_km):
        if len(y_smooth) == 0: 
            self.lbl_info.setText("")
            return
            
        mn = np.min(y_smooth)
        mx = np.max(y_smooth)
        av = np.mean(y_smooth)
        
        label_col = "white"
        val_col = "#00cec9"
            
        html = f"""<span style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 8pt; font-weight: bold;">
        <span style="color: {label_col};">Dist:</span> <span style="color: {val_col};">{dist_km:.2f} km</span> 
        <span style="color: {label_col};">&nbsp;|&nbsp;Elev: Min</span> <span style="color: {val_col};">{mn:.0f} m</span> 
        <span style="color: {label_col};">&nbsp;|&nbsp;Avg</span> <span style="color: {val_col};">{av:.0f} m</span> 
        <span style="color: {label_col};">&nbsp;|&nbsp;Max</span> <span style="color: {val_col};">{mx:.0f} m</span>
        </span>"""
        
        self.lbl_info.setText(html)

    def plot_data(self, x_meters, raw_y, dist_meters, geom, xf):
        self.x_data_km = x_meters / 1000.0
        self.y_data_raw = raw_y
        
        self.max_dist_km = dist_meters / 1000.0
        self.geom = geom
        self.xf = xf
        
        y_smooth = self.apply_smoothing(raw_y)
        
        self.ax.clear()
            
        self.cursor_vline = None
        self.cursor_hline = None
        self.cursor_text = None
        
        self.update_summary(y_smooth, self.max_dist_km)

        # Enforce Dark Theme Palette
        fill_col = "#e67e22"
        line_col = "#ff9f43"
        ax_bg = "#2b2b2b"
        text_col = "#dfe6e9"
        grid_col = "white"
        grid_alpha = 0.15
        border_col = "#636e72"
            
        self.ax.fill_between(self.x_data_km, y_smooth, color=fill_col, alpha=0.3)
        self.ax.plot(self.x_data_km, y_smooth, color=line_col, linewidth=1.2)
        
        mx_plot = np.max(y_smooth) if len(y_smooth) > 0 else 1
        mn_plot = np.min(y_smooth) if len(y_smooth) > 0 else 0

        self.ax.set_facecolor(ax_bg)
        self.figure.patch.set_facecolor(ax_bg)
        
        self.ax.set_xlabel("Distance (Km)", fontsize=7, color=text_col)
        self.ax.set_ylabel("Elevation (m)", fontsize=7, color=text_col)
        self.ax.grid(True, linestyle=':', linewidth=0.5, alpha=grid_alpha, color=grid_col)
        self.ax.tick_params(colors=text_col, labelsize=7)
        
        for spine in ['top', 'right']: 
            self.ax.spines[spine].set_visible(False)
            
        for spine in ['bottom', 'left']: 
            self.ax.spines[spine].set_color(border_col)
            
        if self.max_dist_km <= 0: 
            self.max_dist_km = 0.001
            
        self.ax.set_xlim(0, self.max_dist_km)
        
        if len(y_smooth) > 0:
            pad = (mx_plot - mn_plot) * 0.1 if (mx_plot - mn_plot) > 1 else 1
            self.ax.set_ylim(mn_plot - pad, mx_plot + pad)

        self.canvas.draw()

    def on_mouse_move(self, event):
        if event.inaxes != self.ax or self.x_data_km is None:
            if self.cursor_vline: self.cursor_vline.set_visible(False)
            if self.cursor_hline: self.cursor_hline.set_visible(False)
            if self.cursor_text: self.cursor_text.set_visible(False)
            if self.marker_arrow: self.marker_arrow.hide()
            self.canvas.draw_idle()
            return
            
        idx = (np.abs(self.x_data_km - event.xdata)).argmin()
        x_snap = self.x_data_km[idx]
        y_snap = self.apply_smoothing(self.y_data_raw)[idx]
        
        ylim_min, ylim_max = self.ax.get_ylim()
        xlim_min, xlim_max = self.ax.get_xlim()
        
        crosshair_col, tooltip_bg, tooltip_text = "#00cec9", "#2d3436", "#00cec9"
        
        txt = f"Dist: {x_snap:.2f} Km\nElev: {y_snap:.0f} m"
        
        if self.cursor_vline is None or self.cursor_vline not in self.ax.lines:
            self.cursor_vline, = self.ax.plot([x_snap, x_snap], [ylim_min, ylim_max], color=crosshair_col, linestyle='--', linewidth=0.8, alpha=0.7, zorder=100)
        else:
            self.cursor_vline.set_color(crosshair_col)
            self.cursor_vline.set_data([x_snap, x_snap], [ylim_min, ylim_max])
            self.cursor_vline.set_visible(True)

        if self.cursor_hline is None or self.cursor_hline not in self.ax.lines:
            self.cursor_hline, = self.ax.plot([xlim_min, xlim_max], [y_snap, y_snap], color=crosshair_col, linestyle='--', linewidth=0.8, alpha=0.7, zorder=100)
        else:
            self.cursor_hline.set_color(crosshair_col)
            self.cursor_hline.set_data([xlim_min, xlim_max], [y_snap, y_snap])
            self.cursor_hline.set_visible(True)
            
        x_range = xlim_max - xlim_min
        if x_snap > xlim_max - (0.2 * x_range):
            align_h = 'right'
            offset_x = x_snap - (0.015 * x_range)
        else:
            align_h = 'left'
            offset_x = x_snap + (0.015 * x_range)
            
        align_v = 'center'
        y_pos_text = y_snap

        if self.cursor_text is None or self.cursor_text not in self.ax.texts:
            bbox_props = dict(boxstyle='round,pad=0.3', facecolor=tooltip_bg, alpha=0.8, edgecolor=tooltip_text)
            self.cursor_text = self.ax.text(offset_x, y_pos_text, txt, fontsize=6, color=tooltip_text, bbox=bbox_props, ha=align_h, va=align_v, zorder=100)
        else:
            self.cursor_text.set_text(txt)
            self.cursor_text.set_fontsize(6)
            self.cursor_text.set_color(tooltip_text)
            self.cursor_text.get_bbox_patch().set_alpha(0.8)
            self.cursor_text.get_bbox_patch().set_facecolor(tooltip_bg)
            self.cursor_text.get_bbox_patch().set_edgecolor(tooltip_text)
            self.cursor_text.set_position((offset_x, y_pos_text))
            self.cursor_text.set_horizontalalignment(align_h)
            self.cursor_text.set_verticalalignment(align_v)
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
            QToolTip.hideText()
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
            d_calc = QgsDistanceArea()
            crs_dest = self.iface.mapCanvas().mapSettings().destinationCrs()
            d_calc.setSourceCrs(crs_dest, QgsProject.instance().transformContext())
            
            ellps = QgsProject.instance().ellipsoid()
            if not ellps or ellps.upper() == 'NONE': 
                d_calc.setEllipsoid('WGS84')
            else: 
                d_calc.setEllipsoid(ellps)
                
            real_dist_meters = d_calc.measureLength(geom)
            xf = QgsCoordinateTransform(crs_dest, crs_dest, QgsProject.instance())
            
            try:
                polyline = geom.asPolyline()
                if polyline and len(polyline) >= 2:
                    p1 = polyline[0]
                    p2 = polyline[-1]
                    bearing_rad = d_calc.bearing(p1, p2)
                    self.dock.current_azimuth = (math.degrees(bearing_rad) + 360) % 360
                else:
                    self.dock.current_azimuth = 0.0
            except Exception as e:
                self.dock.current_azimuth = 0.0
            
            # Offline DEM (Raster) Mode Only
            r_name = self.dock.combo.currentText()
            if not r_name or r_name == "No Raster": 
                return
                
            rst = QgsProject.instance().mapLayersByName(r_name)[0]
            geom_rst = QgsGeometry(geom)
            geom_rst.transform(QgsCoordinateTransform(crs_dest, rst.crs(), QgsProject.instance()))
            
            num_points = max(500, min(3000, int(real_dist_meters / 10.0)))
            x = np.linspace(0, real_dist_meters, num_points)
            y = []
            prov = rst.dataProvider()
            
            for d in np.linspace(0, geom_rst.length(), num_points):
                val, res = prov.sample(geom_rst.interpolate(d).asPoint(), 1)
                if res and val > -10000:
                    y.append(val)
                else:
                    y.append(y[-1] if y else 0)
                    
            self.dock.plot_data(x, y, real_dist_meters, geom, xf)
                    
        except Exception:
            pass