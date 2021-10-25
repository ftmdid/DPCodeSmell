'''
Created on Jun 14, 2021

@author: neda
'''

import ast
import tokenize
import intervaltree
#import src.BadSmell as smll

def calculateLongMethodSmell(fileName, projectName):
    try:
        #smell=smll.BadSmell()
        longMethodDict={}
        fileToBeRead = fileName
        fileLines = readFile(fileToBeRead)
        parsedFile =  parseFile(fileToBeRead)
        parsedFileContent = list(ast.walk(parsedFile))
        methodLinesOfCode=0
        methodName=""
        
        for content in parsedFileContent:
            isLargeClass=False
            if isinstance(content, ast.ClassDef):
                #className = content.name
                classLinesOfCode = countLines(content)
                        
                classMethods = findClassFuncNodes(content)
                classMethodCounts = len(classMethods)
                        
                classAttributes = getClassAttributes(content) 
                classAttributesCounts  = len(classAttributes)
                 
                isLargeClass = ((classLinesOfCode>=200) or ((classMethodCounts + classAttributesCounts)>40))
                isLongMethod = False
                for classMethod in classMethods:
                    methodName = classMethod.name
                    methodLinesOfCode = countLines(classMethod)
                    if methodLinesOfCode>30:
                        isLongMethod = True
                    longMethodDict[methodName]={'mName':methodName, 'mLOC':methodLinesOfCode,'isLongMethod': isLongMethod,'isClassMethod':'Yes', 'isLargeClass':isLargeClass, 'fName':fileToBeRead}
                
            elif isinstance(content, ast.FunctionDef):
                methodLinesOfCode=0
                methodName=""
                if checkIfRegMethod(content, fileLines):
                    methodLinesOfCode = countLines(content)
                    methodName = content.name
                    isLongMethod = False
                    if methodLinesOfCode>30:
                        isLongMethod= True
                    longMethodDict[methodName]={'mName':methodName, 'mLOC':methodLinesOfCode,'isLongMethod': isLongMethod,'isClassMethod':'No', 'isLargeClass':isLargeClass, 'fName':fileToBeRead}
        return longMethodDict
    except Exception as ex:
        print(ex)
        print("Exception occurred in longMethodSmell.calculateLongMethodSmell in "+fileName + " of " + projectName)

def countLines(node):
    '''
        https://github.com/chenzhifei731/Pysmell/blob/master/pysmell/detection/astChecker.py
    '''
    childnodes = list(ast.walk(node))
    lines = set()
    for n in childnodes:
     
        if hasattr(n, 'lineno'):
            lines.add(n.lineno)
    return len(lines)
    
def getClassAttributes(node):
    attributesList=[]
    classNode = list(ast.walk(node))
    for n in classNode:
        if isinstance(n, ast.Attribute) or isinstance(n, ast.Assign):
            if hasattr(n, 'targets'):
              
                if hasattr(n.targets[0], "value") and hasattr(n.targets[0].value, "id"):
                    if len(n.targets) == 1 and isinstance(n.targets[0], ast.Attribute) and n.targets[0].value.id=="self":
                        attributesList.append(n.targets[0].attr)
    return list(set(attributesList))

    

def parseFile(filename):
    '''
        Referenced from:https://julien.danjou.info/finding-definitions-from-a-source-file-and-a-line-number-in-python/
        with tokenize.open(filename) as f:
            return ast.parse(f.read(), filename=filename)
    '''
    try:
    #with open(filename, 'r',encoding="utf-8", errors='ignore') as f:
        with open(filename,'r',encoding="utf-8", errors='ignore') as f:
            content = f.read()
            parsedFile = ast.parse(content)
            return parsedFile
    except Exception as ex:
        print(ex)

def findClassFuncNodes(node):
    funcNodes=[]
    fileContent= list(ast.walk(node))
    for item in fileContent:
        if isinstance(item, ast.FunctionDef):
            funcNodes.append(item)
    return funcNodes



def findFuncNodes(node,fileLines):
    funcNodes={}
    fileContent= list(ast.walk(node))
    for item in fileContent:
        if isinstance(item, ast.FunctionDef):
            if 'self' not in fileLines[item.lineno]:
                #calledFuncs = findCallMethods(item) # this returns the  [node of called methods]
                funcNodes.append(item)
                #funcNodes[item.name]=[item, calledFuncs]
    return funcNodes

def checkIfRegMethod(node, fileLines):
    if isinstance(node, ast.FunctionDef):
        if 'self' not in fileLines[node.lineno]:
            return True
    return False
    
def findClassFuncs(node):
    classFuncs = []
    fileContent= list(ast.walk(node))
    for content in fileContent:
        if isinstance(content, ast.FunctionDef):
            classFuncs.append(content)
    return classFuncs



def computeInterval(node):
    '''
        Referenced from:https://julien.danjou.info/finding-definitions-from-a-source-file-and-a-line-number-in-python/
    '''
    min_lineno = node.lineno
    max_lineno = node.lineno
    for node in ast.walk(node):
        if hasattr(node, "lineno"):
            min_lineno = min(min_lineno, node.lineno)
            max_lineno = max(max_lineno, node.lineno)
    return (min_lineno, max_lineno + 1)
            
def fileToTree(filename):
    '''
        Referenced from:https://julien.danjou.info/finding-definitions-from-a-source-file-and-a-line-number-in-python/
    '''
    with tokenize.open(filename) as f:
        parsed = ast.parse(f.read(), filename=filename)
    tree = intervaltree.IntervalTree()
    for node in ast.walk(parsed):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start, end = computeInterval(node)
            tree[start:end] = node
    return tree   

def readFile(fileName):
    #fileLines=[]
    with open(fileName,"r", encoding="utf-8", errors='ignore') as f:
        fileLines = f.readlines()
        f.close()
    return fileLines
          
# for feature envy
def findCallMethods(node):
    funcNodes = list(ast.walk(node))
    funcCalls=[]
    for n in funcNodes:
        if isinstance(n,ast.Call):
            funcCalls.append(n)
            
    return funcCalls
