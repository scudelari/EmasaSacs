##################
# Generate a CSV report of the member's end loads (in the GLOBAL coordinate system)
# Useful for inputting the loads in another FEA such as Ansys.
# Filtering of members is allowed.
# INPUT is the sacsdbdb - *** you must activate this output in the run settings ***
##################
import rhinoinside
rhinoinside.load()
import Rhino
import Rhino.Geometry
import Rhino.DocObjects

import SACS
import SACS.Model
import sys
import os 
import csv
import numpy as np
import sqlite3
import re

def getJointPoint3d(sJoint) -> Rhino.Geometry.Point3d:
    return Rhino.Geometry.Point3d(sJoint.Coordinate.X, sJoint.Coordinate.Y, sJoint.Coordinate.Z)

def getMemberCSys(sMember) -> Rhino.Geometry.Plane:
    mLine = Rhino.Geometry.Line(getJointPoint3d(sMember.Joints[0]), getJointPoint3d(sMember.Joints[1]))
    
    origin = Rhino.Geometry.Point3d((sMember.Joints[0].Coordinate.X+sMember.Joints[1].Coordinate.X)/2.0, (sMember.Joints[0].Coordinate.Y+sMember.Joints[1].Coordinate.Y)/2.0, (sMember.Joints[0].Coordinate.Z+sMember.Joints[1].Coordinate.Z)/2.0)
    mVecX = getJointPoint3d(sMember.Joints[1]) - getJointPoint3d(sMember.Joints[0])
    mVecX.Unitize()
    
    if (sMember.ReferenceJoint == None):
        raise Exception("Members MUST have a reference joint")
    refPoint = getJointPoint3d(sMember.ReferenceJoint)
    refToPoint = mLine.ClosestPoint(refPoint, False)
    refVector = refToPoint - refPoint
    refVector.Unitize()
    
    tempPlane = Rhino.Geometry.Plane(origin, mVecX, refVector) # Plane on X with Y
    tempPlane.Rotate(Rhino.RhinoMath.ToRadians(90), tempPlane.XAxis, tempPlane.Origin)
    return tempPlane

def printPlane(rhinoDoc: Rhino.RhinoDoc, plane: Rhino.Geometry.Plane):
    # Can't add color from Python
    red = Rhino.DocObjects.ObjectAttributes()
    red.ObjectDecoration = Rhino.DocObjects.ObjectDecoration.EndArrowhead
    red.SetUserString("Dir","X")
    rd.Objects.AddLine(Rhino.Geometry.Line(plane.Origin, plane.XAxis, .5), red)

    green = Rhino.DocObjects.ObjectAttributes()
    green.ObjectDecoration = Rhino.DocObjects.ObjectDecoration.EndArrowhead
    green.SetUserString("Dir","Y")
    rd.Objects.AddLine(Rhino.Geometry.Line(plane.Origin, plane.YAxis, .5), green)
    
    blue = Rhino.DocObjects.ObjectAttributes()
    blue.ObjectDecoration = Rhino.DocObjects.ObjectDecoration.EndArrowhead
    blue.SetUserString("Dir","Z")
    rd.Objects.AddLine(Rhino.Geometry.Line(plane.Origin, plane.ZAxis, .5), blue)

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
    sys.exit(1)
 
# Builds the rhino model
rd = Rhino.RhinoDoc.Create(None)
if sacsModel.ModelUnits == 0:
    rd.ModelUnitSystem = Rhino.UnitSystem.Feet
else:
    rd.ModelUnitSystem = Rhino.UnitSystem.Meters

membersQuery = sacsModel.AllMembers()
for m in membersQuery:
    j0 = m.Joints[0]
    j1 = m.Joints[1]
    rd.Objects.AddLine(getJointPoint3d(j0), getJointPoint3d(j1))
    
# Select the reported member end forces - stupid. Must be reported because SACS has a bug in the output and does not fill correctly the end forces
endForcesRepFileName = askopenfilename(title='Select text file with the End Forces report', filetypes=[("SACS files","*.txt")]) # show an "Open" dialog box and return the path to the selected file
if (endForcesRepFileName == ''):
    sys.exit(0)

reUnitLine = re.compile(r"^\s+\*+\s+(?P<ForceUnit>\w*)[\*\s]+(?P<MomentUnit>[\w-]*)")
reDataLine = re.compile(r"^\s+?(?P<mn>.{9})\s{4}(?P<jn>.{4}).{12}(?P<lc>.{4})\s*(?P<fx>-?[\d\.]+)\s*(?P<fy>-?[\d\.]+)\s*(?P<fz>-?[\d\.]+)\s*(?P<mx>-?[\d\.]+)\s*(?P<my>-?[\d\.]+)\s*(?P<mz>-?[\d\.]+)")

forceUnitName = ""
momentUnitName = ""

members = dict()
memberjoints = set()
loadconds = set()
localLoads = dict()

# Parsing the end forces report
foundUnitLine = False
currentMember = None
currentJoint = None
currentTransform = None
with open(endForcesRepFileName) as forcesFile:
    for line in forcesFile:
        if (not foundUnitLine):
            match = reUnitLine.search(line)
            if match:
                forceUnitName = match.group("ForceUnit")
                momentUnitName = match.group("MomentUnit")
                foundUnitLine = True
        else: # now looking for data
            match = reDataLine.search(line)
            if match:
                if (not match.group("mn").isspace()):
                    currentMember = match.group("mn")
                    # Gets the Sacs Member
                    sMember = sacsModel.FindMember(currentMember)
                    mPlane = getMemberCSys(sMember)
                    # Saves the member plane
                    members[currentMember] = mPlane
                    
                    # ************** DEBUG prints the plane
                    printPlane(rd, mPlane)
                    
                if (not match.group("jn").isspace()):
                    currentJoint = match.group("jn")

                loadconds.add(match.group("lc"))
                
                # Reads the vectors - still in the local coordinate system
                forces = Rhino.Geometry.Vector3d(float(match.group("fx")), float(match.group("fy")),float(match.group("fz")))
                moments = Rhino.Geometry.Vector3d(float(match.group("mx")),float(match.group("my")),float(match.group("mz")))

                localLoads[currentMember + " " + currentJoint + " " + match.group("lc")] = (forces, moments)


# Must transform the loads to Global
globalLoads = dict()
for m, mPlane in members.items():
    jointNames = m.split("-")
    for lc in loadconds:
        startActions = localLoads[m + " " + jointNames[0] + " " + lc]
        endActions = localLoads[m + " " + jointNames[1] + " " + lc]
        
        # First change signals as per SACS documentation
        startActions[0].X = -startActions[0].X
        startActions[0].Y = startActions[0].Y
        startActions[0].Z = startActions[0].Z
        startActions[1].X = -startActions[1].X
        startActions[1].Y = startActions[1].Y
        startActions[1].Z = -startActions[1].Z
        
        endActions[0].X = endActions[0].X
        endActions[0].Y = -endActions[0].Y
        endActions[0].Z = -endActions[0].Z
        endActions[1].X = endActions[1].X
        endActions[1].Y = -endActions[1].Y
        endActions[1].Z = endActions[1].Z
        
        # Now, transform to Global START
        startJoint = sacsModel.FindJoint(jointNames[0])
        startPnt = getJointPoint3d(startJoint)
        
        # The plane comes with origin at the member middle
        startPlane = Rhino.Geometry.Plane(startPnt, mPlane.XAxis, mPlane.YAxis)
        
        # TargetPlane
        startGlobal = Rhino.Geometry.Plane(startPnt, Rhino.Geometry.Vector3d.XAxis, Rhino.Geometry.Vector3d.YAxis)
        
        # The start transformator
        startTransformator = Rhino.Geometry.Transform.ChangeBasis(startPlane, startGlobal)
        
        startForcesTransformed = startActions[0]
        startForcesTransformed.Transform(startTransformator)
        startMomentsTransformed = startActions[1]
        startMomentsTransformed.Transform(startTransformator)
        
        # Saves in the dictionary
        globalLoads[m + " " + jointNames[0] + " " + lc] = (startForcesTransformed, startMomentsTransformed)
        
        # Now, transform to Global END
        endJoint = sacsModel.FindJoint(jointNames[1])
        endPnt = getJointPoint3d(endJoint)
        
        # The plane comes with origin at the member middle
        endPlane = Rhino.Geometry.Plane(endPnt, mPlane.XAxis, mPlane.YAxis)
        
        # TargetPlane
        endGlobal = Rhino.Geometry.Plane(endPnt, Rhino.Geometry.Vector3d.XAxis, Rhino.Geometry.Vector3d.YAxis)
        
        # The end transformator
        endTransformator = Rhino.Geometry.Transform.ChangeBasis(endPlane, endGlobal)
        
        endForcesTransformed = endActions[0]
        endForcesTransformed.Transform(endTransformator)
        endMomentsTransformed = endActions[1]
        endMomentsTransformed.Transform(endTransformator)

        # Saves in the dictionary
        globalLoads[m + " " + jointNames[1] + " " + lc] = (endForcesTransformed, endMomentsTransformed)


with open(endForcesRepFileName + ".csv", 'w', newline='') as outputCsv:
    csvWriter = csv.writer(outputCsv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    header = ['Load Condition']
    for mName in members.keys():
        jointNames = mName.split("-")
        header.append(f"{mName} {jointNames[0]} Fx [{forceUnitName}]")
        header.append(f"{mName} {jointNames[0]} Fy [{forceUnitName}]")
        header.append(f"{mName} {jointNames[0]} Fz [{forceUnitName}]")
        
        header.append(f"{mName} {jointNames[0]} Mx [{momentUnitName}]")
        header.append(f"{mName} {jointNames[0]} My [{momentUnitName}]")
        header.append(f"{mName} {jointNames[0]} Mz [{momentUnitName}]")
        
        header.append(f"{mName} {jointNames[1]} Fx [{forceUnitName}]")
        header.append(f"{mName} {jointNames[1]} Fy [{forceUnitName}]")
        header.append(f"{mName} {jointNames[1]} Fz [{forceUnitName}]")
        
        header.append(f"{mName} {jointNames[1]} Mx [{momentUnitName}]")
        header.append(f"{mName} {jointNames[1]} My [{momentUnitName}]")
        header.append(f"{mName} {jointNames[1]} Mz [{momentUnitName}]")
    csvWriter.writerow(header)
    
    for lc in loadconds:
        row = [lc]
        for mName in members.keys():
            jointNames = mName.split("-")
            
            startActions = globalLoads[mName + " " + jointNames[0] + " " + lc]
            
            row.append(startActions[0].X)
            row.append(startActions[0].Y)
            row.append(startActions[0].Z)
            row.append(startActions[1].X)
            row.append(startActions[1].Y)
            row.append(startActions[1].Z)
            
            endActions = globalLoads[mName + " " + jointNames[1] + " " + lc]
            
            row.append(endActions[0].X)
            row.append(endActions[0].Y)
            row.append(endActions[0].Z)
            row.append(endActions[1].X)
            row.append(endActions[1].Y)
            row.append(endActions[1].Z)
            
        csvWriter.writerow(row)
        
rd.SaveAs(sacsModelFileName+".3dm")
rd.Finalize()