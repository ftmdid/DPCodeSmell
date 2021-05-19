'''
Created on May 15, 2021

@author: neda
'''
import ast
import importlib
import inspect
import types

def compareListsForSimiliarItems(x, y):
    return [i for i, j in zip(x, y) if i == j]


def hasSuperClassInExecutableClass(classNode):
    baseClasses = [n.id for n in classNode.bases]
    if baseClasses and len(baseClasses)>0:
        return True
    return False

def getSuperClassesInExecutableClass(classNode):
    baseClasses = [n.id for n in classNode.bases]
    if baseClasses and len(baseClasses)>0:
        return baseClasses
    

def getStartPositionInExecutableClass(objectNode):
    startPosition = objectNode.lineno
    return startPosition

def getEndPositionInExecutableClass(objectNode):
    endPosition = objectNode.end_lineno
    return endPosition

def findMethodsOfAExecutableClass(classNode):
    methodsOfClass = [n for n in classNode.body if isinstance(n, ast.FunctionDef)]
    return methodsOfClass

def findFunctionAttrOfExecutableClass(functionNode):
    functionAttributes = [arg.arg for arg in functionNode.args.args]
    return functionAttributes

def findMethodsOfABuiltinClass(classNode):
    #methodsOfClass= inspect.getmembers(classNode, inspect.isfunction)
    #return methodsOfClass
    methodsOfClass = [nam for nam, obj in vars(classNode).items() if isinstance(obj, types.BuiltinMethodType)]
    return methodsOfClass
    

def findAttributesOfABuiltinClass(classNode):
    attrsOfClass = [nam for nam, obj in vars(classNode).items() if isinstance(obj, types.DynamicClassAttribute)]
    return attrsOfClass
    

def findOverriddenMethods(superClassObj, baseClassObj):
    if checkClassType(superClassObj):
        superClassFuncs = findMethodsOfABuiltinClass(superClassObj)
    else:
        superClassFuncs= [n.name for n in findMethodsOfAExecutableClass(superClassObj)]
    
    baseClassFuncs= [n.name for n in findMethodsOfAExecutableClass(baseClassObj)]

    overRiddenMethods = compareListsForSimiliarItems(superClassFuncs, baseClassFuncs)
    return overRiddenMethods

def findNode(keyword, tree):
    mod = ""
    for each in tree.body:
        if isinstance(each, ast.ClassDef) and each.name==keyword:
            mod = each
    
    if mod == "":
        try:
            mod = importlib.import_module(keyword)
            return mod
        except:
            mod= "Not found"
        
    return mod
    
def checkClassType(clss):
    if type(clss).__module__=="builtins":
        return True
    return False    

    
    
    