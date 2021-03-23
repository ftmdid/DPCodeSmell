'''
Created on Jun 9, 2020

@author: Neda
'''
import itertools
from builtins import isinstance

# def getClassLinesOfAPythonFile(pythonFile):
#     '''
#         python file is a file that includes all files of a specific commit
#     '''
#     try:
#         classList=[]
#         with open(pythonFile) as fileToRead:
#             fileLines=fileToRead.readlines()
#             count=0
#             for line in fileLines:
#                 if line.lstrip().startswith('class '):
#                     print(line.lstrip())
#                     count +=1
#                     print(count)
#                 if line.lstrip().startswith('class ') and (":" in line):
#                     classList.append(line)
#         fileToRead.close()
#         return classList
#     except Exception as ex:
#         print(ex)       
def getClassLinesOfAPythonFile(pythonFile):
    '''
        python file is a file that includes all files of a specific commit
    '''
    try:
        classList=[]
        with open(pythonFile) as fileToRead:
            fileLines=fileToRead.read()
            #lines=fileLines.splitlines()
            import ast
            tree= ast.parse(fileLines)
            for item in ast.walk(tree):
                if isinstance(item, ast.ClassDef):
                    classList.append(item.line)
#             count=0
#             for line in fileLines:
#                 if line.lstrip().startswith('class ')and (":" in line):
#                     print(line.lstrip())
#                     count +=1
#                     print(count)
#                 if line.lstrip().startswith('class ') and (":" in line):
#                     classList.append(line)
        fileToRead.close()
        return classList
    except Exception as ex:
        print(ex)  
    
def getParentsOfClass(txt, classList):  
    classDict={} 
    if "(" and ")" in txt:
        nameOfClass=txt.split('class ')[1].lstrip().split("(")[0]
        classDict[nameOfClass]=[]
        lineOfSuperClass=txt.split("(")[1].split(")")[0].strip()
        if lineOfSuperClass:
            if "." in lineOfSuperClass:
                superClasses=lineOfSuperClass.split(".")
                for each in superClasses:
                    getParentsOfClass("class "+each, classList)
            else:
                if not lineOfSuperClass in classDict[nameOfClass]:
                    classDict[nameOfClass].append(lineOfSuperClass)
                    
                    getParentsOfClass("class "+lineOfSuperClass, classList)
    else:
        for each in classList:
            if ":" in txt:
                nameOfClass=txt.split("class ")[1].split(":")[0].strip()
            else: 
                nameOfClass=txt.split("class ")[1].strip()
            classDict[nameOfClass]=[]
            if each.startswith(txt):
                if "(" in each:
                    superClass = each.split("(")[0]
                    if superClass==txt:
                        getParentsOfClass(each, classList)
                else:
                    superClass=each.split(":")[0]
                    if superClass==txt:
                        getParentsOfClass(each, classList)
    return classDict
           
   
def getParentsOfClassInAFile(pythonFile):
    classList= getClassLinesOfAPythonFile(pythonFile)
    superClassDict={}
    for each in classList:
        result=getParentsOfClass(each,classList)
        for k, v in result.items():
            if k not in superClassDict.keys():
                superClassDict[k]=v
            else:
                if not v in superClassDict[k]:
                    for item in v:
                        superClassDict[k].append(item)

    return superClassDict

def getNumberOfChildrenOfAClass(parentsDict):
     
    children = {}
    for key in parentsDict.keys():
#         if key=="BaseIntelFCompiler":
#             print("Burdayim")
        children[key]=[]
        for k,valueList in parentsDict.items():
            if len(valueList)==1 and (',' in valueList[0]):
                valueList=[ item.lstrip().rstrip() for item in valueList[0].split(",")]
            if key in valueList:
                children[key].append(k)
         
    return children

def calculateDIT(className, parentsDict, count):        
    if className in parentsDict.keys():
        if not (len(parentsDict[className])==1 and parentsDict[className][0]=='object'):
            count +=len(parentsDict[className])
            parentsList= parentsDict[className]
            if len(parentsList)>=1:
                for i in range(0, len(parentsList)):
                    if (parentsList[i]!='object'):
                        count = calculateDIT(parentsList[i], parentsDict, count)
    return count
                    
def calculateNumberOfChildren(className, childrensDict, count):
    if className in childrensDict.keys():
            count +=len(childrensDict[className])
            childrensList= childrensDict[className]
            if len(childrensList)>=1:
                for i in range(0, len(childrensList)):
                    count = calculateNumberOfChildren(childrensList[i], childrensDict, count)
    return count   

def calculateParallelInheritanceHiearchySmell(pythonFile):

    pihSmellListDict={}
    parents=getParentsOfClassInAFile(pythonFile)
    print(len(parents))

    childrens= getNumberOfChildrenOfAClass(parents)
  
    
    keysList=list(set(list(parents.keys())+list(childrens.keys())))
    print(len(keysList))
    for key in keysList:
        if key=="CPUInfoBase":
            print("yere")
        dit = calculateDIT(key, parents, 1)
        #noc = calculateNumberOfChildren(key, childrens, 0)
        noc = len(childrens[key])
        pihSmell= False
        if dit>3 or noc>4:
            pihSmell= True
        pihSmellListDict[key]={'dit':dit,'noc':noc,'isPIHSmell':pihSmell}
        #print(pihSmellListDict)
    return pihSmellListDict
    
            
            

if __name__ == '__main__':
    pythonFile="/Users/neda/Desktop/workspace/BadSmells/util/Zip/numpy/allPythonFiles.py" 
    pihSmellListDict = calculateParallelInheritanceHiearchySmell(pythonFile)
#     for k, v in  pihSmellListDict.items():
#         print(k,v)


























