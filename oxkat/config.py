#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import os


CWD = os.getcwd()
HOME = os.path.expanduser('~')


# ------------------------------------------------------------------------
#
# Singularity containers
#


IDIA_CONTAINER_PATH = HOME+'/containers/'
CHPC_CONTAINER_PATH = HOME+'/lustre/containers'
NODE_CONTAINER_PATH = HOME+'/containers/'


CASA_PATTERN = 'casa'
CLUSTERCAT_PATTERN = 'ddfacet-0.4.1'
CODEX_PATTERN = 'codex-africanus'
CUBICAL_PATTERN = 'cubical'
DDFACET_PATTERN = 'ddfacet-0.5.2'
KILLMS_PATTERN = 'killms'
PYBDSF_PATTERN = 'pybdsf'
RAGAVI_PATTERN = 'ragavi'
SHADEMS_PATTERN = 'shadems'
TRICOLOUR_PATTERN = 'tricolour'
WSCLEAN_PATTERN = 'wsclean'
WSCLEANIDG_PATTERN = 'wsclean*idg'


# ------------------------------------------------------------------------
#
# Paths for components and OUTPUTS
#


OXKAT = CWD+'/oxkat'
PARSETS = CWD+'/parsets'
TOOLS = CWD+'/tools'

GAINPLOTS = CWD+'/GAINPLOTS'
GAINTABLES = CWD+'/GAINTABLES'
IMAGES = CWD+'/IMAGES'
LOGS = CWD+'/LOGS'
SCRIPTS = CWD+'/SCRIPTS'
VISPLOTS = CWD+'/VISPLOTS'


# ------------------------------------------------------------------------
#
# MeerKAT primary beam models
#


BEAM_L = HOME+'/Beams/meerkat_pb_jones_cube_95channels_$(xy)_$(reim).fits'


# ------------------------------------------------------------------------
#
# Slurm settings
#

SLURM_DEFAULTS = {
	'TIME': '12:00:00',
	'PARTITION': 'Main',
	'NTASKS': '1',
	'NODES': '1',
	'CPUS': '8',
	'MEM': '64GB'
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


# ------------------------------------------------------------------------
#
# PBS settings
#

PBS_DEFAULTS = {
	'PROGRAM': 'ASTR1301',
	'WALLTIME': '12:00:00',
	'QUEUE': 'serial',
	'NODES': '1',
	'PPN': '8',
	'MEM': '64gb'
}

PBS_TRICOLOUR = {
	'PROGRAM': 'ASTR1301',
	'WALLTIME': '06:00:00',
	'QUEUE': 'serial',
	'NODES': '1',
	'PPN': '23',
	'MEM': '120gb'
}

PBS_WSCLEAN = {
	'PROGRAM': 'ASTR1301',
	'WALLTIME': '12:00:00',
	'QUEUE': 'serial',
	'NODES': '1',
	'PPN': '23',
	'MEM': '120gb'
}


# ------------------------------------------------------------------------
#
# 1GC defaults
#


PRE_FIELDS = '' # comma-separated list of fields to select from raw MS
PRE_NCHANS = 1024 # integer number of channels in working MS
PRE_TIMEBIN = '8s' # integration time in working MS



# ------------------------------------------------------------------------
#
# wsclean defaults
#


WSC_CONTINUE = False
WSC_FIELD = 0
WSC_STARTCHAN = -1
WSC_ENDCHAN = -1
WSC_CHANNELSOUT = 8
WSC_IMSIZE = 10240
WSC_CELLSIZE = '1.1asec'
WSC_BRIGGS = -0.3
WSC_NITER = 120000
WSC_GAIN = 0.1
WSC_MGAIN = 0.85
WSC_MULTISCALE = False
WSC_SCALES = '0,3,9'
WSC_SOURCELIST = True
WSC_BDA = False
WSC_BDAFACTOR = 24
WSC_NWLAYERSFACTOR = 3
WSC_PADDING = 1.2
WSC_NOMODEL = False
WSC_MASK = 'auto'
WSC_THRESHOLD = 1e-6
WSC_AUTOTHRESHOLD = 0.3
WSC_AUTOMASK = 5.0
WSC_FITSPECTRALPOL = 4
WSC_PREDICTCHANNELS = 64
WSC_MEM = 95
WSC_USEIDG = False # use image-domain gridder
WSC_IDGMODE = 'CPU'
WSC_PARALLELDECONVOLUTION = 0 # 0 or specify max facet size


# ------------------------------------------------------------------------
#
# MakeMask defaults
#


MAKEMASK_THRESH = 6.0
MAKEMASK_DILATION = 2


# ------------------------------------------------------------------------
#
# DDFacet defaults
#


# [Data]
DDF_DDID = 'D*'
DDF_FIELD = 'F0'
DDF_COLNAME = 'CORRECTED_DATA'
DDF_CHUNKHOURS = 2
DDF_DATASORT = 1
# [Predict]
DDF_PREDICTCOLNAME = 'MODEL_DATA'
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
DDF_NFACETS = 8 # crank this up (32?) to get better beam resolution if FITS beam is used
DDF_PSFOVERSIZE = 1.5
DDF_PADDING = 1.7 # padding needs increasing from default if NFacets is raised to prevent aliasing
# [Weight]
DDF_ROBUST = -0.3
# [Comp]
DDF_SPARSIFICATION = '0' # [100,30,10] grids every 100th visibility on major cycle 1, every 30th on cycle 2, etc.
# [Parallel]
DDF_NCPU = 32
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
DDF_GAIN = 0.12
DDF_THRESHOLD = 0.0
DDF_CYCLEFACTOR = 0
DDF_RMSFACTOR = 3.0	
DDF_DECONVMODE = 'hogbom'
DDF_SSD_DECONVPEAKFACTOR = 0.001
DDF_SSD_MAXMAJORITER = 3
DDF_SSD_MAXMINORITER = 120000
DDF_SSD_ENLARGEDATA = 0
DDF_HOGBOM_DECONVPEAKFACTOR = 0.15
DDF_HOGBOM_MAXMAJORITER = 10
DDF_HOGBOM_MAXMINORITER = 100000
DDF_HOGBOM_POLYFITORDER = 4
# [Mask]
DDF_MASK = 'auto' # 'auto' enables automasking 
                  # 'fits' uses the first *.mask.fits in the current folder
                  # otherwise pass a filename to use a specific FITS image
# [Misc]
DDF_MASKSIGMA = 5.5
DDF_CONSERVEMEMORY = 1


# ------------------------------------------------------------------------
#
# killMS defaults
#


# [VisData]
KMS_TCHUNK = 0.2
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
KMS_MAXFACETSIZE = 0.25
# [DataSelection]
KMS_UVMINMAX = '0.15,8500.0'
KMS_FIELDID = 0
KMS_DDID = 0
# [Actions]
KMS_NCPU = 32
KMS_DOBAR = 0
# [Solvers]
KMS_SOLVERTYPE = 'CohJones'
KMS_DT = 12
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


CLUSTERCAT_NDIR = 7
CLUSTERCAT_CENTRALRADIUS = 0.15
CLUSTERCAT_NGEN = 100
CLUSTERCAT_FLUXMIN = 0.000001
CLUSTERCAT_NCPU = 32
