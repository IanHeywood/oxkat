# ian.heywood@physics.ox.ac.uk


import glob
import numpy
import pickle
import time
import shutil


def stamp():
    return str(time.time()).replace('.','')


def get_antnames(myms):
    tb.open(myms+'/ANTENNA')
    ant_names = tb.getcol('NAME')
    ant_names = [a.lower() for a in ant_names]
    tb.done()
    return ant_names


def get_refant(myms):

    tb.open(myms)

    ant_names = get_antnames(myms)

    ref_pool = ['m000','m001','m002','m003','m004','m006']
    pc_list = numpy.ones(len(ref_pool))*100.0
    idx_list = numpy.zeros(len(ref_pool),dtype=numpy.int8)


    for i in range(0,len(ref_pool)):
        ant = ref_pool[i]
        try:
            idx = ant_names.index(ant)
            sub_tab = tb.query(query='ANTENNA1=='+str(idx),columns=['FLAG'])
            flags = sub_tab.getcol('FLAG')
            vals,counts = numpy.unique(flags,return_counts=True)
            if len(vals) == 1 and vals == True:
                flag_pc = 100.0
            elif len(vals) == 1 and vals == False:
                flag_pc = 0.0
            else:
                flag_pc = 100.*round(float(counts[1])/float(numpy.sum(counts)),2)
            pc_list[i] = flag_pc
            idx_list[i] = idx
        except:
            continue

    ref_idx = idx_list[numpy.where(pc_list==(numpy.min(pc_list)))][0]

    tb.done()

    return ref_idx


myuvrange = '>150m'
badfreqs = ['850~880MHz','1658~1800MHz','944~947MHz','1160~1310MHz','1476~1611MHz','1419.8~1421.3MHz']


mslist = glob.glob('*.ms')

for myms in mslist:


    ref_ant = get_refant(myms)


    gtab0 = 'cal_'+myms+'_'+stamp()+'.G0'
    ktab0 = 'cal_'+myms+'_'+stamp()+'.K0'
    bptab0 = 'cal_'+myms+'_'+stamp()+'.B0'
    gtab1 = 'cal_'+myms+'_'+stamp()+'.G1'
    ktab1 = 'cal_'+myms+'_'+stamp()+'.K1'
    bptab1 = 'cal_'+myms+'_'+stamp()+'.B1'


    for badfreq in badfreqs:
        badspw = '*:' + badfreq
        flagdata(vis=myms, mode='manual', spw=badspw)


    flagdata(vis=myms,mode='quack',quackinterval=8.0,quackmode='beg')
    flagdata(vis=myms,mode='manual',autocorr=True)
    flagdata(vis=myms,mode='clip',clipzeros=True)
    flagdata(vis=myms,mode='clip',clipminmax=[0.0,100.0])

    flagdata(vis=myms,mode='tfcrop',datacolumn='data',field='0')


    setjy(vis=myms,
        field='0',
        standard='Perley-Butler 2010',
        scalebychan=True,
        usescratch=True)
    

    gaincal(vis=myms,
        field='0',
        uvrange=myuvrange,
        caltable=gtab0,
        gaintype='G',
        solint='int',
        calmode='p',
        minsnr=5)


    gaincal(vis=myms,
        field='0',
        uvrange=myuvrange,
        caltable=ktab0,
        refant = str(ref_ant),
        gaintype = 'K',
        solint = 'inf',
        parang=False,
        gaintable=[gtab0],
        gainfield=['0'],
        interp=['nearest'],
        combine = '')


    bandpass(vis=myms,
        field=bpcal,
        uvrange=myuvrange,
        caltable=bptab0,
        refant = str(ref_ant),
        solint='inf',
        combine='scan',
        solnorm=False,
        minblperant=4,
        minsnr=3.0,
        bandtype='B',
        fillgaps=64,
        parang=False,
        gainfield=['0','0'],
        interp = ['nearest','nearest'],
        gaintable=[gtab0,ktab0])


    applycal(vis=myms,
        gaintable=[gtab0,ktab0,bptab0],
        field='0',
        calwt=False,
        parang=False,
        applymode='calonly',
        gainfield=['0','0','0'],
        interp = ['nearest','nearest','nearest'])


    flagdata(vis=myms,mode='rflag',datacolumn='residual',field='0')


    clearstat()


    gaincal(vis=myms,
        field='0',
        uvrange=myuvrange,
        caltable=gtab1,
        gaintype='G',
        solint='int',
        calmode='p',
        minsnr=5)


    gaincal(vis=myms,
        field='0',
        uvrange=myuvrange,
        caltable=ktab1,
        refant = str(ref_ant),
        gaintype = 'K',
        solint = 'inf',
        parang=False,
        gaintable=[gtab1],
        gainfield=['0'],
        interp=['nearest'],
        combine = '')


    bandpass(vis=myms,
        field=bpcal,
        uvrange=myuvrange,
        caltable=bptab1,
        refant = str(ref_ant),
        solint='inf',
        combine='scan',
        solnorm=False,
        minblperant=4,
        minsnr=3.0,
        bandtype='B',
        fillgaps=64,
        parang=False,
        gainfield=['0','0'],
        interp = ['nearest','nearest'],
        gaintable=[gtab1,ktab1])


    applycal(vis=myms,
        gaintable=[gtab1,ktab1,bptab1],
        field='0',
        calwt=False,
        parang=False,
        applymode='calonly',
        gainfield=['0','0','0'],
        interp = ['nearest','nearest','nearest'])
