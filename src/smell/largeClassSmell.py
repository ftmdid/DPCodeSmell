'''
Created on May 4, 2021

@author: neda
'''

import src.BadSmell as smll
import src.runOperations as op
import src.removeComments as rC

def calculateLargeClassSmell(fileName):
    try:
        smell=smll.BadSmell()
        #with open(fileName, "r") as f:
        with open(fileName,  encoding="utf-8", errors='ignore') as f:
            classesList={}
            fileLines= f.read()
            
            lines = rC.remove_comments_and_docstrings(fileLines).split('\n')
            
            classes=smell.getClassLinesOfFile(lines)
            
                
            if classes!=None and len(classes.items())>=1:
                
                for key, value in classes.items(): 
                    classLOC = 0
                    classMethodCount= 0
                    classInsAttr = 0 
                    classAttr = 0 
                    if 'start' and 'end' in value:  
                        classLines=lines[int(value['start']):int(value['end'])]
                        if len(classLines)>0:
                            classLinesStr="\n".join(classLines)
                            classLOC=op.loc(classLinesStr)['net']
                            classMethodCount=len(smell.checkClassMethodsWithSelf(classLines))
                            classInsAttr=len(smell.getClassInstanceAttributesWithSelf(classLines))
                            classAttr = len(smell.getClassAttributesForRefusedBequest(classLines))
                            
                            classInsAttr += classAttr
                            isLargeClass=False
                            if (classLOC>=200) or (classAttr+classMethodCount>40):
                                isLargeClass=True
                            classesList[key]={'classLOC':classLOC,'classMethodCount':classMethodCount,'classAttributesCount':classInsAttr,'isLargeClass':isLargeClass }
            return classesList
                
        f.close()
    except Exception as ex:
        print(ex)
        print("Exception occurred in largeClassSmell.calculateLargeClassSmell in "+fileName)