import sys
import re
import MachineClient

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
                        command=re.findall(r"G01|[XYZ]-?\d*\.\d*", line)
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
#Parses x, y, z-coordinates from the command list and returns x, y, z
#coordinates in tuple. If commandlist doesn't contain different coordinate that
#coordinate is set to 0. 
def parse_coordinates(command:list)->tuple:
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
#Moves spindle to given coordinates. Uses MachineClient class to show where
#spindle is moving.
#SOME ERROR PREVENTION SHOULD ADD HERE, eg. what if all coordinates are 0.
def move_spindle(machine:MachineClient, coordinates:list):
    #Moving spindle x-position
    if coordinates[1]==0 and coordinates[2]==0:
        machine.move_x(coordinates[0])
    #Moving spindle y-position
    elif coordinates[0]==0 and coordinates[2]==0:
        machine.move_y(coordinates[1])
    #Moving spindle z-position
    elif coordinates[0]==0 and coordinates[1]==0:
        machine.move_z(coordinates[2])
    #Linear movement to given xyz-coordinates
    elif coordinates[0]!=0 and coordinates[1]!=0:
        machine.move(coordinates[0], coordinates[1], coordinates[2])

#Finds and sets spindle feed rate. Uses MachineClient class to show where
#what the set feed rate is.
def parse_and_set_feed_rate(machine:MachineClient, command:str):
    #Feed rate in mm/min
    feed_rate=re.findall(r"\d*\.\d?", command)
    #Feed rate in mm/s
    feed_rate=float(feed_rate[0])/60
    machine.set_feed_rate(feed_rate)

#Finds spindle speed (rpm) from g-code command and sets that to spindle with 
#using MachineClient class.
def parse_and_set_spindle_speed(machine:MachineClient, command:str):
    spindle_speed=feed_rate=re.findall(r"\d+", command)
    machine.set_spindle_speed(int(spindle_speed[0]))

#Finds tool number from g-code command and shows that for user by using
#MachineClient class.
def change_machine_tool(machine:MachineClient, command:str):
    #Finds tool number from g-code.
    tool=re.findall(r"(?!0)\d+", command)
    #Calling machine to use that tool.
    machine.change_tool(tool[0])

def handle_cooling(machine:MachineClient, command):
    if command=="M08":
        machine.coolant_on()
    else:
        machine.coolant_off()


def main():
    #filename=sys.argv[1]
    filename="rectangle.gcode"
    #Reading files G-codes to list
    commands=read_file(filename)

    #Interface object for printing what machine does
    machine=MachineClient.MachineClient()
    #Translating G-codes with using that interface
    for command in commands:
        #Moving spindle
        if command[0]=="G01":
            coordinates=parse_coordinates(command)
            move_spindle(machine, coordinates)

        elif command[0]=="G00":
            coordinates=parse_coordinates(command)
            #If no coordinates given, machine movement 
            if coordinates[0]==coordinates[1]==coordinates[2]==0:
                machine.set_movement_mode()
            else:
                move_spindle(machine, coordinates)
        #Spindle feed rate set
        elif command[0].startswith("F"):
            parse_and_set_feed_rate(machine, command[0])
        #Spindle speed set
        elif command[0].startswith("S"):
            parse_and_set_spindle_speed(machine, command[0])
        #Changing machine tool
        elif command[0].startswith("T"):
            change_machine_tool(machine, command[0])

        elif command[0]=="M08" or command[0]=="M09":
            handle_cooling(machine, command[0])
if __name__ == "__main__":
    main()