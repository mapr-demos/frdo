#!/bin/bash -

################################################################################
# 
# This is the script that allows you to start or stop the FrDO demo on the 
# cluster. It launches the fintrans source (gess), the online part (sisenik) 
# and the processing of the data cluster-side to create the heatmap.
#
# Usage: ./frdo.sh
#

#######################################
# gess

#######################################
# sisenik
python sisenik.py


#######################################
# Hive


