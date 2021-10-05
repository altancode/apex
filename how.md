# How I Use Apex (October 2, 2021)
I thought it might be useful to share how I used Apex and, in doing so, why Apex exists.

## My Setup
My equipment is a little dated but works very well.   The JVC RS500 projector, for example, continues to give excellent results.

1. JVC RS500 Projector
2. Onkyo TX-NR818 Receiver
3. HDFury Vertex2
4. Apple TV 4K (2nd generation)

## In The Beginning
When I first created Apex, I was using an NVIDIA Sheild.  However, I've recently
replaced it with a 2nd generation Apple TV 4K.

With the Shield, Apex would optimization switching between HDR 1200 and HDR 4000 modes.
As mentioned in the README, one aspect of Apex is that it performs this reliably and does not need "worst case timeouts".

## How it's connected

The audio/video components are connected as follows

```
   AppleTV 4K -(HDMI)-> Vertex 2 -(HDMI)-> Onkyo TX-NR818
                                 -(HDMI)-> JVC RS500
```

Now let's add Apex

```
   Apex -(serial)-> Vertex 2
            -(ip)-> Vertex 2
            -(ip)-> JVC RS500
            -(ip)-> Onkyo TX-NR818
```

## Setup Preconditions
I've previously setup the following, which are used by my Apex workflows

1. I have created HDR 1200 and HDR 4000 custom gammas
1. I have setup Vertex2 to enable JVC macros
1. I have created an EDID that enables LLDV and stored it in the Vertex2
1. I have created a 2nd EDID that enables LLDV but removes 59.96 resolutions.  This is stored in the Vertex2 also
1. My Apex box has an operational IR receiver

## Why Two EDID Tables?
This is a personal preference.

The JVC projectors are known for having horrific delay when switching frame rates or resultions.
With some sources, this leads to a very frustrating experience.   For example, hitting Play may
result in a 15 second delay.  Similarly, pressing Stop (or the content ending) may result in 
another 15 second delay.  This experience is particularly poor when previewing content.

The AppleTV treats different EDID as different displays and remembers the video settings for each.
Taking advantage of this, my full EDID w/LLDV is used for "Movies" where I want the content
displayed at the source frame rate.  When this EDID is active, I've configured Apple TV to 
Match Frame Rate.   My 2nd EDID is used for "Streaming" where I'm willing to watch all content
in 59.96.  For this EDID I have configured AppleTV to not match frame rate (and use 4k 59.96).
When using the Streaming EDID, the JVC never has the frustrating 15+ second delays.

## JVC HDR, LLDV and User Modes
The LLDV EDID I've geneated is consistent with my JVC HDR 1200 gamma table.  I've configured Vertex 2 to
send the command to activate this mode via serial (which is then received and processed robustly
by Apex).  With this setup, when Apple TV enables Dolby Vision, the Vertex 2 will tell Apex to enable
my HDR 1200 mode.   Apex will then robustly place the JVC RS500 into this mode.

## JVC SD, HDR and Other Modes
As an aside, evertyhign is setup for non-LLDV (aka, HDR10 content mastered at ~1200 and ~4000) as
well as SDR modes.

## My Current Apex Profiles
Below are my most commonly used Apex profiles.   These are the profiles to enable Movie mode as well
as to enable Streaming mode.   The are the same with the exception of the EDID selection.

First the Movie Profile

```
  profileAppleTVMovie:
  # Tell Vertex 2 to use the EDID in table 1 (which is my Movie EDID)
  - op: raw
    target: 'hdfury_generic'
    cmd: set
    data: 'edidtableinp0 1'
    requirePowerOn: False

  # Place Vertex 2 into splitter mode and select input 1
  - op: raw
    target: 'hdfury_generic'
    cmd: set
    data: 'insel 1 4'
    requirePowerOn: False

  # Power on my Onkyo TX-NR818
  - op: raw
    target: onkyo_iscp
    cmd: PWR
    data: '01'
    requirePowerOn: False

  # Select the Onkyo's HDMI input that receives audio from the Vertex2
  - op: raw
    target: onkyo_iscp
    cmd: SLI 
    data: '22'
    requirePowerOn: False

  # Set the Onkyo volume to a better default
  - op: raw
    target: onkyo_iscp
    cmd: MVL
    data: '3C'
    requirePowerOn: False

  # Power on the JVC projector
  - op: apex-power
    data: 'on'

  # Tell Apex to "follow" the HDR mode specified by Vertex2 (via serial)
  - op: apex-hdfurymode
    target: 'jvc_pj'
    data: 'follow'

  # Have Apex intelligently select HDMI 1 input on the JVC 
  - op: apex-hdmi
    target: 'jvc_pj'
    data: '1'
```

Now the Streaming Profile

```

  profileAppleTVStreaming:
  # Tell Vertex 2 to use the EDID in table 2 (which is my Streaming EDID)
  - op: raw
    target: 'hdfury_generic'
    cmd: set
    data: 'edidtableinp0 2'
    requirePowerOn: False

  # Place Vertex 2 into splitter mode and select input 1
  - op: raw
    target: 'hdfury_generic'
    cmd: set
    data: 'insel 1 4'
    requirePowerOn: False

  # Power on my Onkyo TX-NR818
  - op: raw
    target: onkyo_iscp
    cmd: PWR
    data: '01'
    requirePowerOn: False

  # Select the Onkyo's HDMI input that receives audio from the Vertex2
  - op: raw
    target: onkyo_iscp
    cmd: SLI
    data: '22'
    requirePowerOn: False

  # Set the Onkyo volume to a better default
  - op: raw
    target: onkyo_iscp
    cmd: MVL
    data: '3C'
    requirePowerOn: False

  # Power on the JVC projector
  - op: apex-power
    data: 'on'

  # Tell Apex to "follow" the HDR mode specified by Vertex2 (via serial)
  - op: apex-hdfurymode
    target: 'jvc_pj'
    data: 'follow'

  # Have Apex intelligently select HDMI 1 input on the JVC 
  - op: apex-hdmi
    target: 'jvc_pj'
    data: '1'
```

