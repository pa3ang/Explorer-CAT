# PA3ANG  V1.0  April 2025
# made on Windows (geometrics Tkinter
# script is platform independent
#
# program is basically made to support the Radio-Kits Explorer 20 meter version
# CAT protocol is based on Kenwood TS-480
# limited set of command's is used

import serial
import time
from tkinter import *

# Serial port settings
SERIAL_PORT = "COM17"
SERIAL_SPEED = 9600
SERIAL_STOPBITS = serial.STOPBITS_TWO
SERIAL_TIMEOUT = 1.0

# Frequentie presets
MEMORIES = [
    (7020000, "CWN"),
    (7073000, "LSB"),
    (14020000, "CWN"),
    (14060000, "CW"),
    (14100000, "CWN"),
    (14195000, "USB"),
    (14245000, "USB"),
    (14292000, "USB"),
]

# Mode Mapping
MODE_MAP = {
    "1": "LSB",
    "2": "USB",
    "3": "CW",
    "7": "CWN",
    "6": "DAT",
}

# Initialise Tkinter window
window = Tk()
window.geometry("464x122")
window.wm_title(f"Simpel CAT Program RK Explorer. @ {SERIAL_PORT}, {SERIAL_SPEED} Bd")

# Global variables
current_frequency 	= MEMORIES[0][0]
last_frequency 		= 0  
current_vfo 		= "A"
current_mode 		= StringVar()
current_mode.set("USB") 
current_volume 		= 1  
cw_speed 		= 12

# Funtions 
def serial_write(cmd):
    """ Send the CAT-commando to the Explorer. """
    try:
        with serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_SPEED, stopbits=SERIAL_STOPBITS, timeout=SERIAL_TIMEOUT) as ser:
            ser.write(str.encode(cmd))
    except serial.SerialException as e:
        print(f"Seriele fout: {e}")

def read_explorer():
    """ Read relevant values from the Explorer. """
    global current_frequency, last_frequency, current_vfo, current_mode, current_volume, current_speed 

    try:
        with serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_SPEED, stopbits=SERIAL_STOPBITS, timeout=SERIAL_TIMEOUT) as ser:
        
            # read Frequency of active VFO
            cmd = b'FA;' if current_vfo == "A" else b'FB;'
            ser.write(cmd) 
            response = ser.read(14).decode('ascii', errors='ignore')
            if response.startswith("F"+current_vfo):
                freq_hz = response[2:12]
                current_frequency = int(freq_hz)*10
                freq_khz = int(freq_hz) / 100
                if freq_khz != last_frequency:
                    current_frequency 	= freq_khz
                    last_frequency 	= freq_khz
                    # put frequency on screen
                    entry_frequency.delete(0, END)  
                    entry_frequency.insert(0, f"{freq_khz:.3f}")  
                    
            # read Mode   
            ser.write(b'MD;')
            response = ser.read(4).decode('ascii', errors='ignore')
            if response.startswith("MD"):
            	mode_code = response[2]
            	mode_name = MODE_MAP.get(mode_code, "Unknown")
            	# update drop down menu
            	current_mode.set(mode_name)
            	
            # read selected VFO	
            ser.write(b'FT;')
            response = ser.read(4).decode('ascii', errors='ignore')
            if response.startswith("FT"):
                current_vfo = "A" if response[2] == "0" else "B"
                # update buttton
                button_vfo.config(text=f"VFO {current_vfo}") 
                
            # read AF Gain
            ser.write(b'AG0;')
            response = ser.read(7).decode('ascii', errors='ignore')
            if response.startswith("AG"):
                current_volume = int(response[2:6])/16
                # update slider
                volume_slider.set(current_volume) 
	        
            # read CW Speed 
            ser.write(b'KS;')
            response = ser.read(6).decode('ascii', errors='ignore')
            if response.startswith("KS"):
                cw_speed = int(response[3:5])
                # update slider
                cw_speed_slider.set(cw_speed)  
                  
    except serial.SerialException as e:
        print(f"Seriele fout: {e}")


def set_direct_frequency():
    """ Read frequency from panel, convert, check and send to Explorer. """
    try:
        freq_khz = float(entry_frequency.get())	# Read frequency as float (bijv. 7073.5)
        freq_hz = int(freq_khz * 1000)  	# Translate to Hz 
        
        if 1000000 <= freq_hz <= 30000000:  	# Check range(5 MHz - 15 MHz)
            set_frequency(freq_hz)
        else:
            print("Fout: Frequentie buiten bereik.")
    except ValueError:
        print("Fout: Ongeldige invoer, voer een geldig getal in.")
        
def set_volume(level):
    """ Send new volumme setting. """
    global current_volume
    current_volume = max(0, min(15, level)) 
    set_volume 	= int(current_volume*16)
    cmd 	= f"AG0{set_volume:03d};"
    serial_write(cmd)
    
def set_cw_speed(speed):
    """ Change CW Speed. """
    global cw_speed
    cw_speed = max(12, min(30, speed)) 
    cmd = f"KS{cw_speed:03d};"
    serial_write(cmd)

def toggle_vfo():
    """ Change VFO A/B. """
    global current_vfo
    new_vfo 	= "B" if current_vfo == "A" else "A"
    cmd 	= "FT1;" if current_vfo == "A" else "FR0;"
    serial_write(cmd)  # Stuur VFO-wissel commando
    
def set_frequency(frequency):
    """ Set new frequency in active VFO. """
    global current_frequency, current_vfo
    current_frequency = frequency
    prefix 	= "F"+current_vfo+"0000" if frequency < 10000000 else "F"+current_vfo+"000"
    cmd 	= f"{prefix}{frequency:07d};"
    serial_write(cmd)

def set_mode(selected_mode):
    """ Set new mode. """
    mode_code = {v: k for k, v in MODE_MAP.items()}.get(selected_mode, "2")  # Default naar USB
    cmd = f"MD{mode_code};"
    serial_write(cmd)

def set_memory(frequency, mode):
    set_mode(mode)
    set_frequency(frequency)

# Create compact screen based on Python Tkinter / Windows
# Input for direct frequency
entry_frequency = Entry(window, width=10, font=('Arial', 14))
entry_frequency.grid(column=0, row=1, padx=5, columnspan=2)
entry_frequency.bind("<Return>", lambda event: set_direct_frequency())

# Mode drop-down menu
mode_menu = OptionMenu(window, current_mode, *MODE_MAP.values(), command=set_mode)
#mode_menu.config(width=4)
mode_menu.grid(column= 2, row=1, ipady=3, padx=2)

# VFO A/B button
button_vfo = Button(window, text="VFO ?", bg="lightblue", command=toggle_vfo, width=6)
button_vfo.config(width=9)
button_vfo.grid(column=  3, row=1, ipady=3, padx=2)

# Frequency 1kHz tuning buttons
Button(window, text="-1 kHz",   bg="lightblue", command=lambda: set_frequency(current_frequency-1000),  width=9).grid(column= 4, row=1, ipady=3, padx=2)
Button(window, text="+1 kHz ",  bg="lightblue", command=lambda: set_frequency(current_frequency+1000),  width=9).grid(column= 5, row=1, ipady=3, padx=2)

# Label for AF Gain and slider
label_gain = Label(window, text="AF Gain")
label_gain.grid(column=4, row=2, padx=6)
volume_slider = Scale(window, from_=0, to=15, orient=HORIZONTAL, length=68, command=lambda current_volume: set_volume(int(current_volume)))
volume_slider.grid(column= 5, row=2, ipady=0, padx=2)

# Label for CW Speed and slider
label_speed = Label(window, text="CW Speed")
label_speed.grid(column=4, row=3, padx=6)
cw_speed_slider = Scale(window, from_=12, to=30, orient=HORIZONTAL, length=68, command=lambda cw_speed: set_cw_speed(int(cw_speed)))
cw_speed_slider.grid(column= 5, row=3, ipady=0, padx=2)

# Memory buttons 
for idx, (freq, mode) in enumerate(MEMORIES):
    row_number = 2 + (idx // 4)
    column_number = idx % 4
    Button(window, text=str(freq // 1000)+"/"+str(mode), command=lambda f=freq, m=mode: set_memory(f,m), width=9).grid(column=column_number, row=row_number, ipady=4, padx=2)

# Automatic update for ever routine
def update_status():
    read_explorer()
    window.after(1000, update_status)

update_status()
window.mainloop()
