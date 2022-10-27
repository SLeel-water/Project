##
## Read from a serial port and print received data.
## Set portName to be the name of teh serial port to be used.
##
## Author:  Greg Watkins
## Date:    10 Sep 2021
##

import serial
import time
import sys
from tkinter import *
from random import randint
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, FigureCanvasAgg
from matplotlib.figure import Figure
import tkinter as tk
import PySimpleGUI as sg
import numpy as np
from numpy.fft import fft, ifft
def addplot(canvasElement):
    """
    Adds matplotlib axes to a canvas element.
    Plots can then be drawn on the axes.

    reference: matplotlib-window-with-gui-window
    
    Input: canvasElement
        An sg.Canvas element placed in the layout.
    Output: ax
        axes for plotting figAgg - the aggregated figure and canvas.
        Once this is returned by this function you can plot on it like
        any other matplotlib subplot.
    Author: DX 
    """

    # create a figure
    fig = Figure()
    # create a set of axes on the figure
    ax = fig.add_subplot(1,1,1)

    canvas = canvasElement.TKCanvas

    # place the element on the canvas
    figAgg = FigureCanvasTkAgg(fig, canvas)
    figAgg.draw()
    figAgg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return ax, figAgg


serialString = ""  # Used to hold data coming over UART
portName = "COM6"          # PC format
#portName = "/dev/tty.DXDevice-ESP32SPP"    # Mac format


# define the serial port.
# specify parameters as needed
serialPort = serial.Serial()
serialPort.port=portName 
serialPort.baudrate=115200
serialPort.bytesize=8
serialPort.timeout=2 
serialPort.stopbits=serial.STOPBITS_ONE

# used to test packet legitimacy
integers=[48,49,50]

# arrays to store sensor data and time (x and y axes data)
sample_time=0.02
time=[]
sensor_data=[]

# m - counter var for time calcs, k -  counter var for maintaining sensor_data and time length
m=0
k=0

# bool to check when to break while loop (i.e when exit button is pressed)
closer = True

# open the port
try:
    serialPort.open()
except:
    print("Port open failed: " + portName)
    for e in sys.exc_info():
        print("  ",e)
    

if serialPort.isOpen():
    print("**************************************")
    print("** Serial port opened: {}".format(portName))
    print("**************************************")

    # define the layout for PySimpleGUI window
    layout=[
        [sg.Canvas(key="myCanvasKey")],
        [sg.Canvas(key='Heart Rate')],
        [sg.Button('Exit',key = 'EXIT_BUTTON')]
         ]
    window=sg.Window("Matplotlib integrated in PySimpleGUI", layout, finalize=True)
    canvasElement = window["myCanvasKey"]
    ax, figAgg = addplot(canvasElement)
    #the canvas element for the heart rate graph
    HRElement = window['Heart Rate']
    axHR, figAggHR = addplot(HRElement)
    #
    while closer:
        # Wait until there is data waiting in the serial buffer
        if serialPort.in_waiting > 0:
            # Read data out of the buffer until a carraige return / new line is found
            serialString = serialPort.readline()
            #print(serialString)
            #print(serialString.decode("Ascii"), end = "")

            #Create an if statement so that if there is no packet, reply user
            if serialString[0] in integers:

                # loop through packet to append to string
                for i in range(50):
                    sensor_data.append(int(serialString[5*i+4:5*i+8]))
                    time.append(sample_time*m)
                    m +=1
                #sequenceNO= int(serialString[0:2])

                # loop through 6 times before starting to delete data off string
                if k<6:
                    k=k+1
                if k==6: 
                    sensor_data=sensor_data[50:]
                    time= time[50:]

                # clear axes
                ax.cla()

                # label shit
                ax.set_xlabel("X Axis")
                ax.set_ylabel("Y Axis")
                ax.set_title("Random Data")
                ax.set_ylim(0,4000)

                # replot, then redraw
                ax.plot(time, sensor_data)
                figAgg.draw()

                # This is FFT from Antonias code, I changed the total data variable to sensor_data variable. 
                data_df = sensor_data-np.mean(sensor_data)
                
                fft_PPG = fft(data_df)
                fft_y = np.abs(fft_PPG)
                sample_rate = data_df.mean()
                N = len(fft_PPG)
                n = np.arange(N)
                T = N/sample_rate
                freq = n/T 

                # clunky bandpass filter using FFT data
                min_freq = 0.5
                max_freq = 10
                x_data, y_data = np.array([]), np.array([])
                for i in range(len(freq)):
                    if min_freq <= freq[i] <= max_freq:
                        x_data = np.append(x_data, freq[i])
                        y_data = np.append(y_data, fft_y[i])

                # Get BPM
                        bpm_freq = x_data[y_data.argmax()]
                        bpm_point = np.array([bpm_freq, max(y_data)])


                SEC15STORAGEY = []
                SEC15STORAGEX = []
                # if len(y) == 250:
                #     for i in range(len(y)):
                #         SEC15STORAGEY.append(y[i])
                #     for i in range(len(y)):
                #         SEC15STORAGEX = time
                # elif len(y) > 250:
                #     for i in range(len(y[-50:0])):
                #         SEC15STORAGEY.append(y[(-50+i):0])
                #     for i in range(len(time[-50:0])):
                #         SEC15STORAGEX.append(time[(-50+i):0])
                for i in range(len(bpm_freq)):
                    print(bpm_freq[i])
                # clear axes
                axHR.cla()

                # label shit
                axHR.set_xlabel("X Axis")
                axHR.set_ylabel("Y Axis")
                axHR.set_title("Random Data")
                axHR.set_ylim(0,20000)

                # replot, then redraw
                axHR.plot(SEC15STORAGEX, SEC15STORAGEY)
                figAggHR.draw()


        # detect user input on gui, but pass if no input in 10ms
        event, values = window.read(timeout = 10)

        # close gui when exit button pressed
        if event in ['EXIT_BUTTON', sg.WIN_CLOSED]:
            window.close()

            # turn closer to false so that loop ends when gui is closed
            closer = False

            
            #print(sensor_data)
            #print(time)
else:
    print("Exiting")