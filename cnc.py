"""
 **********Program author**********
 Name: Matti Linna
 E-Mail: masaoskari.linna@gmail.com
 **********************************
 Description:
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

"""
import sys
import re
import MachineClient

#Some constant strings for program
RAPID_POSITIONING="rapid positioning"
LINEAR_MOTION="linear motion"
ABSOLUTE_POSITIONING=0
INCREMENTAL_POSITIONING=1

#Machine class to keeping known what setups to cnc-machine is done.
class Machine:
    def __init__(self, feed_rate:float=0, spindle_speed:int=0, tool:str="", \
                 is_cooling_on: bool=False):
       #Interface object for printing what machine does
       self.client_=MachineClient.MachineClient()
       self.feed_rate_=feed_rate
       self.spindle_speed_=spindle_speed
       self.tool_=tool
       self.is_cooling_on_=is_cooling_on
       self.motion_mode_=""
       self.positioning_mode_=-1
       self.x_=0
       self.y_=0
       self.z_=0
    

    #Moves spindle to given coordinates. Uses MachineClient class to show where
    #spindle is moving. Sets spindle feed rate if it's given.
    def move_spindle(self, command:list):

        #Search coordinates from command.
        coordinates=self.parse_coordinates(command)
       
        #Search directions where spindle is going to move.
        directions=re.findall(r"[XYZ]", " ".join(command))
    
        #Showing spindle movement mode to user (rapid or linear).
        self.check_movement_mode(command)

        #If some coordinates are given the spindle will move to given position.
        if len(directions)!=0:

            #Setting linear motion (G01) feed rate
            if command[len(command)-1].startswith("F") and command[0]=="G01":
                self.parse_and_set_feed_rate(command)

            #When G01 command is given without feed rate parameter or the feed
            #rate is not defined earlier in the program, the program gives
            #error message and stops.
            elif command[0]=="G01" and self.feed_rate_==0:
                print("ERROR! Set the feed rate before you can use cut!")
                return False
            
            #Moving spindle x-position (tooks also care is spindle positioning
            #absolute or incremental)
            if "X" in directions and "Y" not in directions and \
                "Z" not in directions:
                if self.positioning_mode_==INCREMENTAL_POSITIONING:
                    if coordinates[0]!=0:
                        self.client_.move_x(self.x_+coordinates[0])
                        self.x_+=coordinates[0]
                else:
                    self.x_=coordinates[0]
                    self.client_.move_x(coordinates[0])

            #Moving spindle y-position
            elif "Y" in directions and "X" not in directions and \
                "Z" not in directions:
                if self.positioning_mode_==INCREMENTAL_POSITIONING:
                    if coordinates[1]!=0:
                        self.client_.move_y(self.y_+coordinates[1])
                        self.y_+=coordinates[1]
                else:
                    self.y_=coordinates[1]
                    self.client_.move_y(coordinates[1])

            #Moving spindle z-position
            elif "Z" in directions and "X" not in directions and \
                "Y" not in directions:
                
                if self.positioning_mode_==INCREMENTAL_POSITIONING:
                    if coordinates[2]!=0:
                        self.client_.move_z(self.z_+coordinates[2])
                        self.z_+=coordinates[0]
                else:
                    self.z_=coordinates[2]
                    self.client_.move_z(coordinates[2])

            #Linear movement to given xy-coordinates
            elif "X" in directions and "Y" in directions and "Z" not in \
                directions:
                if self.positioning_mode_==INCREMENTAL_POSITIONING:
                    if coordinates[0]!=0 or coordinates[1]!=0:
                        self.client_.move(self.x_+coordinates[0], \
                                          self.y_+coordinates[1])
                        self.x_+=coordinates[0]
                        self.y_+=coordinates[1]
                else:
                    self.x_=coordinates[0]
                    self.y_=coordinates[1]
                    self.client_.move(coordinates[0], coordinates[1], self.z_)

            #There could be also movement implementations in other planes for
            #example xz-plane...
        
    #Checks the spindle movement mode (is it rapid or linear), sets it to
    #machine and shows that for user by using MachineClient class.
    def check_movement_mode(self, command:list):

        #Rapid positioning G00
        if command[0]=="G00":
            if self.motion_mode_=="" or self.motion_mode_==LINEAR_MOTION:
                self.motion_mode_=RAPID_POSITIONING
                self.client_.set_movement_mode(RAPID_POSITIONING)

        #Linear motion G00
        elif command[0]=="G01":
            if self.motion_mode_=="" or self.motion_mode_==RAPID_POSITIONING:
                self.motion_mode_=LINEAR_MOTION
                self.client_.set_movement_mode(LINEAR_MOTION)

    #Parses x, y, z-coordinates from the command list and returns x, y, z
    #coordinates in tuple. If commandlist doesn't contain different coordinate 
    #that coordinate is set to 0. 
    def parse_coordinates(self, command:list)->tuple:
        x, y, z=0, 0, 0
        #Finds x,y,z-coordinates from given command:
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

    #Finds and sets spindle feed rate. Uses MachineClient class to show
    #what the set feed rate is.
    def parse_and_set_feed_rate(self, command:list):
        
        #Feed rate in mm/min
        feed_rate=re.findall(r"\d*\.\d?", command[len(command)-1])

        #Feed rate in mm/s
        feed_rate=float(feed_rate[0])/60

        #If the given feed rate is same that earlier set, the feed rate set
        #is not shown to user.
        if feed_rate==self.feed_rate_:
            return
        
        #Setting and showing the feed rate for user.
        self.feed_rate_=feed_rate
        self.client_.set_feed_rate(feed_rate)

    #Finds spindle speed (rpm) from g-code command and sets that to spindle with 
    #using MachineClient class.
    def parse_and_set_spindle_speed(self, command:list):
        spindle_speed=re.findall(r"\d+", command[0])
        self.spindle_speed_=int(spindle_speed[0])
        self.client_.set_spindle_speed(int(spindle_speed[0]))


    #Turns spindle on or off. If the spindle rotational speed is not given, the
    #error message is given and the progam will stop.
    def turn_spindle_on_or_off(self, command:list):
        #Spindle on
        if command[0]=="M03":
            #Checks that spindle speed is given before it is turned on. If it
            #is not the program gives error message and stops.
            if self.spindle_speed_==0:
                print("Cannot start the spindle because spindle rotation speed"\
                      " is not given.")
                return False
            else:
                self.client_.turn_rotation_on_off(True)
        #Spindle off if command is M05
        else:
            self.client_.turn_rotation_on_off(False)

    #Sets what tool will be used in machine but not change it.
    def set_tool(self, command:list):
        tool=re.findall(r"\d+", command[0])
        self.tool_=tool[0]

    #Changes the before given tool to machine. Gives error message and stops
    #the program if tool is not set earlier. Also stops cooling and turns
    #spindle off.
    def change_machine_tool(self):
        #Stops the spindle and sets the cooling off that the tool can be changed
        self.spindle_speed_=0
        self.is_cooling_on_=False

        #Changing tool if it is given earlier.
        if self.tool_=="":
            print("ERROR! The tool must be chosen before it can be changed.")
            return False
        else:
            self.client_.change_tool(self.tool_)

    #Sets cooling on/off depending the given command. Also gives error message
    #if the cooling is on/off and the user tries to turn it on/off.
    def handle_cooling(self, command:list):
        #Cooling on
        if command[0]=="M08":
            if self.is_cooling_on_==True:
                print("The cooling is already on!")
            else:
                self.client_.coolant_on()
                self.is_cooling_on_=True

        #Cooling off
        elif command[0]=="M09":
            if self.is_cooling_on_==False:
                print("Error! Cooling cannot be set off because it is not on.")
            else:
                self.is_cooling_on_==False
                self.client_.coolant_off()

    #Moves machine to home position
    def move_home(self, command:list):
        self.client_.home()
        self.move_spindle(command)
    
    #Tells what settings are done to machine when setupping it. Uses 
    #MachineClient class to show these settings to user.
    def setup_machine(self, command:list):
        setup_text=f"[{command[0]}] "
        if command[0]=="G17":
            setup_text+="All commands are now to be interpreted in the"\
                " XY plane."
        elif command[0]=="G21":
            setup_text+="Units are set to millimeters when programming."
        elif command[0]=="G40":
            setup_text+="Set tool radius compensation off."
        elif command[0]=="G49":
            setup_text+="Set tool lenght offset compensation off."
        elif command[0]=="G54":
            setup_text+="Setting a specific coordinate system as the reference"\
            " point for cutting a particular part."
        elif command[0]=="G80":
            setup_text+="Motion modes cancelled."
        elif command[0]=="G90":
            setup_text+="Setting machine positioning mode to absolute and"\
            " taking current position as the reference point."
            self.positioning_mode_=ABSOLUTE_POSITIONING
            self.x_, self.y_, self.z_=0, 0, 0
        elif command[0]=="G91":
            setup_text+="Setting machine positioning mode to incremental."
            self.positioning_mode_=INCREMENTAL_POSITIONING
        elif command[0]=="G94":
            setup_text+="Feed rate mode units are set to units per minute mode."
        #Showing setting text to user.
        self.client_.show_machine_setups(setup_text)

    #Stops machine 
    def stop(self):
        self.client_.stop_machine()

#Reads G-code commands from the given file. Ignores comments, line numbers and
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
                #If command have parameters, the parameters and that command is 
                #added to list in list.
                words=line.split(" ")
                for word in words:

                    #Finds G01 commands and its parameters x, y, z-coordinates
                    #and feed rate.
                    if re.match(r"G01", word):
                        command=re.findall(r"G01|[XYZ]-?\d*\.\d*|F\d*\.\d?", \
                                           line)
                        commands.append(command)

                    #Finds G00 commands and its parameters x, y or z-coordinates
                    elif re.match(r"G00", word):
                        command=re.findall(r"G00|[XYZ]-?\d*\.\d*", line)
                        commands.append(command)

                    #Finds G28 command and its parameters x, y or z-coordinates
                    elif re.match(r"G28", word):
                        command=re.findall(r"G28|[XYZ]-?\d*\.\d*", line)
                        commands.append(command)

                    #Finds other commands that starts with G, T, M, F or S
                    #characters but that wich are not G01 or G00.
                    elif re.match(r"(?!G01|G00|G28)[GTMS]\d", word):
                        commands.append([word.strip()])
        file.close()

    except FileNotFoundError:
        print(f"Could not read file: {filename}")

    return commands


def main():
    """if len(sys.argv)>=2:
        filename=sys.argv[1]
    else:
        print("Run the program using commandline command: python cnc.py"\
              " <g-code-filename>. Ensure that you have writed g-code program"\
                " file name right.")
        return"""
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
        elif command[0]=="M03" or command[0]=="M05":
            if machine.turn_spindle_on_or_off(command)==False:
                return
            
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
            machine.handle_cooling(command)

        #Moves machine to home position
        elif command[0]=="G28":
            machine.move_home(command)

        #Reading and parsing machine initial setup commands.
        elif command[0]=="G17" or command[0]=="G21" or command[0]=="G40" or\
            command[0]=="G49" or command[0]=="G54" or command[0]=="G80" or \
            command[0]=="G90" or command[0]=="G91" or command[0]=="G94":
            machine.setup_machine(command)

        #Stops machine
        elif command[0]=="M30":
            machine.stop()

if __name__ == "__main__":
    main()