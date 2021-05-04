'''
Created on May 4, 2021

@author: neda
'''
from radon.complexity import cc_visit
from src.cohesion.lcom import LCOM4
from src.cohesion.reflection import ModuleReflection
import src.BadSmell as smll
import ast


def getASTClassName(moduleReflectionObject):
    astClasses=moduleReflectionObject.classes()
    astClassesList=[]
    for elem in astClasses:
        astClassesList.append(elem.name().rpartition('.')[-1])
    return astClassesList

def calculateClassComplexity(x,className):
    classComplexityList=[]
    complexty=0
    for each in x:
        if each.letter=='M':
            if each.classname==className.lstrip().rstrip():
                complexty += each.complexity
                classComplexityList.append([each.fullname,each.complexity])
    return (classComplexityList,complexty)


def calculateDataClassSmell(fileInTheFolder, projectName):
    dataClassList={}
    smell = smll.BadSmell()
    try: 
        with open(fileInTheFolder, encoding="utf-8", errors='ignore') as f:  #for numpy
            lines = f.readlines()
            classes = smell.getClassLinesOfFile(lines)
            linsStr = "".join(lines)
            x = cc_visit(linsStr)
            temp = fileInTheFolder
            fixturs = ModuleReflection.from_file(temp)
                    
            fixtursClasses = getASTClassName(fixturs)  # this is to eliminate the classes within comment
            temp = temp[:-3]
            temp = temp.replace("/", ".")
            temp = temp[1:]
                         
            if classes != None and len(classes.items()) >= 1:
                         
                for key, _ in classes.items(): 
                    if key in fixtursClasses:
                        if  '__init__' in fileInTheFolder:
                            temp = temp.replace('__init__', "")
                        if '__main__' in fileInTheFolder:
                            temp = temp.replace('__main__', '')
                        
                        className = temp + "." + key
                        ref = fixturs.class_by_name(className)
                        lcom = LCOM4().calculate(ref)
                                     
                        # classComplexityList,complexty=calculateClassComplexity(x, clss)
                        _, complexty = calculateClassComplexity(x, key)
             
                        isDataClass = False
                        if (lcom > 1 or complexty > 50):
                            isDataClass = True                      
                                                            
                        dataClassList[key] = {'wmc':complexty, 'lcom':lcom, 'isDataClass':isDataClass}
             
            f.close()
            return dataClassList
    except (TypeError or SyntaxError or TabError) as ex2:
        #pass
        print(ex2.tostring() + "occurred, but it continues")
    except Exception as ex:
        print(ex)  
        print("Exception occurrred in " + projectName + " dataClassSmell.calculateDataClassSmell in :" + fileInTheFolder)


def isValidPythonFile(fname):
    '''
    Referenced from: https://stackoverflow.com/questions/35796360/how-to-validate-the-syntax-of-a-python-script
    '''
    #with open(fname, encoding='windows-1252') as f:
    with open(fname) as f:
    #with open(fname, encoding="utf8", errors='ignore') as f:
        contnts = f.read()
    try:
        ast.parse(contnts)
        #or compile(contents, fname, 'exec', ast.PyCF_ONLY_AST)
        return True
    except SyntaxError:
        return False                
    
