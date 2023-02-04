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
#Moves spindle to given coordinates. Uses Machineclient class to show where
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

#Finds and sets spindle feed rate. Uses Machineclient class to show where
#what the set feed rate is.
def parse_and_set_feed_rate(machine:MachineClient, command:str):
    feed_rate=re.findall(r"\d*\.\d?", command)
    machine.set_feed_rate(float(feed_rate[0]))

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


if __name__ == "__main__":
    main()