# ian.heywood@physics.ox.ac.uk


import pickle
from optparse import OptionParser


parser = OptionParser(usage='%prog [options] rms_map')
parser.add_option('--col',dest='column_selection',help='Data column',default='DATA')
parser.add_option('--fields',dest='fields',help='Select "cals", "targets" or "all"',default='all')
(options,args) = parser.parse_args()
coloumn_selection = options.coloumn_selection
fields = options.fields


project_info = pickle.load(open('project_info.p','rb'))
myms = project_info['master_ms']
bpcal = project_info['primary']
pcal = project_info['secondary']
targets = project_info['target_list'] 

cal_ids = bpcal[1]+','+pcal[1]
target_ids = []
for target in targets:
	target_ids.append(target[1])
target_ids = ','.join(target_ids)

syscall = 'tricolour '
syscall += '--data-column '+coloumn_selection+' '

if fields == 'cals':
elif fields == 'targets':
elif field_selection == 'all'


def generate_syscall_tricolour(myms,datacol='DATA',fields=''):

    syscall = 'source '+TRICOLOUR_VENV+' && '

    syscall += 'tricolour '
    syscall += '--data-column '+datacol+' '
    syscall += '--field-names '+fields+' '

    syscall += '&& deactivate'

    return syscall

