# How I Use Apex (October 2, 2021)
I thought it might be useful to share how I used Apex and, in doing so, why Apex ists.

## My Setup
My equipment is dated but works very well.   The JVC RS500 projector, for example, continues to give excellent results.

1. JVC RS500 Projector
2. Onkyo TX-NR818 Receiver
3. HDFury Vertex2
4. Apple TV 4K (2nd generation)

## In The Beginning
When I first created Apex, I was using an NVIDIA Sheild.  However, I've recently
replaced it with a 2nd generation Apple TV 4K.

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

The JVC projectors are known for having horiffic delay when switching frame rates or resultions.
