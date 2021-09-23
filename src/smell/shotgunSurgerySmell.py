'''
Created on Aug 15, 2021
Modified on Sept 15, 2021
@author: neda
'''
import ast
import src.smell.longMethodSmell as lMethod
import src.smell.featureEnvySmell as fEnvy
import src.helper as helperMethods
import src.smell.parallelInheritance as inheritance
from src.runOperations import find_between



def calculateShotgunSurgery(fileInTheFolder, projectName):
    #fileCommitID = find_between(fileInTheFolder, "@", "@")
    #filePath= inheritance.downloadProjectInASpecificCommit(projectName, fileCommitID) # project that is modified before bug fix commit
    #foreignClassCallOfEachClassInAProject=calculateForeignMethodsOfClasses(filePath, projectName)
    foreignClassCallOfEachClassInAProject=calculateForeignMethodsOfClasses(fileInTheFolder, projectName)
    parsedFile =  lMethod.parseFile(fileInTheFolder)
    parsedFileContent = list(ast.walk(parsedFile))
    methodResultDict= {}
    classMethodResultDict={}
    for content in parsedFileContent:
        if isinstance(content, ast.ClassDef):
            methodResult=[]
            for childNode in list(ast.walk(content)):
                if isinstance(childNode, ast.FunctionDef): 
                    searchKeyword = content.name +"."+childNode.name
                    methodResult = searchForMethod(searchKeyword, foreignClassCallOfEachClassInAProject)
                    methodResultDict[childNode.name]= {'CM':methodResult[0],'CC':methodResult[1]}
            classMethodResultDict[content.name]=methodResultDict
    return classMethodResultDict
    
                   
def searchForMethod(searchKeyword, dictToBeSearched):
    CM=[]
    CC=[]
    for className, value in dictToBeSearched.items():
        for methodName, v in value.items():
            if searchKeyword in v:
                CM.append(methodName)
                CC.append(className)
    return [CM,CC]
          


def calculateForeignMethodsOfClasses(fileName, projectName):
    try:
        #methodsOfFile = fEnvy.getMethodsInFile(fileName)
        #classOfFile = fEnvy.getClassesInFile(fileName)
        parsedFile =  lMethod.parseFile(fileName)
        parsedFileContent = list(ast.walk(parsedFile))
        classOfFile = getClassesInFile(parsedFileContent)
        methodsOfFile = getMethodsInFile(parsedFileContent)
        textOfFile = lMethod.readFile(fileName)
        classDict={}
        for content in parsedFileContent:
            if isinstance(content, ast.ClassDef):
                classData=visitClassNode(content, methodsOfFile,classOfFile, textOfFile) # returns NIC and foreign calls
                classDict[content.name]=classData[1] 
        return classDict  
        
        # for content in parsedFileContent:
        #     if isinstance(content, ast.ClassDef):
        #         for childNode in list(ast.walk(content)):
        #             if isinstance(childNode, ast.FunctionDef): 
        #                 searchKeyword = content.name +"."+childNode.method
            
    
        
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.calculateShotgunSurgery in "+fileName + " of " + projectName)


def getClassesInFile(parsedFileContent):
    classOfFile = []
    for content in parsedFileContent:
        if isinstance(content, ast.ClassDef):
            classOfFile.append(content.name)
    return classOfFile

def getMethodsInFile(parsedFileContent):
    methodsOfFile=[]
    for content in parsedFileContent:
        if isinstance(content, ast.ClassDef):
            continue
        elif isinstance(content, ast.FunctionDef):
            methodsOfFile.append(content.name)
    return methodsOfFile
    
          
def visitClassNode(content, methodsOfFile,classOfFile, textOfFile):
    methodsOfClass= fEnvy.getClassMethods(content)
    if hasattr(content, 'bases') and len(content.bases)>0:
        NIC=[]
        NIC.append(content.bases)
        NIC.append(fEnvy.getImportStatementsInClass(content))
        if len(NIC)>0:
            calls=getMethodCallOfEachClass(content, methodsOfFile,methodsOfClass,classOfFile, textOfFile)
        return [len(NIC), calls] # calls: AID
    else:
        NIC = []
        NIC.append(fEnvy.getImportStatementsInClass(content))
        if len(NIC)>0:
            calls = getMethodCallOfEachClass(content, methodsOfFile,methodsOfClass,classOfFile,textOfFile)
        return [len(NIC), calls]  # calls: AID    

def getImportStatementsInClass(content):
    NIC = 0
    functions = fEnvy.getClassFunctions(content)
    for fnc in functions:
            NIC.append(fEnvy.checkForImportStatementsInFuncDefinition(fnc))
    return NIC        

def checkIfParentClassIsCalled(parentClassList,functionName,textOfFile,childNode):
    return [True for x in parentClassList if x+"."+functionName in textOfFile[childNode.lineno-1].lstrip().rstrip()]
    
def getMethodCallOfEachClass(node,methodsOfFile,methodsOfClass, classOfFile, textOfFile):
    
    childnodes = list(ast.walk(node))
    pythonMethods = fEnvy.getPythonMethods()
    parentClassList= fEnvy.getClassOfParent(node)
    foreignCallsFromFunc={}
    foreignCalls=[]
    nodesList=[]
    for childNode in childnodes:
        if isinstance(childNode, ast.FunctionDef):
            foreignCalls=[]
            methodName = childNode.name
            for child in list(ast.walk(childNode)):
                if isinstance (child, ast.Call):     
                            functionName = fEnvy.visitCall(child)
                            if not ([child.lineno, functionName] in nodesList):
                                nodesList.append([child.lineno, functionName])
                                
                                if "super()."+functionName in textOfFile[child.lineno-1].lstrip().rstrip():
                                    if hasattr(childNode, 'bases') and len(childNode.bases)>0:
                                        if len(childNode.bases)==1:
                                            superClass = childNode.bases[0].id
                                            if functionName!="super":
                                                foreignCalls.append(superClass+"."+functionName)
                                        
                                elif True in checkIfParentClassIsCalled(parentClassList,functionName,textOfFile,child):
                                    for x in parentClassList:
                                        if x+"."+functionName  in textOfFile[child.lineno-1].lstrip().rstrip():
                                            foreignCalls.append(x+"."+functionName)
                                else:
                                    if functionName in pythonMethods:
                                        continue
                                    elif functionName in methodsOfFile:
                                        continue
                                    elif functionName in methodsOfClass:
                                        continue
                                    elif functionName in classOfFile: #create an instance of another class
                                        continue 
                                    else:
                                        tString = textOfFile[child.lineno-1].lstrip().rstrip()
                                        if "self."+functionName in tString:
                                            if hasattr(childNode, 'bases') and len(childNode.bases)>0:
                                                if len(childNode.bases)==1:
                                                    superClass = childNode.bases[0].id
                                                    foreignCalls.append(superClass+"."+functionName)      
                    
            foreignCalls = helperMethods.removeEmptyStringsFromListOfStrings(foreignCalls)
            foreignCalls = list(set(foreignCalls))
            foreignCallsFromFunc[methodName]=foreignCalls
    return foreignCallsFromFunc   