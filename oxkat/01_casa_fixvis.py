# ianh@astro.ox.ac.uk


import numpy
import glob
import pickle
import shutil


project_info = pickle.load(open('project_info.p','rb'))


myms = glob.glob('*wtspec.ms')[0]


fixvis(vis=myms,outputvis=myms)
