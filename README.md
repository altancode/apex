# Apex

Apex is a powerful tool to control your JVC projector.   Apex offers several features.

1. Apex optimizes the JVC + HD Fury HDR experience.
2. Apex allows deep control of the JVC using both network connectivity and IR

# Apex HDR Experience Optimization

The JVC RS500/RS600 projector models have the tech specs to support HDR very well (at least for projectors), but JVC provided a truly terrible HDR implementation. Amazing people on AVS have come up with ways to get HDR working on these projectors.  One part of this requires using an HDFury product, such as the Vertex 2, and connecting it via serial/RS232 to the JVC projector.  The HDFury then sends "macro" commands via RS232 which cause the JVC to select appropriate HDR (or non-HDR) picture mode. 

Apex optimizes this step by intelligently working with the JVC projector.  Without Apex, you must select a single default "delay" on the HDFury product.  When the HDFury product sees a content HDR transition, it waits the amount of time specified by this delay, and then sends the "macro".  A delay is often needed because the JVC stops listening to all commands when changing certain modes and this sometimes occurs when HDR content is started or ended.  The JVC may be in the "not listening" state for many seconds, perhaps up to 20.  Because of this, many people set the HDFury delay to 20 seconds.  However, this means that the user must always wait 20 seconds for the correct HDR mode to be selected, even if the JVC is ready to display content immediately or anything faster than 20 seconds.

Apex works intelligently with the JVC and sends the macro command as soon as the JVC is ready to receive the command.   If the JVC is ready after 1 second, the HDR switch occurs after about 1 second.   JVC ready after 5 seconds?  The switch occurs after about 5 seconds.  If it takes a full 20 seconds, the switch will occur at that time.

Apex removes the need to connect a serial cable to the JVC because Apex communicates with the JVC using Internet Protocol.  The HDFury is now connected by serial to the device running Apex.

# Apex Deep Control

Apex allows commands from JVC's "External Control Command Communicaiton Specification" to be performed by network commands or IR keypresses.
Unlike using the projector's IR remote, or an automation solution like Harmony, Apex verifies that commands are actually performed.  With
Apex, for example, you don't need to hard code length (40 second?) delays because the JVC is switching inputs or is powering on.   Apex will
make sure the command is performed when the JVC is paying attention.

Deep control allows the following types of settings to be adjusted

* Lens Menory
* Aperture
* Contrast
* Brightness
* Gamma table
* Mask
* Lamp Power
* Etc.

# Apex Profiles

Everything (almost) in Apex is a profile.   A profile is a named collection of JVC control commands.  A profile can have 1 command or many commands.
Place whatever commands are needed to configure your JVC for your specific situation.  For example, you could createa a profile called 
"cinemascope" which activates the appropriate picture mode, lens zoom, lens aperture and mask settings.  You can be confident that all the commands
in your profile will be performed.

In addition to custom profiles, Apex has several "core" profiles that are used with the HDR + HDFury integraton.   When the HD Fury devices
tells Apex (via serial) to activate a specific picture mode, Apex activates a core profile named similar to the picture mode.  For example,
if HD Fury says to activate picture mode User 2 then Apex will enable profile "_APEX_PMUser2".  The default setting for profile "_APEX_PMUser2"
is to use the Apex Optimized Picture Mode algorithm for User 2.  However, you can add any commands you want to the core profiles.

Apex allows external devices to activate profiles using network communication.   Additionally, Apex allows profiles to be activated based on
IR commands.

# Is Apex Right for Me?

Apex may be right of you if...
* You are currently using, or plan to use, a JVC RS500/600 projector with an HDFury device to enable proper HDR?   
* Your current HDFury macros use the JVC picture modes (USER1, USER3, NORMAL, etc.)?
* You prefer to use IP connectivity to your JVC projector rather than running a serial/RS232 cable?
* You are annoyed by HDR modes activating or deactivating with seemly randomly delays after starting or stopping content? 
* Your JVC does not reliabily turn on or off and you'd like rock solid behavior?
* You are tired of hard coding 40+ second delays into your Harmony scripts in order to get the JVC to switch HDMI inputs
* Your HTPC integration with the JVC is not cutting it and you'd like a robust solution to control the JVC 

# Example of Apex's HDR Optimization Value

You use an NVIDIA Shield as a media player and use different applications such as Netflix and Kodi.  
* Play HDR with Netflix
  * Without Apex, when you start HDR content in Netflix, the HDR mode will not activate for about 20 seconds.
  * With Apex, the HDR mode activates almost immediately

* Play HDR with Kodi (w/frame rate matching set to "on start")
  * Without Apex, when you start HDR content, the HDR mode will activate many seconds after the frame rate changes
  * With Apex, the HDR mode activates almost immediately 

* Stop HDR content from Kodi
  * Without Apex, Kodi displays its menu and the color intensity is all wrong for close to 20 seconds and then changes
  * With Apex, Kodi displays its menu and the HDR mode turns off almost immediately

Note: There are lots of variables that impact the behavior described above, but the above is representative of what I see.  The non-Apex cases assume 
a HDFury "delay" setting of 20 seconds.

# Apex Setup

Apex is written in Python 3.  There are a million ways to run python code.  Below is one simple approach.  

1. Create a directory somewhere called apex
1. Retrieve Apex from the Repo
1. Install the requirements using "pip3 install -r requirements.txt"
1. Configure Apex with the IP address of your JVC and the device name of your serial port.  In the apex.yaml file, change "jvcip" to be the IP of the JVC projector and change "hdfury" to be the serial device name of the HDFury device.
1. Configure Apex for network control.  In the apex.yaml file, change "netcontrolport" to the port that Apex is listen on for external commands.  Also change 
"netcontrolsecret" to a secret value for your specific setup.
1. Eventually you'll want to have Apex start automatically, but to get started you can simply use "python3 apex.py"

# HDFury Setup

The HDFury device, such as the Vertex 2, requires the following configuration:

If you don't know how the serial ports are named on the device running Apex, you can launch Apex with the flag "--showserialports" and it will output the potential serial ports

1. Make sure the HDFury device's serial output is connected to the device running Apex.  If you use a serial extension cable, ensure it is a straight serial cable (NOT a NULL modem cable).  
1. Set the Macro "Sync Delay (secs)" to be 1.  I wish it could be set to 0, but the HDFury does not work correctly when 0 is specified.
1. Make sure the Macro "Send on every sync" is checked. 
1. Don't forget to press the "Send Macro Values" button on the bottom of the screen.   This is required for the HDFury device is save the new settings.

# Profile Details

Profiles are stored in the apex.yaml file.  All profiles, whether custom or core, exist under the "profiles" entry.  Below is an example.

```
profiles:
# Apex Core Profiles
# Profile names beginning with _APEX_ have specific meaning and should not be removed
# However, you are more than welcone to change the contents of the profile

  _APEX_PMFilm:
  - op: apexpm
    data: '00'

  _APEX_PMCinema:
  - op: apexpm
    data: '01'
```

All profiles follow a standard format.  First there is the profile name.   This is followed by an operation ("op") which is followed by a
couple of different parameters.

## Profile Operations

The following operations are supported

* apexpm.  This is Apex special sauce state machine that optimizes picture mode selection.  If you want to select a picture mode, you
should use apexpm instead of alternative methods.   When using apexpm, a "data" field must exist.  This indicates which picture mode
to activate.   

* raw.  The raw operatiobn mode allows any JVC control command to be executed.   Raw requires a "cmd" field and then either a "data" field or
a numeric field.   Either one can be used, the two options exist to make your life easier.  If numeric is specified, Apex takes the
specified signed integer and converts it into the JVC control format.  Alternatively, you can use the "data" field.  This field allows ASCII
data to be specified.

Here is an example of a raw command with numberic

```
  # set the aperture to -10
  - op: raw
    cmd: PMLA
    numeric: -10
```

Here is an example of a raw command with data

```
  # Gamma Custom 2
  - op: raw
    cmd: PMGT
    data: '5'
```

* rccode.  This standards for remote control code.  This operation allows buttons from the remote to be simulated.  Using rccode is
not recommended because the JVC control protocol treats these exactly like IR commands, which means they might be missed or
ignored.  The rccode operation is included only for completeness.   

Here is an example rccode that displays (or removes) the "Menu"

```
  # RC code for Menu
  - op: rccode
    data: '732E'
```


# Tips

If you don't know how the serial ports are named on the device running Apex, you can launch Apex with the flag "showserialports" and it will output the potential serial ports

IR integration reuqires Apex to be running on a Linux machine

# Discussion?

Want to discuss Apex?  Check out this [thread on AVSForum](https://www.avsforum.com/threads/apex-—-jvc-rs500-600-hdfury-hdr-macro-optimization.3177726/#post-60365429)
