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
                        commands.append(word.strip())
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

if __name__ == "__main__":
    main()