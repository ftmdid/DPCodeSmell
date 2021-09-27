'''
Created on Jul 13, 2021

@author: neda
'''
import ast
import src.smell.longMethodSmell as lMethod
import src.pythonMethods as pMethods
import src.helper as helperMethods

def calculateFeatureEnvy(fileName, projectName):
    try:
        featureEnvyDict={}
        methodsOfFile = getMethodsInFile(fileName)
        classOfFile = getClassesInFile(fileName)
        parsedFile =  lMethod.parseFile(fileName)
        parsedFileContent = list(ast.walk(parsedFile))
        textOfFile = lMethod.readFile(fileName)
        totalCalls=0
        for content in parsedFileContent:
            if isinstance(content, ast.ClassDef):
                
                NIC=0
                AID=0
                ALD=0
                className=content.name
                classData=visitClassNode(content, methodsOfFile,classOfFile, textOfFile)
                
                isFeatureEnvy=False
                if classData:
                    NIC = classData[0]
                    AID = len(classData[1])
                    ALD = len(classData[2])
                    totalCalls = len(classData[3])
                    isFeatureEnvy= ((AID>4) and (AID<=totalCalls) and (ALD>3) and (NIC<3))
                featureEnvyDict[className]={'NIC':NIC, 'AID':AID, 'ALD':ALD, 'totalCalls':totalCalls, 'isFeatureEnvy':isFeatureEnvy, 'fName':fileName}    
        return featureEnvyDict
    except Exception as ex:
        print(ex)
        print("Exception occurred in featureEnvySmell.calculateFeatureEnvy in "+fileName + " of " + projectName)
             

def visitClassNode(content, methodsOfFile,classOfFile, textOfFile):
    methodsOfClass= getClassMethods(content)
    if hasattr(content, 'bases') and len(content.bases)>0:
        NIC=[]
        NIC=len(content.bases)
        NIC +=getImportStatementsInClass(content)
        if NIC>0:
            calls=visitFunctionNodeWInheritance(content, methodsOfFile,methodsOfClass,classOfFile, textOfFile)
        else: 
            calls=visitFunctionNodeForClassWoutInheritance(content,methodsOfClass)
        return [NIC, calls[0], calls[1], calls[2]] # calls[0]: AID and calls[1]: ALD, calls[2]: total calls
    else:
        NIC = 0
        NIC = getImportStatementsInClass(content)
        if NIC>0:
            calls = visitFunctionNodeWInheritance(content, methodsOfFile,methodsOfClass,classOfFile,textOfFile)
        else: 
            calls=visitFunctionNodeForClassWoutInheritance(content,methodsOfClass)
        return [NIC, calls[0], calls[1], calls[2]]
def getImportStatementsInClass(content):
    NIC = 0
    functions = getClassFunctions(content)
    for fnc in functions:
            NIC +=len(checkForImportStatementsInFuncDefinition(fnc))
    return NIC
    
def getClassOfParent(content):
    try:
        parentClassList= []
        for i in range(len(content.bases)):
            if hasattr(content.bases[i],'id'):
                parentClassList.append(content.bases[i].id)
            elif hasattr(content.bases[i],'attr'):
                parentClassList.append(content.bases[i].attr)
            elif hasattr(content.bases[i],'value'):
                if hasattr(content.bases[i].value,'id'):
                    parentClassList.append(content.bases[i].value.id)
                elif hasattr(content.bases[i].value,'attr'):
                    parentClassList.append(content.bases[i].value.attr)
                else: 
                    raise Exception("problem with getClassOfParent")
            elif hasattr(content.bases[i], 'func'):
                parentClassList.append(content.bases[i].func.attr)
            
            else:
                raise Exception("problem with getClassOfParent")
                
        return parentClassList
    except Exception as ex:
        print(ex)
        print("Exception occurred in featureEnvySmell.getClassOfParent()")
         

               
def checkForImportStatementsInFuncDefinition(node):
    importedClasses = []
    funcBody =list(ast.walk(node))
    for content in funcBody:
        if isinstance(content, ast.Import):
            importedClasses.append(content)
        elif isinstance(content, ast.ImportFrom):
            importedClasses.append(content)
    return importedClasses
                    
def getClassFunctions(node):
    functions = [n for n in node.body if isinstance(n, ast.FunctionDef)]
    return functions

def visitFunctionNodeWInheritance(node,methodsOfFile,methodsOfClass, classOfFile, textOfFile):
    
    childnodes = list(ast.walk(node))
    pythonMethods = getPythonMethods()
    parentClassList= getClassOfParent(node)
    foreignCalls=[]
    localCalls =[]
    totalCalls=[]
    nodesList=[]
    for childNode in childnodes:
        if isinstance(childNode, ast.FunctionDef):
            for child in list(ast.walk(childNode)):
                if isinstance(child, ast.Call):
                    functionName = visitCall(child)
                    if not ([child.lineno, functionName] in nodesList):
                        nodesList.append([child.lineno, functionName])
                        
                        if "super()."+functionName in textOfFile[child.lineno-1].lstrip().rstrip():
                            if functionName!="super":
                                foreignCalls.append(functionName)
                                totalCalls.append(functionName)
                        elif True in [True for x in parentClassList if x+"."+functionName in textOfFile[child.lineno-1].lstrip().rstrip()]:
                            foreignCalls.append(functionName)
                            totalCalls.append(functionName)
                        else:
                            if functionName in pythonMethods:
                                totalCalls.append(functionName)
                            elif functionName in methodsOfFile:
                                totalCalls.append(functionName)
                            elif functionName in methodsOfClass:
                                localCalls.append(functionName)
                                totalCalls.append(functionName)
                            elif functionName in classOfFile: #create an instance of another class
                                continue 
                            else:
                                tString = textOfFile[child.lineno-1].lstrip().rstrip()
                                if "self."+functionName in tString:
                                    foreignCalls.append(functionName)
                                        
                                totalCalls.append(functionName)
    totalCalls = helperMethods.removeEmptyStringsFromListOfStrings(totalCalls)
    localCalls = helperMethods.removeEmptyStringsFromListOfStrings(localCalls)
    foreignCalls = helperMethods.removeEmptyStringsFromListOfStrings(foreignCalls)
    return [foreignCalls, localCalls,totalCalls]   

                        
def getClassMethods(classNode):
    classMethods =[]
    childnodes = list(ast.walk(classNode))
    for childNode in childnodes:
        if isinstance(childNode, ast.FunctionDef):
            classMethods.append(childNode.name)
    return classMethods

def getMethodsInFile(fileToBeRead):
    methodsOfFile=[]
    parsedFile =  lMethod.parseFile(fileToBeRead)
    parsedFileContent = list(ast.walk(parsedFile))
    for content in parsedFileContent:
        if isinstance(content, ast.FunctionDef):
            funcName = content.name
            funcArgumnts=[a.arg for a in content.args.args]
            if 'self' not in funcArgumnts:
                methodsOfFile.append(funcName)

    return methodsOfFile

def getClassesInFile(fileToBeRead):
    classesOfFile=[]
    parsedFile =  lMethod.parseFile(fileToBeRead)
    parsedFileContent = list(ast.walk(parsedFile))
    for content in parsedFileContent:
        if isinstance(content, ast.ClassDef):
            className = content.name
            #funcArgumnts=[a.arg for a in content.args.args]
            classesOfFile.append(className)

    return classesOfFile

def getPythonMethods():
    pythonMethods = pMethods.builtInFunctions+pMethods.dictionaryMethods+\
                    pMethods.fileMethods + pMethods.listArrayMethods +\
                    pMethods.listArrayMethods + pMethods.setMethods +\
                    pMethods.stringMethods + pMethods.tupleMethods
    pythonMethods = [method.replace('()', '')for method in pythonMethods if '()' in method]
    return pythonMethods
    
def visitCall(node):
    try:
        callID=""
        try:
            callID= node.func.id
        except AttributeError:
            if isinstance(node.func, ast.Attribute):

                if hasattr(node.func, "attr"):
                
                    callID= node.func.attr

            elif isinstance(node.func, ast.Subscript):
                if hasattr(node.func.value, "id"):
                    callID= node.func.value.id
                elif hasattr(node.func.value, "attr"):
                    callID= node.func.value.attr
            else:
                if hasattr(node.func, "func"):
                    if isinstance(node.func.func, ast.Name):
                        callID = node.func.func.id
                    elif isinstance(node.func.func, ast.Attribute):
                        callID = node.func.func.attr
        return callID
    except Exception as ex:
        print(ex)
        print("Exception occurred in featureEnvySmell.visitCall()")
        
        
            
    

def visitFunctionNodeForClassWoutInheritance(node,methodsOfClass):
    
    childnodes = list(ast.walk(node))
    #pythonMethods = getPythonMethods()
    foreignCalls=[]
    localCalls =[]
    totalCalls=[]
    nodesList=[]
    for childNode in childnodes:
        if isinstance(childNode, ast.FunctionDef):
            for child in list(ast.walk(childNode)):
                if isinstance(child, ast.Call):
                    functionName = visitCall(child)
                    if not ([child.lineno, functionName] in nodesList):
                        nodesList.append([child.lineno, functionName])
                        if functionName in methodsOfClass:
                                localCalls.append(functionName)
                                totalCalls.append(functionName)
                        else:   
                            totalCalls.append(functionName)
    totalCalls = helperMethods.removeEmptyStringsFromListOfStrings(totalCalls)
    localCalls = helperMethods.removeEmptyStringsFromListOfStrings(localCalls)
    #foreignCalls = helperMethods.removeEmptyStringsFromListOfStrings(foreignCalls)
    return [foreignCalls, localCalls,totalCalls]  
        