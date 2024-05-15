import  jpype     
import  asposecells     
jpype.startJVM() 
from asposecells.api import Workbook
workbook = Workbook("Despatch_160CH_hybrid.xlsx")
workbook.Save("Output.pptx")
jpype.shutdownJVM()
