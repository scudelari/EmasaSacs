##################
# Generate a CSV report of the member's end loads (in the GLOBAL coordinate system)
# Useful for inputting the loads in another FEA such as Ansys.
# Filtering of members is allowed.
# INPUT is the sacsdbdb - *** you must activate this output in the run settings ***
##################

import SACS
import SACS.Model
import sys
import os 
import csv
import numpy as np
import sqlite3


from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
from tkinter.filedialog import asksaveasfilename
from tkinter.simpledialog import askstring
Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing

# Select the input SACS model
sacsResDBName = askopenfilename(title='Select the output database with the SACS results', filetypes=[("SACS output database","sacsdbdb.*")]) # show an "Open" dialog box and return the path to the selected directory
if (sacsResDBName == ''):
    sys.exit(0)

# INPUT: Array with the desired members
members = ["0016-604L", "0017-604L", "0018-604L", "0019-604L", "704L-0019"]

# Opens the DB connection to the results
con = sqlite3.connect(sacsResDBName)
cur = con.cursor()

# Building the query with IN in a python list
placeholder= '?' # For SQLite. See DBAPI paramstyle.
placeholders= ', '.join(placeholder for unused in members)
query = 'SELECT * FROM R_SOLVEMEMBERENDFORCESRESULTS WHERE MemberName in (%s) ORDER BY LoadConditionName,MemberName' % placeholders

# Builds the load dictionary
loadConds = dict()

# Gets the result data
currentLc = None
memberLcLoads = None
for row in cur.execute(query, members):
    if (currentLc != row[4]): #row[4] = LoadConditionName
        # Saves the previous load
        if (currentLc != None):
            loadConds[currentLc] = memberLcLoads
        currentLc = row[4]
        memberLcLoads = dict()
        
    memberLcLoads[row[2]] = (row[9:15], row[15:21])# row[2] = MemberName
   
# Saves the last one 
loadConds[currentLc] = memberLcLoads


#for l in sacsModel.AllLoadings():
#    a=0
#    a=a+1
endForcesReport = None

forceUnitName = ""
momentUnitName = ""
if sacsModel.ModelUnits == 0:   #in_lb_F (0)
    forceUnitName = "kip"
    momentUnitName = "kip-in"
elif sacsModel.ModelUnits == 1: #m_kN_C (1) 
    forceUnitName = "kN"
    momentUnitName = "kN-m"
else:                           #m_kg_C (2) 
    forceUnitName = "tonne"
    momentUnitName = "tonne-cm"
    
with open(outputCsvPath, 'w', newline='') as outputCsv:
    csvWriter = csv.writer(outputCsv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    header = ['Load']
    for mName in members:
        header.append(f"{mName} S Fx [{forceUnitName}]")
        header.append(f"{mName} S Fy [{forceUnitName}]")
        header.append(f"{mName} S Fz [{forceUnitName}]")
        
        header.append(f"{mName} S Mx [{momentUnitName}]")
        header.append(f"{mName} S My [{momentUnitName}]")
        header.append(f"{mName} S Mz [{momentUnitName}]")
        
        header.append(f"{mName} E Fx [{forceUnitName}]")
        header.append(f"{mName} E Fy [{forceUnitName}]")
        header.append(f"{mName} E Fz [{forceUnitName}]")
        
        header.append(f"{mName} E Mx [{momentUnitName}]")
        header.append(f"{mName} E My [{momentUnitName}]")
        header.append(f"{mName} E Mz [{momentUnitName}]")
    csvWriter.writerow(header)
    
    for ef in endForcesReport:
        row = [ef.LoadId]
        row.append(np.asarray(ef.ValuesA))
        row.append(np.asarray(ef.ValuesB))
    
    