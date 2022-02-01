#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import logging
import numpy
import sys
from pyrap.tables import table
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates import solar_system_ephemeris, EarthLocation, AltAz
from astropy.coordinates import get_body_barycentric, get_body, get_moon


def rad2deg(xx):
    return 180.0*xx/numpy.pi


def get_fields(myms):
    fieldtab = table(myms+'/FIELD',ack=False)
    ids = fieldtab.getcol("SOURCE_ID")
    names = fieldtab.getcol("NAME")
    dirs = fieldtab.getcol("PHASE_DIR")
    return ids,names,dirs


def match_field(ids,names,dirs,i):
    idx = numpy.where(ids == i)[0]
    radec = rad2deg(dirs[idx,0,:])[0]
    return names[i],radec[0],radec[1]


def calcsep(ra0,dec0,ra1,dec1):
    c0 = SkyCoord(ra0*u.deg,dec0*u.deg,frame='fk5')
    c1 = SkyCoord(ra1*u.deg,dec1*u.deg,frame='fk5')
    sep = round(c0.separation(c1).deg,4)
    return sep 


def format_coords(ra0,dec0):
    c = SkyCoord(ra0*u.deg,dec0*u.deg,frame='fk5')
    hms = str(c.ra.to_string(u.hour))
    dms = str(c.dec)
    return hms,dms


def main():

    # MeerKAT
    obs_lat = -30.71323598930457
    obs_lon = 21.443001467965008
    loc = EarthLocation.from_geodetic(obs_lat,obs_lon) #,obs_height,ellipsoid)


    myms = sys.argv[1].rstrip('/')
    maintab = table(myms,ack=False)
    scans = list(numpy.unique(maintab.getcol('SCAN_NUMBER')))
    ids,names,dirs = get_fields(myms)

    logfile = 'sun_'+myms+'.log'
    logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s |  %(message)s', datefmt='%d/%m/%Y %H:%M:%S ')


    logging.info(myms+' | '+str(len(ids))+' fields | '+str(len(scans))+' scans')
    #header = 'Scan  Field        ID    t[iso]                    t[s]                 t0[s]                t1[s]                int0    int1    Duration[m]  N_int'
    header = '# t[iso]                     Scan  Field Name         SunRA[deg]   SunDec[deg]  SunRA[hms]       SunDec[dms]      SunSep[deg]  SunAlt[deg]  MoonRA[deg]  MoonDec[deg] MoonRA[hms]      MoonDec[dms]     MoonSep[deg] MoonAlt[deg]'
    logging.info('-'*len(header))
    logging.info(header)
    logging.info('-'*len(header))
    for scan in scans:
        subtab = maintab.query(query='SCAN_NUMBER=='+str(scan))
        field = numpy.unique(subtab.getcol('FIELD_ID'))[0]
        name,field_ra,field_dec = match_field(ids,names,dirs,field)
        field_hms,field_dms = format_coords(field_ra,field_dec)
        t_scan = numpy.mean(subtab.getcol('TIME'))
        t = Time(t_scan/86400.0,format='mjd')
        with solar_system_ephemeris.set('builtin'):
            sun = get_body('Sun', t, loc)
            moon = get_body('Moon', t, loc)
        sun_ra = sun.ra.value
        sun_dec = sun.dec.value
        sun_altaz = sun.transform_to(AltAz(obstime=t,location=loc))
        sun_alt = sun_altaz.alt.value
        moon_ra = moon.ra.value
        moon_dec = moon.dec.value
        moon_altaz = moon.transform_to(AltAz(obstime=t,location=loc))
        moon_alt = moon_altaz.alt.value
        sun_hms,sun_dms = format_coords(sun_ra,sun_dec)
        moon_hms,moon_dms = format_coords(moon_ra,moon_dec)
        delta_ra_sun = field_ra - sun_ra
        delta_dec_sun = field_dec - sun_dec
        delta_ra_moon = field_ra - moon_ra
        delta_dec_moon = field_dec - moon_dec
        sun_sep = calcsep(field_ra,field_dec,sun_ra,sun_dec)
        moon_sep = calcsep(field_ra,field_dec,moon_ra,moon_dec)
    #   print field,name,sun_sep
        logging.info('%-28s %-5i %-5i %-12s %-12f %-12f %-16s %-16s %-12f %-12f %-12f %-12f %-16s %-16s %-12f %-12f' %
            (t.iso,scan,field,name,sun_ra,sun_dec,sun_hms,sun_dms,sun_sep,sun_alt,moon_ra,moon_dec,moon_hms,moon_dms,moon_sep,moon_alt))

    logging.info('-'*len(header))


if __name__ == "__main__":

    main()