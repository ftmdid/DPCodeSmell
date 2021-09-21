'''
Created on Mar 20, 2018

@author: neda
'''


import yaml
from os import path
import os
# import src.GitLogs as GL
from datetime import datetime
from git import Repo
from git import GitCommandError
import sys
import csv
import shutil
# import re
#import helper as help



class FileOperations(object):
    """
        FileOperations class gets the gitLog's commit history data, 
        finds the configuration file and sends the related information to the GitLogs and
        FilteredLogs classes. 
    """
    
    def __init__(self,projectName):
        '''
        Constructor
        '''
        self.projectName=projectName
        self.commands = ""
        self.gitRepoURL = "" 
        self.commitData= "" 
        self.gitLog = ""
        self.hexshas = ""
        self.keywordsForFiltering = []
        self.filteredLog = ""
        self.shellScriptCmd = ""
        self.shellScriptFileURL = ""
        self.shellScriptFolderURL = ""
    
#     def getInstanceOfGitLogs(self):
#         '''
#             getInstanceOfGitLogs: is a method that gets the instance of GitLogs class
#             returns 'an instance of GitLogs class'
#         '''
#         self.gitLog = GL.GitLogs()
#         return self.gitLog
        
    def checkIfFileInvalid(self, aFileName, funcName):
        '''
            checkIfFileInvalid: is a method is that checks the configuration file 
                                if the file name is an instance of a string, 
                                if it is empty or 
                                if it includes .yml extension or not. 
            Args: 
                aFileName: name of the file
                funcName: the method that uses this file
        '''
        if not isinstance(aFileName, str):
            raise IOError("FileOperations."+funcName+": Invalid file name")
        if aFileName == "":
            raise IOError("FileOperations."+funcName+": Invalid file name")
        if not ".yml" in aFileName:
            raise IOError("FileOperations."+funcName+": Invalid file name")

    def readYMLFile(self):
        '''
            readYMLFile: is a method that finds the configuration file and 
                        checks if the configuration file is valid or not. 
            returns 'data available in configconfigInfo.yml(configuration file)'
        '''
        pathToDirec=path.dirname(path.dirname(__file__))
        fileNameToBeRead = self.find('configInfo.yml', pathToDirec)
        self.checkIfFileInvalid(fileNameToBeRead, 'readYMLFile')
        try:
            with open(fileNameToBeRead, "r") as stream:
                data = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            raise IOError("FileOperations.readYMLFile: File open error, " + exc)
        return data  
    
    def find(self,name, path):
        '''
            find: is a method is for finding a file in a directory
            Args: 
                name: name of the file
                path: the directory
            returns 'the file with it's path'
        '''
        for root, _, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)
            
    def getDirURLToClone(self):
        """
            getDirURLToClone: is a method that reads the /util/configInfo.yml file and brings the path of the
                              directory that the python project will be downloaded into
            returns 'the path of the directory that python project will be downloaded into'
        """
        self.cloneDir = self.readYMLFile()['clone']['path']
        return self.cloneDir
    
    def getGitHubURL(self):
        """
            getGitHubURL: is a method that reads the /util/configInfo.yml file and brings the url of the github 
            returns 'the url of the github
        """
        self.gitGitHubURL = self.readYMLFile()['github']['url']
        return self.gitGitHubURL
   
    
    def getGitRepoURL(self):
        """
            getDirURLToClone: is a method that reads the /util/configInfo.yml file and brings the url of the python project 
                              that will be downloaded
            returns 'the url of the python project'
        """
        
        self.gitRepoURL = self.readYMLFile()[self.projectName]['url']
        return self.gitRepoURL
    
    def getGitLogCmd(self):
        """
            getGitLogCmd: is a method that reads the /util/configInfo.yml file and brings the commands to 
                          read the project's gitlog history
            returns 'the command line information that helps to get the log history from the project'
        """
        self.gitLogCmd = self.readYMLFILE()['log']['cmd']
        return self.gitLogCmd
    
    def createTxtLogFile(self, fileName):
        '''
            createTxtLogFile: is a method that creates a text file. 
                              The project's gitlog history will be written into that text file.
            returns 'the gitLogReport.txt file with it's path. 
            
        '''
        path= os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util')
        #fileName= 'gitLogReport.txt'
        return os.path.join(path,fileName)
      
    def writeLogToTxtFile(self, hexshas, fileName):
        '''
            writeLogToTxtFile: is a method that gets log data, makes a call to createTxtLogFile to get the 
                               information about the text file and then sends those data to the writeLogToTxtFile
                               which will write gitlog data into the .txt file. 
            Args:
                hexshas (str) : gitlog data that will be written into the .txt file.    
        '''
        self.hexshas = hexshas 
        createdLogfile = self.createTxtLogFile(fileName)
        
        (self.getInstanceOfGitLogs()).writeLogsToTxtFile(createdLogfile, self.hexshas)
        
        
    def writeFileContentToPythonFile(self, hexshas, fileName):
        '''

        '''
        self.hexshas = hexshas 
        createdPythonfile = self.createPythonFile(fileName)
        try:
            self.hexshas = self.hexshas
            self.fileName = fileName
            textFile= open(createdPythonfile, "wb")
            textFile.write(self.hexshas.encode('utf-8', 'surrogateescape'))
            #return file
            textFile.close()
        except IOError as ex:
            raise IOError("FileOperations.writeFileContentToPythonFile: " + str(ex))
        
    def createPythonFile(self, fileName):
        '''
            
        '''
        path= os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util/Python/'+self.projectName)
        return os.path.join(path,fileName)
      
    
    def writeLogToCsvFile(self, hexshas):
        '''
            writeLogToCsvFile: is a method that gets log data, and then sends those data to the writeDataToCSVLogFile
                               which will write gitlog data into the csv file. 
            Args:
                hexshas (str) : gitlog data that will be written into the .csv file.    
        '''
        self.hexshas = hexshas
        (self.getInstanceOfGitLogs()).writeDataToCSVLogFile(self.hexshas)
    
    def getGitKeywordsForFilteringLogs(self):
        """
            getGitKeywordsForFilteringLogs: is a method that reads the /util/configInfo.yml.yml file and brings the 
                              keywords that will be used to filter log history
            returns 'the keywords available in /util/configInfo.yml file'
        """
        return self.readYMLFile()['filter']['keywords']
    
    def writeFilteredLogToCSVFile(self, hexshas):
        '''
            writeLogToCsvFile: is a method that gets log data, and then sends those log data and the keywords that will be used to filter log history
                               to the writeFilteredDataToCSVLogFile which will write gitlog data into the csv file. 
            Args:
                hexshas (str) : gitlog data that will be written into the .csv file.    
        '''
        self.hexshas = hexshas
        projDir = os.path.join(self.getDirURLToClone())
        self.keywordsForFiltering = self.getGitKeywordsForFilteringLogs()
        (self.getInstanceOfFilteredLogs()).writeFilteredDataToCSVLogFile(self.keywordsForFiltering, hexshas, projDir)
    '''
    Code is referenced from: 
    https://stackoverflow.com/questions/15063936/csv-error-field-larger-than-field-limit-131072
    '''
    def increaseCSVReaderSize(self):
        maxInt = sys.maxsize
        try:
            csv.field_size_limit(maxInt) # for overflow csv error
        except OverflowError:
            maxInt = int(maxInt / 10)
    
    '''
            Read from csv file is referenced from:
            https://stackoverflow.com/questions/41585078/how-do-i-read-and-write-csv-files-with-python
    '''       
    def readCSVFile(self,docsPath):
        self.increaseCSVReaderSize()
        with open(docsPath) as docsFile:
            reader = csv.reader(docsFile, delimiter=",", quotechar='"')
            next(reader, None) # skip the headers
            docsList = [row for row in reader]
        return docsList
      
    def convertStrToDatetimeObj(self, dateTimeStr):
        dateTimeStrObj = dateTimeStr.split(' ')
        dateTimeStr = dateTimeStrObj[2]+" "+dateTimeStrObj[3]+" "+dateTimeStrObj[5]+" "+ dateTimeStrObj[4]
        try:
            dt = datetime.strptime(dateTimeStr, '%b %d %Y %H:%M:%S')
            return dt
        except ValueError as x:
            print ("FileOperations.convertStrToDatetimeObj: Unable to convert string to datetime object, " + x)
        
    def createCopyOfModifiedPythonFilesInFolder(self, filesList, projectName):
        
        repoPath= os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Projects/'+projectName)
        repo = Repo(repoPath)
        commitsList  = repo.iter_commits()
        next(commitsList)
        hexhas = ""
        try:

            projectPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'util/Python/'+projectName)
            if not os.path.exists(projectPath): # check if project folder is available in util/python folder
                os.makedirs(projectPath)
                 
            self.removeFilesInDir(projectPath)
            for each in filesList:
                filePath=each[2]
                #Extract filename from path
                _, tail = os.path.split(filePath)
                filePath = tail
                   
                filePath = filePath.split(".py")[0]
                dirPath = os.path.join(projectPath, filePath)
                self.createFolder(dirPath)
                
                
                fileName = filePath  +"@"+str(each[0]) +"@"+str(each[3])+".py"
                hexhas = repo.git.show('%s:%s' % (each[0], each[2])) # each[0]=commitID, each[2]=fileURL
                #self.writeFileContentToPythonFile(hexhas, fileName)
                self.writeFileContentToPythonFile(hexhas, (os.path.join(dirPath,fileName)))
            return repoPath

        except GitCommandError as ex:
            print (ex)
    
    def createFolder(self, directory):
        try: 
            if not os.path.exists(directory):
                os.makedirs(directory)
        except OSError:
            print ('Error: Creating directory. ' + directory)
    
    def createOnePythonFile(self, projectPath, projectName, commitID):
        pythonFiles =[]
        for path, drec,_ in os.walk(projectPath):
            for name in drec:
                if commitID in name:
                    #print(name)
                    direct= os.path.join(path, name)
                    for pathForDirect,_,files in os.walk(direct):
                        for fileName in files:
                            if fileName[-3:]==".py":
                                if not fileName.lower().startswith('test'):
                                    pythonFiles.append(os.path.join(pathForDirect,fileName))

        try:
            fileName="allPythonFilesIn_"+projectName+"_withCommitID_"+commitID+".py"
            newPythonFile= os.path.join(projectPath,fileName)
            if os.path.exists(newPythonFile):
                os.remove(newPythonFile)
            # else:
                # print("Can not delete the file since it doesn't exists")
            with open(newPythonFile,'w+') as writer:
                #count=0
                for each in pythonFiles:
                    if each!=newPythonFile:
                        with open(each,encoding='windows-1252', errors='ignore') as infile:
                        #with open(each,encoding='utf-8') as infile:
                            source = infile.read()+'\n'
                            writer.write(source)
                            # infile.close()
                writer.close()
        except Exception as ex:
                    print(ex)
                    print("Exception occurrred in FileOperations.createOnePythonFile()")
        return newPythonFile
    
    def checkPythonFile(self, pythonFile): # check python file for syntax error
        '''
            This is added due to SyntaxError: from __future__ imports must occur at the beginning of the file
            AllPythonFile.py was giving issues from of from __future__ imports since it has to be at the beginning of the file
        '''
        try:
            futureLinesIndexNum=[]
            with open(pythonFile, 'r+') as fp:
                lines=fp.readlines()
                fp.seek(0)
                for each in lines:
                    if each.lstrip().startswith('from __future__'):
                        futureLinesIndexNum.append(each)
                    elif  each.lstrip().startswith('import numpy as np'):
                        pass
                    elif "os.chdir('../" in each:
                        
                        newSente="os.mkdir(os.path.join(os.path.dirname(os.getcwd()),'"
                        each=each.replace("os.chdir('../",newSente)
                        each=each+")"
                        each=each+"\n"
                        fp.write(each)
                    elif each.lstrip().startswith("import Array"):
                        each="import array"+"\n"
                        fp.write(each)
                    
                    else:
                        fp.write(each)
                
                fp.truncate()
                fp.close()
            
            with open(pythonFile, 'r+') as f:
                lines=f.readlines()
                counter=0
                
                for each in futureLinesIndexNum:
                    lines.insert(counter,each)
                    counter +=1
                lines.insert(counter,"import numpy as np")
                lines.insert(counter+1, "\n")
                f.seek(0)
                f.writelines(lines)
                f.close()
            print("Done with checkPythonFile")
                    
        except Exception as ex:
            print(ex)
    
    # if there are files under the clones directory, delete the files to download it again
    def removeFilesInDir(self, cloneDir):
        for fileInDir in os.listdir(cloneDir):
            dirToDel = os.path.join(cloneDir, fileInDir)
            try:
                if os.path.isfile(dirToDel):
                    os.unlink(dirToDel)
                else:
                    shutil.rmtree(dirToDel)
            except Exception as e:
                print(e)

    
