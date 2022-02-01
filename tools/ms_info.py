#!/usr/bin/python
# ian.heywood@physics.ox.ac.uk


import logging
import sys
import numpy
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.time import Time
from pyrap.tables import table
from optparse import OptionParser


def rad2deg(xx):
    return 180.0*xx/numpy.pi


def main():

    parser = OptionParser(usage='%prog [options] msname')
    parser.add_option('--nofield',dest='dofield',help='Do not list FIELD information',action='store_false',default=True)
    parser.add_option('--noscan',dest='doscan',help='Do not list SCAN information',action='store_false',default=True)
    parser.add_option('--nospw',dest='dospw',help='Do not list SPECTRAL_WINDOW information',action='store_false',default=True)
    parser.add_option('--noant',dest='doant',help='Do not list ANTENNA information',action='store_false',default=True)
    parser.add_option('--nocolour',dest='docolour',help='Do not use colour in the terminal output',action='store_false',default=True)
    (options,args) = parser.parse_args()
    dospw = options.dospw
    doant = options.doant
    dofield = options.dofield
    doscan = options.doscan
    docolour = options.docolour

    if len(args) != 1:
            ri('Please specify a Measurement Set')
            sys.exit()
    else:
            myms = args[0].rstrip('/')

    logfile = 'msinfo_'+myms+'.log'

    logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s |  %(message)s', datefmt='%d/%m/%Y %H:%M:%S ')
    stream = logging.StreamHandler()
    stream.setLevel(logging.DEBUG)
    streamformat = logging.Formatter('%(asctime)s |  %(message)s', datefmt='%d/%m/%Y %H:%M:%S ')
    stream.setFormatter(streamformat)
    mylogger = logging.getLogger(__name__)
    mylogger.setLevel(logging.DEBUG)
    mylogger.addHandler(stream)

    mylogger.info('')
    mylogger.info('--MS: '+myms)
    mylogger.info('')

    # ------- GETTING INFORMATION -------

    fldtab = table(myms+'/FIELD',ack=False)
    names = fldtab.getcol('NAME')
    ids = fldtab.getcol('SOURCE_ID')
    dirs = fldtab.getcol('PHASE_DIR')
    fldtab.done()

    statetab = table(myms+'/STATE',ack=False)
    modes = statetab.getcol('OBS_MODE')
    statetab.done()

    maintab = table(myms,ack=False)
    meanexp = round(numpy.mean(maintab.getcol('EXPOSURE')),2)
    times = maintab.getcol('TIME')
    t0 = times[0]
    t1 = times[-1]
    length = round((t1 - t0),0)

    start_time = Time(t0/86400.0,format='mjd').iso
    end_time = Time(t1/86400.0,format='mjd').iso

    chanwidths = []
    spwtab = table(myms+'/SPECTRAL_WINDOW',ack=False)
    nspw = len(spwtab)
    spwnames = spwtab.getcol('NAME')
    spwfreqs = spwtab.getcol('REF_FREQUENCY')
    for name in spwnames:
            subtab = spwtab.query(query='NAME=="'+name+'"')
            chanwidth = subtab.getcol('CHAN_WIDTH')[0][0]/1e6
            chanwidths.append(chanwidth)
    nchans = spwtab.getcol('NUM_CHAN')
    spwtab.done()

    scanlist = []
    scans = numpy.unique(maintab.getcol('SCAN_NUMBER'))
    for sc in scans:
            subtab = maintab.query(query='SCAN_NUMBER=='+str(sc))
            st0 = subtab.getcol('TIME')[0]
            st1 = subtab.getcol('TIME')[-1]
            sfield = numpy.unique(subtab.getcol('FIELD_ID'))[0]
            if 'STATE_ID' in subtab.colnames():
                ii = numpy.unique(subtab.getcol('STATE_ID'))
                if ii[0] > 0:
                    sintent = modes[ii[0]]
                else:
                    sintent = 'None'
            else:
                sintent = 'None'
            st = round((st1-st0),0)
            nint = int(st/meanexp)
            scanlist.append((sc,sfield,st,nint,sintent))

    field_integrations = []
    for fld in ids:
        tot = 0.0
        for sc in scanlist:
            if sc[1] == fld:
                tot += float(sc[2])
        field_integrations.append((fld,tot))

    anttab = table(myms+'/ANTENNA',ack=False)
    nant = len(anttab)
    antpos = anttab.getcol('POSITION')
    antnames = anttab.getcol('NAME')
    anttab.done()

    A1 = numpy.unique(maintab.getcol('ANTENNA1'))
    A2 = numpy.unique(maintab.getcol('ANTENNA2'))

    usedants = numpy.unique(numpy.concatenate((A1,A2)))

    maintab.done()

    # ------- PRINTING INFORMATION -------

    mylogger.info('     Observation start:        '+start_time)
    mylogger.info('     Observation end:          '+end_time)
    mylogger.info('')

    mylogger.info('     Track length:             '+str(length)+' s ('+str(round((length/3600.0),2))+' h)')
    mylogger.info('     Mean integration time:    '+str(meanexp)+' s')
    mylogger.info('')


    if dofield:

        mylogger.info('---- FIELDS:')
        mylogger.info('')
        mylogger.info('     ROW   SOURCE_ID  NAME                  RA[hms]           DEC[dms]          RA[deg]   DEC[deg]  EXP[s]    EXP[h]')

        for i in range(0,len(names)):
            ra_rad = float(dirs[i][0][0])
            dec_rad = float(dirs[i][0][1])
            ra_deg = str(round(rad2deg(dirs[i][0][0]),4))
            dec_deg = str(round(rad2deg(dirs[i][0][1]),4))
            coord = SkyCoord(ra_rad,dec_rad,frame='icrs',unit='rad')
            coord_str = coord.to_string('hmsdms')
            ra_str = coord_str.split(' ')[0]
            dec_str = coord_str.split(' ')[1]
            exp_s = str(round(field_integrations[i][1],0))
            exp_h = str(round(field_integrations[i][1]/3600.0,3))
            
            mylogger.info('     %-6s%-11s%-22s%-18s%-18s%-10s%-10s%-10s%-10s' % (i,str(ids[i]),names[i],ra_str,dec_str,ra_deg,dec_deg,exp_s,exp_h))

        mylogger.info('')

    if doscan:

        mylogger.info('---- SCANS:')
        mylogger.info('')
        mylogger.info('     SCAN  SOURCE_ID  NAME                  LENGTH[s]         INTS        INTENT')

        for sc in scanlist:
            mylogger.info('     %-6s%-11s%-22s%-18s%-12s%s' % (sc[0],sc[1],names[sc[1]],sc[2],sc[3],sc[4]))

        mylogger.info('')

    if dospw:

        mylogger.info('---- SPECTRAL WINDOWS:')
        mylogger.info('')
        mylogger.info('     ROW   CHANS      WIDTH[MHz]            REF_FREQ[MHz]')

        for i in range(0,nspw):
                mylogger.info('     %-6s%-11s%-22s%-14s' % (i,str(nchans[i]),str(chanwidths[i]),str(spwfreqs[i]/1e6)))

        mylogger.info('')

    if doant:

        mylogger.info('---- ANTENNAS:')
        mylogger.info('')
        mylogger.info('     '+str(len(usedants))+' / '+str(nant)+' antennas in the main table')
        mylogger.info('')
        mylogger.info('     ROW   NAME       POSITION')

        for i in range(0,nant):
                if i in usedants:
                        mylogger.info('     %-6s%-11s%-14s' % (i,(antnames[i]),str(antpos[i])))
                else:
                        mylogger.info('     %-6s%-11s%-14s' % (i,(antnames[i]),str(antpos[i])))

        mylogger.info('')

if __name__ == '__main__':
        main()
