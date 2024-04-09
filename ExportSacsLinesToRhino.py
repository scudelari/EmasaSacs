import rhinoinside
rhinoinside.load()
import Rhino
import Rhino.Geometry

import SACS
import SACS.Model

# For file dialogs
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing

# Select the input SACS model
sacsFileName = askopenfilename(title='Select the SACS model with the frames', filetypes=[("SACS files","sacinp.*")]) # show an "Open" dialog box and return the path to the selected file
sacsModel = SACS.Model(sacsFileName)

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
    rd.Objects.AddLine(Rhino.Geometry.Point3d(j0.Coordinate.X,j0.Coordinate.Y,j0.Coordinate.Z), Rhino.Geometry.Point3d(j1.Coordinate.X,j1.Coordinate.Y,j1.Coordinate.Z))

rd.SaveAs(sacsFileName+".3dm")
rd.Finalize()
a=0
a=a+1