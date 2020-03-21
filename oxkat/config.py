#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import os

CWD = os.getcwd()
HOME = os.path.expanduser('~')


# ------------------------------------------------------------------------
#
# CONTAINER SETUP
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
TRICOLOUR_PATTERN = 'tricolour'
WSCLEAN_PATTERN = 'wsclean'


# ------------------------------------------------------------------------
#
# PATHS FOR COMPONENTS AND OUTPUTS
#


OXKAT = CWD+'/oxkat'
PARSETS = CWD+'/parsets'
TOOLS = CWD+'/tools'

GAINPLOTS = CWD+'/gainplots'
#GAINTABLES = CWD+'/gaintables'
IMAGES = CWD+'/images'
LOGS = CWD+'/logs'
SCRIPTS = CWD+'/scripts'


# ------------------------------------------------------------------------
#
# MeerKAT primary beam models
#


BEAM_L = HOME+'/Beams/meerkat_pb_jones_cube_95channels_$(xy)_$(reim).fits'


# ------------------------------------------------------------------------
#
# SLURM DEFAULTS
#


SLURM_TIME = '24:00:00'
SLURM_PARTITION = 'Main'
SLURM_NTASKS = '1'
SLURM_NODES = '1'
SLURM_CPUS = '32'
SLURM_MEM = '236GB'


# ------------------------------------------------------------------------
#
# PBS DEFAULTS
#


PBS_PROGRAM = 'ASTR1301'
PBS_WALLTIME = '12:00:00'
PBS_QUEUE = 'serial'
PBS_NODES = '1'
PBS_PPN = '8'
PBS_MEM = '64gb'


# ------------------------------------------------------------------------
#
# WSCLEAN DEFAULTS
#


WSC_STARTCHAN = -1
WSC_ENDCHAN = -1
WSC_CHANNELSOUT = 8
WSC_IMSIZE = 10240
WSC_CELLSIZE = '1.1asec'
WSC_BRIGGS = -0.3
WSC_NITER = 120000
WSC_MULTISCALE = False
WSC_SCALES = '0,3,9'
WSC_SOURCELIST = True
WSC_BDA = False
WSC_BDAFACTOR = 24
WSC_NOMODEL = False
WSC_MASK = 'auto'
WSC_AUTOTHRESHOLD = 0.3
WSC_AUTOMASK = 5.0
WSC_FITSPECTRALPOL = 4
WSC_PREDICTCHANNELS = 64
WSC_MEM = 95


# ------------------------------------------------------------------------
#
# MAKEMASK DEFAULTS
#


MAKEMASK_THRESH = 6.0
MAKEMASK_DILATION = 3


# ------------------------------------------------------------------------
#
# DDFACET DEFAULTS
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
DDF_OUTPUTALSO = 'nNs'
DDF_OUTPUTIMAGES = 'DdPMRIikz' # add 'A' to re-include spectral index map
DDF_OUTPUTCUBES = 'MmRi' # output intrinsic and apparent resid and model cubes
# [Image]
DDF_NPIX = 10215
DDF_CELL = 1.1
# [Predict]
DDF_DIAMMAX = 0.25
DDF_DIAMMIN = 0.05
DDF_NFACETS = 32
DDF_PSFOVERSIZE = 1.5
# [Weight]
DDF_ROBUST = -0.3
# [Comp]
DDF_SPARSIFICATION = '0' # [100,30,10]
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
DDF_DECONVMODE = 'hogbom'
DDF_SSD_DECONVPEAKFACTOR = 0.001
DDF_SSD_MAXMAJORITER = 3
DDF_SSD_MAXMINORITER = 120000
DDF_SSD_ENLARGEDATA = 0
DDF_HOGBOM_DECONVPEAKFACTOR = 0.4
DDF_HOGBOM_MAXMAJORITER = 10
DDF_HOGBOM_MAXMINORITER = 40000
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
# KILLMS DEFAULTS
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
# PYBDSF DEFAULTS
#


PYBDSF_THRESH_PIX = 5.0
PYBDSF_THRESH_ISL = 3.0
PYBDSF_CATALOGTYPE = 'srl'
PYBDSF_CATALOGFORMAT = 'fits'


# ------------------------------------------------------------------------
#
# CLUSTERCAT DEFAULTS
#


CLUSTERCAT_NDIR = 7
CLUSTERCAT_CENTRALRADIUS = 0.15
CLUSTERCAT_NGEN = 100
CLUSTERCAT_FLUXMIN = 0.000001
CLUSTERCAT_NCPU = 32
