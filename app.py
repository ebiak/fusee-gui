#!/bin/python3
import tkinter as tk
from tkinter import filedialog,ttk,Entry,Label,Button,PhotoImage,Listbox,Scrollbar,Text,Checkbutton,messagebox,Toplevel,BooleanVar
import fusee_launcher as fusee
import mock_arguments
import json
import platform
import subprocess
usb_backend  = fusee.HaxBackend.create_appropriate_backend()
#intiating the main window
root = tk.Tk()
root.title("fusee-gui")
root.minsize(400,300)
root.maxsize(400,300)
#checking for a switch and updating the status
def update():
    device = usb_backend.find_device(0x0955, 0x7321)
    if device:
        rcmstat.config(image=rcmDetected)
        payloadInject.config(state=tk.NORMAL)
    else:
        rcmstat.config(image=rcmNotDetected)
        payloadInject.config(state=tk.DISABLED)
    root.after(333,update)
#payload selection dialog the x is for the enter key bind
def selectPayload(x = 1):
    filename = filedialog.askopenfilename(initialdir="./", title = "Select File",
    filetypes=(("Binary","*.bin"),("All Files", "*.*")))
    if filename != "":
        payloadEntry.delete(0,tk.END)
        payloadEntry.insert(0,filename)
        #storing the current payload location so you don't have to choose it again
        f = open("settings.json","r")
        data = json.load(f)
        f.close()
        data["current"]=filename
        f = open("settings.json","w+")
        f.write(json.dumps(data,indent=4))
        f.close()
def sendPayload(payload):
    args = mock_arguments.MockArguments()
    args.payload   = payload
    args.relocator = "intermezzo.bin"
    #currently the logs arent "real time" they appear after the process has already finished
    Log.config(state=tk.NORMAL)
    logs = fusee.do_hax(args)
    for i in logs:
        Log.insert(tk.END,i+"\n")
    Log.config(state=tk.DISABLED)
    
#add a new favorite payload
def FavPayloadAdd(payload):
    e=0
    if payload != "":
        for i in payloadFavorites.get(0,tk.END):
            if payload == i:
                e+=1
        if e == 0:
            payloadFavorites.insert(tk.END,payload)
            f = open("settings.json","r")
            data = json.load(f)
            f.close()
            data["favorites"]=[]
            for i in payloadFavorites.get(0,tk.END):
                data["favorites"].append(i)
            f = open("settings.json","w+")
            f.write(json.dumps(data,indent=4))
            f.close()
#delete a favorite payload
def FavPayloadDel():
    payloadFavorites.delete(tk.ANCHOR)
    f = open("settings.json","r")
    data = json.load(f)
    f.close()
    data["favorites"]=[]
    for i in payloadFavorites.get(0,tk.END):
        data["favorites"].append(i)
    f = open("settings.json","w+")
    f.write(json.dumps(data,indent=4))
    f.close()
#and finally using a favorite payload
def FavPayloadSelect(event):
    payloadEntry.delete(0,tk.END)
    payloadEntry.insert(0,payloadFavorites.get(tk.ACTIVE))
    f = open("settings.json","r")
    data = json.load(f)
    f.close()
    data["current"]=payloadFavorites.get(tk.ACTIVE)
    f = open("settings.json","w+")
    f.write(json.dumps(data,indent=4))
    f.close()
def patchEhci(password,top):
    proc = subprocess.Popen(['echo {} | sudo -S ./ehci_patch.py'.format(password)], stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    output = proc.stdout.read()
    errOutput = proc.stderr.read()
    Log.config(state=tk.NORMAL)
    Log.insert(tk.END,output)
    Log.insert(tk.END,errOutput)
    Log.config(state = tk.DISABLED)
    top.destroy()
#the dialog for entering your password in case of patching ehci drivers
def ehciDialog():
    if platform.system() != "Linux":
        messagebox.showerror("Non linux oprating system detected","Don't use this on non linux operating systems ,it's not tested and there is no reason to")
    else:
        top = Toplevel(root)
        Label(top, text="Enter your password:").pack()
        e = Entry(top,show="*")
        e.pack(padx=5)
        e.bind('<Return>',lambda event: patchEhci(e.get(),top))
        okButton = Button(top, text="OK",command=lambda: patchEhci(e.get(),top))
        okButton.pack(pady=5)
        Label(top,text="after entering your password and pressing ok\n you should see something like \n\"Opration not permitted\" in the log box").pack()
        root.wait_window(top)
#updating the check box
def updateCb():
    f = open("settings.json","r")
    data = json.load(f)
    f.close()
    data["askOnStart"]=StartUpVar.get()
    f = open("settings.json","w+")
    f.write(json.dumps(data,indent=4))
    f.close()
#intiating tabs
tabControl = ttk.Notebook(root)
payloadTab = ttk.Frame(tabControl)
tabControl.add(payloadTab, text = "Payload")
# The tools tab which will be completed in future releases
# toolsTab = ttk.Frame(tabControl)
# tabControl.add(toolsTab,text = "Tools")

settingsTab = ttk.Frame(tabControl)
tabControl.add(settingsTab,text = "Settings")
#payload tab widgets
payloadLabel = Label(payloadTab,text="select payload:",font="arial 10 bold")
payloadLabel.grid(column=0,row=0,sticky=tk.W)
try:
    f=open("settings.json","r")
    settings = json.load(f)
    f.close()

    payloadEntry = Entry(payloadTab,width = 22,font="arial 15")
    payloadEntry.grid(column=0,row=1)
    payloadEntry.delete(0,tk.END)
    payloadEntry.insert(0,settings["current"])
except:
    f = open("settings.json","w+")
    f.write("{}")
    f.close()

    payloadEntry = Entry(payloadTab,width = 22,font="arial 15")
    payloadEntry.grid(column=0,row=1)

browse = PhotoImage(file = "res/browse.png")
payloadSelectFile = Button(payloadTab,image = browse,command=selectPayload)
payloadSelectFile.bind('<Return>',selectPayload)
payloadSelectFile.grid(column=2,row=1)

payloadInject = Button(payloadTab,text = "Inject Payload",command=lambda: sendPayload(payloadEntry.get()))
payloadInject.bind('<Return>',lambda event: sendPayload(payloadEntry.get()))
payloadInject.grid(column=3,row=1)

payloadFavoritesLable = Label(payloadTab,text = "Favorites:",font = "arial 10 bold")
payloadFavoritesLable.grid(column = 0,row = 2,sticky=tk.W)

payloadFavorites = Listbox(payloadTab,width = 44 ,height = 6,selectmode="single")
payloadFavorites.grid(column = 0,columnspan = 4,row=3,sticky = tk.W)
payloadFavorites.bind("<Double-Button-1>",FavPayloadSelect)
payloadFavorites.bind("<Return>",FavPayloadSelect)
try:
    for i in settings["favorites"]:
        payloadFavorites.insert(tk.END,i)
except:
    pass
pfAddIco=PhotoImage(file="res/add.png")
pfDelIco=PhotoImage(file="res/delete.png")

#favorite payload button
pfAdd= Button(payloadTab,image=pfAddIco,command=lambda: FavPayloadAdd(payloadEntry.get()))
pfDel= Button(payloadTab,image=pfDelIco,command=FavPayloadDel)
pfAdd.grid(row=3,column=3,sticky=tk.NE,padx=5)
pfDel.grid(row=3,column=3,sticky=tk.E,padx=5)
tabControl.pack(expan = 1, fill = "both")

#settings tab
spacer1 = Label(settingsTab,text=" ")
spacer1.grid(row=0,column=0)

ehciPatch = Button(settingsTab,text="Patch EHCI",command=ehciDialog)
ehciPatch.grid(row=1,column=1)

note1 = Label(settingsTab,text = "(Note: Only for use on Linux)")
note1.grid(row=1,column=2)

spacer2 = Label(settingsTab,text=" ")
spacer2.grid(row=2,column=0)
#asking for ehci patch on start up check box
StartUpVar = BooleanVar()
StartUpCB = Checkbutton(settingsTab,text = "Ask for EHCI patch on app start up",variable=StartUpVar,command=updateCb)
try:
    if settings["askOnStart"]:
        StartUpCB.select()
        ehciDialog()
except:
    pass
StartUpCB.grid(row=3,column=1,columnspan=2)
#a little note
Label(settingsTab,text="(Note: Also only for Linux)").grid(row = 4,column=1,columnspan=2)
#RCM Status and log
rcmDetected = PhotoImage(file="res/rcm_detected.png")
rcmNotDetected = PhotoImage(file="res/rcm_undetected.png")
rcmstat = Label(root,image=rcmNotDetected)
rcmstat.place(x=5,y=212)
Log = Text(root,width=23,height=3,state=tk.DISABLED,font="arial 10",wrap = tk.WORD)
Log.place(x=130,y=212,width=265,height=84)
update()
#start up the window
root.mainloop()