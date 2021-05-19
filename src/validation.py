'''
Created on Sep 15, 2020

@author: neda
'''


import os
import src.BadSmell as BS
import csv
import src.helper as help
import src.parallelInheritance as inheritance
from future.builtins.misc import isinstance
# from radon import complexity


#import src.defectAnalysis as defectAnalysis


def getMethodFilesInProject(pythonFiles, validationFolder):
    methodsListForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/methodsListForTool.csv'
    methodsListForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, methodsListForTool), 'w+'))
    methodsListForToolCSVfileOut.writerow(['Method Name', 'start LOC', 'File Name'])
    for each in pythonFiles:
        methods = getRequestedItemFiles(each, 'def')
        if methods:
            for k, _ in methods.items():
                methodsListForToolCSVfileOut.writerow([k, methods[k]['start'], each])
                
def getClassFilesInProject(pythonFiles, validationFolder):
    classListForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/classListForTool.csv'
    classListForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, classListForTool), 'w+'))
    classListForToolCSVfileOut.writerow(['Class Name', 'start LOC', 'File Name'])
    for each in pythonFiles:
        classes = getRequestedItemFiles(each, 'class')
        if classes:
            for k, _ in classes.items():
                classListForToolCSVfileOut.writerow([k, classes[k]['start'], each])
    
def getLargeClassInfoInProject(pythonFiles, badSmellDetection, validationFolder):
    
    largeClassValidationForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/LargeClassValidationForTool.csv'
    largeClassValidationForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, largeClassValidationForTool), 'w+'))
    largeClassValidationForToolCSVfileOut.writerow(['Class Name', 'Class LOC', 'class method count', 'class Attribute count', 'File Name'])
    for each in pythonFiles:
        result = badSmellDetection.checkForLargeClass(each)
        if result:
            for key, _ in result.items():
                if str(result[key]['isLargeClass']) == str(True):
                    largeClassValidationForToolCSVfileOut.writerow([key, result[key]['classLOC'], result[key]['classMethodCount'], result[key]['classAttributesCount'], each])

def getLongParameterListSmellsInProject(pythonFiles, badSmellDetection, validationFolder):
    longParamaterValidationForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/longParamaterValidationForTool.csv'
    longParamaterForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, longParamaterValidationForTool), 'w+'))
    longParamaterForToolCSVfileOut.writerow(['Method Name', 'Method LOC', 'method parameter count','is Long Parameter List', 'File Name'])
    for each in pythonFiles:
        result = badSmellDetection.checkForLongParameterList(each)
        if result:
            for key, _ in result.items():
                #if str(result[key]['isLongParameterList']) == str(True):
                    #print(result)
                    longParamaterForToolCSVfileOut.writerow([key, result[key]['methodLoc'], result[key]['methodParameterCount'], str(result[key]['isLongParameterList']),each])

def getMessageChainInProject(pythonFiles, badSmellDetection, validationFolder):
    messageChainValidationForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/messageChainValidationForTool.csv'
    messageChainValidationForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, messageChainValidationForTool), 'w+'))
    messageChainValidationForToolCSVfileOut.writerow(['Line', 'Message Chain Count', 'Is Message Chain', 'File Name'])
    for each in pythonFiles:
        result = badSmellDetection.checkForMessageChain(each)
        if result:
            for key, _ in result.items():
                if str(result[key]['isMessageChain']) == str(True): #print(result)
                    messageChainValidationForToolCSVfileOut.writerow([key, result[key]['messageChainCount'], result[key]['isMessageChain'], each])

def getRequestedItemFiles(fileName, requestedItem):
        '''
            Some part of it is referenced from: https://stackoverflow.com/questions/58142456/how-to-get-the-scope-of-a-class-in-terms-of-starting-line-and-end-line-in-python
        '''
        try:
            with open(fileName,'r') as fle:
                source= fle.readlines()
                #totalLine=len(source)
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
                
def getParallelInheritanceHierarchySmellInProject(validationFolder, os):
    parallelInheritanceHiearchyValidationForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/parallelInheritanceHiearchyValidationForTool.csv'
    parallelInheritanceHiearchyForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, parallelInheritanceHiearchyValidationForTool), 'w+'))
    parallelInheritanceHiearchyForToolCSVfileOut.writerow(['Class Name', 'Depth of Inheritance', 'Number of Children', 'Is Parallel Inheritance Hiearchy Smell'])
    pythonFile = "/Users/neda/Desktop/workspace/BadSmells/util/Validation/ToolValidation/allPythonFiles.py"
    parallelInheritanceHiearchySmellListDict = inheritance.calculateParallelInheritanceHiearchySmell(pythonFile)
    for k, _ in parallelInheritanceHiearchySmellListDict.items():
        parallelInheritanceHiearchyForToolCSVfileOut.writerow([k, parallelInheritanceHiearchySmellListDict[k]['dit'], parallelInheritanceHiearchySmellListDict[k]['noc'], parallelInheritanceHiearchySmellListDict[k]['isPIHSmell']])

def getLazyClassInProject(badSmellDetection, validationFolder):
    lazyClassValidationForTool = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation/lazyClassValidationForTool.csv'
    lazyClassForToolCSVfileOut = csv.writer(open(os.path.join(validationFolder, lazyClassValidationForTool), 'w+'))
    lazyClassForToolCSVfileOut.writerow(['Class Name', 'Number of Methods', 'Number of Attributes', 'Depth of Inheritance', 'Is Lazy Class Smell'])
    pythonFile = "/Users/neda/Desktop/workspace/BadSmells/util/Validation/ToolValidation/allPythonFiles.py"
    pihSmellListDict = inheritance.calculateParallelInheritanceHiearchySmell(pythonFile)
    lazyClassList = {}
    with open(pythonFile, "r") as f:
        lines = f.readlines()
        classes = badSmellDetection.getClassLinesOfFile(lines)
        classMethodCount = 0
        classAttr = 0
        dit = 0
        if classes != None and len(classes.items()) >= 1:
            for key, value in classes.items():
                classLines = lines[int(value['start']):int(value['end'])]
                if len(classLines) > 0:
                    classLinesStr = "\n".join(classLines)
                    classMethodCount = badSmellDetection.checkClassMethods(classLines)
                    classAttr = badSmellDetection.getClassAttribututes(classLinesStr)
                    if key.lstrip().rstrip() in pihSmellListDict.keys():
                        dit = pihSmellListDict[key]['dit']
                    else:
                        dit = "none"
                    isLazyClass = False
                    print("classMethodCount=" + str(classMethodCount) + " classAttributesCount=" + str(classAttr) + " dit=" + str(dit) + " isLazyClass=" + str(isLazyClass))
                    if dit != "none":
                        if (classMethodCount < 5 and classAttr < 5) or dit < 2:
                            isLazyClass = True
                        lazyClassList[key] = {'classMethodCount':classMethodCount, 'classAttributesCount':classAttr, 'dit':dit, 'isLazyClass':isLazyClass}
    
    f.close()
    for k, _ in lazyClassList.items():
        lazyClassForToolCSVfileOut.writerow([k, lazyClassList[k]['classMethodCount'], lazyClassList[k]['classAttributesCount'], lazyClassList[k]['dit'], lazyClassList[k]['isLazyClass']])


    
if __name__ == '__main__':
    
    #projectPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'DemoProjects/numpy')
    projectName="numpy"
    pythonFiles= help.getAllPythonFilesInProject(projectName)
    
    #print("There are "+str(len(pythonFiles)) + " in total")
    
    badSmellDetection = BS.BadSmell()
    
    validationFolder = os.path.dirname(os.path.dirname(__file__)) + '/util/Validation/ToolValidation'
    
   
    
    #getLargeClassInfoInProject(pythonFiles, badSmellDetection, validationFolder)
         
  
    #getClassFilesInProject(pythonFiles, validationFolder)
                 
    #getMethodFilesInProject(pythonFiles, validationFolder)
    
    #getLongParameterListSmellsInProject(pythonFiles, badSmellDetection, validationFolder)
 
    #getMessageChainInProject(pythonFiles, badSmellDetection, validationFolder)
    
    #getParallelInheritanceHierarchySmellInProject(validationFolder)
     
    #getLazyClassInProject(badSmellDetection, validationFolder)
             
    
    def getClassName(instance):
        return instance.__class__.__name__
    #fileName= os.path.join(validationFolder,"allPythonFilesIn_keras_withCommitID_0a9c0ca4.py")
    fileName= os.path.join(validationFolder,"untitled.py")
    
    
    import ast
    import inspect

    
    with open(fileName, "r") as source:
        contents=source.read()
        lines=contents.split("\n")
        tree = ast.parse(contents) 
        for each in tree.body:
           

            if isinstance(each, ast.ClassDef):
                print(each)
                print(each.name)
                
                import src.refusedBequest as rb
      
                # baseClssStartPosition = rb.getStartPosition(each)
                # print(baseClssStartPosition)
                # baseClssEndPosition = rb.getEndPosition(each)
                # print(baseClssEndPosition)
                #
                baseClssFunctions = rb.findMethodsOfAExecutableClass(each)
                
                if rb.hasSuperClassInExecutableClass(each):
                    superClss=rb.getSuperClassesInExecutableClass(each)
                    if len(superClss)==1:
                        superClssNode = rb.findNode(superClss[0], tree)
                       
                        if rb.checkClassType(superClssNode):
                            print("builtin")
                            superClssFunctions = rb.findMethodsOfABuiltinClass(superClssNode)   
                        else:
                            superClssFunctions =rb.findMethodsOfAExecutableClass(superClssNode)
                
                        
                        print(dir(superClssNode))
                        print(rb.findOverriddenMethods(superClssNode, each))
                        





                # baseClss=each.bases
                # if baseClss and len(baseClss)>0:
                #     #print(dir(baseClss[0])) 
                #     membrs= inspect.getmembers(each)
                #     #indx = membrs.index('__dict__')
                #     for itm in membrs:
                #         if '__dict__' in itm:
                #             for fncs in (itm[1]['body']):
                #                 print(inspect.getmembers(fncs))                           
                    
                    #print(list(set(dir(baseClss[0])) - set(dir(each))))
                    
                # for itm in (inspect.getmembers(each)):
                #     print(itm)
                #

    '''
    
                baseClss=each.bases
                print(baseClss)
                if baseClss and len(baseClss)>0:
                    for i in range(len(baseClss)):
                        print(baseClss[i].id)
                
                #print(each.bases.id)
                print(lines[each.lineno-1])
                
                for classItem in each.body:
                    print(classItem)
                    if isinstance(classItem, ast.FunctionDef):
                        for fncItem in classItem.body:
                            print(fncItem)
                           
    '''
    
    
    
    print("Done with validation!")


    