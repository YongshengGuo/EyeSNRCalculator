'''
Created on Mar 17, 2022
The script is used to calculate SNR of quick eye/AMI eye in AEDT circuit 
NRZ,PAM4 eye is tested,  PAM8 should be in support also.
SNR is output in dB

SNR calculated rule:
mu2 = sum(EyeLevelx^2)
sigma2 = sum(sigmaLevelx^2)
SNR(db) = 10*log(mu2/sigma2)
x is eye levels 0,1,2,3...

@author: yongsheng.guo@ansys.com
'''
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
from System.Windows.Forms import MessageBox
import os,sys,re
import json
global oDesktop
appPath = os.path.realpath(__file__)
appDir = os.path.split(appPath)[0]
libPath = os.path.join(appDir,'circuit.dll')
clr.AddReferenceToFileAndPath(libPath)
# sys.path.append(r"D:\Study\Script\repository\Circuit\CircuitPy")
from circuitPy2 import circuitBase

if __name__ == "__main__":
    cir = circuitBase()
    cir.initProject()
    cir.message("SNR Calculator V4 20220806")
    cir.message("@author: yongsheng.guo@ansys.com")
    datas = cir.exportSolutionDatas()
    os.environ["Path"] =  os.path.join(oDesktop.GetExeDir(),r"commonfiles\CPython\3_7\winx64\Release\python") + (":",";")['nt' in os.name] + os.environ["Path"]
    output = os.popen("python {0} {1}".format(os.path.join(appDir,"EyeSNRV4"),datas),"r")
    txt = output.read()
    MessageBox.Show(txt)
    cir.message(txt)