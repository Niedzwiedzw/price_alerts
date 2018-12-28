#! pyw -3.7

import os

currentDir = os.path.dirname(os.path.realpath(__file__))
mainFilePath = os.path.join(currentDir, 'alert.py')
runtimeScriptPath = os.path.join(currentDir, 'runtime.bat')

script = f"""
:loop
{mainFilePath}
ping localhost -n 6 > nul
goto loop
"""

with open(runtimeScriptPath, 'w') as file:
    file.write(script)

os.system(runtimeScriptPath)
