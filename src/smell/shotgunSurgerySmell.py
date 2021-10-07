'''
    Created on Aug 15, 2021
    @author: neda
'''

import ast
import src.smell.longMethodSmell as lMethod
import src.smell.featureEnvySmell as fEnvy
import src.helper as helperMethods
import src.smell.parallelInheritance as inheritance
from src.runOperations import find_between, getMethodLinesOfClass
from src.removeComments import remove_comments_and_docstrings
import src.BadSmell as smell
import re


def calculateShotgunSurgery(fileInTheFolder, projectName):
    try:
        fileCommitID = find_between(fileInTheFolder, "@", "@")
        filePath= inheritance.downloadProjectInASpecificCommit(projectName, fileCommitID) # project that is modified before bug fix commit

        try:
            parsedWholeFile =  lMethod.parseFile(filePath)
            foreignClassCallOfEachClassInAProject=calculateForeignMethodsOfClassesWithAST(filePath,parsedWholeFile, projectName)
        except Exception as ex:
            foreignClassCallOfEachClassInAProject = calculateForeignMethodsOfClassesWOutAST(filePath,projectName)  
        
        methodResultDict= {}
        classMethodResultDict={}
        try:
            parsedFile =  lMethod.parseFile(fileInTheFolder)
            parsedFileContent = list(ast.walk(parsedFile))
        
        
            for content in parsedFileContent:
                if isinstance(content, ast.ClassDef):
                    methodResult=[]
                    methodResultDict= {}
                    for childNode in list(ast.walk(content)):
                        if isinstance(childNode, ast.FunctionDef): 
                            searchKeyword = content.name +"."+childNode.name
                            methodResult = searchForMethod(searchKeyword, foreignClassCallOfEachClassInAProject)
                            isShotgunSurgery=False
                            if len(methodResult[0])>5 and len(methodResult[1])>4:
                                isShotgunSurgery=True
                            methodResultDict[childNode.name]= {'CM':methodResult[0],'CC':methodResult[1], 'isShotgunSurgery':isShotgunSurgery}
        
                        classMethodResultDict[content.name]=methodResultDict
        except:
            smll = smell.BadSmell()
            classWithMethods={}
            with open(fileInTheFolder,  encoding="utf-8", errors='ignore') as f:
                fileLines= f.read()
                lines= remove_comments_and_docstrings(fileLines).split("\n")
                classes = smll.getClassLinesOfFile(lines)
                classWithMethods= findClassMethods(classes, lines)
                f.close()

            classMethodResultDict={}
            for className, value in classWithMethods.items():
                methodResultDict= {}
                for methodName in value:
                    searchKeyword=className.lstrip().rstrip()+"."+methodName.lstrip().rstrip()
                    methodResult = searchForMethod(searchKeyword, foreignClassCallOfEachClassInAProject)
                    isShotgunSurgery=False
                    if len(methodResult[0])>5 and len(methodResult[1])>4:
                        isShotgunSurgery=True
                    methodResultDict[methodName]= {'CM':methodResult[0],'CC':methodResult[1], 'isShotgunSurgery':isShotgunSurgery}
        
                classMethodResultDict[className]=methodResultDict
        
        return classMethodResultDict 
       
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.calculateShotgunSurgery in "+projectName)

def findClassMethods(classes,lines):
    try:
        classWithMethods={}
        for key, value in classes.items(): 
            classWithMethods[key.lstrip().rstrip()]=[]
            if ('start' and 'end') in value:
                classLines=lines[int(value['start']):int(value['end'])]
                classMethods=checkClassMethods(classLines)
                classWithMethods[key.lstrip().rstrip()]=classMethods
        return classWithMethods
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.findClassMethods")

def checkClassMethods(classLines):
            try:
                methodsList=[]
                for each in classLines:
                    if re.match(r'def(.+?)( ?\()', each.lstrip()) and not (each.lstrip().startswith("#")):
                        currentMethod=each.split('def')[1].lstrip().split('(')[0]
                        methodsList.append(currentMethod.lstrip().rstrip())
                
                return methodsList
            except Exception as ex:
                print(ex)
                print("Exception occurred in BadSmell.checkClassMethodsWithSelf method")  
                
def checkForFunctionaCallsWoutAST(methods, classLines, parentClasses,className,classWithMethods):
    try:
        foreignCallsDict= {}
        string_check= re.compile('[=@!#$%^&*()<>?/\|}{~:]') 
        if  methods:
            for key, value in methods.items():
                funcCall=""
                methodLines= classLines[int(value['start']):int(value['end'])]
                foreignCallsDict[key]=[]
                for line in methodLines:
                    if "self." in line:  
                        if "(" in line: 
                            if string_check.search(line.split("self.")[1].split("(")[0])==None:
                                if line.split("self.")[1].split("(")[0]==line.split("self.")[1].split("(")[0].strip():
                                    funcCall= line.split("self.")[1].split("(")[0]
                            if funcCall in classWithMethods[className]:
                                continue
                            else:
                                for eachParent in parentClasses:
                                    if eachParent in classWithMethods.keys():
                                        if funcCall in classWithMethods[eachParent]:
                                            funcCall= eachParent+"."+funcCall
                                            foreignCallsDict[key].append(funcCall)
                        
                    elif "cls." in line:
                        if "("  in line:  
                            if string_check.search(line.split("cls.")[1].split("(")[0])==None:
                                if line.split("cls.")[1].split("(")[0]==line.split("cls.")[1].split("(")[0].strip():
                                    funcCall= line.split("cls.")[1].split("(")[0]
                            if funcCall in classWithMethods[className]:
                                continue
                            else:
                                for eachParent in parentClasses:
                                    if eachParent in classWithMethods.keys():
                                        if funcCall in classWithMethods[eachParent]:
                                            funcCall= eachParent+"."+funcCall
                                            foreignCallsDict[key].append(funcCall)
                    
                   
                    
                    elif 'super().' in line:
                        funcCall=line.split("super().")[1].split("(")[0]
                        if parentClasses:
                            for eachParent in parentClasses:
                                if eachParent in classWithMethods.keys():
                                    if funcCall in classWithMethods[eachParent]:
                                        funcCall=eachParent+"." +funcCall
                                        foreignCallsDict[key].append(funcCall)
                    else: 
                        if parentClasses:
                            for eachParent in parentClasses:
                                if (eachParent+".") in line:
                                    funcCall=line.split(eachParent+".")[1].split("(")[0]
                                    funcCall= eachParent+"."+funcCall
                                    foreignCallsDict[key].append(funcCall)
        
        return foreignCallsDict
                                       
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.checkForFunctionaCallsWoutAST ")
 

def calculateForeignMethodsOfClassesWOutAST(fileName, projectName):
    try:
        smll = smell.BadSmell()
        with open(fileName,  encoding="utf-8", errors='ignore') as f:
            classDict={}
            fileLines= f.read()
        
            lines= remove_comments_and_docstrings(fileLines).split("\n")
                  
            classes = smll.getClassLinesOfFile(lines)
            
            classWithMethods= findClassMethods(classes, lines)
            if classes!=None and len(classes.items())>=1:
                
                for className, value in classes.items(): 
                    if ('start' and 'end') in value:
                        parentClasses=[]
                        classLines=[]
                        methods={}
                        classLines=lines[int(value['start']):int(value['end'])]
                        methods = getMethodLinesOfClass(classLines)
                        if len(classLines)>0:
                            if "(" and ")" in classLines[0] :
                                if "," in classLines[0]:
                                    parentClasses= classLines[0].split("(")[1].split(")")[0].split(",")
                                    for i in range(len(parentClasses)):
                                        if "." in parentClasses[i]:
                                            parentClasses[i]=parentClasses[i].split(".")[1]
                                            
                                else:
                                    parentClass=classLines[0].split("(")[1].split(")")[0]
                                    if "." in parentClass:
                                        parentClass= parentClass.split(".")[1]
                                    parentClasses.append(parentClass)
                                    
                                parentClasses= [each.lstrip().rstrip() for each in parentClasses]
                                    
                                    
                            
                                
                        foreignCallsDict=checkForFunctionaCallsWoutAST(methods, classLines, parentClasses,className,classWithMethods)
                        classDict[className]=foreignCallsDict 
        f.close()
        return classDict
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.calculateForeignMethodsOfClassesWOutAST in "+projectName)
    
               
def searchForMethod(searchKeyword, dictToBeSearched):
    CM=[]
    CC=[]
    for className, value in dictToBeSearched.items():
        for methodName, v in value.items():
            if searchKeyword in v:
                CM.append(className+"."+methodName)
                CC.append(className)
                
    CM= list(set(CM))
    CC= list(set(CC))
    return [CM,CC]
          
def calculateForeignMethodsOfClassesWithAST(fileName,parsedFile, projectName):
    try:
        # parsedFile =  lMethod.parseFile(fileName)
        parsedFileContent = list(ast.walk(parsedFile))
        classOfFile = getClassesInFile(parsedFileContent)
        #methodsOfFile = getMethodsInFile(parsedFileContent)
        classMethodsOfFile= calculateClassMethods(parsedFileContent) # this has the methods of the classes in the file
        textOfFile = lMethod.readFile(fileName)
        classDict={}
        for content in parsedFileContent:
            if isinstance(content, ast.ClassDef):
                classData=visitClassNode(content,classOfFile, textOfFile, classMethodsOfFile) # returns NIC and foreign calls
                classDict[content.name]=classData[1] 
        return classDict    
         
    except Exception as ex:
        print(ex)
        print("Exception occurred in shotgunSurgerySmell.calculateShotgunSurgery in "+fileName + " of " + projectName)

def calculateClassMethods(parsedFileContent):  
    classDict= {} 
    for content in parsedFileContent:
        if isinstance(content, ast.ClassDef):
            className= content.name
            classDict[className]=[]
            for childNode in list(ast.walk(content)):
                if isinstance(childNode, ast.FunctionDef):
                    methodName= childNode.name
                    classDict[className].append(methodName) 
    return classDict

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
       
def visitClassNode(content,classOfFile, textOfFile, classMethodsOfFile):
    methodsOfClass= fEnvy.getClassMethods(content)
    if hasattr(content, 'bases') and len(content.bases)>0:
        NIC=[]
        NIC.append(content.bases)
        NIC.append(fEnvy.getImportStatementsInClass(content))
        if len(NIC)>0:
            calls=getMethodCallOfEachClass(content,methodsOfClass,classOfFile, textOfFile,classMethodsOfFile)
        return [len(NIC), calls] # calls: AID
    else:
        NIC = []
        NIC.append(fEnvy.getImportStatementsInClass(content))
        if len(NIC)>0:
            calls = getMethodCallOfEachClass(content,methodsOfClass,classOfFile,textOfFile,classMethodsOfFile)
        return [len(NIC), calls]  # calls: AID    

def getImportStatementsInClass(content):
    NIC = 0
    functions = fEnvy.getClassFunctions(content)
    for fnc in functions:
            NIC.append(fEnvy.checkForImportStatementsInFuncDefinition(fnc))
    return NIC        

def checkIfParentClassIsCalled(parentClassList,functionName,textOfFile,childNode):
    return [True for x in parentClassList if x+"."+functionName in textOfFile[childNode.lineno-1].lstrip().rstrip()]
    
def getMethodCallOfEachClass(node,methodsOfClass, classOfFile, textOfFile,classMethodsOfFile):
    
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
                                
                            if (("super()."+functionName) in textOfFile[child.lineno-1].lstrip().rstrip()):
                                if hasattr(node, 'bases'):
                                    if len(node.bases)==1:
                                        if hasattr(node.bases[0],"id"):
                                            superClass = node.bases[0].id
                                        elif hasattr(node.bases[0], "attr"):
                                            superClass = node.bases[0].attr
                                        foreignCalls.append(superClass+"."+functionName)
                                    elif len(node.bases)>1:
                                        superClasses=[]
                                        for i in range(len(node.bases)):
                                            if hasattr(node.bases[i], "id"):
                                                superClasses.append(node.bases[i].id)
                                            elif hasattr(node.bases[i], "attr"):
                                                superClasses.append(node.bases[i].attr)
                                        for superClass in superClasses:
                                            if superClass in classMethodsOfFile.keys():
                                                if (functionName in classMethodsOfFile[superClass]):
                                                    foreignCalls.append(superClass+"."+functionName)      
                                        
                            elif True in checkIfParentClassIsCalled(parentClassList,functionName,textOfFile,child):
                                for x in parentClassList:
                                    if x+"."+functionName  in textOfFile[child.lineno-1].lstrip().rstrip():
                                        foreignCalls.append(x+"."+functionName)
                            else:
                                if functionName in pythonMethods:
                                    continue
                                elif functionName in methodsOfClass:
                                    continue
                                elif functionName in classOfFile: #create an instance of another class
                                    continue 
                                else:
                                    tString = textOfFile[child.lineno-1].lstrip().rstrip()
                                    if "self."+functionName in tString:
                                        if hasattr(node, 'bases'):
                                            if len(node.bases)==1:
                                                superClass=""
                                                if hasattr(node.bases[0], "id"):
                                                    superClass = node.bases[0].id
                                                elif hasattr(node.bases[0], "attr"):
                                                    superClass = node.bases[0].attr
                                                foreignCalls.append(superClass+"."+functionName)
                                            elif len(node.bases)>1:
                                                superClasses=[]
                                                for i in range(len(node.bases)):
                                                    if hasattr(node.bases[i], "id"):
                                                        superClasses.append(node.bases[i].id)
                                                    elif hasattr(node.bases[i], "attr"):
                                                        superClasses.append(node.bases[i].attr)
                                                
                                                for superClass in superClasses:
                                                    if superClass in classMethodsOfFile.keys():
                                                        if (functionName in classMethodsOfFile[superClass]):
                                                            foreignCalls.append(superClass+"."+functionName) 
                                                      
                    
            foreignCalls = helperMethods.removeEmptyStringsFromListOfStrings(foreignCalls)
            foreignCalls = list(set(foreignCalls))
            foreignCallsFromFunc[methodName]=foreignCalls
    return foreignCallsFromFunc   