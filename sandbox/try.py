'''
Created on Oct 9, 2020

@author: neda
'''
class A:
    def __init__(self):
        self.b=0
    def calculateHowManyCowsCanFitOnTheMoon(self):
        pass
    def doLocalCalculation(self):
        pass
    def doNonLocalCalculation(self,strForCalculation):
        pass
    def setSth(self):
        pass
        
classAObject=A()
strForCalculation="aaa"
result=classAObject.calculateHowManyCowsCanFitOnTheMoon().doLocalCalculation().doNonLocalCalculation(strForCalculation).setSth().doNonLocalCalculation(strForCalculation).calculateHowManyCowsCanFitOnTheMoon()
print(result)