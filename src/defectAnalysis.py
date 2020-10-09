'''
Created on Sep 20, 2020

@author: neda
'''

import os
import csv
import itertools

def createFileListsForEachFolder(readerCSV, folderName):
    fileListForFolder=[]
    for row in readerCSV:
        if row[7]==folderName:
            fileListForFolder.append(row)
    return fileListForFolder

def checkIfLargeClassSmellLeadToDefect(fileListForFolder):
    fileList=[]
    for each in fileListForFolder:
        if int(each[5])-int(each[4])>0 and int(each[5])-int(each[4])<5:
            diff=int(each[5])-int(each[4])
            fileList.append([each[0],each[2],each[1],diff])
    return fileList
        

def getCSVFileData(fileName):
    try:
        csvFilePath = os.path.dirname(os.path.dirname(__file__)) + '/util/Analysis/Bad Smells/' + fileName
        with open(csvFilePath) as csvFile:
            readerCSV = csv.reader(csvFile, delimiter=",")
            readerForMethods = []
            count = 0
            for row in readerCSV:
            # row[0]=commit id, row[1]=filename, row[2]=classname, row[3]=isLargeClas, row[4]=indexoffile,
            # row[5]=index of bug, row[6]=number of files in folder, row[7]=foldername
                if count > 0:
                    readerForMethods.append(row)
                count += 1
            csvFile.close()
            return readerForMethods
            
    except Exception as ex:
        print(ex)
        print("Exception occurred in defectAnalysis.checkForDefectAnalysis")

def checkForDefectAnalysis(fileName):
    readerForMethods= getCSVFileData(fileName)
    fileList=[]
    for each in readerForMethods:
        fileListForFolder=createFileListsForEachFolder(readerForMethods, each[7])
        result=checkIfLargeClassSmellLeadToDefect(fileListForFolder)
        if result:
            fileList.append(result)
    return fileList

def removeDuplicatesFromListofList(fileList):
    newFileList= []
    fileList=(list(itertools.chain.from_iterable(fileList))) #merge lists
    for elem in fileList:
        if elem not in newFileList:
            newFileList.append(elem)
    return newFileList

if __name__ == '__main__':
    fileName="LargeClassRelationAnalysis.csv"
    fileList=checkForDefectAnalysis(fileName)
    fileList= removeDuplicatesFromListofList(fileList)
    for each in fileList:
        print(each)