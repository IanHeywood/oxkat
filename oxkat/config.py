 #!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import json
import os
import sys


# ------------------------------------------------------------------------
#
# Check for project_info file and get band
#

if os.path.isfile('project_info.json'):
    with open('project_info.json') as f:
        project_info = json.load(f)
    BAND = project_info['band']
else:
    BAND = 'not yet determined'


# ------------------------------------------------------------------------
#
# Paths for components and OUTPUTS
#

CWD = os.getcwd()
HOME = os.path.expanduser('~')

OXKAT = CWD+'/oxkat'
DATA = CWD+'/data'
TOOLS = CWD+'/tools'

GAINPLOTS = CWD+'/GAINPLOTS'
GAINTABLES = CWD+'/GAINTABLES'
IMAGES = CWD+'/IMAGES'
LOGS = CWD+'/LOGS'
SCRIPTS = CWD+'/SCRIPTS'
VISPLOTS = CWD+'/VISPLOTS'


# ------------------------------------------------------------------------
#
# Singularity settings
#

# Set to False to disable singularity entirely
USE_SINGULARITY = True

# If your data are symlinked and located in a path that singularity
# cannot see by default then set BIND to that path.
# If you wish to bind multiple paths then use a comma-separated list.
BIND = ''
BINDPATH = '$PWD,'+CWD+','+BIND

IDIA_CONTAINER_PATH = ['/idia/software/containers/',HOME+'/containers/']
CHPC_CONTAINER_PATH = [HOME+'/containers/']
HIPPO_CONTAINER_PATH = None
NODE_CONTAINER_PATH = [HOME+'/containers/']


ASTROPY_PATTERN = 'oxkat-0.5_vol2'
CASA_PATTERN = 'oxkat-0.5_vol1'
CLUSTERCAT_PATTERN = 'oxkat-0.5_vol3'
CUBICAL_PATTERN = 'oxkat-0.5_vol2'
DDFACET_PATTERN = 'oxkat-0.5_vol3'
KILLMS_PATTERN = 'oxkat-0.5_vol3'
OWLCAT_PATTERN = 'oxkat-0.5_vol2'
PACOR_PATTERN = 'oxkat-0.5_vol3'
PYBDSF_PATTERN = 'oxkat-0.5_vol3'
RAGAVI_PATTERN = 'oxkat-0.5_vol1'
SHADEMS_PATTERN = 'oxkat-0.5_vol2'
TRICOLOUR_PATTERN = 'oxkat-0.5_tricolour'
WSCLEAN_PATTERN = 'oxkat-0.5_vol2'


# ------------------------------------------------------------------------
#
# Slurm resource settings
#

SLURM_ACCOUNT = '' # e.g. b09-mightee-ag, b24-thunderkat-ag
SLURM_RESERVATION = '' # e.g. lsp-mightee

SLURM_NODELIST = '' # Specify node(s) to use
SLURM_EXCLUDE = 'highmem-003' # Specify node(s) to exclude


SLURM_DEFAULTS = {
	'TIME': '12:00:00',
	'PARTITION': 'Main',
	'NTASKS': '1',
	'NODES': '1',
	'CPUS': '8',
	'MEM': '64GB',
}

SLURM_TRICOLOUR = {
    'TIME': '06:00:00',
    'PARTITION': 'Main',
    'NTASKS': '1',
    'NODES': '1',
    'CPUS': '32',
    'MEM': '230GB'
}

SLURM_WSCLEAN = {
    'TIME': '12:00:00',
    'PARTITION': 'Main',
    'NTASKS': '1',
    'NODES': '1',
    'CPUS': '32',
    'MEM': '230GB'
}

SLURM_EXTRALONG = {
    'TIME': '48:00:00',
    'PARTITION': 'Main',
    'NTASKS': '1',
    'NODES': '1',
    'CPUS': '32',
    'MEM': '230GB'
}

SLURM_HIGHMEM = {
    'TIME': '36:00:00',
    'PARTITION': 'HighMem',
    'NTASKS': '1',
    'NODES': '1',
    'CPUS': '32',
    'MEM': '480GB'
}

# ------------------------------------------------------------------------
#
# PBS resource settings
#

CHPC_ALLOCATION = 'ASTR1301'

PBS_DEFAULTS = {
	'PROGRAM': CHPC_ALLOCATION,
	'WALLTIME': '12:00:00',
	'QUEUE': 'serial',
	'NODES': '1',
	'PPN': '8',
	'MEM': '64gb'
}

PBS_TRICOLOUR = {
	'PROGRAM': CHPC_ALLOCATION,
	'WALLTIME': '06:00:00',
	'QUEUE': 'serial',
	'NODES': '1',
	'PPN': '24',
	'MEM': '120gb'
}

PBS_WSCLEAN = {
	'PROGRAM': CHPC_ALLOCATION,
	'WALLTIME': '12:00:00',
	'QUEUE': 'serial',
	'NODES': '1',
	'PPN': '24',
	'MEM': '120gb'
}

PBS_EXTRALONG = {
    'PROGRAM': CHPC_ALLOCATION,
    'WALLTIME': '48:00:00',
    'QUEUE': 'serial',
    'NODES': '1',
    'PPN': '24',
    'MEM': '120gb'
}

# ------------------------------------------------------------------------
#
# 1GC settings
#

# Scan intents, for automatic identification of cals/targets
CAL_1GC_TARGET_INTENT = 'TARGET'     # (partial) string to match for target intents
CAL_1GC_PRIMARY_INTENT = 'BANDPASS'  # (partial) string to match for primary intents
CAL_1GC_SECONDARY_INTENT = 'PHASE'   # (partial) string to match for secondary intents

# Pre-processing, operations applied when master MS is split to working MS
PRE_FIELDS = ''                      # Comma-separated list of fields to select from raw MS
                                     # Names or IDs, do not mix, do not use spaces
PRE_SCANS = ''                       # Comma-separated list of scans to select from raw MS
PRE_NCHANS = 1024                    # Integer number of channels for working MS
PRE_TIMEBIN = ''                     # Integration time for working MS, leave empty for no averaging

# Reference antennas
CAL_1GC_REF_ANT = 'auto'             # Comma-separated list to manually specify refant(s)
CAL_1GC_REF_POOL = ['m000','m001','m002','m003','m004','m006'] 
                                     # Pool to re-order for reference antenna list for 'auto'

# Field selection, IDs only at present. (Use tools/ms_info.py.)
CAL_1GC_PRIMARY = 'auto'             # Primary calibrator field ID
CAL_1GC_TARGETS = 'auto'             # Comma-separated target field IDs
CAL_1GC_SECONDARIES = 'auto'         # Comma-separated secondary IDs
                                     # - Lists of equal length in targets and secondaries maps cals to targets
                                     # - A single ID in uses same secondary for all targets
                                     # - A length mismatch reverts to auto, so double check!

# Sky model for primary calibrator --- EXPERIMENTAL (use 1GC_primary_models.py setup)
CAL_1GC_PRIMARY_MODEL = 'auto'       # setjy = use setjy component model only
                                     # auto = try to find a suitable model of the field sources in data/calmodels, defer to setjy if not found
                                     # or specify the location/of/wsclean-prefix for an arbitrary model cube

# GBK settings
CAL_1GC_DELAYCUT = 2.5               # [now defunct] Jy at central freq. Do not solve for K on secondaries weaker than this
CAL_1GC_FILLGAPS = 24                # Maximum channel gap over which to interpolate bandpass solutions



# Polarisation settings
CAL_1GC_DOPOL = True                 # Set to False to not perform 1GC pol cal, even if a valid polarisation calibrator is present
CAL_1GC_PAWORKERS = 8                # Number of parallel instances of parallactic angle correction processes

# Base models for polarisation calibrators
# Band-specific modifiers can be implemented in their relevant sections below

# fluxdensity, spix, reffreq, polindex, polangle
CAL_1GC_3C138_MODEL = ([8.4012],[-0.54890527955337987, -0.069418066176041668, -0.0018858519926001926],'1.45GHz',[0.075],[-0.19199])
CAL_1GC_3C286_MODEL = ([14.918703],[-0.50593909976893958,-0.070580431627712076,0.0067337240268301466],'1.45GHz',[0.095],[0.575959])

# Band specific options

if BAND == 'UHF':       

    CAL_1GC_FREQRANGE = '*:850~900MHz'        # Clean part of the band to use for generating UHF 1GC G-solutions
    CAL_1GC_UVRANGE = '>150m'               # Selection for baselines to include during 1GC B/G solving (K excluded)
    CAL_1GC_0408_MODEL = ([27.907,0.0,0.0,0.0],[-1.205],'850MHz')

    CAL_1GC_BAD_FREQS = ['*:540~570MHz',      # Lower band edge 
                        '*:1010~1150MHz']     # Upper band edge

    CAL_1GC_BL_FLAG_UVRANGE = '<600'        # Baseline range for which BL_FREQS are flagged
    CAL_1GC_BL_FREQS = []            

elif BAND == 'L':

    CAL_1GC_FREQRANGE = '*:1300~1400MHz'
    CAL_1GC_UVRANGE = '>150m'
    CAL_1GC_0408_MODEL = ([17.066,0.0,0.0,0.0],[-1.179],'1284MHz')

    CAL_1GC_BAD_FREQS = ['*:850~900MHz',      # Lower band edge
                        '*:1658~1800MHz',     # Upper bandpass edge
                        '*:1419.8~1421.3MHz'] # Galactic HI

    CAL_1GC_BL_FLAG_UVRANGE = '<600'
    CAL_1GC_BL_FREQS = ['*:900MHz~915MHz',    # GSM and aviation
                        '*:925MHz~960MHz',                
                        '*:1080MHz~1095MHz',  # Aircraft transponder response
                        '*:1565MHz~1585MHz',  # GPS
                        '*:1217MHz~1237MHz',
                        '*:1375MHz~1387MHz',
                        '*:1166MHz~1186MHz',
                        '*:1592MHz~1610MHz',  # GLONASS
                        '*:1242MHz~1249MHz',
                        '*:1191MHz~1217MHz',  # Galileo
                        '*:1260MHz~1300MHz',
                        '*:1453MHz~1490MHz',  # Afristar
                        '*:1616MHz~1626MHz',  # Iridium
                        '*:1526MHz~1554MHz',  # Inmarsat
                        '*:1600MHz']          # Alkantpan
                                              # https://github.com/ska-sa/MeerKAT-Cookbook/blob/master/casa/L-band%20RFI%20frequency%20flagging.ipynb

elif BAND == 'S0':

    CAL_1GC_FREQRANGE = '*:2300~2400MHz'
    CAL_1GC_UVRANGE = '>150m'
    CAL_1GC_0408_MODEL = ([9.193,0.0,0.0,0.0],[-1.144],'2187MHz')   
    CAL_1GC_BAD_FREQS = ['*:1700~1800MHz',    # Lower band edge 
                        '*:2500~2650MHz']     # Upper band edge
    CAL_1GC_BL_FLAG_UVRANGE = '<600'
    CAL_1GC_BL_FREQS = []

elif BAND == 'S1':

    CAL_1GC_FREQRANGE = ''
    CAL_1GC_UVRANGE = '>150m'
    CAL_1GC_0408_MODEL = ([8.244,0.0,0.0,0.0],[-1.138],'2406MHz')   
    CAL_1GC_BAD_FREQS = ['*:1967~2056MHz',    # Lower band edge 
                        '*:2756~2845MHz']     # Upper band edge
    CAL_1GC_BL_FLAG_UVRANGE = '<600'
    CAL_1GC_BL_FREQS = []

elif BAND == 'S2':

    CAL_1GC_FREQRANGE = ''
    CAL_1GC_UVRANGE = '>150m'
    CAL_1GC_0408_MODEL = ([7.468,0.0,0.0,0.0],[-1.133],'2625MHz')   
    CAL_1GC_BAD_FREQS = ['*:2187~2275MHz',    # Lower band edge 
                        '*:2975~3063MHz']     # Upper band edge
    CAL_1GC_BL_FLAG_UVRANGE = '<600'
    CAL_1GC_BL_FREQS = []

elif BAND == 'S3':

    CAL_1GC_FREQRANGE = ''
    CAL_1GC_UVRANGE = '>150m'
    CAL_1GC_0408_MODEL = ([6.822,0.0,0.0,0.0],[-1.128],'2483MHz')   
    CAL_1GC_BAD_FREQS = ['*:2405~2493MHz',    # Lower band edge 
                        '*:3194~3282MHz']     # Upper band edge
    CAL_1GC_BL_FLAG_UVRANGE = '<600'
    CAL_1GC_BL_FREQS = []

elif BAND == 'S4':

    CAL_1GC_FREQRANGE = '*:2900~3000MHz'
    CAL_1GC_UVRANGE = '>150m'     
    CAL_1GC_0408_MODEL = ([6.423,0.0,0.0,0.0],[-1.124],'3000MHz')   
    CAL_1GC_BAD_FREQS = ['*:2600~2690MHz',    # Lower band edge 
                        '*:3420~3600MHz']     # Upper band edge
    CAL_1GC_BL_FLAG_UVRANGE = '<600'
    CAL_1GC_BL_FREQS = []


# LINE modifiers
CAL_1GC_LINE_FILLGAPS = 48

# ------------------------------------------------------------------------
#
# 2GC settings
#


# CASA gaincal settings
CAL_2GC_UVRANGE = '>150m'            # Selection for baselines to include during G solving
CAL_2GC_PSOLINT = '64s'              # Solution interval for phase-only selfcal
CAL_2GC_APSOLINT = 'inf'             # Solution interval for amplitude and phase selfcal

# CubiCal
CAL_2GC_DELAYCAL_PARSET = DATA+'/cubical/2GC_delaycal.parset'


# ------------------------------------------------------------------------
#
# 3GC peeling settings
#

CAL_3GC_PEEL_NCHAN = 32
CAL_3GC_PEEL_BRIGGS = -0.6
CAL_3GC_PEEL_DIR1COLNAME = 'DIR1_DATA'
CAL_3GC_PEEL_REGION = ''  # Specify DS9 peeling region 
                          # Leave blank to search for <fieldname>*peel*.reg in the current path
CAL_3GC_PEEL_PARSET = DATA+'/cubical/3GC_peel.parset'
CAL_3GC_FACET_REGION = '' # Specify DS9 region to define tessel centres
                          # Leave blank to search for <fieldname>*facet*.reg in the current path
                          # Regions specified here and above will apply to all fields, and so can
                          # be used to e.g. peel the same source from a compact mosaic rather than
                          # having to provide multiple copies of the same region on a per-field basis


# ------------------------------------------------------------------------
#
# Flag settings
#

SAVE_FLAGS = False


# ------------------------------------------------------------------------
#
# wsclean defaults
#
# General
WSC_MEM = 90
WSC_ABSMEM = -1 # in GB; mem is used if absmem is negative, calculated automatically for HPC, see absmem_helper
WSC_CONTINUE = False
WSC_PARALLELREORDERING = 8
# Outputs
WSC_MAKEPSF = False
WSC_NODIRTY = False
WSC_SOURCELIST = True
# Data selection
WSC_FIELD = 0
WSC_STARTCHAN = -1
WSC_ENDCHAN = -1
WSC_MINUVL = ''
WSC_MAXUVL = ''
WSC_EVEN = False
WSC_ODD = False
WSC_INTERVAL0 = None
WSC_INTERVAL1 = None
WSC_INTERVALSOUT = None
# Image dimensions
WSC_IMSIZE = 10240
WSC_CELLSIZE = '1.1asec'
# Gridding / degridding
WSC_USEWGRIDDER = True
WSC_WGRIDDERACCURACY = 5e-5
WSC_BDA = False
WSC_BDAFACTOR = 10
WSC_NOMODEL = False
WSC_NWLAYERSFACTOR = 5
WSC_PADDING = 1.2
WSC_USEIDG = False # use image-domain gridder (not useable yet)
WSC_IDGMODE = 'CPU'
WSC_PREDICTCHANNELS = 64
# Weighting
WSC_BRIGGS = -0.3
WSC_TAPERGAUSSIAN = ''
# Deconvolution
WSC_PARALLELDECONVOLUTION = 2560
WSC_MULTISCALE = False
WSC_SCALES = '0,3,9'
WSC_NITER = 80000
WSC_GAIN = 0.15
WSC_MGAIN = 0.9
WSC_CHANNELSOUT = 8
WSC_FITSPECTRALPOL = 4
WSC_JOINCHANNELS = True
WSC_NONEGATIVE = False
WSC_STOPNEGATIVE = False
WSC_CIRCULARBEAM = False
# Masking
WSC_MASK = 'auto'
WSC_THRESHOLD = 1e-6
WSC_AUTOMASK = 4.0
WSC_AUTOTHRESHOLD = 1.0
WSC_LOCALRMS = True

# Band modifiers
if BAND == 'UHF':
    WSC_CELLSIZE = '1.7asec'
    WSC_BRIGGS = -0.5
    WSC_BDAFACTOR = 4
    WSC_NWLAYERSFACTOR = 5
if BAND == 'S0':
    WSC_CELLSIZE = '0.65asec'
if BAND == 'S1':
    WSC_CELLSIZE = '0.61asec'
if BAND == 'S2':
    WSC_CELLSIZE = '0.58asec'
if BAND == 'S3':
    WSC_CELLSIZE = '0.54asec'    
if BAND == 'S4':
    WSC_CELLSIZE = '0.5asec'


# ------------------------------------------------------------------------
#
# MakeMask defaults
#


MAKEMASK_THRESH = 6.0
MAKEMASK_BOXSIZE = 500
MAKEMASK_SMALLBOX = 50
MAKEMASK_ISLANDSIZE = 30000
MAKEMASK_DILATION = 3


# ------------------------------------------------------------------------
#
# DDFacet defaults
#


# [Data]
DDF_DDID = 'D*'
DDF_FIELD = 'F0'
DDF_COLNAME = 'CORRECTED_DATA'
DDF_CHUNKHOURS = 0.5
DDF_DATASORT = 1
# [Predict]
DDF_PREDICTCOLNAME = '' # MODEL_DATA or leave empty to disable predict
DDF_INITDICOMODEL = ''
# [Output]
DDF_OUTPUTALSO = 'oenNS'
DDF_OUTPUTIMAGES = 'DdPMmRrIikz' # add 'A' to re-include spectral index map
DDF_OUTPUTCUBES = 'MmRi' # output intrinsic and apparent resid and model cubes
# [Image]
DDF_NPIX = 10125
DDF_CELL = 1.1
# [Facets]
DDF_DIAMMAX = 0.25
DDF_DIAMMIN = 0.05
DDF_NFACETS = 4 # crank this up (32?) to get better beam resolution if FITS beam is used
DDF_PSFOVERSIZE = 1.5
DDF_PADDING = 3.0 # padding needs increasing from default if NFacets is raised to prevent aliasing
# [Weight]
DDF_ROBUST = 0.0
# [Convolution Functions]
# DDF_NW = 100 # Increase for strong off-axis sources
# [Comp]
DDF_SPARSIFICATION = '0' # [100,30,10] grids every 100th visibility on major cycle 1, every 30th on cycle 2, etc.
# [Parallel]
DDF_NCPU = 8
# [Cache]
DDF_CACHERESET = 0
DDF_CACHEDIR = '.'
DDF_CACHEHMP = 1
# [Beam]
DDF_BEAM = '' # specify beam cube of the form: meerkat_pb_jones_cube_95channels_$(xy)_$(reim).fits
DDF_BEAMNBAND= 10
DDF_DTBEAMMIN = 1
DDF_FITSPARANGLEINCDEG = 0.5
DDF_BEAMCENTRENORM = True
DDF_FEEDSWAP = 1
DDF_BEAMSMOOTH = False
# [Freq]
DDF_NBAND = 8
DDF_NDEGRIDBAND = 8
# [DDESolutions]
DDF_DDSOLS = ''
DDF_DDMODEGRID = 'AP'
DDF_DDMODEDEGRID = 'AP'
# [Deconv]
DDF_GAIN = 0.15
DDF_FLUXTHRESHOLD = 3e-6
DDF_CYCLEFACTOR = 0
DDF_RMSFACTOR = 3.0	
DDF_DECONVMODE = 'hogbom'
DDF_SSD_DECONVPEAKFACTOR = 0.001
DDF_SSD_MAXMAJORITER = 3
DDF_SSD_MAXMINORITER = 120000
DDF_SSD_ENLARGEDATA = 0
DDF_HOGBOM_DECONVPEAKFACTOR = 0.1
DDF_HOGBOM_MAXMAJORITER = 5
DDF_HOGBOM_MAXMINORITER = 100000
DDF_HOGBOM_POLYFITORDER = 4
# [Mask]
DDF_MASK = 'auto' # 'auto' enables automasking 
                  # 'fits' uses the first *.mask.fits in the current folder
                  # otherwise pass a filename to use a specific FITS image
# [Misc]
DDF_MASKSIGMA = 4.5
DDF_CONSERVEMEMORY = 1


# Band modifiers
if BAND == 'UHF':
    DDF_CELL = 1.7
    DDF_ROBUST = -0.5
if BAND == 'S0':
    DDF_CELL = 0.65
if BAND == 'S1':
    DDF_CELL = 0.61
if BAND == 'S2':
    DDF_CELL = 0.58
if BAND == 'S3':
    DDF_CELL = 0.54
if BAND == 'S4':
    DDF_CELL = 0.5


# ------------------------------------------------------------------------
#
# killMS defaults
#


# [VisData]
KMS_TCHUNK = 0.5
KMS_INCOL = 'CORRECTED_DATA'
KMS_OUTCOL = 'MODEL_DATA'
# [Beam]
KMS_BEAM = ''
KMS_BEAMAT = 'Facet'
KMS_DTBEAMMIN = 1
KMS_CENTRENORM = 1
KMS_NCHANBEAMPERMS = 95
KMS_FITSPARANGLEINCDEG = 0.5
KMS_FITSFEEDSWAP = 1
# [ImageSkyModel]
KMS_DICOMODEL = ''
KMS_MAXFACETSIZE = 0.25
# [DataSelection]
KMS_UVMINMAX = '0.15,8500.0'
KMS_FIELDID = 0
KMS_DDID = 0
# [Actions]
KMS_NCPU = 16
KMS_DOBAR = 0
KMS_DEBUGPDB = 0
# [Solvers]
KMS_SOLVERTYPE = 'KAFCA' # or 'CohJones', note case sensitivity
KMS_DT = 5
KMS_NCHANSOLS = 8
# [KAFCA]
KMS_NITERKF = 9
KMS_COVQ = 0.05


# ------------------------------------------------------------------------
#
# PyBDSF defaults
#


PYBDSF_THRESH_PIX = 5.0
PYBDSF_THRESH_ISL = 3.0
PYBDSF_CATALOGTYPE = 'srl'
PYBDSF_CATALOGFORMAT = 'fits'


# ------------------------------------------------------------------------
#
# ClusterCat defaults
#


CLUSTERCAT_NDIR = 8
CLUSTERCAT_CENTRALRADIUS = 0.0
CLUSTERCAT_NGEN = 100
CLUSTERCAT_FLUXMIN = 0.000001
CLUSTERCAT_NCPU = 8


# ------------------------------------------------------------------------
#
# MeerKAT primary beam models
#


BEAM_L = HOME+'/Beams/meerkat_pb_jones_cube_95channels_$(xy)_$(reim).fits'

