'''
Created on Jun 9, 2020

@author: Neda
'''
import ast
import tokenize
def getClassListInAPythonFile(pythonFile):
    #pythonFile="/Users/Neda/OneDrive - Auburn University/PhDworkspace/BadSmells/DemoProjects/numpy/allPythonFiles.py" 
    '''
        python file is a file that includes all files in a specific commit
    '''
    try:    
        classList=[]
        with tokenize.open(pythonFile) as fle:
            parsedFile = ast.parse(fle.read(), pythonFile)
            for item in ast.walk(parsedFile):
                if isinstance(item, ast.ClassDef):
                    lineNo=item.lineno
                    with open(pythonFile,'r') as f: # read a specific line from a text file
                        linesVariables=f.readlines()
                        classLine=linesVariables[lineNo-1]
                        classList.append(classLine)
                        f.close()
                fle.close()
            return classList
    except Exception as ex:
        print(ex)       
    
def calculateDIT(className, classList):  
    count=2 # one the class itself and plus object  
    classDict={} 

    if '(' and ')' in className:
        clsName=className.split('class')[1].lstrip().split("(")[0]
        classDict[clsName]=[]
        count+=1
#         if clsName=="lapack_ilp64_opt_info":
#             print(clsName)
        superClass= className.split("(")[1].split(")")[0]
        
        superClassList=[]
        if not ("," in superClass):
            if "." in superClass:
                superClass=superClass.split(".")[0]
            classDict[clsName].append(superClass)
            if not getClassNameFromList(superClass, classList):
                calculateDIT(superClass,classList)
        else:
            superClassList=superClass.split(",")
            for item in superClassList:
                count+=1
                if "." in superClass:
                    item=item.split(".")[0]
                classDict[clsName].append(item)
                if not getClassNameFromList(item, classList):
                    calculateDIT(item,classList)
                
    else:
        clsName=className.split('class')[1].lstrip().split(":")[0]
        classDict[clsName]=[]
    return [count,classDict]
           
    

def getClassNameFromList(className, classList):
    for each in classList:
        if className in each:
            return  each
    return False 
    
def getDIT(pythonFile):
    allClassDictForChildren={}
    classList= getClassListInAPythonFile(pythonFile)
    for each in classList:
        result=calculateDIT(each,classList)
        #depthOfInheritanceTree=result[0]  # count of dit
        clsName=list(result[1])[0]
        values=result[1][clsName]
        allClassDictForChildren[clsName]=values

    return allClassDictForChildren

def calculateNumberOfChildren(classDictionary):
    children={}
    numberOfChildren={}
    for i in classDictionary.values():

        if len(i)==1:
            children[i[0]]=[]
            for k,v in classDictionary.items():
                if i[0] in v:
                    children[i[0]].append(k)
        elif len(i)>1:
            for each in i: 
                if not each in children.keys():
                    children[each]=[]
                for k,v in classDictionary.items():
                   
                    if each in v:
                        children[each].append(k)
        
                            
    for k, v in children.items():
        numberOfChildren[k]=len(children[k])
    return [children, numberOfChildren]

pythonFile="/Users/Neda/OneDrive - Auburn University/PhDworkspace/BadSmells/DemoProjects/numpy/allPythonFiles.py" 
dit=getDIT(pythonFile)
ancestorClassesForEachClass=dit #Ancestor of each class























