Apex
==============
The initial version of Apex optimizes the JVC + HD Fury Macro experience.

The JVC RS500/RS600 projector models have the tech specs to support HDR very well (at least for projectors), but JVC provided a truly terrible HDR implementation. Amazing people on AVS have come up with ways to get HDR working on these projectors.  One part of this requires using an HDFury product, such as the Vertex 2, and connecting it via serial/RS232 to the JVC projector.  The HDFury then sends "macro" commands via RS232 which cause the JVC to select appropriate HDR (or non-HDR) picture mode. 

Apex optimizes this step by intelligently working with the JVC projector.  Without Apex, you must select a single default "delay" on the HDFury product.  When the HDFury product sees a content HDR transition, it waits the amount of time specified by this delay, and then sends the "macro".  A delay is often needed because the JVC stops listening to all commands when changing certain modes and this sometimes occurs when HDR content is started or ended.  The JVC may be in the "not listening" state for many seconds, perhaps up to 20.  Because of this, many people set the HDFury delay to 20 seconds.  However, this means that the user must always wait 20 seconds for the correct HDR mode to be selected, even if the JVC is ready to display content immediately or anything faster than 20 seconds.

Apex works intelligently with the JVC and sends the macro command as soon as the JVC is ready to receive the command.   If the JVC is ready after 1 second, the HDR switch occurs after about 1 second.   JVC ready after 5 seconds?  The switch occurs after about 5 seconds.  If it takes a full 20 seconds, the switch will occur at that time.

Apex removes the need to connect a serial cable to the JVC because Apex communicates with the JVC using Internet Protocol.  The HDFury is now connected by serial to the device running Apex.

Apex Setup
==============
Apex is written in Python 3.  There are a million ways to run python code.  Below is one simple approach.  

1) Create a directory somewhere called apex
2) Retrieve Apex from the Repo
3) Install the requirements using "pip3 install -r requirements.txt"
4) Configure Apex with the IP address of your JVC and the device name of your serial port.  In the apex.yaml file, change "jvcip" to be the IP of the JVC projector and change "hdfury" to be the serial device name of the HDFury device.
5) Eventually you'll want to have Apex start automatically, but to get started you can simply use "python3 apex.py"

It outputs basic info to stdout and more detailed info to x0.log

HDFury Setup
==============
The HDFury requires the following configuration:

1) Make sure the HDFury device's serial output is connected to the device running Apex.  If you use a serial extension cable, ensure it is a straight serial cable (NOT a NULL modem cable).  
2) Set the Macro "Sync Delay (secs)" to be 1.  I wish it could be set to 0, but the HDFury does not work correctly when 0 is specified.
3) Make sure the Macro "Send on every sync" is checked. 
4) Don't forget to press the "Send Macro Values" button on the bottom of the screen.   This is required for the HDFury device is save the new settings.

Tips
==============
If you don't know how the serial ports are named on the device running Apex, you can launch Apex with the flag "--showserialports" and it will output the potential serial ports

Apex also supports a basic passthrough mode where Apex's intelligent behavior is disabled and it acts as a dumb serial to IP bridge.  This mode can be used to compare behavior with and without Apex's intelligence.  Use the flag "-passthrough" when launching Apex to enable passtrhough mode.