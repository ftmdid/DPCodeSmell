'''
Created on Mar 27, 2019

@author: Neda
'''

import re
import src.runOperations as op
# import src.pythonMethods as pyMethods

import src.smell.longParameterListSmell as longParameterList
import src.smell.refusedBequestSmell as refusedBequest
import src.smell.dataClassSmell as dataClass
import src.smell.lazyClassSmell as lazyClass
import src.smell.largeClassSmell as largeClass
import src.smell.messageChainSmell as messageChain
import src.smell.longMethodSmell as longMethod
import src.smell.parallelInheritance as pih
import src.smell.featureEnvySmell as fEnvy





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
                            
                    if line.lstrip().startswith('class ') and (":" in line) and not(line.startswith('#')):
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
                    classes[current_class]['end'] = totalLine
                    #classes[current_class]['end'] = -1
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
                
               
    def checkClassMethodsWithSelf(self,classLines):
            try:
                methodsList=[]
                for each in classLines:
                    if re.match(r'def (.+?)( ?\()', each.lstrip()):
                        if 'self'  in each:
                            currentMethod=each.split('def')[1].lstrip().split('(')[0]
                            methodsList.append(currentMethod.lstrip().rstrip())
                
                return methodsList
            except Exception as ex:
                print(ex)
                print("Exception occurred in BadSmell.checkClassMethodsWithSelf method") 
    
    def checkClassMethodsWithCls(self,classLines):
            try:
                methodsList=[]
                for each in classLines:
                    if re.match(r'def (.+?)( ?\()', each.lstrip()):
                        if 'cls'  in each:
                            currentMethod=each.split('def')[1].lstrip().split('(')[0]
                            methodsList.append(currentMethod.lstrip().rstrip())
                
                return methodsList
            except Exception as ex:
                print(ex)
                print("Exception occurred in BadSmell.checkClassMethodsWithCls method") 
    
    def getClassInstanceAttributesWithSelf(self,classLines):
        try:
            attributesList=[]
            for each in classLines:
                if re.match(r'(.+?)?(self\.)(.+)(.+)?', each.lstrip().rstrip()):
                    currentAttribute = re.search(r'(.+?)?(self\.)(.+)(.+)?', each.lstrip().rstrip()).group(3)
                    if ":" in currentAttribute:
                        currentAttribute = currentAttribute.split(":")[0]
                    
                    if "=" in currentAttribute:
                        currentAttribute = currentAttribute.split("=")[0]

                    if "," in currentAttribute:
                        currentAttribute = currentAttribute.split(",")[0]

                    if "." in currentAttribute:
                        currentAttribute = currentAttribute.split(".")[0] 

                    if ")" in currentAttribute:
                        currentAttribute = currentAttribute.split(")")[0] 
                        
                    if not "(" in  currentAttribute: 
                        if "." in currentAttribute:
                            currentAttribute= currentAttribute.split('.')[0]
                           
                        if ' ' in currentAttribute:
                            indx = currentAttribute.index(' ')
                            currentAttribute= currentAttribute[0:indx]
                        
                        if '[' in currentAttribute:
                            currentAttribute= currentAttribute.split('[')[0]
                        
                        if ";" in currentAttribute:
                            currentAttribute = currentAttribute.split(";")[0]
                           
                        
                        attributesList.append(currentAttribute.lstrip().rstrip())  
                     
            return list(set(attributesList)) 
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.getClassInstanceAttributesWithSelf method")  
            
    def getClassInstanceAttributesWithCls(self,classLines):
        try:

            attributesList=[]
            for each in classLines:
                if re.match(r'(.+?)?(cls\.)(.+)(.+)?', each.lstrip().rstrip()):
                    currentAttribute = re.search(r'(.+?)?(cls\.)(.+)(.+)?', each.lstrip().rstrip()).group(3)
                    if ":" in currentAttribute:
                        currentAttribute = currentAttribute.split(":")[0]
                    
                    if "=" in currentAttribute:
                        currentAttribute = currentAttribute.split("=")[0]

                    if "," in currentAttribute:
                        currentAttribute = currentAttribute.split(",")[0]

                    if "." in currentAttribute:
                        currentAttribute = currentAttribute.split(".")[0] 

                    if ")" in currentAttribute:
                        currentAttribute = currentAttribute.split(")")[0] 
                        

                    if not "(" in  currentAttribute: 
                        if "." in currentAttribute:
                            currentAttribute= currentAttribute.split('.')[0]
                           
                        if ' ' in currentAttribute:
                            indx = currentAttribute.index(' ')
                            currentAttribute= currentAttribute[0:indx]
                        
                        if '[' in currentAttribute:
                            currentAttribute= currentAttribute.split('[')[0]
                           
                        
                        attributesList.append(currentAttribute.lstrip().rstrip())  
                          
            return list(set(attributesList)) 
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.getClassInstanceAttributesWithCls method")  

            
    def getClassAttributes(self, classLines):
        try:
            classAttrList=[]
            
            classLineIndex=self.findClassDefinitionLine(classLines)
            firstMethodIndex=self.findFirstMethodDefinitionLine(classLines)
            classLines=classLines[classLineIndex:firstMethodIndex]
            if classLines:
                for each in classLines:
                    if not re.match(r'class (.+)(.+?):',each):
                        if '=' in each:
                            stringToBeSearched=each.split('=')[0]
                            if re.match('    [a-zA-Z0-9]+(.+)?[a-zA-Z0-9]+',stringToBeSearched):
                                classAttrList.append(each.split('=')[0].lstrip().rstrip())
            
            return list(set(classAttrList))
            
        except Exception as ex:
            print(ex)
            print("Exception occurred in BadSmell.getClassAttributesForRefusedBequest method")



                
    def findFirstMethodDefinitionLine(self, classLines):
        for each in classLines:
                if 'def ' in each:
                    return classLines.index(each)
    
    def findClassDefinitionLine(self, classLines):
        for each in classLines:
                if 'class ' in each:
                    return classLines.index(each)                
    
                    
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
            
    def checkForMessageChain(self,fileName):
        try:
            messageChainList=messageChain.calculateMessageChainSmell(fileName)
            return messageChainList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkForMessageChain in :"+fileName)
  
    def checkForLongParameterList(self,fileName):
        try:
            longParameterList=longParameterList.calculateLongParameterListSmell(fileName)
            return longParameterList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkLongParameterList in :"+fileName)
        
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
            
    def checkForRefusedBequest(self,fileInTheFolder, projectName):
        try:
            refusedBequestList=refusedBequest.calculateRefusedBequestSmell(fileInTheFolder, projectName)
            return refusedBequestList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkForRefusedBequest in :"+fileInTheFolder)
    
    def checkForLongMethod(self,fileInTheFolder, projectName):
        try:
            longMethodList=longMethod.calculateLongMethodSmell(fileInTheFolder, projectName)
            return longMethodList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkForRefusedBequest in :"+fileInTheFolder)
            
    def checkForFeatureEnvy(self,fileName, projectName):
        try:
            featureEnvyList=fEnvy.calculateFeatureEnvy(fileName, projectName)
            return featureEnvyList
        except Exception as ex:
            print(ex)
            print("Exception occurrred in BadSmell.checkForFeatureEnvy in :"+fileName)
  
    