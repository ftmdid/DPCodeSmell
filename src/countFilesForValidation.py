'''
Created on Jul 25, 2020

@author: neda
'''
import os
import csv

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
        
    
countFilesFolderForValidation()     
    