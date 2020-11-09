
'''
Created on Sep 15, 2020

@author: neda
'''


import os
import src.BadSmell as BS
import csv
import src.helper as help
import src.parallelInheritance as inheritance

import src.defectAnalysis as defectAnalysis


def getMethodFilesInProject(pythonFiles, validationFolder):
    methodsListForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/methodsListForTool.csv'
    methodsListForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, methodsListForTool), 'w+'))
    methodsListForToolCSVfileOut.writerow(['Method Name', 'start LOC', 'File Name'])
    for each in pythonFiles:
        methods = getRequestedItemFiles(each, 'def')
        if methods:
            for k, v in methods.items():
                methodsListForToolCSVfileOut.writerow([k, methods[k]['start'], each])
                
def getClassFilesInProject(pythonFiles, validationFolder):
    classListForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/classListForTool.csv'
    classListForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, classListForTool), 'w+'))
    classListForToolCSVfileOut.writerow(['Class Name', 'start LOC', 'File Name'])
    for each in pythonFiles:
        classes = getRequestedItemFiles(each, 'class')
        if classes:
            for k, v in classes.items():
                classListForToolCSVfileOut.writerow([k, classes[k]['start'], each])
    

def getLargeClassInfoInProject(pythonFiles, badSmellDetection, validationFolder):
    
    largeClassValidationForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/LargeClassValidationForTool.csv'
    largeClassValidationForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, largeClassValidationForTool), 'w+'))
    largeClassValidationForToolCSVfileOut.writerow(['Class Name', 'Class LOC', 'class method count', 'class Attribute count', 'File Name'])
    for each in pythonFiles:
        result = badSmellDetection.checkForLargeClass(each)
        if result:
            for key, value in result.items():
                if str(result[key]['isLargeClass']) == str(True):
                    largeClassValidationForToolCSVfileOut.writerow([key, result[key]['classLOC'], result[key]['classMethodCount'], result[key]['classAttributesCount'], each])

def getLongParameterListSmellsInProject(pythonFiles, badSmellDetection, validationFolder):
    longParamaterValidationForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/longParamaterValidationForTool.csv'
    longParamaterForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, longParamaterValidationForTool), 'w+'))
    longParamaterForToolCSVfileOut.writerow(['Method Name', 'Method LOC', 'method parameter count', 'File Name'])
    for each in pythonFiles:
        result = badSmellDetection.checkForLongParameterList(each)
        if result:
            for key, value in result.items():
                if str(result[key]['isLongParameterList']) == str(True):
                    #print(result)
                    longParamaterForToolCSVfileOut.writerow([key, result[key]['methodLoc'], result[key]['methodParameterCount'], each])


def getRequestedItemFiles(fileName, requestedItem):
        '''
            Some part of it is referenced from: https://stackoverflow.com/questions/58142456/how-to-get-the-scope-of-a-class-in-terms-of-starting-line-and-end-line-in-python
        '''
        try:
            with open(fileName,'r') as fle:
                source= fle.readlines()
                totalLine=len(source)
                currentItem = None
                items={}
                for lineno, line in enumerate(source, start=0):
                    if currentItem and not line.startswith(' '):
                        if line != '\n':
                            items[currentItem]['end'] = lineno - 1
                            currentItem = None
            
                    if line.lstrip().startswith(requestedItem) and ('=' not in line) and ('(' and ')' in line) and (":" in line):
                        if not 'self,' in line.lstrip().split(')')[0].split('(')[1]:
                            currentItem = line.lstrip().split('(')[0].split(requestedItem)[1].lstrip().rstrip()
                            items[currentItem] = {'start': lineno}
                
                if currentItem:
                    items[currentItem]['end'] = -1
           
                return items
                fle.close()
        except Exception as ex:
            print(ex)
            print("Exception occurred in getRequestedItemFiles method")
                

# def getParallelInheritanceHiearchOfAFile():

if __name__ == '__main__':
    
    #projectPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'DemoProjects/numpy')
    projectName="numpy"
    pythonFiles= help.getAllPythonFilesInProject(projectName)
    
    print("There are "+str(len(pythonFiles)) + " in total")
    
    badSmellDetection = BS.BadSmell()
    
    validationFolder = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation'
 
    parallelInheritanceHiearchyValidationForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/parallelInheritanceHiearchyValidationForTool.csv'
    parallelInheritanceHiearchyForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, parallelInheritanceHiearchyValidationForTool), 'w+'))
    parallelInheritanceHiearchyForToolCSVfileOut.writerow(['Class Name', 'Depth of Inheritance', 'Number of Children' ,'Is Parallel Inheritance Hiearchy Smell'])

    parallelInheritanceHiearchySmellListDict={}
    pythonFile="/Users/neda/Desktop/workspace/BadSmells/util/Zip/numpy/allPythonFiles.py" 
    parallelInheritanceHiearchySmellListDict= inheritance.calculateParallelInheritanceHiearchySmell(pythonFile)
     
    for k, _ in parallelInheritanceHiearchySmellListDict.items():
        parallelInheritanceHiearchyForToolCSVfileOut.writerow([k, parallelInheritanceHiearchySmellListDict[k]['dit'],parallelInheritanceHiearchySmellListDict[k]['noc'],parallelInheritanceHiearchySmellListDict[k]['isPIHSmell']])
       
    #getLargeClassInfoInProject(pythonFiles, badSmellDetection, validationFolder)
         
  
    #getClassFilesInProject(pythonFiles, validationFolder)
                 
    #getMethodFilesInProject(pythonFiles, validationFolder)
    
    #getLongParameterListSmellsInProject(pythonFiles, badSmellDetection, validationFolder)
 
#     messageChainValidationForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/messageChainValidationForTool.csv'
#     messageChainValidationForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, messageChainValidationForTool), 'w+'))
#     messageChainValidationForToolCSVfileOut.writerow(['Line', 'Message Chain Count', 'Is Message Chain', 'File Name'])
#     for each in pythonFiles:
#         result = badSmellDetection.checkForMessageChain(each)
#         if result:
#             for key, value in result.items():
#                 if str(result[key]['isMessageChain']) == str(True):
#                     #print(result)
#                     messageChainValidationForToolCSVfileOut.writerow([key, result[key]['messageChainCount'], result[key]['isMessageChain'], each])
#


    