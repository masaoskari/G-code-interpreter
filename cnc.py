import sys
import re
import MachineClient
class Machine:
    def __init__(self, feed_rate:float=0, spindle_speed:int=0, tool:str="", \
                 is_cooling_on: bool=False):
       #Interface object for printing what machine does
       self.client_=MachineClient.MachineClient()
       self.feed_rate_=feed_rate
       self.spindle_speed_=spindle_speed
       self.tool_=tool
       self.is_cooling_on_=is_cooling_on

    #Moves spindle to given coordinates. Uses MachineClient class to show where
    #spindle is moving. Sets spindle feed rate if it's given.
    def move_spindle(self, command:list):
        #Taking coordinates from command
        coordinates=self.parse_coordinates(command)
        #If coordinates are not defined, setting spindle movement mode.
        if coordinates[0]==coordinates[1]==coordinates[2]==0:
            if command[0]=="G00":
                self.client_.set_movement_mode("rapid positioning")
            #If only G01 is given:
            elif command[0]=="G01":
                self.client_.set_movement_mode("linear motion")
        else:
            #Setting linear motion (G01) feed rate
            if self.feed_rate_==0 and command[len(command)-1].startswith("F") \
                and command[0]=="G01":

                self.parse_and_set_feed_rate(command)
            #When G01 command is given without feed rate parameter or the feed
            #rate is not defined earlier in the program, the program gives
            #erro message and stops.
            elif command[0]=="G01" and self.feed_rate_==0:
                print("ERROR! Set the feed rate before you can use cut!")
                return False
            #Moving spindle x-position
            if coordinates[1]==0 and coordinates[2]==0:
                self.client_.move_x(coordinates[0])
            #Moving spindle y-position
            elif coordinates[0]==0 and coordinates[2]==0:
                self.client_.move_y(coordinates[1])
            #Moving spindle z-position
            elif coordinates[0]==0 and coordinates[1]==0:
                self.client_.move_z(coordinates[2])
            #Linear movement to given xyz-coordinates
            elif coordinates[0]!=0 and coordinates[1]!=0:
                self.client_.move(coordinates[0], coordinates[1], coordinates[2])

    #Parses x, y, z-coordinates from the command list and returns x, y, z
    #coordinates in tuple. If commandlist doesn't contain different coordinate 
    #that coordinate is set to 0. 
    def parse_coordinates(self, command:list)->tuple:
        x, y, z=0, 0, 0
        for word in command:
            if word.startswith("X"):
                x_coord_string = re.findall(r"[-]?\d*\.\d+", word)[0]
                x=float(x_coord_string)
            elif word.startswith("Y"):
                y_coord_string = re.findall(r"[-]?\d*\.\d+", word)[0]
                y=float(y_coord_string)
            elif word.startswith("Z"):
                z_coord_string = re.findall(r"[-]?\d*\.\d+", word)[0]
                z=float(z_coord_string)
        return x, y, z

    #Finds and sets spindle feed rate. Uses MachineClient class to show where
    #what the set feed rate is.
    def parse_and_set_feed_rate(self, command:list):
        #Feed rate in mm/min
        feed_rate=re.findall(r"\d*\.\d?", command[len(command)-1])
        #Feed rate in mm/s
        feed_rate=float(feed_rate[0])/60
        if feed_rate==self.feed_rate_:
            return
        self.feed_rate_=feed_rate
        self.client_.set_feed_rate(feed_rate)

    #Finds spindle speed (rpm) from g-code command and sets that to spindle with 
    #using MachineClient class.
    def parse_and_set_spindle_speed(self, command:list):
        spindle_speed=re.findall(r"\d+", command[0])
        self.spindle_speed_=int(spindle_speed[0])
        self.client_.set_spindle_speed(int(spindle_speed[0]))

    #Turns spindle on or off
    def turn_spindle_on_or_off(self, command:list):
        if command[0]=="M03":
            self.client_.turn_rotation_on_off(True)
        else:
            self.client_.turn_rotation_on_off(False)
            
    #Sets what tool will be used in machine but not change it
    def set_tool(self, command:list):
        tool=re.findall(r"\d+", command[0])
        self.tool_=tool[0]

    #Changes the before given tool to machine. Gives error message and stops
    #the program if tool is not set earlier. Also stops cooling and turns
    #spindle off.
    def change_machine_tool(self):
        self.spindle_speed_=0
        self.is_cooling_on_=False
        if self.tool_=="":
            print("ERROR! The tool must be chosen before it can be changed.")
            return False
        else:
            self.client_.change_tool(self.tool_)

    #Sets cooling on/off depending the given command. Also gives error message
    #if the cooling is on/off and the user tries to turn it on/off.
    def handle_cooling(self, command):
        if command=="M08":
            if self.is_cooling_on_==True:
                print("The cooling is already on!")
            else:
                self.client_.coolant_on()
                self.is_cooling_on_=True
        else:
            if self.is_cooling_on_==False:
                print("Error! Cooling cannot be set off because it is not on.")
            else:
                self.client_.coolant_off()
    #Moves machine to home position
    def move_home(self):
        self.client_.home()

#Reads G-code commands from the given file. Ignores comments and
#other text which are not commands. Returns commands in list.
def read_file(filename:str)->list:
    commands=[]
    try:
        with open(filename, 'r') as file:
            for line in file:
                #Ignoring comments and those initialization codes (%)
                if line.startswith(("%","(")):
                    continue
                #Using regular expressions to get those single commands to list.
                #If command have parameters the parameters and that command is 
                #added to list in list.
                words=line.split(" ")
                for word in words:
                    #Finds G01 commands and its parameters x,z or z-coordinates
                    if re.match(r"G01", word):
                        command=re.findall(r"G01|[XYZ]-?\d*\.\d*|F\d*\.\d?", line)
                        commands.append(command)
                    #Finds G00 commands and its parameters x,z or z-coordinates
                    elif re.match(r"G00", word):
                        command=re.findall(r"G00|[XYZ]-?\d*\.\d*", line)
                        commands.append(command)
                    #Finds other commands that starts with G, T, M, F or S
                    #characters but that wich are not G01 or G00.
                    elif re.match(r"(?!G01|G00)[GTMFS]\d", word):
                        commands.append([word.strip()])
        file.close()

    except FileNotFoundError:
        print(f"Could not read file: {filename}")

    return commands


def main():
    #filename=sys.argv[1]
    filename="rectangle.gcode"
    #Reading files G-codes to list
    commands=read_file(filename)
    print(commands)
    #Machine object to handle different commands
    machine=Machine()
    #Loop throught this g-code program
    for command in commands:
        #Moving spindle with linear motion
        if command[0]=="G01":
            if machine.move_spindle(command)==False:
                return
        #Moving spindle with rapid positioning
        elif command[0]=="G00":
            machine.move_spindle(command)
        #Spindle feed rate set
        elif command[0].startswith("F"):
            machine.parse_and_set_feed_rate(command)
        #Spindle speed set
        elif command[0].startswith("S"):
            machine.parse_and_set_spindle_speed(command)
        #Spindle turn on/off
        elif command[0]=="M03" or command[0]=="M09":
            machine.turn_spindle_on_or_off(command)
        #Setting what tool will be used in machine
        elif command[0].startswith("T"):
            machine.set_tool(command)
        #Changes the before given tool to machine. Gives error if tool is not
        #set and stops the program.
        elif command[0]=="M06":
            if machine.change_machine_tool()==False:
                return
        #Turns cooling on/off, depending of given command
        elif command[0]=="M08" or command[0]=="M09":
            machine.handle_cooling(command[0])
        #Moves machine to home position
        elif command[0]=="G28":
            machine.move_home()

if __name__ == "__main__":
    main()