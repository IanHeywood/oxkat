#!/usr/bin/env python3
# Per-channel weight calibration for the target field(s) after 1GC.
#
# CASA's applycal(calwt=True) scales WEIGHT_SPECTRUM by a channel-averaged
# gain amplitude per baseline and correlation, so the bandpass shape never
# makes it into the weights. Here we recompute the calibrated weights per
# row, channel and correlation as
#
#     WEIGHT_SPECTRUM = |g_p g_q|^2 / SIGMA_SPECTRUM^2
#
# where |g_p g_q| = |DATA / CORRECTED_DATA|. Taking the gain product from the
# visibilities themselves picks up exactly what applycal applied (all tables,
# all interpolation), but assumes the applied Jones terms are diagonal.
# SIGMA_SPECTRUM describes the uncalibrated DATA and is not touched by
# applycal, so this step is idempotent and can be re-run after another
# applycal. WEIGHT is set to the mean of WEIGHT_SPECTRUM over unflagged
# channels.


import json
import numpy
import sys
from optparse import OptionParser
from pyrap.tables import table


def get_field_ids(msname,fieldnames):

    ft = table(msname+'::FIELD',ack=False)
    names = list(ft.getcol('NAME'))
    ft.close()
    ids = []
    for name in fieldnames:
        if name in names:
            ids.append(names.index(name))
        else:
            print('Field '+name+' not found in '+msname+', skipping')
    return ids


def calibrate_weights(msname,field,rowchunk):

    t0 = table(msname,readonly=False,ack=False)
    colnames = t0.colnames()
    for col in ['DATA','CORRECTED_DATA','WEIGHT_SPECTRUM']:
        if col not in colnames:
            print(col+' not present in MS')
            sys.exit(1)
    if 'SIGMA_SPECTRUM' in colnames:
        sigcol = 'SIGMA_SPECTRUM'
    else:
        print('No SIGMA_SPECTRUM, using SIGMA')
        sigcol = 'SIGMA'

    tt = t0.query(query='FIELD_ID=='+str(field))
    nrows = tt.nrows()
    print('FIELD_ID '+str(field)+': '+str(nrows)+' rows')

    for start in range(0,nrows,rowchunk):
        nr = min(rowchunk,nrows-start)
        data = tt.getcol('DATA',startrow=start,nrow=nr)
        corr = tt.getcol('CORRECTED_DATA',startrow=start,nrow=nr)
        sig = tt.getcol(sigcol,startrow=start,nrow=nr).astype(numpy.float64)
        flag = tt.getcol('FLAG',startrow=start,nrow=nr)
        wtspec = tt.getcol('WEIGHT_SPECTRUM',startrow=start,nrow=nr)

        if sigcol == 'SIGMA':
            sig = numpy.broadcast_to(sig[:,None,:],data.shape)

        absdata = numpy.abs(data).astype(numpy.float64)
        abscorr = numpy.abs(corr).astype(numpy.float64)
        good = (absdata > 0.0) & (abscorr > 0.0) & (sig > 0.0) & numpy.isfinite(abscorr)

        # Leave the existing weights where the gain product can't be recovered
        gg2 = numpy.where(good,(absdata/numpy.where(good,abscorr,1.0))**2,0.0)
        newwt = numpy.where(good,gg2/numpy.where(good,sig,1.0)**2,wtspec)
        wtspec = newwt.astype(numpy.float32)

        unflagged = ~flag
        nunflagged = unflagged.sum(axis=1)
        wt = numpy.where(nunflagged > 0,
            (wtspec*unflagged).sum(axis=1)/numpy.maximum(nunflagged,1),
            wtspec.mean(axis=1)).astype(numpy.float32)

        tt.putcol('WEIGHT_SPECTRUM',wtspec,startrow=start,nrow=nr)
        tt.putcol('WEIGHT',wt,startrow=start,nrow=nr)
        print('Rows '+str(start)+' to '+str(start+nr-1)+' done')

    tt.close()
    t0.close()


def main():

    parser = OptionParser(usage='%prog [options] [msname]')
    parser.add_option('--fields',dest='fields',help='Comma-separated field names (default = targets in project_info.json)',default='')
    parser.add_option('--rowchunk',dest='rowchunk',help='Number of rows per chunk (default = 10000)',default=10000)
    (options,args) = parser.parse_args()

    with open('project_info.json') as f:
        project_info = json.load(f)

    if len(args) == 1:
        msname = args[0].rstrip('/')
    else:
        msname = str(project_info['working_ms'])

    if options.fields != '':
        fieldnames = options.fields.split(',')
    else:
        fieldnames = [str(xx) for xx in project_info['target_names']]

    for field in get_field_ids(msname,fieldnames):
        calibrate_weights(msname,field,int(options.rowchunk))


if __name__ == "__main__":

    main()
