# G-code-interpreter
This program implements a simple g-code interpreter which reads g-code program
from file and parses it and shows user in console what the machine will do 
when using that program. If the given g-code program is somehow wrote wrong 
the program will give error messages in common situations. For example program
gives an error message and stops program if the spindle feed rate is not set
before the machine is command to cut.

Program uses Machine class to keeping known what setups to machine is done and
MachineClient class to show user what g-code program does. You will find more
details how program works in comments below.

The program can be used by adding cnc.py, MachineClient.py and the g-code
program in the same folder. Then it starts with command row command:

>python cnc.py rectangle.gcode
