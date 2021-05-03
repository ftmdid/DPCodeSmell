'''
Created on Mar 27, 2019

@author: Neda
'''

import re
import src.runOperations as op
# import src.pythonMethods as pyMethods
import src.parallelInheritance as pih
# from radon.complexity import cc_rank, cc_visit

import src.dataClassSmell as dataClass
import src.lazyClassSmell as lazyClass
import src.longParameterListSmell as longParameterList
import src.largeClassSmell as largeClass
import src.messageChainSmell as messageChain



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
                #totalLine=len(source)
                classes = {}
                current_class = None
                for lineno, line in enumerate(source, start=0):
                    if current_class and not line.startswith(' '):
                        if line != '\n':
                            classes[current_class]['end'] = lineno - 1
                            current_class = None
                            
                    if line.lstrip().startswith('class ') and (":" in line):
                        if (current_class in classes.keys())  and ('end' not in  classes[current_class].keys()):
                            classes[current_class]['end'] = lineno - 1
                            current_class = None
                        if "(" and ")" in line:
                            current_class=line.split('class ')[1].lstrip().split('(')[0].lstrip().rstrip()
                            classes[current_class] = {'start': lineno}
                        else:
                            className=line.split('class ')[1].lstrip().split(':')[0].lstrip().rstrip()
                            if not ' ' in className:
                                current_class=className.lstrip().rstrip()
                                classes[current_class] = {'start': lineno}
                if current_class:
                    #classes[current_class]['end'] = totalLine
                    classes[current_class]['end'] = -1
                return classes
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
                    if re.match(r'def (.+?)( ?\()', each.lstrip()):
                        if 'self'  in each:
                            currentMethod=each.split('def')[1].lstrip().split('(')[0]
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
      
    def getFunctionDefinition(self,methodLines):
        methodDef=""
        for i in range(len(methodLines)):
            if methodLines[i]:
                if re.search(".+\) ?:", methodLines[i]):
                    methodLines[i]=methodLines[i].split(":")[0]+":"
                    methodDef +=methodLines[i]
                    return methodDef
                else:
                    methodDef +=methodLines[i]
                           
        return methodDef
               
    def getFunctionParametersCount(self,methodLines):
        '''
            This method is method level smell and we check if number of parameters is greater 
            than or equal to 5, that is a sign of long parameter list smell. 
        ''' 
        if not (")" and ":" in methodLines[0]):
            methodDef= self.getFunctionDefinition(methodLines)
        else:
            methodDef=methodLines[0]  
            
        funcAttrCount = 0
        line=methodDef
        if ',' in line:
            attrbts = line.split(",")
            funcAttrCount = len(attrbts)
        else:
            funcAttr=line.split("(")[1].split("):")[0]
            if not funcAttr:
                funcAttrCount  
            else:
                funcAttrCount = 1
        return funcAttrCount
    
    def checkForLargeClass(self,fileName):
        try:
            largeClassList= largeClass.calculateLargeClassSmell(fileName)
            return largeClassList
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.checkForLargeClass in "+fileName)
  
    def checkForLongParameterList(self,fileName):
        try:
            longParameterList=longParameterList.calculateLongParameterListSmell(fileName)
            return longParameterList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkLongParameter List in :"+fileName)
       
    def checkForParallelInheritanceHiearchy(self,fileInTheFolder, projectName):
        commitID=op.find_between(fileInTheFolder, "@", "@")
        pythonFile=pih.downloadProjectInASpecificCommit(projectName, commitID)
        pihSmellListDict=pih.calculateParallelInheritanceHiearchySmell(pythonFile)
        parallelInheritanceHiearchyList={}
        try:
            with open(fileInTheFolder, "r") as fileToRead:
                
                lines=fileToRead.readlines()
                classes=self.getClassLinesOfFile(lines)
                
                if classes!=None and len(classes.items())>=1:
                    
                    for key, _ in classes.items(): 
                        if key.lstrip().rstrip() in  pihSmellListDict.keys():
                            parallelInheritanceHiearchyList[key.lstrip().rstrip()]=pihSmellListDict[key.lstrip().rstrip()]
                        else:
                            parallelInheritanceHiearchyList[key.lstrip().rstrip()]={'dit':'none','noc':'none','isPIHSmell':False}  
                fileToRead.close()
            return parallelInheritanceHiearchyList
        
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkForParallelInheritanceHiearchy List in :"+fileInTheFolder)
            
    def checkForLazyClass(self,fileInTheFolder, projectName):
        try:
            lazyClassList=lazyClass.calculateLazyClassSmell(fileInTheFolder, projectName) 
            return lazyClassList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkForLazyClass List in :"+fileInTheFolder)        
        
    def checkForDataClass(self,fileInTheFolder, projectName):
        try:
            dataClassList=dataClass.calculateDataClassSmell(fileInTheFolder, projectName)
            return dataClassList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkForDataClass in :"+fileInTheFolder)
    
    def checkForMessageChain(self,fileName):
        try:
            messageChainList=messageChain.calculateMessageChainSmell(fileName)
            return messageChainList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkForMessageChain in :"+fileName)
    