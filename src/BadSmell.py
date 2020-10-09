'''
Created on Mar 27, 2019

@author: Neda
'''

import ast
import inspect
import os
import importlib.util
import re
import src.runOperations as op
import src.pythonMethods as pyMethods

class BadSmell(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
       
    def getClassLinesOfFile(self,source):
        '''
            Some part of it is referenced from: https://stackoverflow.com/questions/58142456/how-to-get-the-scope-of-a-class-in-terms-of-starting-line-and-end-line-in-python
        '''
        try:
                totalLine=len(source)
                classes = {}
                current_class = None
                for lineno, line in enumerate(source, start=0):
                    if current_class and not line.startswith(' '):
                        if line != '\n':
                            classes[current_class]['end'] = lineno - 1
                            current_class = None
            
                    if line.lstrip().startswith('class ') and ('=' not in line) and ('(' and ')' in line) and (":" in line):
                        current_class = re.search(r'class (.+?)(?:\(|:)', line).group(1)
                        classes[current_class] = {'start': lineno}
                    
                if current_class:
                    classes[current_class]['end'] = totalLine
                    #classes[current_class]['end'] = -1
                return classes
    #             fle.close()
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.getClassLinesOfFile method")
    
    def getMethodsLinesOfFile(self,fileName):
        try:
            with open(fileName,'r') as fle:
                source=fle.readlines()
                totalLine=len(source)
                methods = {}
                current_method = None
                for lineno, line in enumerate(source, start=0):
                    if current_method and not line.startswith(' '):
                        if line != '\n':
                            methods[current_method]['end'] = lineno - 1
                            current_method = None
                    if re.match(r'def (.+?)( ?\()', line.lstrip()):
                        if 'self' not in line:
#                     if line.lstrip().startswith('def ') and ('self' not in line) and ('(' and ')' in line) and( ":" in line):
#                     #if line.lstrip().startswith('def') and ('=' not in line) and ('(' and ')' in line) and( ":" in line):
                        #current_method = re.search(r'def (.+?)(?:\(|:)', line).group(1)
                            current_method=line.split('def')[1].lstrip().split('(')[0]
                            methods[current_method] = {'start': lineno}
            
                if current_method:
                    methods[current_method]['end'] = totalLine
                    #methods[current_method]['end'] = -1
                fle.close()
                return methods
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.getMethodsLinesOfFile method")
               
    def checkClassMethods(self,classLines):
            try:
                methodsList=[]
                for each in classLines:
                    if 'def' in each and 'self' in each:
                        if each.lstrip().startswith('def ') and (('(self' in each) or('(self,' in each)) and ("(" and ")" in each) and( ":" in each):
                            currentMethod = re.search(r'def (.+?)(?:\(|:)', each).group(1)
                            methodsList.append(currentMethod)
                
                return len(methodsList)
            except Exception as ex:
                print(ex)
                print("Exception occurred in BadSmell.checkClassMethods method") 
    
    def getClassAttribututes(self,classLines):
        try:
            classLines = op.strip_blanklines(classLines)
            nondoctring = op.strip_docstring(classLines)
            noncomment = op.strip_comments(nondoctring, '#')
            classLines=noncomment.split('\n')
            attributesList=[]
            for each in classLines:
                if each.lstrip().startswith('self.') and ('=' in each):
                    currentAttribute = re.search(r'self.(.+?)=', each).group(1)
                    attributesList.append(currentAttribute)
            return len(list(set(attributesList))) 
        except Exception as ex:
            print(ex)
            print("Exception occurred in getClassAttributes method")   
                    
    def getClassName(self,classLines):
        current_class=""
        for each in classLines:
            if each.lstrip().startswith('class'):
                current_class = re.search(r'class (.+?)(?:\(|:)', each).group(1)
        return current_class
      
    def checkForLargeClass(self,fileName):
        try:
            with open(fileName, "r") as f:
                classesList={}
                lines=f.readlines()
                classes=self.getClassLinesOfFile(lines)
                classLOC = 0
                classMethodCount= 0
                classAttr = 0
                
                if classes!=None and len(classes.items())>=1:
                    
                    for key, value in classes.items():  
                        if 'start' and 'end' in value:  
                            classLines=lines[int(value['start']):int(value['end'])]
                            if len(classLines)>0:
                                classLinesStr="\n".join(classLines)
                                classLOC=op.loc(classLinesStr)['net']
                                #classLOC=int(value['end'])-int(value['start'])
                                classMethodCount=self.checkClassMethods(classLines)
                                classAttr=self.getClassAttribututes(classLinesStr)
                                isLargeClass=False
                                if (classLOC>=200) or (classAttr+classMethodCount>40):
                                    isLargeClass=True
                                classesList[key]={'classLOC':classLOC,'classMethodCount':classMethodCount,'classAttributesCount':classAttr,'isLargeClass':isLargeClass }
                return classesList
                
            f.close()
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.checkForLargeClass in "+fileName)
    
    def getFunctionDefinition(self,methodLines):

        methodDef=""
        for i in range(len(methodLines)):
            if methodLines[i]:
                if re.search(".+\) ?:", methodLines[i]):
                    methodLines[i]=methodLines[i].split(":")[0]+":"
#                     if re.search(".+\) ?:", methodLines[i]):
                    methodDef +=methodLines[i]
                    return methodDef
                else:
                    methodDef +=methodLines[i]
                       
                    
                    
        return methodDef
#             
    '''
            This method is method level smell and we check if number of parameters is greater 
            than or equal to 5, that is a sign of long parameter list smell. 
    '''        
    def getFunctionParametersCount(self,methodLines):
        if not (")" and ":" in methodLines[0]):
            methodDef= self.getFunctionDefinition(methodLines)
        else:
            methodDef=methodLines[0]
         
#         methodDef=methodDef.split(":")[0].rstrip()    
            
        funcAttrCount = 0
        line=methodDef
        if ',' in line:
#             lines=line.split(":")[0]
            attrbts = line.split(",")
            funcAttrCount = len(attrbts)
        else:
            funcAttr=line.split("(")[1].split("):")[0]
            if not funcAttr:
                funcAttrCount  
            else:
                funcAttrCount = 1
        return funcAttrCount
                
            
    
    def checkForLongParameterList(self,fileName):
        try:
            with open(fileName, "r") as fileToBeRead:
                if fileName=="/Users/neda/git/Research/BadSmells/DemoProjects/numpy/numpy/compat/_inspect.py":
                    print("Come on you can do this!")
                lines= fileToBeRead.readlines()
                methodsParameterList={}
                methodParameterCount=0
                methodsLines=self.getMethodsLinesOfFile(fileName)
                if methodsLines!=None and len(methodsLines.items())>=1:
                    #for key, value in methodsLines.items():
                    for key in methodsLines:  
                        if key=="formatargspec":
                            print("Hadi yapabilirsin")
                        value=methodsLines[key]
                        if 'start' and 'end' in value:  
                            if value['end']>value['start']:
                                methodLines=lines[int(value['start']):int(value['end'])]
                            if value['end']==value['start']:
                                methodLines=lines[int(value['start']):int(value['start'])+1]
                            methodLOC=op.get_line_count("".join(methodLines))
                            methodParameterCount=self.getFunctionParametersCount(methodLines)
                            isLongParameterList=False
                            if methodParameterCount>=5:
                                isLongParameterList=True
                            methodsParameterList[key]={'methodLoc':methodLOC,'methodParameterCount':methodParameterCount,'isLongParameterList':isLongParameterList}
                return methodsParameterList
            fileToBeRead.close()
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkLongParameter List in :"+fileName)
     
       
    def checkForMessageChain(self,fileName):
        try:
            messageChainDictForTheFile={}
            with open(fileName, "r") as fileToBeRead:
                lines= fileToBeRead.readlines()
                for line in lines: 
                    if ")." in line or (") ." in line):
                        messageChain=self.checkForChain(line,0)
                        isMessageChain=False
                        if messageChain>=4:
                            isMessageChain=True
                        messageChainDictForTheFile[line.lstrip().rstrip()]={'messageChainCount':messageChain,'isMessageChain':isMessageChain}
    #         for k,v in  messageChainDictForTheFile.items():
    #             print(v)
            return messageChainDictForTheFile
        except Exception as ex:
            print(ex)
            print("Exception occurred in checkForMessageChain of "+fileName)

    def checkForChain(self,textToBeChecked, messageCount):
        
    
    #     pythonMethods=[]
        pythonMethods=pyMethods.builtInFunctions+pyMethods.dictionaryMethods+pyMethods.fileMethods+pyMethods.listArrayMethods+pyMethods.setMethods+pyMethods.stringMethods+pyMethods.tupleMethods
       
        if ")." in textToBeChecked:
           
            #patternFound=find_between(textToBeChecked, ").", "(")
            patternIndex=textToBeChecked.find(").")
            restOfStr=textToBeChecked[patternIndex+2:]
            methodStartIndex=restOfStr.find("(")
            #methodEndIndex=restOfStr.find(")")
            methodName=restOfStr[:methodStartIndex]
            
            if len(methodName)>0:
                if (methodName+"()" in pythonMethods):
                    return messageCount
                else:
                    return self.checkForChain(restOfStr,messageCount+1)
            else:
                return messageCount
            messageCount=len(methodName)
        else:
            return messageCount
            
    
    
    
    
    def getDepthOfInheritanceTreeOfClass(self):
        pythonFile = self.fileOp.createOnePythonFile() # create allPythonFiles.py in util folder
        self.fileOp.checkPythonFile(pythonFile) # This is added due to SyntaxError: from __future__ imports must occur at the beginning of the file
    
#         try:
        #pythonFile="/Users/Neda/OneDrive - Auburn University/PhDworkspace/BadSmells/DemoProjects/numpy/allPythonFiles.py" 
        _, tail=os.path.split(pythonFile)
        spec = importlib.util.spec_from_file_location(tail, pythonFile)
        foo = importlib.util.module_from_spec(spec)
        print("module is imported")
        spec.loader.exec_module(foo)   
        print("module is executed")
        try:
            with open(pythonFile) as f:
                source= f.read()
                #compile(source,pythonFile,'exec')
                tree = ast.parse(source)
                print("module is parsed")
                for exp in tree.body:
                    if isinstance(exp, ast.ClassDef): #print exp.name
                        cls = getattr(foo, exp.name)
                        print(inspect.getmro(cls))
                            
                    f.close()                      
            
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkLongParameter List in :"+pythonFile)
    
    







#         