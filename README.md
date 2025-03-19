# Days Elapsed Tracker

Automatically tracks and displays the number of days since specified on a 4x7 segment display.

## General layout

The code for V1 is extraordinarily simple, and the device connects to any known networks when it boots up, then syncs its time with an NTP server and calculates the elapsed days since whichever date is specified. Time zone is locked to EST/DST and daylight savings is accounted for.

Resulting day count is then displayed on a 3461BS 4x7 segment display. The code is written in micropython and implemented on an ESP32s2 with built in WiFi.

## Wifi Credentials

Credentials must be stored on device in a csv file with the following format:

```
"SSID1", "Password1"
"SSID2", "Password2"
"SSIDX", "PasswordX"
```

This is mainly so that I'm not uploading my wifi credentials to my public github.

## Circuitry

Each digit needs to be individually addressed on the 7seg display, and only one can be addressed at a time due to the segments having common grounds, so this display relies on persistence of vision. 330R current limiting resistors are placed at the terminals of each digit to not blow my ESP32. Rough display wiring layout is shown below.

![image.png](\media\7SegLayout.png)![image.png](\media\7SegCircuitDiagram.png)

The direct pin mappings are detailed a bit more in the code.

## Assembly

Enclosure STLs are included on the github. Currently on V1.1-C, and the final assembly is pictured below.

![image.png](\media\V1.1-C_Full_Enclosure.png)