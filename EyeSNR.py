'''
Created on Mar 17, 2022
The script is used to calculate SNR of quick eye/AMI eye in AEDT circuit 
NRZ,PAM4 eye is tested,  PAM8 should support also.
SNR is output in dB

SNR calculated rule:
mu2 = sum(EyeLevelx^2)
sigma2 = sum(sigmaLevelx^2)
SNR(db) = 10*log(mu2/sigma2)

@author: yongsheng.guo@ansys.com
'''
import sys,os
import json
import numpy as np

class EyeDensity(object):
    def __init__(self, datas = None, grid = None,gridSize = None, yRange = None,name = "Eye Density"):
        '''
        Constructor
        '''
        self.datas = datas
        self._UI = None
        self._grid = grid #[500,500]
        self._gridSize = gridSize #[1,1]
        self._yRange = yRange  #[0,1.2]
        self._vref = None
        self.name = name
        
        self._autoDelay = 0
        self._MuSigma = None
        
        self.ax = None
        self.fig = None
        
    @property
    def UI(self):
        return self._UI
    
    @UI.setter
    def UI(self,UI):
        self._UI = UI
        
    @property
    def Density(self):
        if self.datas is None:
            raise("not have Density data")
        if len(self.datas.shape)!=2:
            self.datas.resize(self.Grid[::-1])
        return self.datas
        
    @property
    def GridSize(self):
        if self._gridSize is None:
            if self._yRange is None:
                return [1,1]
            else:
                self._gridSize = [self.UI/self.Grid[0],(self._yRange[1]-self._yRange[0])/self.Grid[1]]
            
        return self._gridSize
    
    @GridSize.setter
    def GridSize(self,size):
        self._gridSize = size
    
    @property
    def Grid(self):
        """
        return [xgrid,ygrid],which is reverse of density shape
        """
        if self._grid is None:
            if self.Density is not None:
                self._grid = self.Density.shape[::-1]
            else:
                raise("could not get grid size ")
        return self._grid
    
    @Grid.setter
    def Grid(self,grid):
        self._grid = grid
    
    @property
    def Vref(self):
        if self._vref is None:
            self._vref = self.getMaxWidthPos()
        return self._vref
    
    @property
    def MuSigma(self):
        if self._MuSigma is None:
#             samps = self.getYSamples([0.45,0.55])
            samps = self.getYSamples([0.4,0.6])
            yLevels = self.getYLevels(samps)
            self._MuSigma = self.getYLevelsMuSigma(yLevels)
        return self._MuSigma
    
    @property
    def SNR(self):
        return self.calcSNR(self.MuSigma,249.5)
    
    def __add__(self,eye):
        self.datas = self.Density + eye.Density
        self._MuSigma = None
        self._vref = None
        return self
        
    
    def getYSamples(self,sampleWindow =[0.4,0.6],crossing = None):
        
        if crossing is None:
            crossing = int(self.Grid[1]/2)
        u,s = self.getPosMinMuSigma(crossing)
        density = np.roll(self.datas,-int(u),axis=1)

#         density = self.Density
#         bsize = np.array(sampleWindow)*self.Grid[0]
        xlb,xrb = np.array(sampleWindow)*self.Grid[0]
        ySamples = density[:,int(xlb):int(xrb)]
        vpds = ySamples.sum(axis = 1)
        return vpds
    
    def getYLevels(self,vec):
        #normalization Vec
        vec2 = vec/np.average(vec)*100
        vec2[vec<1] = 0
        
        vpds = np.stack((range(vec2.shape[0]),vec2),axis = -1)
        pdsG = [[]]
        for p in np.array_split(vpds,int(self.Grid[0]/5)+1):
            if p[:,1].any():
                pdsG[-1] += list(p)
            else:
                pdsG.append([])
        pdsG = [np.array(x) for x in filter(lambda x:x,pdsG)]
        return pdsG
    
    def getYLevelsMuSigma(self,yLevels):
        return np.array([self.getVecMuSigma(yl[:,0], yl[:,1]) for yl in yLevels])
    
    def calcSNR(self,muSigmas,mid = None):
        mu = muSigmas[:,0]
        Sigmas = muSigmas[:,1]
        if mu.shape[0] == 2:
            print("Modulation: NRZ")
        elif mu.shape[0] == 4:
            print("Modulation: PAM4")
        elif mu.shape[0] == 8:
            print("Modulation: PAM4")
        else:
            print("unknown modulation with EyeLevel count {0}".format(mu.shape[0] ))
            
        if mid is None:
            mid = np.average(mu)
        mu = mu - mid
        mu2 = np.average(mu**2)
        sigma2 = np.average(Sigmas**2)
        SNR = 10*np.log10(mu2/sigma2)
        return SNR
    
    def getVecMuSigma(self,vec,vdensity=None):
        """
        vdensity
        """
        if vdensity is None or vdensity.sum() == 0:
            probability = 1.0/vec.shape[0]
        else:
            probability = vdensity/vdensity.sum()
            
        mu = np.sum(vec*probability)
        sigma = np.sum(probability*(vec-mu)**2)**0.5
        return mu,sigma
    
    def getPosMinMuSigma(self,pos):
        vec = self.Density[pos,:]
        delays = np.linspace(1,vec.shape[0]+1,8,dtype=int)[0:-1]
        rollVecs = np.stack([np.roll(vec,delay) for delay in delays])
        muSigma = np.apply_along_axis(lambda d:self.getVecMuSigma(np.arange(rollVecs.shape[1])+1,d),1,rollVecs)
        muSigma[:,0] -= delays+1
        muSigma[muSigma<0] += self.Grid[0]
        muSigma = muSigma[muSigma[:,1].argsort()]
        return muSigma[0]

    @staticmethod
    def getFromSolutionData(pkl,grid = [500,500]):
        """
        intput: a list of solutionData
        [dataDict->{Datas:[x,ys list],Header:[data lables],"key":VariationKey}]
        first of Header element is X values, others is Y values
        """
        import pickle
        pkl_file = open(pkl, 'rb')
        solutions = pickle.load(pkl_file)
        if not solutions:
            return
        
        data0 = solutions[0]
        header = data0["Header"]
        name = header[1]
        datas = np.array(data0["Datas"][name])
        datas = datas.reshape(-1,700)
        #sample to 500*500
        datas = datas[:,100:-100]
        eye = __class__(datas, grid = grid,name = name)
        return eye
        

def calcSNR():
    path = r"C:\work\Project\AE\Circuit_PAM4\Circuit_PAM4_SNR_simple\QuickEyeAnalysis.dat"
    eye = EyeDensity.getFromSolutionData(path)
    print("{0}: {1:.2f} dB".format(eye.name,eye.SNR))


def main():
    args = sys.argv[1:]
    if len(args)<0:
        print("no input found")
        exit()
    eye = EyeDensity.getFromSolutionData(args[0])    
    print("{0}: {1:.2f} dB".format(eye.name,eye.SNR))

    
if __name__ == '__main__': 
    calcSNR()
#     main()

