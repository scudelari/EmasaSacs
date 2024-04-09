### DIVIDES MEMBERS BY JOINTS THAT ARE LAYING ON THEM
import sys
import rhinoinside
rhinoinside.load()
import Rhino
import Rhino.Geometry
from Rhino.Geometry import Point3d
from Rhino.Geometry import Line

import SACS
import SACS.Model

# For file dialogs
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
from tkinter.simpledialog import askstring
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing

# IMPORTANT - The start naming of the broken elements
elementId = 0xA000

# Select the input SACS model
sacsFileName = askopenfilename(title='Select the SACS model with the frames', filetypes=[("SACS files","sacinp.*")]) # show an "Open" dialog box and return the path to the selected file
sacsModel = SACS.Model(sacsFileName)

# Enter the member name - empty will mean all members in model
memberNamesRaw = askstring(title='Member', prompt='Enter the name of the member. May be space separated for many. Empty will work on all members.')

memberNames = list()
if (memberNamesRaw == None or memberNamesRaw == ''):
    membersQuery = sacsModel.AllMembers()
    for m in membersQuery:
        memberNames.append(m.Id)
else:
    for s in memberNamesRaw.split():
        memberNames.append(s)

if memberNames.count == 0:
    sys.exit(0) # Nothing to do

# Gets the list of joints
joints = sacsModel.AllJoints()

global fLine

# Works on the member list
for m in memberNames:
    origMember = sacsModel.FindMember(m)
    if (origMember == None):
        continue
    
    # Builds the original frame line
    j0 = origMember.Joints[0]
    j1 = origMember.Joints[1]
    fLine = Line(j0.Coordinate.X,j0.Coordinate.Y,j0.Coordinate.Z, j1.Coordinate.X,j1.Coordinate.Y,j1.Coordinate.Z)
    
    # Gets the joints that are near the line
    nearJoints = list()
    for j in joints:
        if (fLine.DistanceTo(Point3d(j.Coordinate.X, j.Coordinate.Y,j.Coordinate.Z), True) < 0.000001):
            nearJoints.append(j)
    
    # no intersecting joint - nothing to do with this member
    if (len(nearJoints) < 3):
        continue
    
    # the key function to sort the joints
    def __sortKey(ji_):
        a=0
        a=a+1
        return fLine.From.DistanceToSquared(Point3d(ji_.Coordinate.X, ji_.Coordinate.Y,ji_.Coordinate.Z))

    # Sorts the near joint list based on the distance to the start joint
    nearJoints.sort(key = __sortKey)

    # Adds the new members
    for i in range(len(nearJoints) - 1):
        newMember = sacsModel.AddMember(nearJoints[i], nearJoints[i+1], origMember.Group)
        newMember.ChordAngle = origMember.ChordAngle
        newMember.OffsetCS = origMember.OffsetCS
        newMember.Offsets = (origMember.Offsets[0].ValueDict, origMember.Offsets[1].ValueDict)
        # Releases 
        if (i == 0): # First!
            newMember.StartRelease = origMember.StartRelease.ValueDict
        if (i == len(nearJoints) - 2): # Last
            newMember.EndRelease = origMember.EndRelease.ValueDict
        
    # Deletes the old member
    origMember.Delete()
    
# Saves the model
sacsModel.SaveAs(sacsFileName + "_divided")