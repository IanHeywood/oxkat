#!/usr/bin/env python
from __future__ import division, absolute_import, print_function
import sys,os
if "PYTHONPATH_FIRST" in list(os.environ.keys()) and int(os.environ["PYTHONPATH_FIRST"]):
    sys.path = os.environ["PYTHONPATH"].split(":") + sys.path
import os
import sys
#sys.path=os.environ["PYTHONPATH"].split(":")+sys.path
from pyrap.tables import table
from pyrap.images import image
from SkyModel.Sky import ClassSM
import optparse
import numpy as np
import glob
import os
from SkyModel.Other import reformat
SaveFile="last_MyCasapy2BBS.obj"
import pickle
import scipy.ndimage
from SkyModel.Tools import ModFFTW
from SkyModel.PSourceExtract import ClassIslands
import scipy.special
from DDFacet.Other import logger
log=logger.getLogger("MakeMask")
from SkyModel.Other.progressbar import ProgressBar
import collections
from SkyModel.Other.MyHist import MyCumulHist
from SkyModel.PSourceExtract import Gaussian
from SkyModel.Sky import ModRegFile
from DDFacet.ToolsDir import ModFFTW
import DDFacet.Imager.SSD.ClassIslandDistanceMachine
from DDFacet.ToolsDir.rad2hmsdms import rad2hmsdms
from DDFacet.Other import MyPickle
from DDFacet.ToolsDir import ModCoord
import DDFacet.Other.MyPickle
from matplotlib.path import Path
from astropy.io import fits

def PutDataInNewImage(oldfits,newfits,data):
    hdu=fits.open(oldfits)
    hdu[0].data=data
    hdu.writeto(newfits+'.fits',overwrite=True)

def read_options():
    desc=""" cyril.tasse@obspm.fr"""
    
    opt = optparse.OptionParser(usage='Task to build a boolean mask file from a restored fits image, Usage: %prog <options>',version='%prog version 1.0',description=desc)
    group = optparse.OptionGroup(opt, "* Data-related options")
    group.add_option('--RestoredIm',type="str",help="Name of the restored image",default=None)
    group.add_option('--Th',type="float",default=10,help="Threshold in sigma above which to draw an island, default is %default")
    group.add_option("--Box",type="str",default="30,2",help="Box size to compute the noise (using the very classy min() statistics). Default is %default")
    group.add_option("--OutName",type="str",help="Output name (optional). If not specified, will just add .mask.fits at the end if RestoredIm",default="mask")
    group.add_option("--OutNameNoiseMap",type="str",help="If you want to save the noise image image. Default is %default",default="")
    group.add_option("--ExternalMask",type="str",help="Use an external mask in addition. Default is %default",default="")
    group.add_option("--ds9Mask",type="str",help="You can use a ds9 reg file too. Green circle to include, Red circles to explude. This goes in combination to the --Th threshold. Default is %default",default="")
    group.add_option('--UseIslands',type="int",help="Deprecated - look at the code",default=0)
    group.add_option('--RevertInput',type="int",help="look at the code",default=0)
    group.add_option('--ConvNoise',type="int",help="look at the code",default=0)
    group.add_option('--OutMaskExtended',type="str",help="look at the code",default=0)
    group.add_option('--BaseImageName',type="str",help="look at the code",default="")
    
    #group.add_option("--MedFilter",type="str",default="50,10")
    opt.add_option_group(group)

    
    options, arguments = opt.parse_args()

    f = open(SaveFile,"wb")
    pickle.dump(options,f)
    

            

#####################"

    


class ClassMakeMask():
    def __init__(self,FitsFile=None,
                 Th=5.,
                 Box=(50,10),
                 UseIslands=False,
                 OutName="mask",
                 ds9Mask="",
                 OutNameNoiseMap="",
                 options=None,
                 RevertInput=False):

        self.ds9Mask=ds9Mask
        self.FitsFile=FitsFile
        self.Th=Th
        self.Box,self.IncrPix=Box
        self.Boost=self.IncrPix
        self.box=self.Box,self.Box
        self.CasaIm=image(self.FitsFile)
        self.Restored=self.CasaIm.getdata()
        if options.RevertInput:
            print("Reverting the image...", file=log)
            self.Restored*=-1
        self.UseIslands=UseIslands
        self.OutName=OutName
        self.OutNameNoiseMap=OutNameNoiseMap
        self.options=options

        im=self.CasaIm
        c=im.coordinates()
        incr=np.abs(c.dict()["direction0"]["cdelt"][0])
        self.incr_rad=incr

        ra,dec=c.dict()["direction0"]["crval"]
        self.rarad, self.decrad = ra*np.pi/180, dec*np.pi/180
        self.CoordMachine = ModCoord.ClassCoordConv(self.rarad, self.decrad)

        if self.UseIslands:
            PMaj=(im.imageinfo()["restoringbeam"]["major"]["value"])
            PMin=(im.imageinfo()["restoringbeam"]["minor"]["value"])
            PPA=(im.imageinfo()["restoringbeam"]["positionangle"]["value"])

            
            ToSig=(1./3600.)*(np.pi/180.)/(2.*np.sqrt(2.*np.log(2)))
            SigMaj_rad=PMaj*ToSig
            SigMin_rad=PMin*ToSig
            SixMaj_pix=SigMaj_rad/incr
            SixMin_pix=SigMin_rad/incr
            PPA_rad=PPA*np.pi/180

            x,y=np.mgrid[-10:11:1,-10:11:1]
            self.RefGauss=Gaussian.GaussianXY(x,y,1.,sig=(SixMin_pix,SixMaj_pix),pa=PPA_rad)
            self.RefGauss_xy=x,y
            
            self.BeamMin_pix=SixMin_pix*(2.*np.sqrt(2.*np.log(2)))
            self.BeamMaj_pix=SixMaj_pix*(2.*np.sqrt(2.*np.log(2)))
            self.RBeam_pix=SixMaj_pix
            print("Restoring Beam size of (%3.3f, %3.3f) pixels"%(self.BeamMin_pix, self.BeamMaj_pix), file=log)
        
        
        

        # #################"
        # _,_,nx,ny=self.Restored.shape
        # xc,yc=nx//2,nx//2
        # sup=200
        # x,y=np.mgrid[-sup:sup:1,-sup:sup:1]
        # G=Gaussian.GaussianXY(x,y,1.,sig=(7,18),pa=0.)
        # self.Restored[0,0,xc:xc+2*sup,yc:yc+2*sup]+=G[:,:]

        # xc,yc=nx//2+10,nx//2+10

        # G=Gaussian.GaussianXY(x,y,1.,sig=(3,3),pa=0.)
        # self.Restored[0,0,xc:xc+2*sup,yc:yc+2*sup]+=G[:,:]


        # #################"
        
        
        #self.Restored=np.load("testim.npy")
        self.A=self.Restored[0,0]

    def GiveVal(self,A,xin,yin):
        x,y=round(xin),round(yin)
        s=A.shape[0]-1
        cond=(x<0)|(x>s)|(y<0)|(y>s)
        if cond:
            value="out"
        else:
            value="%8.2f mJy"%(A.T[x,y]*1000.)
        return "x=%4i, y=%4i, value=%10s"%(x,y,value)


    def giveBrightFaintMask(self):
        print("Build facetted bright/faint mask...", file=log)
        GD=None
        Mask=self.ImMask
        nx=Mask.shape[-1]
        CurrentNegMask=np.logical_not(Mask).reshape((1,1,nx,nx))
        PSFServer=None
        IdSharedMem=None
        DicoDirty=None
        
        IslandDistanceMachine=DDFacet.Imager.SSD.ClassIslandDistanceMachine.ClassIslandDistanceMachine(GD,
                                                                                                       CurrentNegMask,
                                                                                                       PSFServer,
                                                                                                       DicoDirty,
                                                                                                       IdSharedMem=IdSharedMem)
        ListIslands=IslandDistanceMachine.SearchIslands(None,Image=self.Restored)
        ListIslands=IslandDistanceMachine.ConvexifyIsland(ListIslands)#,PolygonFile="%s.pickle"%OutMaskExtended)
        Mask=np.zeros((nx,nx),np.float32)
        for Island in ListIslands:
            x,y=np.array(Island).T
            Mask[x,y]=1

 
        OutTest="%s.convex_mask"%self.FitsFile
        ImWrite=Mask.reshape((1,1,nx,nx))
        PutDataInNewImage(self.FitsFile,OutTest,np.float32(ImWrite))


        ListPolygons=IslandDistanceMachine.ListPolygons
        
        BaseImageName=self.FitsFile.split(".app.")[0]
        if self.options.BaseImageName: BaseImageName=self.options.BaseImageName 
        D=DDFacet.Other.MyPickle.Load("%s.DicoFacet"%BaseImageName)

        #LSol=[D[iFacet]["iSol"][0] for iFacet in D.keys()]
        DicoDir={}
        for iFacet in list(D.keys()):
            iSol=D[iFacet]["iSol"][0]
            if not iSol in list(DicoDir.keys()):
                DicoDir[iSol]=[iFacet]
            else:
                DicoDir[iSol].append(iFacet)
            
        MaskBright=np.zeros((nx,nx),np.float32)
        MaskFaint=np.zeros((nx,nx),np.float32)
        for iSol in list(DicoDir.keys()):
            print("===================== Processing direction %2.2i/%2.2i ====================="%(iSol,len(DicoDir)), file=log)
            ThisFacetMask=np.zeros_like(Mask)-1
            for iFacet in DicoDir[iSol]:
                PolyGon=D[iFacet]["Polygon"]
                l,m=PolyGon.T
                x,y=((l/self.incr_rad+nx//2)), ((m/self.incr_rad+nx//2))
                poly2=np.array([x,y]).T
                x0,x1=x.min(),x.max()
                y0,y1=y.min(),y.max()
                xx,yy=np.mgrid[x0:x1:(x1-x0+1)*1j,y0:y1:(y1-y0+1)*1j]
                xx=np.int16(xx)
                yy=np.int16(yy)
                
                pp=np.zeros((poly2.shape[0]+1,2),dtype=poly2.dtype)
                pp[0:-1,:]=poly2[:,:]
                pp[-1,:]=poly2[0,:]
                #ListPolygons.append(pp)
                mpath = Path(pp)
                
                p_grid=np.zeros((xx.size,2),np.int16)
                p_grid[:,0]=xx.ravel()
                p_grid[:,1]=yy.ravel()
                mask_flat = mpath.contains_points(p_grid)
                
                IslandOut=np.array([xx.ravel()[mask_flat],yy.ravel()[mask_flat]])
                x,y=IslandOut
                ThisFacetMask[x,y]=1
                #raFacet, decFacet = self.CoordMachine.lm2radec(np.array([lmShift[0]]),
                #                                               np.array([lmShift[1]]))
            ThisFacetMask=ThisFacetMask[::-1,:].T
            ThisFacetMask= (np.abs(Mask - ThisFacetMask)<1e-6)
            
            IslandDistanceMachine=DDFacet.Imager.SSD.ClassIslandDistanceMachine.ClassIslandDistanceMachine(GD,
                                                                                                           1-ThisFacetMask.reshape((1,1,nx,nx)),
                                                                                                           PSFServer,
                                                                                                           DicoDirty,
                                                                                                           IdSharedMem=IdSharedMem)
            ListIslands=IslandDistanceMachine.SearchIslands(None,Image=self.Restored)
            ListIslands=IslandDistanceMachine.ConvexifyIsland(ListIslands)
            DFlux=np.zeros((len(ListIslands),),np.float32)
            for iIsland,Island in enumerate(ListIslands):
                x,y=np.array(Island).T
                DFlux[iIsland]=np.sum(self.Restored[0,0,x,y])

            iIsland_bright=np.argmax(DFlux)
            
            for iIsland,Island in enumerate(ListIslands):
                x,y=np.array(Island).T
                if iIsland==iIsland_bright:
                    MaskBright[x,y]=1
                else:
                    MaskFaint[x,y]=1

        OutTest="%s.bright_mask"%self.FitsFile
        ImWrite=MaskBright.reshape((1,1,nx,nx))
        PutDataInNewImage(self.FitsFile,"%s.fits"%OutTest,np.float32(ImWrite))
 
        OutTest="%s.faint_mask"%self.FitsFile
        ImWrite=MaskFaint.reshape((1,1,nx,nx))
        PutDataInNewImage(self.FitsFile,"%s.fits"%OutTest,np.float32(ImWrite))

        

    
    def ComputeNoiseMap(self):
        print("Compute noise map...", file=log)
        Boost=self.Boost
        Acopy=self.Restored[0,0,0::Boost,0::Boost].copy()
        SBox=(self.box[0]//Boost,self.box[1]//Boost)

        # MeanAbs=scipy.ndimage.filters.mean_filter(np.abs(Acopy),SBox)
        # Acopy[Acopy>0]=MeanAbs[Acopy>0]
        # Noise=np.sqrt(scipy.ndimage.filters.median_filter(np.abs(Acopy)**2,SBox))

        x=np.linspace(-10,10,1000)
        f=0.5*(1.+scipy.special.erf(x/np.sqrt(2.)))
        n=SBox[0]*SBox[1]
        F=1.-(1.-f)**n
        ratio=np.abs(np.interp(0.5,F,x))

        Noise=-scipy.ndimage.filters.minimum_filter(Acopy,SBox)/ratio




        Noise[Noise<0]=1e-10

        # indxy=(Acopy>5.*Noise)
        # Acopy[indxy]=5*Noise[indxy]
        # Noise=np.sqrt(scipy.ndimage.filters.median_filter(np.abs(Acopy)**2,SBox))

        # indxy=(Acopy>5.*Noise)
        # Acopy[indxy]=5*Noise[indxy]
        # Noise=np.sqrt(scipy.ndimage.filters.median_filter(np.abs(Acopy)**2,SBox))

        #NoiseMed=np.median(Noise)
        #Noise[Noise<NoiseMed]=NoiseMed

        self.Noise=np.zeros_like(self.Restored[0,0])
        for i in range(Boost):
            for j in range(Boost):
                s00,s01=Noise.shape
                s10,s11=self.Noise[i::Boost,j::Boost].shape
                s0,s1=min(s00,s10),min(s10,s11)
                self.Noise[i::Boost,j::Boost][0:s0,0:s1]=Noise[:,:][0:s0,0:s1]
        ind=np.where(self.Noise==0.)
        self.Noise[ind]=1e-10

        if self.options.OutMaskExtended:
            GD=None
            MaskExtended=(self.Noise<0.1*np.median(self.Noise))
            OutMaskExtended=self.options.OutMaskExtended
            nx=MaskExtended.shape[-1]
            CurrentNegMask=np.logical_not(MaskExtended).reshape((1,1,nx,nx))
            PSFServer=None
            IdSharedMem=None
            DicoDirty=None

            IslandDistanceMachine=DDFacet.Imager.SSD.ClassIslandDistanceMachine.ClassIslandDistanceMachine(GD,
                                                                                                           CurrentNegMask,
                                                                                                           PSFServer,
                                                                                                           DicoDirty,
                                                                                                           IdSharedMem=IdSharedMem)
            ListIslands=IslandDistanceMachine.SearchIslands(None,Image=self.Restored)
            ListIslands=IslandDistanceMachine.ConvexifyIsland(ListIslands)#,PolygonFile="%s.pickle"%OutMaskExtended)
            ListPolygons=IslandDistanceMachine.ListPolygons

            MaskOut=np.zeros_like(CurrentNegMask)
            N=0
            for Island in ListIslands:
                x,y=np.array(Island).T
                #if x.size<=10: continue
                MaskOut[0,0,x,y]=1
            
            #ff,pol,_,_dec,ra=self.CasaIm.toworld((0,0,0,0))
            ListPolygonsRADEC=[]
            for Polygon in ListPolygons:
                xx,yy=Polygon.T
                ThisPolygon=[]
                for iP in range(xx.shape[0]):
                    xcc,ycc =xx[iP],yy[iP]
                    ff,pol,dec,ra=self.CasaIm.toworld((0,0,xcc,ycc))
                    ThisPolygon.append((ra,dec))
                ListPolygonsRADEC.append(np.array(ThisPolygon))

            FName="%s.pickle"%OutMaskExtended
            print("Saving %s"%FName, file=log)
            MyPickle.Save(ListPolygonsRADEC,FName)

            REGName="%s.reg"%OutMaskExtended
            RM=ModRegFile.PolygonNpToReg(ListPolygonsRADEC,REGName)
            RM.makeRegPolyREG()
            
            # TestArray=np.zeros_like(CurrentNegMask)
            # nx=TestArray.shape[-1]
            # xx,yy=20,100
            # TestArray[0,0,xx,yy]=1
            # PutDataInNewImage(self.FitsFile,"TestCoord.fits",np.float32(TestArray))
            # ff,pol,dec,ra=self.CasaIm.toworld((0,0,xx,yy))
            # pp=[[xx,yy],[yy,xx],
            #     [nx//2-xx,yy],[nx//2+xx,yy],
            #     [nx//2-yy,xx],[nx//2+yy,xx]]
            # for isol in range(len(pp)):
            #     xx,yy=pp[isol]
            #     ff,pol,dec,ra=self.CasaIm.toworld((0,0,xx,yy))
            #     sRA =rad2hmsdms(ra,Type="ra").replace(" ",":")
            #     sDEC =rad2hmsdms(dec,Type="dec").replace(" ",":")
            #     stop
            
            
            MaskOut=np.zeros_like(CurrentNegMask)
            N=0
            for Island in ListIslands:
                x,y=np.array(Island).T
                if x.size<=10: continue
                MaskOut[0,0,x,y]=1
                N+=1
            print("Number of large enough islands %i"%N, file=log)
            MaskExtended=MaskOut
            PutDataInNewImage(self.FitsFile,OutMaskExtended,np.float32(MaskExtended))

        NoiseMed=np.median(self.Noise)
        self.Noise[self.Noise<NoiseMed]=NoiseMed
            
        nx=self.Noise.shape[-1]

        if self.options.ConvNoise:
            print("Convolve...", file=log)
            NoiseMap,G=ModFFTW.ConvolveGaussianWrapper(self.Noise.reshape((1,1,nx,nx)),Sig=4*SBox[0])
            NoiseMap/=np.sum(G)
            self.Noise=NoiseMap[0,0]
        
        if self.OutNameNoiseMap!="":
            #print>>log, "Save noise map as %s"%self.OutNameNoiseMap
            #self.CasaIm.saveas(self.OutNameNoiseMap)
            #CasaNoise=image(self.OutNameNoiseMap)
            #CasaNoise.putdata(self.Noise)
            #CasaNoise.tofits(self.OutNameNoiseMap+".fits")
            #del(CasaNoise)
            PutDataInNewImage(self.FitsFile,self.OutNameNoiseMap,np.float32(self.Noise))

            PutDataInNewImage(self.FitsFile,self.OutNameNoiseMap+".mean",np.float32(np.zeros_like(self.Noise)))


    # def ComputeNoiseMap(self):
    #     print "Compute noise map..."
    #     Boost=self.Boost
    #     Acopy=self.Restored[0,0,0::Boost,0::Boost].copy()
    #     SBox=(self.box[0]//Boost,self.box[1]//Boost)
    #     Noise=np.sqrt(scipy.ndimage.filters.median_filter(np.abs(Acopy)**2,SBox))
    #     self.Noise=np.zeros_like(self.Restored[0,0])
    #     for i in range(Boost):
    #         for j in range(Boost):
    #             s00,s01=Noise.shape
    #             s10,s11=self.Noise[i::Boost,j::Boost].shape
    #             s0,s1=min(s00,s10),min(s10,s11)
    #             self.Noise[i::Boost,j::Boost][0:s0,0:s1]=Noise[:,:][0:s0,0:s1]
    #     print " ... done"
    #     ind=np.where(self.Noise==0.)
    #     self.Noise[ind]=1e-10



    def MakeMask(self):
        self.ImMask=(self.Restored[0,0,:,:]>self.Th*self.Noise)
        self.ImMask[:,-1]=0
        self.ImMask[:,0]=0
        self.ImMask[0,:]=0
        self.ImMask[-1,:]=0
        #self.ImIsland=scipy.ndimage.filters.median_filter(self.ImIsland,size=(3,3))


    def MaskSelectedDS9(self):
        ds9Mask=self.ds9Mask
        print("Reading ds9 region file: %s"%ds9Mask, file=log)
        R=ModRegFile.RegToNp(ds9Mask)
        R.Read()
        
        IncludeCat=R.CatSel
        
        ExcludeCat=R.CatExclude
        
        print("  Excluding pixels", file=log)
        for iRegExclude in range(R.CatExclude.shape[0]):
            
            rac,decc,Radius=R.CatExclude.ra[iRegExclude],R.CatExclude.dec[iRegExclude],R.CatExclude.Radius[iRegExclude]
            RadiusPix=(1.1*Radius/self.incr_rad)
            freq,pol,_,_=self.CasaIm.toworld((0,0,0,0))

            _,_,yc,xc=self.CasaIm.topixel((freq,pol,decc,rac))

            xGrid,yGrid=np.mgrid[int(xc-RadiusPix):int(xc+RadiusPix)+1,int(yc-RadiusPix):int(yc+RadiusPix)+1]
            xGrid=xGrid.ravel()
            yGrid=yGrid.ravel()

            for iPix in range(xGrid.size):
                # if iPix%10000==0:
                #     print iPix,"/",xGrid.size
                ipix,jpix=xGrid[iPix],yGrid[iPix]
                _,_,dec,ra=self.CasaIm.toworld((0,0,jpix,ipix))
                #d=np.sqrt((ra-rac)**2+(dec-decc)**2)
                d=self.GiveAngDist(ra,dec,rac,decc)
                if d<Radius:
                    self.ImMask[jpix,ipix]=0
        

        #self.ImMask.fill(0)
        print("  Including pixels", file=log)
        for iRegInclude in range(IncludeCat.shape[0]):
            rac,decc,Radius=IncludeCat.ra[iRegInclude],IncludeCat.dec[iRegInclude],IncludeCat.Radius[iRegInclude]
            RadiusPix=(1.1*Radius/self.incr_rad)
            freq,pol,_,_=self.CasaIm.toworld((0,0,0,0))

            _,_,yc,xc=self.CasaIm.topixel((freq,pol,decc,rac))
            
            xGrid,yGrid=np.mgrid[int(xc-RadiusPix):int(xc+RadiusPix)+1,int(yc-RadiusPix):int(yc+RadiusPix)+1]
            xGrid=xGrid.flatten().tolist()
            yGrid=yGrid.flatten().tolist()

            for ipix,jpix in zip(xGrid,yGrid):
                _,_,dec,ra=self.CasaIm.toworld((0,0,jpix,ipix))
                #d=np.sqrt((ra-rac)**2+(dec-decc)**2)
                d=self.GiveAngDist(ra,dec,rac,decc)
                #print ipix,jpix
                if d<Radius: 
                    #print "ones",ipix,jpix
                    self.ImMask[jpix,ipix]=1

            

        

    def GiveAngDist(self,ra1,dec1,ra2,dec2):
        sin=np.sin
        cos=np.cos
        #cosA = sin(dec1)*sin(dec2) + cos(dec1)*cos(dec1)*cos(ra1 - ra2) 
        #A=np.arccos(cosA)
        A=np.sqrt(((ra1-ra2)*cos((dec1+dec2)/2.))**2+(dec1-dec2)**2)
        return A

    def BuildIslandList(self):
        import scipy.ndimage

        print("  Labeling islands", file=log)
        self.ImIsland,NIslands=scipy.ndimage.label(self.ImMask)
        ImIsland=self.ImIsland
        NIslands+=1
        nx,_=ImIsland.shape

        print("  Found %i islands"%NIslands, file=log)
        
        NMaxPix=100000
        Island=np.zeros((NIslands,NMaxPix,2),np.int32)
        NIslandNonZero=np.zeros((NIslands,),np.int32)

        print("  Extracting pixels in islands", file=log)
        pBAR= ProgressBar('white', width=50, block='=', empty=' ',Title="      Extracting ", HeaderSize=10, TitleSize=13)
        comment=''



        for ipix in range(nx):
            
            pBAR.render(int(100*ipix / (nx-1)), comment)
            for jpix in range(nx):
                iIsland=self.ImIsland[ipix,jpix]
                if iIsland:
                    NThis=NIslandNonZero[iIsland]
                    Island[iIsland,NThis,0]=ipix
                    Island[iIsland,NThis,1]=jpix
                    NIslandNonZero[iIsland]+=1

        print("  Listing pixels in islands", file=log)

        NMinPixIsland=5
        DicoIslands=collections.OrderedDict()
        for iIsland in range(1,NIslands):
            ind=np.where(Island[iIsland,:,0]!=0)[0]
            if ind.size < NMinPixIsland: continue
            Npix=ind.size
            Comps=np.zeros((Npix,3),np.float32)
            for ipix in range(Npix):
                x,y=Island[iIsland,ipix,0],Island[iIsland,ipix,1]
                s=self.Restored[0,0,x,y]
                Comps[ipix,0]=x
                Comps[ipix,1]=y
                Comps[ipix,2]=s
            DicoIslands[iIsland]=Comps

        print("  Final number of islands: %i"%len(DicoIslands), file=log)
        self.DicoIslands=DicoIslands
        

    def FilterIslands(self):
        DicoIslands=self.DicoIslands
        NIslands=len(self.DicoIslands)
        print("  Filter each individual islands", file=log)
        #pBAR= ProgressBar('white', width=50, block='=', empty=' ',Title="      Filter ", HeaderSize=10,TitleSize=13)
        #comment=''

        NormHist=True

        for iIsland in list(DicoIslands.keys()):
            #pBAR.render(int(100*iIsland / float(len(DicoIslands.keys())-1)), comment)
            x,y,s=DicoIslands[iIsland].T
            #Im=self.GiveIm(x,y,s)
            #pylab.subplot(1,2,1)
            #pylab.imshow(Im,interpolation="nearest")
            # pylab.subplot(1,2,2)

            sr=self.RefGauss.copy()*np.max(s)

            xm,ym=int(np.mean(x)),int(np.mean(y))
            Th=self.Th*self.Noise[xm,ym]

            xg,yg=self.RefGauss_xy

            MaskSel=(sr>Th)
            xg_sel=xg[MaskSel].ravel()
            yg_sel=yg[MaskSel].ravel()
            sr_sel=sr[MaskSel].ravel()
            if sr_sel.size<7: continue

            ###############
            logs=s*s.size#np.log10(s*s.size)
            X,Y=MyCumulHist(logs,Norm=NormHist)
            logsr=sr_sel*sr_sel.size#np.log10(sr_sel*sr_sel.size)
            Xr,Yr=MyCumulHist(logsr,Norm=NormHist)
            Cut=0.9
            ThisTh=np.interp(Cut,Yr,Xr)
            #ThisTh=(ThisTh)/sr_sel.size
            
            #Im=self.GiveIm(xg_sel,yg_sel,sr_sel)
            #pylab.subplot(1,2,2)
            #pylab.imshow(Im,interpolation="nearest")
            


            ind=np.where(s*s.size>ThisTh)[0]
            #print ThisTh,ind.size/float(s.size )
            DicoIslands[iIsland]=DicoIslands[iIsland][ind].copy()
        #     pylab.clf()
        #     pylab.plot(X,Y)
        #     pylab.plot([ThisTh,ThisTh],[0,1],color="black")
        #     pylab.plot(Xr,Yr,color="black",lw=2,ls="--")
        #     pylab.draw()
        #     pylab.show(False)
        #     pylab.pause(0.1)
        #     import time
        #     time.sleep(1)
        # stop

    # def FilterIslands2(self):
    #     DicoIslands=self.DicoIslands
    #     NIslands=len(self.DicoIslands)
    #     print>>log, "  Filter each individual islands"
    #     #pBAR= ProgressBar('white', width=50, block='=', empty=' ',Title="      Filter ", HeaderSize=10,TitleSize=13)
    #     #comment=''

    #     NormHist=False

    #     gamma=1.
    #     d0=1.
    #     for iIsland in [DicoIslands.keys()[0],DicoIslands.keys()[2]]:#DicoIslands.keys():
    #         #pBAR.render(int(100*iIsland / float(len(DicoIslands.keys())-1)), comment)
    #         x,y,s=DicoIslands[iIsland].T
    #         #Im=self.GiveIm(x,y,s)
    #         #pylab.subplot(1,2,1)
    #         #pylab.imshow(Im,interpolation="nearest")
    #         # pylab.subplot(1,2,2)

    #         #sr=self.RefGauss.copy()*np.max(s)

    #         xm,ym=int(np.mean(x)),int(np.mean(y))
    #         Th=self.Th*self.Noise[xm,ym]

    #         Np=x.size
    #         DMat=np.sqrt((x.reshape((Np,1))-x.reshape((1,Np)))**2+(y.reshape((Np,1))-y.reshape((1,Np)))**2)#/self.RBeam_pix
            
    #         C=s.reshape((Np,1))*(1./(d0+DMat))**gamma
    #         #C=1./(d0+DMat)**gamma

            
    #         #C-=np.diag(np.diag(C))
    #         #MaxVec=np.mean(C,axis=1)
    #         #ind=(MaxVec>s).ravel()

    #         MaxVec=np.sum(C,axis=1)#*s#/Th

    #         pylab.clf()

    #         for iPix in range(C.shape[0])[0::10]:
    #             X,Y=MyCumulHist(C[iPix],Norm=False)
    #             pylab.plot(X,Y,color="gray")

    #         ic=np.argmax(s)
    #         X,Y=MyCumulHist(C[ic],Norm=False)
    #         pylab.plot(X,Y,color="black",ls="--",lw=2)

    #         pylab.draw()
    #         pylab.show(False)
    #         pylab.pause(0.1)

    #     #     Im0=self.GiveIm(x,y,s)
    #     #     #Im1=self.GiveIm(x,y,MaxVec)
    #     #     MNorm=MaxVec/s
    #     #     Im1=self.GiveIm(x,y,MNorm)
    #     #     ImMask=self.GiveIm(x,y,(MaxVec>1.))

    #     #     pylab.clf()
    #     #     pylab.subplot(1,3,1)
    #     #     pylab.imshow(Im0,interpolation="nearest")
    #     #     pylab.colorbar()
    #     #     #pylab.title("Th = %f"%Th)
    #     #     pylab.subplot(1,3,2)
    #     #     pylab.imshow(Im1,interpolation="nearest",vmin=MNorm.min(),vmax=MNorm.max())
    #     #     pylab.colorbar()
    #     #     pylab.subplot(1,3,3)
    #     #     pylab.imshow(ImMask,interpolation="nearest")
    #     #     pylab.draw()
    #     #     pylab.show(False)
    #     #     pylab.pause(0.1)
    #     #     import time
    #     #     time.sleep(1)
            
            

    #     #     # xg,yg=self.RefGauss_xy

    #     #     # MaskSel=(sr>Th)
    #     #     # xg_sel=xg[MaskSel].ravel()
    #     #     # yg_sel=yg[MaskSel].ravel()
    #     #     # sr_sel=sr[MaskSel].ravel()
    #     #     # if sr_sel.size<7: continue

    #     #     #DicoIslands[iIsland]=DicoIslands[iIsland][ind].copy()
    #     # #     pylab.clf()
    #     # #     pylab.plot(X,Y)
    #     # #     pylab.plot([ThisTh,ThisTh],[0,1],color="black")
    #     # #     pylab.plot(Xr,Yr,color="black",lw=2,ls="--")
    #     # #     pylab.draw()
    #     # #     pylab.show(False)
    #     # #     pylab.pause(0.1)
    #     # #     import time
    #     # #     time.sleep(1)
    #     stop


    def IslandsToMask(self):
        self.ImMask.fill(0)
        DicoIslands=self.DicoIslands
        NIslands=len(self.DicoIslands)
        print("  Building mask image from filtered islands", file=log)
        #pBAR= ProgressBar('white', width=50, block='=', empty=' ',Title="      Building ", HeaderSize=10,TitleSize=13)
        #comment=''
        for iIsland in list(DicoIslands.keys()):
            #pBAR.render(int(100*iIsland / float(len(DicoIslands.keys())-1)), comment)
            x,y,s=DicoIslands[iIsland].T
            self.ImMask[np.int32(x),np.int32(y)]=1


    def GiveIm(self,x,y,s):
        dx=np.int32(x-x.min())
        dy=np.int32(y-y.min())
        nx=dx.max()+1
        ny=dy.max()+1
        print(nx,ny)
        Im=np.zeros((nx,ny),np.float32)
        Im[dx,dy]=s
        return Im

    def CreateMask(self):
        self.ComputeNoiseMap()
        self.MakeMask()

        if self.ds9Mask!="":
            self.MaskSelectedDS9()

        ExternalAndMask=self.options.ExternalMask
        if ExternalAndMask is not None and ExternalAndMask is not "":
            from DDFacet.Imager import ClassCasaImage
            CleanMaskImageName=ExternalAndMask
            print("Use mask image %s"%CleanMaskImageName, file=log)
            CleanMaskImage = np.bool8(ClassCasaImage.FileToArray(CleanMaskImageName,False))[0,0]
            self.ImMask=(self.ImMask & CleanMaskImage)

        if self.UseIslands:
            # Make island list
            self.BuildIslandList()
            self.FilterIslands()
            self.IslandsToMask()

        # self.plot()
        nx,ny=self.ImMask.shape
        ImWrite=self.ImMask.reshape((1,1,nx,ny))
        
        PutDataInNewImage(self.FitsFile,self.FitsFile+"."+self.OutName,np.float32(ImWrite))

    
    def plot(self):
        import pylab
        pylab.clf()
        ax1=pylab.subplot(2,3,1)
        vmin,vmax=-np.max(self.Noise),5*np.max(self.Noise)
        MaxRms=np.max(self.Noise)
        ax1.imshow(self.A,vmin=vmin,vmax=vmax,interpolation="nearest",cmap="gray",origin="lower")
        ax1.format_coord = lambda x,y : self.GiveVal(self.A,x,y)
        pylab.title("Image")

        ax2=pylab.subplot(2,3,3,sharex=ax1,sharey=ax1)
        pylab.imshow(self.Noise,vmin=0.,vmax=np.max(self.Noise),interpolation="nearest",cmap="gray",origin="lower")
        ax2.format_coord = lambda x,y : self.GiveVal(self.Noise,x,y)
        pylab.title("Noise Image")
        pylab.xlim(0,self.A.shape[0]-1)
        pylab.ylim(0,self.A.shape[0]-1)


        ax3=pylab.subplot(2,3,6,sharex=ax1,sharey=ax1)
        ax3.imshow(self.ImMask,vmin=vmin,vmax=vmax,interpolation="nearest",cmap="gray",origin="lower")
        ax3.format_coord = lambda x,y : self.GiveVal(self.ImMask,x,y)
        pylab.title("Island Image")
        pylab.xlim(0,self.A.shape[0]-1)
        pylab.ylim(0,self.A.shape[0]-1)

        pylab.draw()
        pylab.show(False)

def main(options=None):
    
    if options==None:
        f = open(SaveFile,'rb')
        options = pickle.load(f)

    s0,s1=options.Box.split(",")
    Box=(int(s0),int(s1))
        
    MaskMachine=ClassMakeMask(options.RestoredIm,
                              Th=options.Th,
                              Box=Box,
                              UseIslands=options.UseIslands,
                              OutName=options.OutName,
                              ds9Mask=options.ds9Mask,
                              OutNameNoiseMap=options.OutNameNoiseMap,
                              options=options)
    MaskMachine.CreateMask()
    #MaskMachine.giveBrightFaintMask()

if __name__=="__main__":
    read_options()
    f = open(SaveFile,'rb')
    options = pickle.load(f)
    main(options=options)

def test():
    FitsFile="/media/tasse/data/DDFacet/Test/MultiFreqs3.restored.fits"
    Conv=ClassMakeMask(FitsFile=FitsFile,Th=5.,Box=(50,10))
    Conv.ComputeNoiseMap()
    Conv.FindIslands()

    nx,ny=Conv.ImIsland.shape
    ImWrite=Conv.ImIsland.reshape((1,1,nx,ny))

    PutDataInNewImage(FitsFile,FitsFile+".mask",np.float32(ImWrite))

    #Conv.plot()

    # import pylab
    # pylab.clf()
    # ax=pylab.subplot(1,2,1)
    # pylab.imshow(Conv.Restored[0,0],cmap="gray")
    # pylab.subplot(1,2,2,sharex=ax,sharey=ax)
    # pylab.imshow(Conv.IslandsMachine.ImIsland,cmap="gray")
    # pylab.draw()
    # pylab.show(False)
    # stop
