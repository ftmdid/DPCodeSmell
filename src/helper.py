'''
Created on Jul 25, 2020

@author: neda
'''
import os
import csv
import src.runOperations as op
from os import walk
from os.path import join 

def countFilesFolderForValidation():
    validationFolder = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation'
       
    validationFoldersFilesCSVfile = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ValidationFoldersFiles.csv'
    validationFoldersFilesCSVfileOut = csv.writer(open(os.path.join(validationFolder, validationFoldersFilesCSVfile), 'w+'))
    validationFoldersFilesCSVfileOut.writerow(['Folder Name' ,'File Count In Folder', ' ', 'Avg'])
  
    folderFilesList=[]
    directory= os.path.dirname(os.path.dirname(__file__)) + '/util/Python/numpy'  
    folderCount=0
    for x in os.scandir(directory):
        if x.is_dir():
            folderCount+=1
            filesInFolder=[y for y in os.scandir(x.path)]
            folderFilesList.append([x.name, len(filesInFolder)])
            #validationFoldersFilesCSVfileOut.writerow([x.name, len(filesInFolder)])
    sumOfFilesInTotal = 0
    for x in folderFilesList:
        sumOfFilesInTotal += x[1]
    
    sortedList = sorted(folderFilesList, key=lambda x:x[0])
   

    total = 0
    for i in range(len(sortedList)):
        if i==0:
            total +=int(sortedList[0][1])  
        else:
            total +=int(sortedList[i][1])
            
        percntage = str(100 *float(total)/float(sumOfFilesInTotal))+'%'
        validationFoldersFilesCSVfileOut.writerow([sortedList[i][0],sortedList[i][1],total, percntage])
        
def getTotalLinesInAProject(projectName):
    try:
        pythonFiles= getAllPythonFilesInProject(projectName)
        totalLine=0
        for each in pythonFiles:
            with open(each, "r") as fileToBeRead:
                lines = fileToBeRead.read()
                if lines and lines!="\n":
                    linesOfFile = op.loc(lines)
                    if linesOfFile:  
                        totalLine += int(linesOfFile['net'])#no comment, no blank line
        return totalLine
    except Exception as ex:
        print(ex)
        print("Exception occurred in helper.getTotalLinesInAProject() method")
        
def getAllPythonFilesInProject(projectName):
    pythonFiles = []
    projectPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'DemoProjects/'+projectName)
    for path, _, files in walk(projectPath):
        for name in files:
            if not name.lower().startswith('test'):
                if name[-3:] == ".py":
                    pythonFiles.append(join(path, name)) #pythonFiles that has all the python files in numpy project
        
    return pythonFiles
# countFilesFolderForValidation()

projectName='django'  
print(len(getAllPythonFilesInProject(projectName)))
print(getTotalLinesInAProject(projectName))
    