'''
Created on Jul 13, 2021

@author: neda
'''
import ast
import src.longMethodSmell as lMethod
import src.pythonMethods as pMethods



def visitClassNode(content, methodsOfFile):
    methodsOfClass= getClassMethods(content)
    if hasattr(content, 'bases') and len(content.bases)>0:
        NIC=len(content.bases)
        calls=visitFunctionNode(content, methodsOfFile,methodsOfClass)
        return [NIC, calls[0], calls[1], calls[2]] # calls[0]: AID and calls[1]: ALD, calls[2]: total calls
                
def visitFunctionNode(node,methodsOfFile,methodsOfClass):
    foreignCalls=[]
    localCalls =[]
    totalCalls=[]
    pythonMethods = getPythonMethods()
    childnodes = list(ast.walk(node))
    for childNode in childnodes:
        if isinstance(childNode, ast.FunctionDef):
            for child in list(ast.walk(childNode)):
                if isinstance(child, ast.Call):
                    functionName= visitCall(child)
                    if functionName in pythonMethods:
                        totalCalls.append(functionName)
                    elif functionName in methodsOfFile:
                        totalCalls.append(functionName)
                    elif functionName in methodsOfClass:
                        localCalls.append(functionName)
                        totalCalls.append(functionName)
                    else:
                        foreignCalls.append(functionName) 
                        totalCalls.append(functionName)
    return [foreignCalls, localCalls,totalCalls]               
                    
                    
def visitCall(node):
    callID=""
    try:
        callID= node.func.id
    except AttributeError:
        if isinstance(node.func, ast.Attribute):
            callID = node.func.attr
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
        # else:
        #     print("here")
    return callID

def getClassMethods(classNode):
    classMethods =[]
    childnodes = list(ast.walk(classNode))
    for childNode in childnodes:
        if isinstance(childNode, ast.FunctionDef):
            classMethods.append(childNode.name)
    return classMethods

def getMethodsInFile(fileToBeRead):
    methodsOfFile=[]
    #fileLines = lMethod.readFile(fileToBeRead)
    parsedFile =  lMethod.parseFile(fileToBeRead)
    parsedFileContent = list(ast.walk(parsedFile))
    for content in parsedFileContent:
        if isinstance(content, ast.FunctionDef):
            funcName = content.name
            funcArgumnts=[a.arg for a in content.args.args]
            if 'self' not in funcArgumnts:
                methodsOfFile.append(funcName)

    return methodsOfFile

def getPythonMethods():
    pythonMethods = pMethods.builtInFunctions+pMethods.dictionaryMethods+\
                    pMethods.fileMethods + pMethods.listArrayMethods +\
                    pMethods.listArrayMethods + pMethods.setMethods +\
                    pMethods.stringMethods + pMethods.tupleMethods
    pythonMethods = [method.replace('()', '')for method in pythonMethods if '()' in method]
    return pythonMethods
    
            
            
        








        