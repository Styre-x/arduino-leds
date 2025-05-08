# arduino-leds
programs for my arduino led music sync \
Easy to use with an arduino, it allows control over RGB light strips.

# Required python packages:
sounddevice numpy pyserial

# Hardware:
Using an arduino uno plugged into my desktop, I set up a circuit using the diagram in Circuit.pdf. Use a breadboard or similar to wire it up and it works :)
## NOTE ##
Green pin is **11** not **8**.\
Make sure the ground is common but 12/24V are NOT being sent to the Arduino! Sending more than 5 will fry the poor thing. 

# Running
Run the script. It is written for Linux, so the device name will be different on other operating systems. \
You can move and chmod the ledstrip file into /usr/bin for a single command to launch the script, assuming it is located in ~/Documents.

# Known issues:
You may need to change the permissions of your arduino to allow for you to access it, it works in vscode but not my native terminal with default permissions.