'''
Created on May 18, 2018

@author: neda
'''


import os
import csv 

# from git import Repo
# import requests
# import json
# import logging


class GitLogs(object):
    """
        GitLogs class gets the gitLog's commit history data, brings it into the correct structure and 
        write the structured data into the csv file. It also writes unstructured gitlog's history data
        into the txt file. 
    """

    def __init__(self,projectName):    
        """
            Constructor
        """
        self.fileName = ""
        self.hexshas = ""
        self.projectName=projectName
        
        
         
    def writeLogsToTxtFile(self, fileName, data):
        """
            writeLogsToTxtFile is a method that write gitlog data to a text file. 
            Args:
                fileName (str) : the filename of the text file that the gitlog data will be written into
                data (str): the gitlog data that includes all the commits details
        """
        try:
            self.hexshas = data
            self.fileName = fileName
            textFile= open(self.fileName, "wb")
            textFile.write(self.hexshas.encode('utf-8'))
            #return file
            textFile.close()
        except IOError:
            raise IOError("GitLogs.writeLogsToTxtFile: File open error")
           
    
    def createLogDictionary(self,data):
        """ 
            createLogDictionary is a method that helps to create a dictionary using gitlogs
            Args:
                data (str): GitLog data
            return: 'a dictionary that has key-value pairs'
                    keys: ['lSize','cHash','pHash', 'aName', 'aEmail','aDate', 'cName','cEmail','cDate','subject', 'cFiles', 'lAdd', 'lDel']
                    lSize = log size of each commit
                    cHash = commit Hash
                    pHash = parent Hash
                    aName = author Name
                    aEmail = author Email
                    cName = committer Name
                    cEmail = committer Email
                    cDate = committer Date
                    subject = subject of the commit
                    cFiles = changed Files
                    lAdd = number of lines added to the changed file(s)
                    lDel = number of lined deleted from the changed file(s)
        """
        self.hexshas = data
        logDict = {}
        items = self.hexshas.splitlines()
        ind=0
        logDict['cFiles']=[]
        for item in items:  
            if ind == 0:
                logDict['lSize'] = int(item)
                
            elif  ('~||~' in item) and ind==1:
                splittedItem = item.split('~||~')
                splittedItem=splittedItem[1:-1] # the first and last elements of list was empty string and they were removed
                keys = ['cHash','pHash', 'aName', 'aEmail','aDate', 'cName','cEmail','cDate','subject']
                i=0
                for j in range(0,len(splittedItem)):

                    logDict[keys[i]]=splittedItem[j]         
                    i +=1   
            ind +=1
        return logDict
    
    def writeDataToCSVLogFile(self, data):
        """
            writeDataToCSVLogFile: is a method that sends the gitlog data to createLogDictionary() function, 
                                   gets the dictionary. Then it creates a csv file and write the dictionary into
                                   the csv file. The file is located in the "util" folder in the project folder. 
            Args:
                data (str) : gitlog data that will be written into the csv file. 
        """
        self.hexshas=data
        logDict = {}
        lines = self.hexshas.split('log size ')
        path= os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util/commits')
        self.fileName= 'commitsOf'+self.projectName+".csv"
        filePath = os.path.join(path,self.fileName)
    
        try:
            with open(filePath, 'w') as csvfile:
                filewriter = csv.writer(csvfile)
           
                filewriter.writerow(['commitID', 'parentID','Author Name',\
                                     'Author Email','Author Date','committer Name'\
                                     ,'committer Email','committer Date','Subject',\
                                     'logSize' ])
                
                for line in lines:
                    #print line
                    if line :
                        #print(line)
                        
                        #logDict = self.createLogDictionary(line)
                        logDict = self.createLogDictionary(line)
                        filewriter.writerow([logDict['cHash'], logDict['pHash'], logDict['aName'],\
                                            logDict['aEmail'], logDict['aDate'], logDict['cName'],\
                                            logDict['cEmail'], logDict['cDate'], logDict['subject'],logDict['lSize']])
                                  
        except IOError:
            raise IOError("GitLogs.writeDataToCVSLogFile: IOError") 
   
    
    def createModifiedFileList(self,hexshas2):
        """
            createModifiedFileList: is a method that reads the gitlog data for the modified, deleted, added and
                                   renamed files. It creates a python list that has <commitId, fileIndicator, fileName, commitDate>
                                   fileIndicator can be M(modified), D(deleted), R(renamed), A(added)
            Args:
                hexshas2 (str) : gitlog data that will be read to create a python list. 
        """
        filesList = []
      
        #lines = hexshas2.encode("utf-8").split('log size ')
        lines = hexshas2.split('log size ')
        mergeRequestStr = "Merge pull request"
        for line in lines:
            if line!= "":
                lineSplit = line.split('~||~')
                if not (any(mergeRequestStr in item for item in lineSplit)): # This line is to remove "merge pull request" commits
                    if lineSplit != ['']: # lineSplit = [logSize, commitId, date, subject, changedFiles with M, D, R, A]
                        """
                        i is an iterator number. 
                        i=1: refers to the commit number, 
                        i=2: refers to the date,
                        i=3: refers to the subject 
                        i=4: refers to the files that are modified(M), deleted(D), added(A), renamed(R). 
                    """
                        i = 0
                        for each in lineSplit:
                            each = (each.replace('\n', ' ')).replace('\t', ' ') 
                            if i == 10: # file is in the 4th index of lineSplit, doing the calculations with the file
                                each = each.split(" ") # This line is splitting the filename from the file indicator(M,D,R,A) and when you do that you will get ['','M',fileName,'','']
                                x = 0
                                for item in each:
                                    if item != None:
    #                                     if item in ('M', 'D', 'A', 'R'):
                                        if item == 'M':
                                            if each[x+1].endswith('.py') and ('test' not in each[x+1].lower()):
                                                filesList.append([lineSplit[1], each[x], each[x + 1], lineSplit[5]]) #[commitId, 'M', fileNameWithURL,date]
                                    x += 1
                            
                            i += 1
        
        return filesList
            
    def readLogDictionary(self):
        path= os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util')
        self.fileName= 'gitLogReportOf'+self.projectName+".csv"
        filePath = os.path.join(path,self.fileName)
        try:
            logList = []
            with open(os.path.join(path, filePath)) as f:
                rows = csv.reader(f)
                for row in rows: 
                    logList.append(row)
            print ("Done")
            return logList
        except csv.Error or IOError:
            print ("JsonFiles.readLogDictioary Error")
            
    '''
    def createLogDictionary(self,data):
        """ 
            createLogDictionary is a method that helps to create a dictionary using gitlogs
            Args:
                data (str): GitLog data
            return: 'a dictionary that has key-value pairs'
                    keys: ['lSize','cHash','pHash', 'aName', 'aEmail','aDate', 'cName','cEmail','cDate','subject', 'cFiles', 'lAdd', 'lDel']
                    lSize = log size of each commit
                    cHash = commit Hash
                    pHash = parent Hash
                    aName = author Name
                    aEmail = author Email
                    cName = committer Name
                    cEmail = committer Email
                    cDate = committer Date
                    subject = subject of the commit
                    cFiles = changed Files
                    lAdd = number of lines added to the changed file(s)
                    lDel = number of lined deleted from the changed file(s)
        """
        self.hexshas = data
        logDict = {}
        items = self.hexshas.splitlines()
        ind=0
        #fileChanged=[]
        logDict['cFiles']=[]
        for item in items:  
            if ind == 0:
                logDict['lSize'] = int(item)
                if item==193:
                    print("somehting")
            elif  ('~' in item) and ind==1:
                splittedItem = item.split('~')
                splittedItem=splittedItem[1:-1]
                keys = ['cHash','pHash', 'aName', 'aEmail','aDate', 'cName','cEmail','cDate','subject']
                i=0
                for j in range(0,len(splittedItem)):
#                     if j == 0:
#                         if splittedItem[0] == '8f568cfc19f5b5f2aa59b06d4e2b5b8d31423605' or splittedItem[0] == 'c78070d8623fb6f40bf4ef20a1109083ca79ef7a' or splittedItem[0] == '5127b8bd26a58cb9ac8214a89cee16eb14349e59' or splittedItem[0] == 'fa9817778c83eb35b9c2c4332ccb7e5190d1ffa2':
#                             print splittedItem[0]
                    logDict[keys[i]]=splittedItem[j]         
                    i +=1   
            elif item:
                item = item.replace(' ' , '')
                if ('|' in item):
                    item = item.split('|')[0]
                    #fileChanged.append(item)
                    logDict['cFiles'].append(item)
                elif ('changed' and 'file' in item):  
                    if ('insertion' in item):
                        itAdd = HM.findBetween(item, ",", "i")
                        if itAdd:
                            logDict['lAdd'] = itAdd
                        else:
                            logDict['lAdd'] = 0
                    if ('deletion' in item):
                        if '(+)' in item:
                            itDel = HM.findBetween(item, "(+),", "d")
                        else: 
                            itDel = HM.findBetween(item, ",", "d")
                        if itDel:
                            logDict['lDel'] = itDel
                        else:
                            logDict['lDel'] = 0
            ind +=1
        logDict = HM.checkForKeys(logDict)
        return logDict
   
    def writeDataToCSVLogFile(self, data):
        """
            writeDataToCSVLogFile: is a method that sends the gitlog data to createLogDictionary() function, 
                                   gets the dictionary. Then it creates a csv file and write the dictionary into
                                   the csv file. The file is located in the "util" folder in the project folder. 
            Args:
                data (str) : gitlog data that will be written into the csv file. 
        """
        self.hexshas=data
        logDict = {}
        lines = self.hexshas.split('log size ')
        path= os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util/commits')
        self.fileName= 'commitsOf'+self.projectName+".csv"
        filePath = os.path.join(path,self.fileName)
    
        try:
            with open(filePath, 'w') as csvfile:
                filewriter = csv.writer(csvfile)
           
                filewriter.writerow(['commitHash', 'parentHash','authorName',\
                                     'authorEmail','authorDate','committerName'\
                                     ,'committerEmail','committerDate','Subject',\
                                     'linesDeleted','linesAdded','changedFiles',\
                                     'logSize' ])
                
                for line in lines:
                    #print line
                    if line :
                        print(line)
                        logDict = self.createLogDictionary(line)
                        filewriter.writerow([logDict['cHash'], logDict['pHash'], logDict['aName'],\
                                            logDict['aEmail'], logDict['aDate'], logDict['cName'],\
                                            logDict['cDate'], logDict['cEmail'], logDict['subject'],\
                                            logDict['lDel'], logDict['lAdd'], logDict['cFiles'], logDict['lSize']])
                                  
        except IOError:
            raise IOError("GitLogs.writeDataToCVSLogFile: IOError") 
    
    '''


        

 


  
    