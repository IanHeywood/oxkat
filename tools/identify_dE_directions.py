#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import Tigger
import numpy
import os	
import sys
from astLib import astCoords as ac


def rad2deg(xx):
	return 180.0*xx/numpy.pi


def tiggerConvert(gaul):

	# Adapted from code by @SpheMakh

	dict_gaul2lsm = {'Gaus_id':'name', 
					'Isl_id':'Isl_id', 
					'Source_id':'Source_id', 
					'Wave_id':'Wave_id', 
					'RA':'ra_d', 
					'E_RA':'E_RA', 
					'DEC':'dec_d', 
					'E_DEC':'E_DEC', 
					'Total_flux':'i', 
					'E_Total_flux':'E_Total_flux', 
					'Peak_flux':'Peak_flux', 
					'E_Peak_flux':'E_Peak_flux', 
					'Xposn':'Xposn', 
					'E_Xposn':'E_Xposn', 
					'Yposn':'Yposn', 
					'E_Yposn':'E_Yposn', 
					'Maj':'Maj', 
					'E_Maj':'E_Maj', 
					'Min':'Min', 
					'E_Min':'E_Min', 
					'PA':'PA', 
					'E_PA':'E_PA', 
					'Maj_img_plane':'Maj_img_plane', 
					'E_Maj_img_plane':'E_Maj_img_plane', 
					'Min_img_plane':'Min_img_plane', 
					'E_Min_img_plane':'E_Min_img_plane', 
					'PA_img_plane':'PA_img_plane', 
					'E_PA_img_plane':'E_PA_img_plane', 
					'DC_Maj':'emaj_d', 
					'E_DC_Maj':'E_DC_Maj', 
					'DC_Min':'emin_d', 
					'E_DC_Min':'E_DC_Min', 
					'DC_PA':'pa_d', 
					'E_DC_PA':'E_DC_PA', 
					'DC_Maj_img_plane':'DC_Maj_img_plane', 
					'E_DC_Maj_img_plane':'E_DC_Maj_img_plane', 
					'DC_Min_img_plane':'DC_Min_img_plane', 
					'E_DC_Min_img_plane':'E_DC_Min_img_plane', 
					'DC_PA_img_plane':'DC_PA_img_plane', 
					'E_DC_PA_img_plane':'E_DC_PA_img_plane', 
					'Isl_Total_flux':'Isl_Total_flux', 
					'E_Isl_Total_flux':'E_Isl_Total_flux', 
					'Isl_rms':'Isl_rms', 
					'Isl_mean':'Isl_mean', 
					'Resid_Isl_rms':'Resid_Isl_rms', 
					'Resid_Isl_mean':'Resid_Isl_mean', 
					'S_Code':'S_Code', 
					'Total_Q':'q', 
					'E_Total_Q':'E_Total_Q', 
					'Total_U':'u', 
					'E_Total_U':'E_Total_U', 
					'Total_V':'v', 
					'E_Total_V':'E_Total_V', 
					'Linear_Pol_frac':'Linear_Pol_frac', 
					'Elow_Linear_Pol_frac':'Elow_Linear_Pol_frac', 
					'Ehigh_Linear_Pol_frac':'Ehigh_Linear_Pol_frac', 
					'Circ_Pol_Frac':'Circ_Pol_Frac', 
					'Elow_Circ_Pol_Frac':'Elow_Circ_Pol_Frac', 
					'Ehigh_Circ_Pol_Frac':'Ehigh_Circ_Pol_Frac', 
					'Total_Pol_Frac':'Total_Pol_Frac', 
					'Elow_Total_Pol_Frac':'Elow_Total_Pol_Frac', 
					'Ehigh_Total_Pol_Frac':'Ehigh_Total_Pol_Frac', 
					'Linear_Pol_Ang':'Linear_Pol_Ang', 
					'E_Linear_Pol_Ang':'E_Linear_Pol_Ang'}


	dict_pol_flag = {'Gaus_id':0, 
					'Isl_id':0, 
					'Source_id':0, 
					'Wave_id':0, 
					'RA':0, 
					'E_RA':0, 
					'DEC':0, 
					'E_DEC':0, 
					'Total_flux':0, 
					'E_Total_flux':0, 
					'Peak_flux':0, 
					'E_Peak_flux':0, 
					'Xposn':0, 
					'E_Xposn':0, 
					'Yposn':0, 
					'E_Yposn':0, 
					'Maj':0, 
					'E_Maj':0, 
					'Min':0, 
					'E_Min':0, 
					'PA':0, 
					'E_PA':0, 
					'Maj_img_plane':0, 
					'E_Maj_img_plane':0, 
					'Min_img_plane':0, 
					'E_Min_img_plane':0, 
					'PA_img_plane':0, 
					'E_PA_img_plane':0, 
					'DC_Maj':0, 
					'E_DC_Maj':0, 
					'DC_Min':0, 
					'E_DC_Min':0, 
					'DC_PA':0, 
					'E_DC_PA':0, 
					'DC_Maj_img_plane':0, 
					'E_DC_Maj_img_plane':0, 
					'DC_Min_img_plane':0, 
					'E_DC_Min_img_plane':0, 
					'DC_PA_img_plane':0, 
					'E_DC_PA_img_plane':0, 
					'Isl_Total_flux':0, 
					'E_Isl_Total_flux':0, 
					'Isl_rms':0, 
					'Isl_mean':0, 
					'Resid_Isl_rms':0, 
					'Resid_Isl_mean':0, 
					'S_Code':0, 
					'Total_Q':1, 
					'E_Total_Q':1, 
					'Total_U':1, 
					'E_Total_U':1, 
					'Total_V':1, 
					'E_Total_V':1, 
					'Linear_Pol_frac':1, 
					'Elow_Linear_Pol_frac':1, 
					'Ehigh_Linear_Pol_frac':1, 
					'Circ_Pol_Frac':1, 
					'Elow_Circ_Pol_Frac':1, 
					'Ehigh_Circ_Pol_Frac':1, 
					'Total_Pol_Frac':1, 
					'Elow_Total_Pol_Frac':1, 
					'Ehigh_Total_Pol_Frac':1, 
					'Linear_Pol_Ang':1, 
					'E_Linear_Pol_Ang':1}


	lines = [line.strip() for line in open(gaul)]


	for line in range(len(lines)):
		if lines[line]:
			if lines[line].split()[0] is not '#': 
				gaul_params = lines[line-1].split()[1:]
				break


	lsm_params_general = []
	lsm_params_polarization = []


	for param in gaul_params:
		if dict_pol_flag[param] is 0:
			lsm_params_general.append(dict_gaul2lsm[param])
		if dict_pol_flag[param] is 1:
			lsm_params_polarization.append(dict_gaul2lsm[param])


	general_params_string = ' '.join(lsm_params_general)
	pol_params_string = ' '.join(lsm_params_polarization)


	output = gaul.replace('.gaul','.lsm.html')


	cluster = 800.0


	syscall = 'tigger-convert -t ASCII --format "'
	syscall += general_params_string+'" '
	syscall += '-f --rename --cluster-dist '+str(cluster)+' '
	syscall += gaul

	os.system(syscall)

	return output


def writeDS9(nodes,regionfile):
	f = open(regionfile,'w')
	f.write('# Region file format: DS9 version 4.1\n')
	f.write('global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1\n')
	f.write('fk5\n')
	for i in range(0,len(nodes)):
		ra = nodes[i][0]
		dec = nodes[i][1]
		ra_hms = ac.decimal2hms(ra,delimiter=':')
		dec_dms = ac.decimal2dms(dec,delimiter=':')
		f.write('circle('+ra_hms+','+dec_dms+',1.0)\n')
	f.close()


def main():

	
	infile = glob.glob('*.gaul')[0]

#	infile = sys.argv[1]

	regionfile = infile.replace('.gaul','.reg')


	tiggerConvert(infile)


	model = Tigger.load(infile.replace('gaul','lsm.html'))

	nodes = []

	for src in model.sources:
		lead = src.getTag('cluster_lead')
		if lead:
			cluster_flux = src.getTag('cluster_flux')
			if cluster_flux > 0.08:
				ra = rad2deg(src.pos.ra)
				dec = rad2deg(src.pos.dec)
				nodes.append((ra,dec))
#				print src.name,ra,dec,'1.0'

	writeDS9(nodes,regionfile)


if __name__ == "__main__":


    main()


