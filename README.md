# arduino-leds
programs for my arduino led music sync \
Easy to use with an arduino, it allows control over RGB light strips.

# Python or C

Included are two options, Python scripts and a C program + source code.\
C is faster, lighter, and works better, but python is easier to change and add more functions to.\
Either works the same. LEDControl is the compiled x86-64 program. Only download that if you just want to run it quickly. PulseAudio needs to be installed on the system.\
Pass the device to listen to (can be gotten through pactl list sources short and finding *.monitor) and the location of the arduino, usually /dev/ttyACM0.\
Brightness 0-255 can be passed as well as the last argument, but is not required. 

## NOTE ##
Python will listen to a microphone if one is plugged into the system. Changing to a monitor was awful to figure out so I just did it in C.

# Required python packages:
sounddevice numpy pyserial

# Hardware:
Using an arduino uno plugged into my desktop, I set up a circuit using the diagram in Circuit.pdf. Use a breadboard or similar to wire it up and it works :)
## NOTE ##
Green pin is **11** not **8**.\
Make sure the ground is common but 12/24V are NOT being sent to the Arduino! Sending more than 5 will fry the poor thing. 

# Running
Run the script with the device location as the first argument. Windows is COMx, Linux is /dev/ttyACMx. Numbers will differ depending on other serial devices.
