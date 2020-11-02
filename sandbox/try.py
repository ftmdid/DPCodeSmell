'''
Created on Oct 9, 2020

@author: neda
'''
# class A:
#     def __init__(self):
#         self.b=0
#     def calculateHowManyCowsCanFitOnTheMoon(self):
#         pass
#     def doLocalCalculation(self):
#         pass
#     def doNonLocalCalculation(self,strForCalculation):
#         pass
#     def setSth(self):
#         pass
#  
import re
#subject="Fixed 537484: .class file is missing and your code should also have some defects in it."
subject= "Refs #30422 -- Added test for removing temporary files in MultiPartParser when StopUpload is raised."
subject=subject.lower()
p = re.compile('bug[\#?]*[0-9]+ | bug?id=[0-9]+ | \[[0-9]+\]')
matched=False
#if re.search('bug *?[0-9]+ | 'bug *?#*? *?[0-9]+',subject):


pattern=r'bug[\#?]*[0-9]+ | bug *?[0-9]+ | [bug]? *?id *?= *?[0-9]+ | \[*[0-9]+\]*'
if re.search(pattern,subject):
    matched=True
print(matched)






