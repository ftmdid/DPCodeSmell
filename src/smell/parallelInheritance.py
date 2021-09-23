'''
Created on Jun 9, 2020

@author: Neda
'''

import wget
import os
import zipfile
from src.FileOperations import FileOperations
import shutil
# import src.runOperations as op

def checkIfFileExistsInFolder(projectPath, commitID):
    for name in os.listdir(projectPath):
        if commitID in name:
            return name               
    return False  
  
def downloadProjectInASpecificCommit(projectName, commitID):
    try:
        fileOp=FileOperations(projectName)
        outputDirectory = os.path.dirname(os.path.dirname(__file__)) + '/util/Zip'
        if 'src' in outputDirectory:
            outputDirectory = outputDirectory.replace('src/','')
        projectFolder = os.path.join(outputDirectory, projectName)
        isFileExists=checkIfFileExistsInFolder(projectFolder, commitID)
        if isFileExists!=False:
            pythonFile=isFileExists 
            print("project file exists, there is no need to download the "+projectName+" project with version id: "+ commitID)
            return os.path.join(projectFolder,pythonFile)
        
        if not os.path.isdir(projectFolder):
            os.mkdir(projectFolder)
        configFileData= fileOp.readYMLFile()[projectName]['url']
        url = "https://github.com/"+configFileData + "/archive/" + commitID + ".zip"
        #url = "https://github.com/numpy/numpy/archive/" + commitID + ".zip"
        wget.download(url, out=outputDirectory)
        for item in os.listdir(outputDirectory):
            if item.endswith(".zip"):
                fileName = os.path.join(outputDirectory, os.path.basename(item))
                with zipfile.ZipFile(os.path.join(fileName), "r") as zipObj:
                    zipObj.extractall(os.path.join(outputDirectory, projectName))
                zipObj.close()
                os.remove(fileName)
            
        print(projectName +" project with version id: "+commitID+" is downloaded and saved to the local folder")
       
        projectPath = os.path.join(os.path.dirname(os.path.dirname(__file__)) + '/util/Zip', projectName)
                
        pythonFile = fileOp.createOnePythonFile(projectPath, projectName, commitID)
        print(projectName +" project with version id: "+commitID+" is saved to one file")
        for name in os.listdir(projectPath):
            dirToDel = os.path.join(projectPath, name)
            if os.path.isdir(dirToDel):
                shutil.rmtree(dirToDel)
        print(projectName +" project with version id: "+commitID+" is deleted")
    
        return pythonFile  
    except Exception as ex:
        print(ex)
        print("Exception occurrred in parallelInheritance.downloadProjectInASpecificCommit() in project: "+projectName +" with commitID: "+commitID) 
   
def getClassLinesOfAPythonFile(pythonFile):
    '''
        python file is a file that includes all files of a specific commit
    '''
    try:
        classList=[]
        with open(pythonFile) as fileToRead:
            fileLines=fileToRead.readlines()
            for line in fileLines:
                if line.lstrip().startswith('class ') and (":" in line):
                    if "(" and ")" in line:
                        if ":" in line:
                            classList.append(line.lstrip().rstrip())
                    elif not ("(" and ")" in line):
                        if ":" in line:
                            classList.append(line.lstrip().rstrip())
        fileToRead.close()
        return classList
    except Exception as ex:
        print(ex)   
        print("Exception occurrred in parallelInheritanceHierarchy.getClassLinesOfAPythonFile()")
        
def getAllClassesInACommit(classLine):
    try:
        classesInACommit=[]
        for each in classLine:
            if each:
                if len(each.split(":")[1])>0:
                    each = each.split(":")[0]+":"
                if "(" and ")" in each:
                    child=each.split('class ')[1].split("(")[0].lstrip().rstrip()
                    if child not in classesInACommit:
                        classesInACommit.append(child)
                    if ("." not in each) and ("," not in each): 
                        parent= each.split("(")[1].split(")")[0]
                        if parent and (parent not in classesInACommit):
                            classesInACommit.append(parent)
                    elif ("." in each) and ("," not in each):
                        parent=each.split("(")[1].split(")")[0].split(".")[1]
                        if parent and (parent not in classesInACommit):
                            classesInACommit.append(parent)
                        parentsOfParent=each.split("(")[1].split(")")[0].split(".")[0]
                        if parentsOfParent and (parentsOfParent not in classesInACommit):
                            classesInACommit.append(parentsOfParent)
                    elif ("." not in each) and ("," in each):
                        parents=each.split("(")[1].split(")")[0].split(",")
                        for parent in parents:
                            if parent and (parent not in classesInACommit):
                                classesInACommit.append(parent)
                    elif ("." in each) and ("," in each):
                        parents=each.split("(")[1].split(")")[0].split(",")
                        for parent in parents:
                            if "." in parent:
                                if parent.split(".")[1] and (parent.split(".")[1] not in classesInACommit):
                                    classesInACommit.append(parent.split(".")[1])
                                if parent.split(".")[0]  and (parent.split(".")[0] not in classesInACommit):
                                    classesInACommit.append(parent.split(".")[0])
                else:
                    if not each.split('class ')[1].split(":")[0].lstrip().rstrip() in classesInACommit:
                        classesInACommit.append(each.split('class ')[1].split(":")[0].lstrip().rstrip())
        
        return classesInACommit
    except Exception as ex:
        print(ex)
        print("Exception occurrred in parallelInheritance.getAllClassesInACommit()")
    
def getParentsOfAClassesInACommit(classList):
    try:
        parentOfClassDict={}
        for each in classList:
            if each:
                if len(each.split(":")[1])>0:
                    each = each.split(":")[0]+":"
                if "(" and ")" in each:
                    child=each.split('class ')[1].split("(")[0].lstrip().rstrip()
                    parentOfClassDict[child]=[]
                    if ("." not in each) and ("," not in each): 
                        parent= each.split("(")[1].split(")")[0].lstrip().rstrip()
                        if parent!=child:
                            parentOfClassDict[child].append(parent)
                    elif ("." in each) and ("," not in each):
                        parent=each.split("(")[1].split(")")[0].split(".")[1].lstrip().rstrip()
                        if parent!=child:
                            parentOfClassDict[child].append(parent)
                        parentOfClassDict[parent]=[]
                        if parent!=each.split("(")[1].split(")")[0].split(".")[0]:
                            parentOfClassDict[parent].append(each.split("(")[1].split(")")[0].split(".")[0].lstrip().rstrip())
                    elif ("." not in each) and ("," in each):
                        parents=each.split("(")[1].split(")")[0].split(",")
                        for parent in parents:
                            if child!=parent.lstrip().rstrip():
                                parentOfClassDict[child].append(parent.lstrip().rstrip())
                    elif ("." in each) and ("," in each):
                        parents=each.split("(")[1].split(")")[0].split(",")
                        for parent in parents:
                            if "." in parent.lstrip().rstrip():
                                if child!=parent.split(".")[1].lstrip().rstrip():
                                    parentOfClassDict[child].append(parent.split(".")[1].lstrip().rstrip())
                                parentOfClassDict[parent.split(".")[1].lstrip().rstrip()]=[]
                                if parent.split(".")[1].lstrip().rstrip()!=parent.split(".")[0].lstrip().rstrip():
                                    parentOfClassDict[parent.split(".")[1].lstrip().rstrip()].append(parent.split(".")[0].lstrip().rstrip())
                else:
                    child=each.split('class ')[1].split(":")[0].lstrip().rstrip()
                    parentOfClassDict[child]=['object']
        return parentOfClassDict
    except Exception as ex:
        print(ex)
        print("Exception occurrred in parallelInheritance.getParentsOfAClassesInACommit()")
                
def calculateDIT(className, parentsDict, count):   
    try:     
        if className in parentsDict.keys():
            parents=parentsDict[className]
            if (len(parents)==1) and (parents[0]=='object'):
                count =1
            elif (len(parents)==1) and (parents==['']):
                count=1
            elif (len(parents)>=1):
                count += calculateDIT(parents[0], parentsDict, count)  
                                 
        return count
    
    except Exception as ex:
        print(ex)
        print("Exception occurrred in parallelInheritance.calculateDIT()")
                 
           
def getNumberOfChildrenOfClassesInACommit(keys, classLines):
    try:
        childClassesDict={}
        for key in keys:
            childClasses=[]
            for eachClassLine in classLines:
                if "(" and ")" in eachClassLine:
                    if "," in eachClassLine:
                        parentClasses = eachClassLine.split("(")[1].split(")")[0].split(",")
                        for parent in parentClasses:
                            if "." in parent:
                                parent = parent.split(".")[1]
                                if parent==key:
                                    childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
                            else:
                                if parent==key:
                                    childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
                    else:
                        parentClass=eachClassLine.split("(")[1].split(")")[0]
                        if "." in parentClass:
                            parentClass= parentClass.split(".")[1]
                            if parentClass==key:
                                childClasses.append(parentClass)
                        else:
                            if parentClass==key:
                                childClasses.append(parentClass)
            childClassesDict[key]=childClasses
        return childClassesDict
    except Exception as ex:
        print(ex)
        print("Exception occurrred in parallelInheritance.getNumberOfChildrenOfClassesInACommit()")

def calculateNumberOfChildren(key, classLines):
    try:
        childClasses=[]
        for eachClassLine in classLines:
            if "(" and ")" in eachClassLine:
                if "," in eachClassLine:
                    parentClasses = eachClassLine.split("(")[1].split(")")[0].split(",")
                    for parent in parentClasses:
                        if "." in parent:
                            if parent.split(".")[1]==key:
                                childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
                            elif parent.split(".")[0]==key:
                                childClasses.append(parent.split(".")[1])
                        else:
                            if parent==key:
                                childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
                else:
                    parentClass=eachClassLine.split("(")[1].split(")")[0]
                    if "." in parentClass:
                        if parentClass.split(".")[1]==key:
                            childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
                        elif parentClass.split(".")[0]==key:
                            childClasses.append(parentClass.split(".")[1])
                    elif "[" and "]" in parentClass:
                        if parentClass.split("[")[0]==key:
                            childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
        
                    else:
                        if parentClass==key:
                            childClasses.append(eachClassLine.split("(")[0].split("class ")[1].lstrip().rstrip())
        
        childClasses = list(dict.fromkeys(childClasses))
        return len(childClasses)
    except Exception as ex:
        print(ex)
        print("Exception occurrred in parallelInheritance.calculateNumberOfChildren()")
                 
    
def calculateParallelInheritanceHiearchySmell(pythonFile, projectName):
    try:
        pihSmellListDict={}
        
        classLines= getClassLinesOfAPythonFile(pythonFile)
        
        parents= getParentsOfAClassesInACommit(classLines)
        
        keysList=getAllClassesInACommit(classLines)
        if len(keysList)>=1:
            for key in keysList:
                if key!='object':
                    dit = calculateDIT(key, parents, 1)
                    
                    noc = calculateNumberOfChildren(key, classLines)
                
                    pihSmell= False
                    if dit>3 or noc>4:
                        pihSmell= True
                    pihSmellListDict[key]={'dit':dit,'noc':noc,'isPIHSmell':pihSmell}
                
        return pihSmellListDict
    except Exception as ex:
        print(ex)
        print("Exception occurrred in parallelInheritance.calculateParallelInheritanceHiearchySmell()" + " in "+ pythonFile + " of "+ projectName)
     

'''
if __name__ == '__main__':
    pythonFile="/Users/neda/Desktop/workspace/BadSmells/util/Zip/numpy/allPythonFilesIn_numpy_withCommitID_8eb6424.py" 
    pihSmellListDict = calculateParallelInheritanceHiearchySmell(pythonFile)
 
'''
