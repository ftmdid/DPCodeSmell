'''
Created on May 18, 2018

@author: neda
'''


import re



def getCommonData(list1, list2): 
    """ Returns the similiarities between two lists"""
    similiarities = []
    for x in list1: # traverse in the 1st list 
        for y in list2: # traverse in the 2nd list 
            if x == y: # if one common 
                similiarities.append(x)                  
    return similiarities 

def getDifference(list1, list2): 
    """ Returns the differences between two lists"""
    return (list(set(list1) - set(list2)))
   
def listToString(s):  
    """Returns string and accepts list. It converts list to string """
    str1 = ""  # initialize an empty string 
    for ele in s:  # traverse in the string 
        str1 += ele   
    return str1  

"""Line 36 to 71 is from https://gist.github.com/quandyfactory/1671909 """
def get_line_count(blob):
    """Returns the number of lines of code"""
    lines=blob.split('\n')
    return len(lines)

def strip_docstring(blob):
    """Removes docstrings from code"""
    docstring = True
    while docstring == True:
        match_docstring = re.search('\n\s*"""[^"""]*"""', blob)
        if not match_docstring:
            docstring = False
        else:
            blob = blob.replace(blob[match_docstring.span()[0]:match_docstring.span()[1]], '')
    return blob

def strip_blanklines(blob):
    """Strips blank lines from the code"""
    lines = blob.split('\n')
    return '\n'.join([line for line in lines if line.strip() != ''])

def strip_comments(blob, delim='#'):
    """Strips comments from the code"""
    lines = blob.split('\n')
    return '\n'.join([line for line in lines if line.strip()[0] != delim])

def loc(blob, delim='#'):
    """Returns the total line count, nonblank line count, and net line count excluding comments and docstrings"""
    total = get_line_count(blob)
    blob = strip_blanklines(blob)
    nonblank = get_line_count(blob)
    blob = strip_docstring(blob)
    blob = strip_comments(blob, delim)
    net = get_line_count(blob)
    return { 'total': total, 'nonblank': nonblank, 'net': net }

def findWords(text):
    """Find exact words"""
#     count = 0
    wordsList = []
    sText   = text.split("\n")
    for each in sText:
        each = each.lstrip()# lstrip() remove the spaces from the end of a string
        if each.startswith("self.") and not (each.startswith("#") or each.startswith("'''") or each.startswith('"""')):
            if "=" in each:
                each = each.split("=")[0]
                if not  (("(" in each) or (")" in each) )and not ("assert" in each):
                    each = each.rstrip() # rstrip() remove the spaces from the end of a string
                    if ("[" in each) or ("]" in each):
                        each = each.split("[")[0]
                    wordsList.append(each)
    count = len(set(wordsList))
    return count
        
def getClassMethodAndAttrCount(lines):
    """Returns the methods of a class and class attributes that starts with 'self.' """
    clsMethodCount = 0
    clsAttrCount = 0
    if lines.startswith("class"):
        clsMethodCount = lines.count("def ")
        clsAttrCount = findWords(lines)
    return clsMethodCount, clsAttrCount

def getFuncAttrCount(v, i, lines):
    """ Returns the function attributes"""
    funcAttrCount = 0
    if lines.startswith("def"):
        funcAttr = v[i][0].split("):")[0].split("(")[1]
        if "," in funcAttr:
            funcAttrCount = len(funcAttr.split(","))
        else:
            funcAttrCount = 1
    return funcAttrCount

def getClsFncInfo(dataFile, v, i):
    ''' Returns the class method and attribute count, loc count of a file/class, and function attribute count'''
    dataFile = [line for line in dataFile if not line.startswith("@")]
    
    lines = ""
    for line in dataFile:
        lines += line
        lines += "\n"
    
    clsMethodCount, clsAttrCount = getClassMethodAndAttrCount(lines)
    funcAttrCount = getFuncAttrCount(v, i, lines)
    locCount = loc(lines)['net']
    
    return locCount, clsMethodCount, clsAttrCount, funcAttrCount

def appendFileInfoToDict(dataToRead, k, v, i, locCount, clsMethodCount, clsAttrCount, funcAttrCount):
    ''' Appends the file name, the classes and functions in the file with their line name and the class method and 
        class attribute count, loc count of a file/class, and function attribute count
    '''
    if k in dataToRead:
        dataToRead[k].append([v[i][0], "starts @ line" + str(v[i][1]), "LOC=" + str(locCount), "clsMethodCount=" + str(clsMethodCount), "clsAttrCount=" + str(clsAttrCount), "funcAttrCount=" + str(funcAttrCount)])
    else:
        dataToRead[k] = [v[i][0], "starts @ line" + str(v[i][1]), "LOC=" + str(locCount), "clsMethodCount=" + str(clsMethodCount), "clsAttrCount=" + str(clsAttrCount), "funcAttrCount=" + str(funcAttrCount)]

def getLOCOfFiles(dataDict):
    """ Returns  a dict that has the file name, the classes and functions in the file with their line name and the class method and 
        class attribute count, loc count of a file/class, and function attribute count
    """
    dataToRead = {}
    dataFile = []
    for k, v in dataDict.items(): #print (k, v, len(v))
        with open(k) as f:
            allLines = f.readlines()
            if len(v) != 1:
                if len(v) > 2:
                    for i in range(1, len(v)):
                        if v[i] != v[-1]:
                            dataFile = allLines[v[i][1]:v[i + 1][1]]
#                             locCount, clsMethodCount, clsAttrCount, funcAttrCount = getClsFncInfo(dataFile, v, i)
#                             appendFileInfoToDict(dataToRead, k, v, i, locCount, clsMethodCount, clsAttrCount, funcAttrCount)
                        else:
                            dataFile = allLines[v[i][1]:v[0]]
                        
                        locCount, clsMethodCount, clsAttrCount, funcAttrCount = getClsFncInfo(dataFile, v, i)
                            
                        appendFileInfoToDict(dataToRead, k, v, i, locCount, clsMethodCount, clsAttrCount, funcAttrCount)
    return dataToRead
        
def getClassVsFuncInFiles(pythonFiles):
    """ Returns the classes and functions in a file with their line numbers"""
    dataDict = {}
    for eachFile in pythonFiles:
        with open(eachFile) as f:
            dataFile = f.readlines()
            dataDict[eachFile] = [len(dataFile)]
            lineNo = 0
            for line in dataFile:
                if ("class " in line.lstrip() ) and (':' in line.lstrip().split('class ')[1]):
                    if eachFile in dataDict:
                        dataDict[eachFile].append([line.lstrip(), lineNo]) #lstrip() remove spaces from the beginning
        
                if ("def " in line.lstrip()) and not ('self' in line) and ("(" and ")" in line):
                    if eachFile in dataDict:
                        dataDict[eachFile].append([line.lstrip(), lineNo]) #lstrip() remove spaces from the beginning
     
                lineNo += 1
        f.close()
    return dataDict

def checkForEmptyLines(lineStr):
    line = lineStr.replace('\r\n', '').strip()
    docstring = False
    if line == "" \
        or line.startswith("#") \
        or docstring and not (line.startswith('"""') or line.startswith("'''"))\
        or (line.startswith("'''") and line.endswith("'''") and len(line) >3)  \
        or (line.startswith('"""') and line.endswith('"""') and len(line) >3) :
        return False 
        # this is either a starting or ending docstring
    elif line.startswith('"""') or line.startswith("'''"):
        docstring = not docstring
        return False
    elif not line:
        return False
    else:
        return True
    
def removeCommentsFromString(sourceCode):
    sourceCode = strip_blanklines(sourceCode)
    nondoctring = strip_docstring(sourceCode)
    noncomment = strip_comments(nondoctring, '#')
    sourceCode=noncomment.split('\n')
    return sourceCode

def find_between( s, first, last ):
    '''
    Referenced from: https://stackoverflow.com/questions/3368969/find-string-between-two-substrings
    '''
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""









                     

