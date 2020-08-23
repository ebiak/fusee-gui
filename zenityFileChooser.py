import subprocess

def fileChooser(fileType):
    command = f"zenity --file-selection --filename=. --file-filter={fileType}".format(fileType)
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE,universal_newlines=True)
    output, error = process.communicate()
    return output.rstrip()
# debuging
if __name__ == "__main__":
    print(fileChooser("*.png"))