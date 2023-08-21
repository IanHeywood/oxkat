# ian.heywood@physics.ox.ac.uk


import glob
import json
import sys


with open('project_info.json') as f:
    project_info = json.load(f)


flag_file = glob.glob('*manualflags.txt')


if len(flag_file) == 1:
	flag_file = flag_file[0]
else:
	print('No or multiple manual flag files found.')
	sys.exit()


myms = project_info['master_ms']


clearstat()
clearstat()


f = open(flag_file,'r')
line = f.readline().rstrip('\n')
while line:
	if line[0] != '#':
		cols = line.split(':')
		if len(cols) == 1:
			ant = cols[0]
			scans = ''
		elif len(cols) == 2:
			ant = cols[0]
			scans = cols[1]
		else:
			print('Check manual flag instruction:')
			print(line)
			continue
		flagdata(vis=myms,
			mode = 'manual',
			antenna = ant,
			scan = scans)
	line = f.readline().rstrip('\n')
f.close()


if SAVE_FLAGS:
	flagmanager(vis=myms,mode='save',versionname='manual_flags')


clearstat()
clearstat()
