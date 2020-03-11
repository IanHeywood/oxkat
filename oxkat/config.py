#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import os
CWD = os.getcwd()


# ------------------------------------------------------------------------
#
# PATHS FOR COMPONENTS AND OUTPUTS
#


OXKAT = CWD+'/oxkat'
PARSETS = CWD+'/parsets'
TOOLS = CWD+'/tools'

SCRIPTS = CWD+'/scripts'
LOGS = CWD+'/logs'
GAINPLOTS = CWD+'/gainplots'

BEAM = '~/Beams/meerkat_pb_jones_cube_95channels_$(xy)_$(reim).fits'


# ------------------------------------------------------------------------
#
# CONTAINER SETUP
#


IDIA_CONTAINER_PATH = '~/containers/'
CHPC_CONTAINER_PATH = '/home/iheywood/lustre/containers'
NODE_CONTAINER_PATH = '~/containers/'


CASA_PATTERN = 'casa'
CLUSTERCAT_PATTERN = 'ddfacet-0.5.2'
CODEX_PATTERN = 'codex-africanus'
CUBICAL_PATTERN = 'cubical'
DDFACET_PATTERN = 'ddfacet-0.4.1'
KILLMS_PATTERN = 'killms'
PYBDSF_PATTERN = 'pybdsf'
RAGAVI_PATTERN = 'ragavi'
TRICOLOUR_PATTERN = 'tricolour'
WSCLEAN_PATTERN = 'wsclean'


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
PBS_WALLTIME = '24:00:00'
PBS_QUEUE = 'serial'
PBS_NODES = '1'
PBS_PPN = '23'
PBS_MEM = '120gb'


# ------------------------------------------------------------------------
#
# WSCLEAN DEFAULTS
#


WSC_STARTCHAN = -1
WSC_ENDCHAN = -1
WSC_CHANOUT = 8
WSC_IMSIZE = 10240
WSC_CELLSIZE = '1.1asec'
WSC_BRIGGS = -0.3
WSC_NITER = 120000
WSC_MULTISCALE = False
WSC_SCALES = '0,3,9'
WSC_SOURCELIST = True
WSC_BDA = False
WSC_NOMODEL = False
WSC_MASK = 'auto'
WSC_AUTOTHRESHOLD = 0.3
WSC_AUTOMASK = 5.0
WSC_FITSPECTRALPOL = 4
WSC_PREDICTCHANNELS = 64


# ------------------------------------------------------------------------
#
# MAKEMASK DEFAULTS
#


MAKEMASK_THRESH = 6.0


# ------------------------------------------------------------------------
#
# DDFACET DEFAULTS
#


DDF_DDID = 'D*'
DDF_FIELD = 'F0'
DDF_CHUNKHOURS = 2
DDF_COLNAME = 'CORRECTED_DATA'
DDF_PREDICTCOLNAME = 'MODEL_DATA'
DDF_OUTPUTALSO = 'nNs'
DDF_NCPU = 32
#
DDF_SSD_MAXMINORITER = 120000
DDF_SSD_MAXMAJORITER = 3
#
DDF_HOGBOM_MAXMINORITER = 40000
DDF_HOGBOM_MAXMAJORITER = 10
DDF_HOGBOM_POLYFITORDER = 4
DDF_HOGBOM_DECONVPEAKFACTOR = 0.4
#
DDF_PSFOVERSIZE = 1.5
DDF_ROBUST = -0.3
DDF_NPIX = 10215
DDF_CELL = 1.1
DDF_NFACETS = 32
DDF_NDEGRIDBAND = 8
DDF_BEAM = ''
DDF_BEAMNBAND= 10
DDF_DTBEAMMIN = 1
DDF_FEEDSWAP = 1
DDF_BEAMCENTRENORM = True
DDF_FITSPARANGLEINCDEG = 0.5
DDF_NBAND = 8
DDF_MASK = 'auto'
DDF_MASKSIGMA = 5.5
DDF_CACHERESET = 0
DDF_DDSOLS = ''
DDF_INITDICOMODEL = ''


# ------------------------------------------------------------------------
#
# KILLMS DEFAULTS
#


KMS_INCOL = 'CORRECTED_DATA'
KMS_TCHUNK = 0.2
KMS_DT = 12
KMS_BEAM = ''


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
