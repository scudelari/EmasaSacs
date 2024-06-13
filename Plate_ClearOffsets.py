##################
# Will rebuild all the plates of the model removing the joint offsets.
# New joints will be created when necessary.
##################

import SACS
import SACS.Model
import SACS.Types
import SACS.Error
import sys
import os 
import csv
import numpy as np
import sqlite3
import re
import math

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter.simpledialog import askstring
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing


# Select the input SACS model
sacsModelFileName = askopenfilename(title='Select the SACS input model', filetypes=[("SACS files","sacinp.*")]) # show an "Open" dialog box and return the path to the selected file
if (sacsModelFileName == ''):
    sys.exit(0)
    
# Opens the Sacs model
sacsModel = SACS.Model(sacsModelFileName)
if (sacsModel == None):
    print('Failed to open the SACS model.')
    sys.exit(1)

rigidLinkGroup = sacsModel.FindMemberGroup('RGD')
if (rigidLinkGroup == None):
    print('Model must contain a member called RGD to be used as rigid links.')
    sys.exit(1)

# The starting counter for the new elements
global jointId
global plateId
jointId = 0xA000
plateId = 0xA000

global joints
joints = list()
for j in sacsModel.AllJoints():
    joints.append(j)

def AddOrGetJoint(coords = [], tol = 1e-6):
    # First, looks for an existing joint
    for joint in joints:
        npc = np.array(coords)
        npj = np.array(joint.Coordinate.Values)
        jd = math.sqrt( np.sum(np.subtract(npc, npj) ** 2) )
        if (jd < tol):
            return joint
        
    # Not found - adds new
    global jointId
    toret = None

    # keeps adding until success
    while (toret == None):
        try:
            # Adds to the model
            toret = sacsModel.AddJoint(id = hex(jointId)[2:6].upper(), coord = tuple(coords))
        except:
            print(f'Joint Add Failed: {hex(jointId)[2:6].upper()}, {tuple(coords)}')
        else:
            print(f'Joint Added: {hex(jointId)[2:6].upper()}, {tuple(coords)}')
        finally:
            jointId = jointId + 1

    joints.append(toret)
    return toret

originalPlates = sacsModel.AllPlates()
print(f"Total number of plates in model: {originalPlates.__len__()}")
currPlateCounter = 1
for p in originalPlates:
    oldPlateName = p.Id
    newPlateJoints = [None, None, None, None]
    for j in range(4):
        newPlateJoints[j] = AddOrGetJoint( np.add(np.array(p.Joints[j].Coordinate.Values), np.array(p.GlobalOffsets[j].Values) * 0.01), tol = 0.001  )

    rebuildPlate = False

    for j in range(4):
        if (newPlateJoints[j].Id != p.Joints[j].Id):
            # Adds a link if does not exist
            member = sacsModel.FindMember((newPlateJoints[j], p.Joints[j]))
            if (member == None):
                addedmember = sacsModel.AddMember(newPlateJoints[j], p.Joints[j], rigidLinkGroup)
                if (addedmember == None):
                    print(f'Failed to add member: {newPlateJoints[j]}-{p.Joints[j]}')
            rebuildPlate = True

    if (rebuildPlate):
        # keeps adding until success
        addedplate = None
        while (addedplate == None):
            try:
                # Adds to the model
                addedplate = sacsModel.AddPlate(id = hex(plateId)[2:6].upper(), joints = tuple(newPlateJoints), Group = p.Group, Thickness = p.Thickness)
            except:
                print(f'{currPlateCounter}/{originalPlates.__len__()} Plate Failed. {hex(plateId)[2:6].upper()} {[j.Id for j in newPlateJoints]}')
            else:
                print(f'{currPlateCounter}/{originalPlates.__len__()} Plate replaced. {p.Id} {[j.Id for j in p.Joints]} by {hex(plateId)[2:6].upper()} {[j.Id for j in newPlateJoints]}')
            finally:
                plateId = plateId + 1
        p.Delete()
    else:
        print(f"{currPlateCounter}/{originalPlates.__len__()} Plate {p.Id} kept.")
    
    currPlateCounter = currPlateCounter+1
    
# Saves the model
sacsModel.SaveAs(sacsModelFileName + "_PlateNoOffset")
print('Done!')