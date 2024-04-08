import SACS
import SACS.Model
import json
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename

# Select the input JSON
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
jsonMeshFilename = askopenfilename(title='Select the JSON containing the mesh', filetypes=[("JSON files","*.json")]) # show an "Open" dialog box and return the path to the selected file

# The starting counter for the nodes
nodeId = 0xA000
elementId = 0xA000

# Parse the JSON
jsonFile = open(jsonMeshFilename)
jsonContents = json.load(jsonFile)

# This dictionary is used to match the Ansys ids
cornerNodesHelper = dict()
for n in jsonContents['Nodes']:
    cornerNodesHelper[n['Id']] = (hex(nodeId)[2:6].upper(), n['X'], n['Y'], n['Z'])
    nodeId = nodeId+1

# This dictionary contains the assigned Sacs values
cornerNodes = dict()
for key,val in cornerNodesHelper.items():
    cornerNodes[val[0]] = (val[1],val[2],val[3])

rawSurfaces = dict()
for e in jsonContents['Elements']:
    if e['ElementType'] == 5 or e['ElementType'] == 7: # Triangular (5) or Quad (7)
        eleNodes = list()
        for en in e['Nodes']:
            eleNodes.append(cornerNodesHelper[en])
        rawSurfaces[e['Id']] = (hex(elementId)[2:6].upper(), eleNodes, e['ElementType'] )
        elementId = elementId+1

# We must add the intermediate nodes to make surfaces into shells
shells = dict()
intermNodes = dict()
for key,val in rawSurfaces.items():
    if val[2] == 5: # Tri
        mid01 = intermNodes.get(val[1][0][0] + val[1][1][0])
        if mid01 is None:
            mid01 = intermNodes.get(val[1][1][0] + val[1][0][0])
        if mid01 is None:
            intermNodes[val[1][0][0] + val[1][1][0]] = (hex(nodeId)[2:6].upper(), (cornerNodes[val[1][0][0]][0] + cornerNodes[val[1][1][0]][0]) / 2.0, (cornerNodes[val[1][0][0]][1] + cornerNodes[val[1][1][0]][1]) / 2.0, (cornerNodes[val[1][0][0]][2] + cornerNodes[val[1][1][0]][2]) / 2.0)
            nodeId = nodeId+1
            mid01 = intermNodes[val[1][0][0] + val[1][1][0]]
            
        mid02 = intermNodes.get(val[1][1][0] + val[1][2][0])
        if mid02 is None:
            mid02 = intermNodes.get(val[1][2][0] + val[1][1][0])
        if mid02 is None:
            intermNodes[val[1][1][0] + val[1][2][0]] = (hex(nodeId)[2:6].upper(), (cornerNodes[val[1][1][0]][0] + cornerNodes[val[1][2][0]][0]) / 2.0, (cornerNodes[val[1][1][0]][1] + cornerNodes[val[1][2][0]][1]) / 2.0, (cornerNodes[val[1][1][0]][2] + cornerNodes[val[1][2][0]][2]) / 2.0)
            nodeId = nodeId+1
            mid02 = intermNodes[val[1][1][0] + val[1][2][0]]
        
        mid03 = intermNodes.get(val[1][2][0] + val[1][0][0])
        if mid03 is None:
            mid03 = intermNodes.get(val[1][0][0] + val[1][2][0])
        if mid03 is None:
            intermNodes[val[1][2][0] + val[1][0][0]] = (hex(nodeId)[2:6].upper(), (cornerNodes[val[1][2][0]][0] + cornerNodes[val[1][0][0]][0]) / 2.0, (cornerNodes[val[1][2][0]][1] + cornerNodes[val[1][0][0]][1]) / 2.0, (cornerNodes[val[1][2][0]][2] + cornerNodes[val[1][0][0]][2]) / 2.0)
            nodeId = nodeId+1
            mid03 = intermNodes[val[1][2][0] + val[1][0][0]]
        
        eleNodes = [val[1][0][0], mid01[0], val[1][1][0], mid02[0], val[1][2][0], mid03[0]]
        shells[val[0]] = (eleNodes, val[2])
    elif val[2] == 7: # Quads
        mid01 = intermNodes.get(val[1][0][0] + val[1][1][0])
        if mid01 is None:
            mid01 = intermNodes.get(val[1][1][0] + val[1][0][0])
        if mid01 is None:
            intermNodes[val[1][0][0] + val[1][1][0]] = (hex(nodeId)[2:6].upper(), (cornerNodes[val[1][0][0]][0] + cornerNodes[val[1][1][0]][0]) / 2.0, (cornerNodes[val[1][0][0]][1] + cornerNodes[val[1][1][0]][1]) / 2.0, (cornerNodes[val[1][0][0]][2] + cornerNodes[val[1][1][0]][2]) / 2.0)
            nodeId = nodeId+1
            mid01 = intermNodes[val[1][0][0] + val[1][1][0]]
            
        mid02 = intermNodes.get(val[1][1][0] + val[1][2][0])
        if mid02 is None:
            mid02 = intermNodes.get(val[1][2][0] + val[1][1][0])
        if mid02 is None:
            intermNodes[val[1][1][0] + val[1][2][0]] = (hex(nodeId)[2:6].upper(), (cornerNodes[val[1][1][0]][0] + cornerNodes[val[1][2][0]][0]) / 2.0, (cornerNodes[val[1][1][0]][1] + cornerNodes[val[1][2][0]][1]) / 2.0, (cornerNodes[val[1][1][0]][2] + cornerNodes[val[1][2][0]][2]) / 2.0)
            nodeId = nodeId+1
            mid02 = intermNodes[val[1][1][0] + val[1][2][0]]
        
        mid03 = intermNodes.get(val[1][2][0] + val[1][3][0])
        if mid03 is None:
            mid03 = intermNodes.get(val[1][3][0] + val[1][2][0])
        if mid03 is None:
            intermNodes[val[1][2][0] + val[1][3][0]] = (hex(nodeId)[2:6].upper(), (cornerNodes[val[1][2][0]][0] + cornerNodes[val[1][3][0]][0]) / 2.0, (cornerNodes[val[1][2][0]][1] + cornerNodes[val[1][3][0]][1]) / 2.0, (cornerNodes[val[1][2][0]][2] + cornerNodes[val[1][3][0]][2]) / 2.0)
            nodeId = nodeId+1
            mid03 = intermNodes[val[1][2][0] + val[1][3][0]]
            
        mid04 = intermNodes.get(val[1][3][0] + val[1][0][0])
        if mid04 is None:
            mid04 = intermNodes.get(val[1][0][0] + val[1][3][0])
        if mid04 is None:
            intermNodes[val[1][3][0] + val[1][0][0]] = (hex(nodeId)[2:6].upper(), (cornerNodes[val[1][3][0]][0] + cornerNodes[val[1][0][0]][0]) / 2.0, (cornerNodes[val[1][3][0]][1] + cornerNodes[val[1][0][0]][1]) / 2.0, (cornerNodes[val[1][3][0]][2] + cornerNodes[val[1][0][0]][2]) / 2.0)
            nodeId = nodeId+1
            mid04 = intermNodes[val[1][3][0] + val[1][0][0]]
        
        eleNodes = [val[1][0][0], mid01[0], val[1][1][0], mid02[0], val[1][2][0], mid03[0], val[1][3][0], mid04[0]]
        shells[val[0]] = (eleNodes, val[2])

# Builds the SACS model
sacsModel = SACS.Model(1) # m_kN_C (1) 

# Adds the corner joints
sacsJoints = dict()
for key,val in cornerNodes.items():
    js = sacsModel.AddJoint(id = key, coord=(val[0],val[1],val[2]))
    sacsJoints[key] = js
# Adds the intermediate joints
for key,val in intermNodes.items():
    js = sacsModel.AddJoint(id = val[0], coord=(val[1],val[2],val[3]))
    sacsJoints[val[0]] = js

# Makes the shells
shellDefaultGroup = sacsModel.AddShellGroup(id = 'SPY')

for key,val in shells.items():
    shellJoints = list()
    for e in val[0]:
        shellJoints.append(sacsJoints[e])
    if val[1] == 5: # Tri
        sacsModel.AddShell(id = key, joints = shellJoints,Group = shellDefaultGroup)
        
sacsModelFileName = asksaveasfilename(title='Select the target SACS model filename.', filetypes=[("All files","*.*")], initialfile = 'sacinp.meshmodel') # show an "Open" dialog box and return the path to the selected file
sacsModel.SaveAs(sacsModelFileName)