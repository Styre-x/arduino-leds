# arduino-leds
programs for my arduino led music sync

# required packages:
sounddevice numpy pyserial

# Hardware:
Using an arduino uno plugged into my desktop, I set up a circuit using the diagram in Circuit.pdf. Use a breadboard or similar to wire it up and it works :)

Make sure the ground is common but 12/24V are NOT being sent to the Arduino! Sending more than 5 will fry the poor thing. 

# Known issues:
You may need to change the permissions of your arduino to allow for you to access it, it works in vscode but not my native terminal with default permissions.