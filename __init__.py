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
This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    """
    Load ElevationProfile class from file elevation_profile.
    
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .elevation_profile import ElevationProfile
    return ElevationProfile(iface)