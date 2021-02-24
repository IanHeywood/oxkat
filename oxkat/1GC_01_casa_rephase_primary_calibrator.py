# ian.heywood@physics.ox.ac.uk


execfile('oxkat/casa_read_project_info.py')


args = sys.argv
for item in sys.argv:
    parts = item.split('=')
    if parts[0] == 'myms':
        myms = parts[1]
        

if primary_tag == '0408':
    newphasecentre = 'J2000 04h08m20.3782s -65d45m09.080s'
    dorephase = True
elif primary_tag == '1934':
    newphasecentre = 'J2000 19h39m25.0264s -63d42m45.624s'
    dorephase = True
else:
    dorephase = False

if dorephase:
    fixvis(vis = myms,
        field = bpcal,
        phasecenter = newphasecentre,
        refcode = 'J2000',
        datacolumn = 'DATA')

