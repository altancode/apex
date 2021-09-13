-!!! THIS IS A WORK IN PROGRESS !!!
-!!! DO NOT USE !!!

# Apex

Apex is a powerful tool to control your JVC projector.   Apex offers several features.

1. Apex optimizes the JVC + HD Fury HDR experience.
2. Apex allows deep control of the JVC using both network connectivity and IR

# What's New?

The latest release supports picture modes from more recent JVC projectors as well as adding an optional timeout for RAW operations.

# Apex HDR Experience Optimization

The JVC RS500/RS600 projector models have the tech specs to support HDR very well (at least for projectors), but JVC provided a truly terrible HDR implementation. Amazing people on AVS have come up with ways to get HDR working on these projectors.  One part of this requires using an HDFury product, such as the Vertex 2, and connecting it via serial/RS232 to the JVC projector.  The HDFury then sends "macro" commands via RS232 which cause the JVC to select appropriate HDR (or non-HDR) picture mode. 

Apex optimizes this step by intelligently working with the JVC projector.  Without Apex, you must select a single default "delay" on the HDFury product.  When the HDFury product sees a content HDR transition, it waits the amount of time specified by this delay, and then sends the "macro".  A delay is often needed because the JVC stops listening to all commands when changing certain modes and this sometimes occurs when HDR content is started or ended.  The JVC may be in the "not listening" state for many seconds, perhaps up to 20.  Because of this, many people set the HDFury delay to 20 seconds.  However, this means that the user must always wait 20 seconds for the correct HDR mode to be selected, even if the JVC is ready to display content immediately or anything faster than 20 seconds.

Apex works intelligently with the JVC and sends the macro command as soon as the JVC is ready to receive the command.   If the JVC is ready after 1 second, the HDR switch occurs after about 1 second.   JVC ready after 5 seconds?  The switch occurs after about 5 seconds.  If it takes a full 20 seconds, the switch will occur at that time.

Apex removes the need to connect a serial cable to the JVC because Apex communicates with the JVC using Internet Protocol.  The HDFury is now connected by serial to the device running Apex.

# Apex Deep Control

Apex allows commands from JVC's "External Control Command Communication Specification" to be performed by network commands or IR keypresses.
Unlike using the projector's IR remote, or an automation solution like Harmony, Apex verifies that commands are actually performed.  With
Apex, for example, you don't need to hard code length (40 second?) delays because the JVC is switching inputs or is powering on.   Apex will
make sure the command is performed when the JVC is paying attention.

Deep control allows the following types of settings to be adjusted

* Lens Memory
* Aperture
* Contrast
* Brightness
* Gamma table
* Mask
* Lamp Power
* Etc.

# Apex Profiles

Everything (almost) in Apex is a profile.   A profile is a named collection of JVC control commands.  A profile can have 1 command or many commands.
Place whatever commands are needed to configure your JVC for your specific situation.  For example, you could create a profile called 
"cinemascope" which activates the appropriate picture mode, lens zoom, lens aperture and mask settings.  You can be confident that all the commands
in your profile will be performed.

In addition to custom profiles, Apex has several "core" profiles that are used with the HDR + HDFury integration.   When the HD Fury devices
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
* Your JVC does not reliably turn on or off and you'd like rock solid behavior?
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

Note: the following instructions assume Apex is running with a HDFury device and a USB serial port.
If you want to run Apex without a USB serial port (and therefore not use any of the HDFury optimizations),
you need to comment out the "hdfury" line in the apex.yaml file.

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
# However, you are more than welcome to change the contents of the profile

  _APEX_PMFilm:
  - op: apex-pm
    data: '00'

  _APEX_PMCinema:
  - op: apex-pm
    data: '01'
```

All profiles follow a standard format.  First there is the profile name.   This is followed by one or more operations ("op") and respective operation
parameters.

By default, Apex will not send profile operations to the JVC when the JVC is powered off.   This is because the JVC protocol is rather basic and does not
allow Apex to know if the JVC just missed a command or is intentionally ignoring it. This intelligent operation removes many situations where the JVC will
likely ignore commands, allowing Apex to avoid retransmission and unwanted timeouts.  The optional parameter "requirePowerOn" can be set to False to change
the default behavior.

The profile operations are described below.

## "apex-pm" operation
This is Apex special sauce state machine that optimizes picture mode selection.  If you want to select a picture mode, you
should use apex-pm instead of alternative methods.   When using apex-pm, a "data" field must exist.  This indicates which picture mode
to activate.   The optional parameter "requirePowerOn" is supported.  See the default apex.yanl file for the mapping of the data
parameter to picture mode names.

```
  _APEX_PMFilm:
  # Activate picture mode Film
  - op: apex-pm
    data: '00'
```

## "apex-hdmi" operation
Special sauce?   Yes.   Using the operation apex-hdmi avoids activating a HDMI input if it's already active.   The data parameter 
is '1' for HDMI 1 and '2' for HDMI2.  The optional parameter "requirePowerOn" is supported.

```
  profileHDMI1:
  # HDMI1
  - op: apex-hdmi
    data: '1'
```

## "apex-power" operation
More Apex special sauce, the apex-power operation not only tells the JVC to turn on or off, but ensures that it does turn on or off.
Using the raw commands you may find the JVC says it turned off but actually does not.   Because of this, it is recommended that
apex-power be used for all power on/off operations.   When using apex-power, a "data" field must exist.   This indicates whether to 
power on or power off the JVC.  The optional parameter "requirePowerOn" is supported.

```
  - op: apex-power 
  # Power On
    data: 'on'
    requirePowerOn: False

  profilePowerOff:
  # Power Off
  - op: apex-power 
    data: 'off'
```

## "apex-delay" operation
This is for use under special circumstances.  The apex-delay operation causes Apex to wait (aka delay) the specified amount of time before
processing the next operation in the profile.  While this can be used however desired, it was added because the JVC responds that it has
completed restoring lens memory before the lens has reached the final spot.

When using apex-delay, a "data" field must exist.   This indicates the number of milliseconds to delay.
The optional parameter "requirePowerOn" is supported.  

```
  # delay 10 seconds
  - op: apex-delay
    data: '10000'
```

## "apex-hdfurymode" operation
The apex-hdfurymode operation tells Apex whether it should "follow" or "ignore" HDR modes specified by an HD Fury device.
When set to "follow", Apex will act upon HD Fury HDR modes and when set to "ignore", Apex will ignore HD Fury HDR modes.
When using apex-hdfurymode, a "data" field must exist.  It must be set to either "follow" or "ignore".   

The optional parameter "requirePowerOn" is supported.  However, the default is set to False (meaning this command is 
process regardless of the JVC power state).

```
  # Apex will use (aka use) the HDR info provided from HD Fury
  - op: apex-hdfurymode
    data: 'follow'
```
```
  # Apex will ignore the HDR info provided from HD Fury
  - op: apex-hdfurymode
    data: 'ignore'
```

## "apex-ongammad" operation
The apex-ongammad operation tells Apex to watch the JVC's gamma table and, should Gamma D be detected,
perform the commands specified in a profile.   The profile is specified in the operation's data
parameter.   "On Gamma D" detection defaults to off and is enabled by performing the apex-ongammad operation
with a profile.

```
  # this example shows enabling the On Gamma D functionality and performing profile "profileTestSelectGammaCustom1" when detected
  - op: apex-ongammad
    data: 'profileTestSelectGammaCustom1'
```

```
  # this example shows disabling the On Gamma D functionality
  - op: apex-ongammad
    data: ''
```

If the apex-ongammad operation os used, it is very important that the specified profile performs
actions that cause the gamma table to change.   If not, Apex will keep noticing Gamma D and keep
performing the operations in the profile over and over.

## "raw" operation
The raw operation mode allows any JVC control command to be executed.   Raw requires a "cmd" field and then either a "data" field or
a numeric field.   Either one can be used, the two options exist to make your life easier.  If numeric is specified, Apex takes the
specified signed integer and converts it into the JVC control format.  Alternatively, you can use the "data" field.  This field allows ASCII
data to be specified. The optional parameter "requirePowerOn" is supported.

The raw operation also supports an optional "timeout" parameter.  This paramter should not be used unless there is a very specific reason.
When not specified, Apex uses the default Apex algorithm to optimize the JVC's behavior.   However, if there's a unique scenario where 
the JVC performs poorly with this default behavior, a timeout (in milliseconds) can be specified.  When the timeout is specified, Apex will stop attempting to have the JVC
perform the specified command after the specified timeout's duration.   Keep in mind that while a short timeout may seem appropriate at first,
the JVC can be unresponsive for 20+ seconds in some conditions.

Here is an example of a raw command with numeric

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

Here is the same example as above but with the (not recommended for cause use) timeout parameter.   The timeout
is set to 5000 ms (or 5 seconds)

```
  # Gamma Custom 2
  - op: raw
    cmd: PMGT
    data: '5'
    timeout: 5000
```

## "rccode" operation
This stands for remote control code.  This operation allows buttons from the remote to be simulated.  Using rccode is
not recommended because the JVC control protocol treats these exactly like IR commands, which means they might be missed or
ignored.  The rccode operation is included only for completeness.  The optional parameter "requirePowerOn" is supported.

Here is an example rccode that displays (or removes) the "Menu"

```
  # RC code for Menu
  - op: rccode
    data: '732E'
```

That that many older documents pertaining to remote control code often include only a single hex value, such as 2E.  In most
cases you can make those work by simply adding 73 to the front (resulting in 732E).  The full 4 character code is supported by 
Apex because it allows remote control codes to operate when the JVC is configured for "Code B" (opposed to "Code A") IR codes.
If you want to send "Code B" commands, replace the 73 with 63.

## Bringing it Together
As stated, profiles can have multiple operations.  Below is an example profile called "profileExample" that combines some of the
operations mentioned above.

```
  profileExample:
    # select film mode
    - op: apex-pm
    data: '00'

  # set the aperture to -10
  - op: raw
    cmd: PMLA
    numeric: -10

  # Press the Menu button
  - op: rccode
    data: '732E'
```

# Network Control
While any application can support the Apex protocol, Apex comes with a very simple tool to send network commands.
This tool is called apexcmd.py.  Apexcmd tells Apex to enable a specific profile.  You can run apexcmd with or
without a configuration file.

By default, apexcmd looks for the configuration file apexcmd.yaml in the current directory.   This file has the values
for Apex Server IP, Apex port IP and the shared secret.   The name and location of this file can be changed by 
using the --configfile parameter.  It looks like the following

```
#
# Example Apex Command config file
#

ip: 192.168.1.123
port: 12345
secret: secret
```

When using the config file, the --profile parameter specifies the profile to execute.   For example:

```
python3 apexcmd.py --profile profileHDMI1
```

You can override any of the fields in the config with the command line options --ip, --port and --secret.   If
you do not want to use a config file at all, you can specify the --noconfigfile.


# IR Key Support
Apex allows a profile to be activated when an IR Key is received.   Currently Apex supports IR key functionality when
running on Linux systems.   The IR functionality of the system must be setup and operational before Apex can know
about IR keypresses.  This setup is beyond the scope of this document (but perhaps I'll add info later).

The mapping from IR key to profile is done with the apex.yaml file.   The field "keymap" is used.   An example is shown below.

```
keymap:
  KEY_F1: 
    profile: profilePowerOn
  KEY_F2: 
    profile: profilePowerOff
  KEY_1: 
    profile: profileHDMI1
  KEY_2: 
    profile: profileHDMI2
```

In the above example, when Apex receives an IR keypress represented as "KEY_F1", it will activate the profile named "profilePowerOn".  When
Apex receives the IR keypress represented as "KEY_1", Apex will activate the profile named "profileHDMI1".

You can map any supported Linux key code to any defined profile.

# Tips

If you don't know how the serial ports are named on the device running Apex, you can launch Apex with the flag "showserialports" and it will output the potential serial ports

# Discussion?

Want to discuss Apex?  Check out this [thread on AVSForum](https://www.avsforum.com/threads/apex-—-jvc-rs500-600-hdfury-hdr-macro-optimization.3177726/#post-60365429)
