

'''
Created on Oct 10, 2020

@author: neda
'''
import src.Downloads as download
import src.Analysis as analysis
import src.Relation as relation

if __name__ == '__main__':
    
    #projectName='zulip'
    #projectName='keras'
    #projectName='numpy'
    #projectName='models'
    #projectName="django"
    #downloads = download.Downloads(projectName)
    #projectUrl="https://api.github.com/repos/keras-team/keras/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/zulip/zulip/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/django/django/issues?state=closed&page=&per_page=100"
    #projectUrl="https://api.github.com/repos/numpy/numpy/issues?state=closed&page=&per_page=100"
    #projectUrl= "https://api.github.com/repos/tensorflow/models/issues?state=closed&page=&per_page=100"
    
    #numberOfPages=160
    #downloads.downloadGitHubPythonProject()
    #downloads.downloadCommits()
    #downloads.downloadModifiedPythonFiles()
    #downloads.downloadIssuesFromIssueTrackingSys(projectUrl, numberOfPages)
    #projectName='Django'
    
#     
    projectName='django'
    anlysis=analysis.Analysis(projectName)
    anlysis.makeSemanticAndSyntacticAnalysis()
 
#     projectName='zulip'
#     analysis3=analysis.Analysis(projectName)
#     analysis3.makeSemanticAndSyntacticAnalysis()
      
#     projectName='keras'
#     analysis4=analysis.Analysis(projectName)
#     analysis4.makeSemanticAndSyntacticAnalysis()
# #      
#     projectName='models'
#     analysis5=analysis.Analysis(projectName)
#     analysis5.makeSemanticAndSyntacticAnalysis()
# 
#      
#     projectName='numpy'
#     analysis2=analysis.Analysis(projectName)
#     analysis2.makeSemanticAndSyntacticAnalysis()
#    

#----------------------------------------------------------------------#
 
#  
#     projectName="numpy"   
#     relat=relation.Relation(projectName)  
#     relat.checkForRelation(projectName)
 
#     projectName="django"   
#     relation2=relation.Relation(projectName)   
#     relation2.checkForRelation(projectName)  

#         
#     projectName="zulip"   
#     relation3=relation.Relation(projectName)   
#     relation3.checkForRelation(projectName)  
#         
#     projectName="keras"   
#     relation4=relation.Relation(projectName)   
#     relation4.checkForRelation(projectName)  
#         
#     projectName="models"   
#     relation5=relation.Relation(projectName)   
#     relation5.checkForRelation(projectName)
   
    '''

    def downloadProjectInASpecificCommit(projectName, commitID):
        outputDirectory = os.path.dirname(os.path.dirname(__file__)) + '/util/Zip'
        projectFolder = os.path.join(outputDirectory, projectName)
        if not os.path.isdir(projectFolder):
            os.mkdir(projectFolder)
        url = "https://github.com/numpy/numpy/archive/" + commitID + ".zip"
        wget.download(url, out=outputDirectory)
        for item in os.listdir(outputDirectory):
            if item.endswith(".zip"):
                fileName = os.path.join(outputDirectory, os.path.basename(item))
                with zipfile.ZipFile(os.path.join(fileName), "r") as zipObj:
                    zipObj.extractall(os.path.join(outputDirectory, projectName))
                zipObj.close()
                os.remove(fileName)
        import wget
        import os
        import zipfile
        projectName="numpy"
        commitID="8eb6424"
        downloadProjectInASpecificCommit(projectName, commitID)
        
        
        from src.FileOperations import FileOperations
        import shutil
        projectName = "numpy"
        fileOp=FileOperations(projectName)
        projectPath = os.path.join(os.path.dirname(os.path.dirname(__file__)) + '/util/Zip', projectName)
        
    
    pythonFile = fileOp.createOnePythonFile(projectPath)
    
    for name in os.listdir(projectPath):
        dirToDel = os.path.join(projectPath, name)
        if os.path.isdir(dirToDel):
            shutil.rmtree(dirToDel)
    

    
   # os.remove(os.path.join(projectPath,'allPythonFiles.py'))
      
    ''' 
    
    print("Done with Downloading!")
    