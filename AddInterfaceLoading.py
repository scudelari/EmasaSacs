import SACS
import SACS.Model
import sys
import os 
import csv
import re
from scipy.spatial.transform import Rotation as R
import numpy as np

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename

# Select the input CSV
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
csvLoadFilename = askopenfilename(title='Select the CSV containing the loads. Must be in Model Units.', filetypes=[("CSV files","*.csv")]) # show an "Open" dialog box and return the path to the selected file
if (csvLoadFilename == ''):
    sys.exit(0)

# Setup the name of the joint where the loads will be added
targetJointName = "INTR"
csvColNames = {"Fx": "Fx", "Fy": None, "Fz": "Fz", "Mx": None, "My": "My", "Mz": "Mz"} 
anglesRaw = [0, 45, 90, 135, 180, 225, 270, 315]
rotMatrices = dict()
for a in anglesRaw:
    if (a == 0):
        rotMatrices[a] = R.identity()
    else:
        rotMatrices[a] = R.from_rotvec(a * np.array([0, 0, 1]), degrees=True)
lcs = dict()

# Starting counter for the load case name
lcCounter = 1

# Parses the csv into a load dictionary
with open(csvLoadFilename, 'r') as loadCsv:
    csvReader = csv.DictReader(loadCsv)
    for row in csvReader:
        rowDict = dict()
        for key,val in row.items():
            rowDict[key] = val
        lcs[f'J{lcCounter:02d}'] = rowDict
        lcCounter = lcCounter+1


# Opens the SACS model
# Select the input SACS model
sacsFileName = askopenfilename(title=f'Select the SACS model to add the loads. Must have a joint named {targetJointName}', filetypes=[("SACS files","sacinp.*")]) # show an "Open" dialog box and return the path to the selected file
if (sacsFileName == ''):
    sys.exit(0)
sacsModel = SACS.Model(sacsFileName)

targetJoint = sacsModel.FindJoint(targetJointName)
if (targetJoint == None):
    sys.exit(1)

for lcName,jointLoad in lcs.items():
    
    # Can we find these columns in the CSV?    
    x = jointLoad.get(csvColNames["Fx"])
    y = jointLoad.get(csvColNames["Fy"])
    z = jointLoad.get(csvColNames["Fz"])
    mx = jointLoad.get(csvColNames["Mx"])
    my = jointLoad.get(csvColNames["My"])
    mz = jointLoad.get(csvColNames["Mz"])
    
    # Builds the input force vector
    fvec = np.array([0,0,0])
    if (x != None):
        fvec[0] = float(x)
    if (y != None):
        fvec[1] = float(y)
    if (z != None):
        fvec[2] = float(z)
            
    # Builds the input moment vector
    mvec = np.array([0,0,0])
    if (mx != None):
        mvec[0] = float(mx)
    if (my != None):
        mvec[1] = float(my)
    if (mz != None):
        mvec[2] = float(mz)
    
    # loops the requested rotations
    angleCounter = ord('A')
    for rkey,rmat in rotMatrices.items():
        fvecrot = rmat.apply(fvec)
        mvecrot = rmat.apply(mvec)
        
        # Builds the load dictionary for SACS
        jointLoadDict = dict()
        if (abs(fvecrot[0]) > 1E-6):
            jointLoadDict["FX"] = fvecrot[0]
        if (abs(fvecrot[1]) > 1E-6):
            jointLoadDict["FY"] = fvecrot[1]
        if (abs(fvecrot[2]) > 1E-6):
            jointLoadDict["FZ"] = fvecrot[2]
            
        if (abs(fvecrot[0]) > 1E-6):
            jointLoadDict["MX"] = mvecrot[0]
        if (abs(fvecrot[1]) > 1E-6):
            jointLoadDict["MY"] = mvecrot[1]
        if (abs(fvecrot[2]) > 1E-6):
            jointLoadDict["MZ"] = mvecrot[2]
        
        # Adds the loads
        sacsLC = sacsModel.AddLoadCondition(lcName + chr(angleCounter))
        sacsLC.AddJointLoad(targetJoint, jointLoadDict, lcName + chr(angleCounter))        
        
        angleCounter = angleCounter+1

sacsModel.SaveAs(sacsFileName + "_jointLoaded")