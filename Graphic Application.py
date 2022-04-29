import sys
from time import sleep
from tkinter import *

sys.path.append('.')
from C1100 import C1100

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib import pyplot as plt


window = Tk()
figure = plt.Figure(figsize=(5,4), dpi=100)
scatter = FigureCanvasTkAgg(figure, window)
lGraph = figure.add_subplot(121)
rGraph = figure.add_subplot(122)

timeStep = 0.1
nbMesures = 100
Commande=[0,10,20,30,40,50,40,30,20,10,0]
Temps= []
Position = []
Courant = []

def mesurerCourant():
    global timeStep, nbMesures, Courant, Temps,controler
    Courant = []
    Temps = []
    for i in range(nbMesures):
        c = controler.getCurrent()
        Courant.append(c)
        Temps.append(i*timeStep)
        sleep(timeStep)

def mesurerPosition():
    global Position,controler,Temps,timeStep,nbMesures
    Position = []
    Temps = []
    for i in range(nbMesures):
        pos = controler.getPosition()
        Position.append(pos)
        Temps.append(i*timeStep)
        sleep(timeStep)
    return

def OnButtonPressed():
    global lGraph,Temps,Position,timeStep,nbMesures
    timeStep = float(timeStep_field.get())
    nbMesures = int(nbm_field.get())
    mesurerPosition()

    lGraph.clear()
    lGraph.plot(Temps, Position, color='blue', marker='')
    lGraph.set_title('Position en Fonction du Temps', fontsize=14)
    lGraph.set_xlabel('Temps (s)', fontsize=14)
    lGraph.legend(['Position'], fontsize=9)
    lGraph.set_ylabel('Position', fontsize=14)
    lGraph.grid(True)
    scatter.draw()
    return

def plotRightGraph():
    global rGraph,Temps,Courant,timeStep, nbMesures
    timeStep = float(timeStep_field.get())
    nbMesures = int(nbm_field.get())
    mesurerCourant()

    rGraph.clear()
    rGraph.plot(Courant, color='red', marker='')
    rGraph.set_title('Courant en fonction du temps', fontsize=14)
    rGraph.set_xlabel('Temps (s)', fontsize=14)
    rGraph.legend(["Courant"], fontsize=9)
    rGraph.set_ylabel('Courant', fontsize=14)
    rGraph.grid(True)
    scatter.draw()
    return

def ErrorAck():
    global controler
    controler.ErrorAck()
    sleep(0.05)

def Home():
    global controler
    controler.Home()
    
def Unlock():
    global controler
    controler.UnlockMotor()

# MAIN
controler = C1100()
controler.InitControler()

window.title('LinMot project')
window.geometry('1200x650')

plot_button = Button(master = window, height = 2, width = 10, text = "Take Mesure", command=OnButtonPressed)
errorAck_button = Button(master = window, height = 2,  width = 10, text = "Error Ack", command=ErrorAck)
home_button = Button(master = window, height=2,width=10,text="Home",command=Home)
unlock_button = Button(master= window, height=2,width=10,text="Unlock",command=Unlock)
plotR_button = Button(master=window, height = 2, width = 10, text = "Take Mesure", command=plotRightGraph)

timestep_label = Label(master=window, height=2, width=7,text="Timestep")
timeStep_field = Entry(master=window, width=5)

nbm_label = Label(master=window, height=2, width=8,text="Nb Mesures")
nbm_field = Entry(master=window, width=5)

nbm_field.insert(END,'150')
timeStep_field.insert(END,'0.05')

plot_button.place(x=15,y=400)
timestep_label.place(x=15,y=440)
timeStep_field.place(x=80,y=450)
nbm_label.place(x=15,y=470)
nbm_field.place(x=80,y=480)

errorAck_button.place(x=145,y=400)

home_button.place(x=245,y=400)

unlock_button.place(x=345,y=400)

plotR_button.place(x=700, y = 400)

lGraph.plot(Temps, Position, color='red', marker='')
lGraph.plot(Temps, Courant, color='blue', marker='')
lGraph.set_title('Position et Courant en Fonction du Temps', fontsize=14)
lGraph.set_xlabel('Temps (s)', fontsize=14)
lGraph.legend(['Position','Courant'], fontsize=9)
lGraph.set_ylabel('Position/Courant', fontsize=14)
lGraph.grid(True)

rGraph.plot(Courant, color='red', marker='')
rGraph.set_title('Courant en fonction de la Position', fontsize=14)
rGraph.set_xlabel('Position', fontsize=14)
rGraph.legend(["Courant"], fontsize=9)
rGraph.set_ylabel('Courant', fontsize=14)
rGraph.grid(True)

scatter.get_tk_widget().pack(side=TOP, fill=BOTH)

window.mainloop()