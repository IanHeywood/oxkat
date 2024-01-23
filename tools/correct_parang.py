# This script was written by Ben Hugo (SARAO / RATT)

#!/usr/bin/env python3
import ephem
import numpy as np
import datetime
import argparse
import logging
from pyrap.tables import table as tbl
from pyrap.tables import taql
from pyrap.quanta import quantity
from pyrap.measures import measures
from astropy.coordinates import SkyCoord
from astropy import units
import pytz

def create_logger():
    """ Create a console logger """
    log = logging.getLogger("Parangle corrector")
    cfmt = logging.Formatter(('%(name)s - %(asctime)s %(levelname)s - %(message)s'))
    log.setLevel(logging.DEBUG)
    log.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(cfmt)

    log.addHandler(console)

    return log, console, cfmt

log, log_console_handler, log_formatter = create_logger()

def add_column(table, col_name, like_col="DATA", like_type=None):
    """
    Lifted from ratt-ru/cubical
    Inserts a new column into the measurement set.
    Args:
        col_name (str):
            Name of target column.
        like_col (str, optional):
            Column will be patterned on the named column.
        like_type (str or None, optional):
            If set, column type will be changed.
    Returns:
        bool:
            True if a new column was inserted, else False.
    """

    if col_name not in table.colnames():
        # new column needs to be inserted -- get column description from column 'like_col'
        desc = table.getcoldesc(like_col)

        desc[str('name')] = str(col_name)
        desc[str('comment')] = str(desc['comment'].replace(" ", "_"))  # got this from Cyril, not sure why
        dminfo = table.getdminfo(like_col)
        dminfo[str("NAME")] =  "{}-{}".format(dminfo["NAME"], col_name)

        # if a different type is specified, insert that
        if like_type:
            desc[str('valueType')] = like_type
        table.addcols(desc, dminfo)
        return True
    return False

parser = argparse.ArgumentParser(description="Parallactic corrector for MeerKAT")
parser.add_argument("ms", type=str, help="Database to correct")
parser.add_argument("--field", "-f", dest="field", type=int, default=0, help="Field index to correct")
parser.add_argument("--specialEphem", "-se", dest="ephem", default=None, type=str, help="Use special ephemeris body as defined in PyEphem")
parser.add_argument("--doPlot", "-dp", dest="plot", action="store_true", help="Make plots for specified field")
parser.add_argument("--simulate", "-s", dest="sim", action="store_true", help="Simulate only -- make no modifications to database")
parser.add_argument("--parangstep", "-pas", type=float, dest="stepsize", default=1., help="Parallactic angle correction step size in minutes")
parser.add_argument("--chunksize", "-cs", type=int, dest="chunksize", default=1000, help="Chunk size in rows")
parser.add_argument("--datadiscriptor", "-dd", type=int, dest="ddid", default=0, help="Select data descriptor (SPW)")
parser.add_argument("--applyantidiag", "-ad", dest="flipfeeds", action="store_true", help="Apply anti-diagonal matrix -- flips the visibilty hands")
parser.add_argument("--overridefeedangle", "-fa", dest="fa", default=None, help="Override the receptor angle stored in ::FEED for all antennae")
parser.add_argument("--storecolumn", "-sc", dest="storecolumn", default="CORRECTED_DATA", help="Column to store corrected data to -- default CORRECTED_DATA -- must exist")
parser.add_argument("--rawcolumn", "-rc", dest="rawcolumn", default="DATA", help="Column to read uncorrected data from -- default DATA -- must exist")
parser.add_argument("--noparang", "-npa", dest="noparang", action="store_true", help="Apply no parallactic angle derotation -- useful only to apply feedflip matrix")
parser.add_argument("--invertPA", "-ip", dest="invertpa", action="store_true", help="Apply parallactic angle corruption instead of correction")
parser.add_argument("--crosshandphase", "-chp", dest="crossphase", default=0.0, type=float, help="Apply crosshand phase in degrees")
parser.add_argument("--telescopelat", dest="latitude", default="-30:42:47.41", type=str, help="Telescope latitude dd:mm:ss")
parser.add_argument("--telescopelon", dest="longitude", default="21:26:38.0", type=str, help="Telescope longitude dd:mm:ss")
parser.add_argument("--telescopealt", dest="altitude", default=1054, type=float, help="Telescope altitude in meters")

args = parser.parse_args()

if args.plot:
    from matplotlib import pyplot as plt
    import matplotlib.dates as mdates
    log.info("Enabling plotting")

ephemobservatory = ephem.Observer()
ephemobservatory.lat = args.latitude
ephemobservatory.long = args.longitude
ephemobservatory.elevation = args.altitude
ephemobservatory.epoch = ephem.J2000

with tbl(args.ms, ack=False) as t:
    with taql("select * from $t where FIELD_ID=={}".format(args.field)) as tt:
        def __to_datetimestr(t):
            dt = datetime.datetime.utcfromtimestamp(quantity("{}s".format(t)).to_unix_time())
            return dt.strftime("%Y/%m/%d %H:%M:%S")
        dbtime = tt.getcol("TIME_CENTROID")
        start_time_Z = __to_datetimestr(dbtime.min())
        end_time_Z = __to_datetimestr(dbtime.max())
        log.info("Observation spans '{}' and '{}' UTC".format(
                 start_time_Z, end_time_Z))
dm = measures()
ephemobservatory.date = start_time_Z
st = ephemobservatory.date
ephemobservatory.date = end_time_Z
et = ephemobservatory.date
TO_SEC = 3600*24.0
nstep = int(np.round((float(et)*TO_SEC - float(st)*TO_SEC) / (args.stepsize*60.)))
if not args.noparang:
    log.info("Computing PA in {} steps of {} mins each".format(nstep, args.stepsize))
timepa = time = np.linspace(st,et,nstep)
timepadt = list(map(lambda x: ephem.Date(x).datetime(), time))

with tbl(args.ms+"::ANTENNA", ack=False) as t:
    anames = t.getcol("NAME")
    apos = t.getcol("POSITION")
    aposdm = list(map(lambda pos: dm.position('itrf',*[ quantity(x,'m') for x in pos ]),
                      apos))

if args.ephem:
    with tbl(args.ms+"::FIELD", ack=False) as t:
        fieldnames = t.getcol("NAME")
    fieldEphem = getattr(ephem, args.ephem, None)()
    if not fieldEphem:
        raise RuntimeError("Body {} not defined by PyEphem".format(args.ephem))
    log.info("Overriding stored ephemeris in database '{}' field '{}' by special PyEphem body '{}'".format(
        args.ms, fieldnames[args.field], args.ephem))
else:
    with tbl(args.ms+"::FIELD", ack=False) as t:
        fieldnames = t.getcol("NAME")
        pos = t.getcol("PHASE_DIR")
    skypos = SkyCoord(pos[args.field][0,0]*units.rad, pos[args.field][0,1]*units.rad, frame="fk5")
    rahms = "{0:.0f}:{1:.0f}:{2:.5f}".format(*skypos.ra.hms)
    decdms = "{0:.0f}:{1:.0f}:{2:.5f}".format(skypos.dec.dms[0], abs(skypos.dec.dms[1]), abs(skypos.dec.dms[2]))
    fieldEphem = ephem.readdb(",f|J,{},{},0.0".format(rahms, decdms))
    log.info("Using coordinates of field '{}' for body: J2000, {}, {}".format(fieldnames[args.field],
                                                                              np.rad2deg(pos[args.field][0,0]),
                                                                              np.rad2deg(pos[args.field][0,1])))

az = np.zeros(nstep, dtype=np.float32)
el = az.copy()
ra = az.copy()
#racc = az.copy()
dec = az.copy()
#deccc = az.copy()
arraypa = az.copy()
pa = np.zeros((len(anames), nstep), np.float32)

zenith = dm.direction('AZELGEO','0deg','90deg')
if not args.noparang:
    for ti, t in enumerate(time):
        ephemobservatory.date = t
        t_iso8601 = ephemobservatory.date.datetime().strftime("%Y-%m-%dT%H:%M:%S.%f")
        fieldEphem.compute(ephemobservatory)
        az[ti] = fieldEphem.az
        el[ti] = fieldEphem.alt
        ra[ti] = fieldEphem.a_ra
        dec[ti] = fieldEphem.a_dec
        arraypa[ti] = fieldEphem.parallactic_angle()
        # compute PA per antenna
        field_centre = dm.direction('J2000', quantity(ra[ti],"rad"), quantity(dec[ti],"rad"))
        dm.do_frame(dm.epoch("UTC", quantity(t_iso8601)))
        #dm.doframe(aposdm[0])
        #field_centre = dm.measure(dm.direction('moon'), "J2000")
        #racc[ti] = field_centre["m0"]["value"]
        #deccc[ti] = field_centre["m1"]["value"]
        for ai in range(len(anames)):
           dm.doframe(aposdm[ai])
           pa[ai, ti] = dm.posangle(field_centre,zenith).get_value("rad")
    if args.plot:
        def __angdiff(a, b):
            return ((a-b) + 180) % 360 - 180
        for axl, axd in zip(["Az", "El", "RA", "DEC", "ParAng"],
                            [az, el, ra, dec, pa]):
            hfmt = mdates.DateFormatter('%H:%M')
            fig = plt.figure(figsize=(16,8))
            ax = fig.add_subplot(111)
            ax.set_xlabel("Time UTC")
            ax.set_ylabel("{} [deg]".format(axl))
            if axl == "ParAng":
                ax.errorbar(timepadt,
                            np.rad2deg(np.mean(axd, axis=0)),
                            capsize=2,
                            yerr=0.5*__angdiff(np.rad2deg(axd.max(axis=0)),
                                               np.rad2deg(axd.min(axis=0))), label="CASACORE")
                plt.plot(timepadt, np.rad2deg(arraypa), label="PyEphem")
            else:
                ax.plot(timepadt, np.rad2deg(axd))
            ax.xaxis.set_major_formatter(hfmt)
            ax.grid(True)
            plt.show()

    with tbl(args.ms+"::FEED", ack=False) as t:
        receptor_aid = t.getcol("ANTENNA_ID")
        if len(receptor_aid) != len(anames):
            raise RuntimeError("Receptor angles not all filed for the antennas in the ::FEED keyword table")
        receptor_angles = dict(zip(receptor_aid, t.getcol("RECEPTOR_ANGLE")[:,0]))
        if args.fa is not None:
            receptor_angles[...] = float(args.fa)
            log.info("Overriding F Jones angle to {0:.3f} for all antennae".format(float(args.fa)))
        else:
            log.info("Applying the following feed angle offsets to parallactic angles:")
            for ai, an in enumerate(anames):
                log.info("\t {0:s}: {1:.3f} degrees".format(an, np.rad2deg(receptor_angles.get(ai, 0.0))))

    raarr = np.empty(len(anames), dtype=int)
    for aid in range(len(anames)):
        raarr[aid] = receptor_angles[aid]


with tbl(args.ms+"::POLARIZATION", ack=False) as t:
    poltype = t.getcol("CORR_TYPE")
    # must be linear
    for p in poltype:
        if any(p - np.array([9,10,11,12]) != 0):
            raise RuntimeError("Must be full correlation linear system being corrected")

with tbl(args.ms+"::DATA_DESCRIPTION", ack=False) as t:
    if args.ddid < 0 or args.ddid >= t.nrows():
        raise RuntimeError("Invalid DDID selected")
    spwsel = t.getcol("SPECTRAL_WINDOW_ID")[args.ddid]

with tbl(args.ms+"::SPECTRAL_WINDOW", ack=False) as t:
    chan_freqs = t.getcol("CHAN_FREQ")[spwsel]
    chan_width = t.getcol("CHAN_WIDTH")[spwsel]
    nchan = chan_freqs.size
    log.info("Will apply to SPW {0:d} ({3:d} channels): {1:.2f} to {2:.2f} MHz".format(
        spwsel, chan_freqs.min()*1e-6, chan_freqs.max()*1e-6, nchan))
list_apply = []
if abs(args.crossphase) > 1.0e-6:
    log.info("Applying crosshand phase matrix (X) with {0:.3f} degrees".format(args.crossphase))
    list_apply.append("X Jones")
if not args.noparang:
    list_apply.append("P+F Jones")
if args.flipfeeds:
    log.info("Will flip the visibility hands per user request")
    list_apply.append("Anti-diagonal Jones")
log.info("Arranging to apply (inversion):")
for j in list_apply:
    log.info("\t{}".format(j))
if args.invertpa:
    log.warning("Note: Applying corrupting P+F Jones, instead of correction per user request")

if not args.sim:
    log.info("Storing corrected data into '{}'".format(args.storecolumn))
    timepaunix = np.array(list(map(lambda x: x.replace(tzinfo=pytz.UTC).timestamp(), timepadt)))
    nrowsput = 0
    with tbl(args.ms, ack=False, readonly=False) as t:
        if args.storecolumn not in t.colnames():
            log.info(f"Inserting column {args.storecolumn}. Do not interrupt")
            add_column(t, args.storecolumn)
            log.info(f"Inserted column {args.storecolumn}")
        with taql("select * from $t where FIELD_ID=={} and DATA_DESC_ID=={}".format(args.field, args.ddid)) as tt:
            nrow = tt.nrows()
            nchunk = nrow // args.chunksize + int(nrow % args.chunksize > 0)
            for ci in range(nchunk):
                cl = ci * args.chunksize
                crow = min(nrow - ci * args.chunksize, args.chunksize)
                data = tt.getcol(args.rawcolumn, startrow=cl, nrow=crow)
                if data.shape[2] != 4:
                    raise RuntimeError("Data must be full correlation")
                data = data.reshape(crow, nchan, 2, 2)

                def __casa_to_unixtime(t):
                    dt = quantity("{}s".format(t)).to_unix_time()
                    return dt
                mstimecentroid = tt.getcol("TIME", startrow=cl, nrow=crow)
                msuniqtime = np.unique(mstimecentroid)
                # expensive quanta operation -- do only for unique values
                uniqtimemsunix = np.array(list(map(__casa_to_unixtime, msuniqtime)))
                timemsunixindex = np.array(list(map(lambda t: np.argmin(np.abs(msuniqtime-t)),
                                                    mstimecentroid)))
                timemsunix = uniqtimemsunix[timemsunixindex]
                a1 = tt.getcol("ANTENNA1", startrow=cl, nrow=crow)
                a2 = tt.getcol("ANTENNA2", startrow=cl, nrow=crow)

                def give_lin_Rmat(paA, nchan, conjugate=False):
                    N = paA.shape[0] # nrow
                    c = np.cos(paA).repeat(nchan)
                    s = np.sin(paA).repeat(nchan)
                    if conjugate:
                        return np.array([c,s,-s,c]).T.reshape(N, nchan, 2, 2)
                    else:
                        return np.array([c,-s,s,c]).T.reshape(N, nchan, 2, 2)

                def give_crossphase_mat(phase, nrow, nchan, conjugate=False):
                    ones = np.ones(nchan*nrow)
                    zeros = np.zeros(nchan*nrow)
                    e = np.exp((1.j if not conjugate else -1.j) * np.deg2rad(phase)) * ones
                    return np.array([e,zeros,zeros,ones]).T.reshape(nrow, nchan, 2, 2)

                # need to apply anti-diagonal
                if args.flipfeeds:
                    FVmat = np.array([np.zeros(nchan*crow),
                                      np.ones(nchan*crow),
                                      np.ones(nchan*crow),
                                      np.zeros(nchan*crow)]).T.reshape(crow, nchan, 2, 2)
                else: # ignore step
                    FVmat = np.array([np.ones(nchan*crow),
                                      np.zeros(nchan*crow),
                                      np.zeros(nchan*crow),
                                      np.ones(nchan*crow)]).T.reshape(crow, nchan, 2, 2)
                # cojugate exp for left antenna
                XA1 = give_crossphase_mat(args.crossphase, nrow=crow, nchan=nchan,conjugate=True)
                XA2 = give_crossphase_mat(args.crossphase, nrow=crow, nchan=nchan,conjugate=False)

                if not args.noparang:
                    # nearest neighbour interp to computed ParAng
                    pamap = np.array(list(map(lambda x: np.argmin(np.abs(x - timepaunix)), timemsunix)))

                    # apply receptor angles and get a PA to apply per row
                    # assume same PA for all antennas, different F Jones per antenna possibly
                    paA1 = pa[a1, pamap] + raarr[a1]
                    paA2 = pa[a2, pamap] + raarr[a2]

                    PA1 = give_lin_Rmat(paA1, nchan=nchan, conjugate=(args.invertpa))
                    PA2 = give_lin_Rmat(paA2, nchan=nchan, conjugate=(not args.invertpa))
                    JA1 = np.matmul(FVmat, np.matmul(PA1, XA1))
                    JA2 = np.matmul(np.matmul(XA2, PA2), FVmat)
                else:
                    JA1 = np.matmul(FVmat, XA1)
                    JA2 = np.matmul(XA2, FVmat)

                corr_data = np.matmul(JA1, np.matmul(data, JA2)).reshape(crow, nchan, 4)
                tt.putcol(args.storecolumn, corr_data, startrow=cl, nrow=crow)
                log.info("\tCorrected chunk {}/{}".format(ci+1, nchunk))
                nrowsput += crow
        assert nrow == nrowsput
else:
    log.info("Simulating correction only -- no changes applied to data")

