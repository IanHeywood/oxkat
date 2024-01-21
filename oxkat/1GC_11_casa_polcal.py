# ian.heywood@physics.ox.ac.uk


import glob
import sys
import time


execfile('oxkat/casa_read_project_info.py')
execfile('oxkat/config.py')


myuvrange = CAL_1GC_UVRANGE 


if not CAL_1GC_DOPOL:
    print('Skipping polarisation calibration as per config settings.')
    sys.exit()

# Find the gaintables generated at 

    # "polcal_id": "None",
    # "polcal_name": "None",
    # "polcal_tag": "None",

if polcal_tag == 'None':
    print('No polcal identified in project_info file.')
    print('Either this MS does not have a primary pol or something has gone wrong.')
    sys.exit()
elif polcal_tag == '3C138':
    print('Using 3C138 as primary polarisation calibrator')
    polcal_model = CAL_1GC_3C138_MODEL
elif polcal_tag == '3C286':
    print('Using 3C286 as primary polarisation calibrator')
    polcal_model = CAL_1GC_3C138_MODEL

polflux = polcal_model[0]
polspix = polcal_model[1]
polfreq = polcal_model[2]
polindex = polcal_model[3]
polangle = polcal_model[4]

setjy()