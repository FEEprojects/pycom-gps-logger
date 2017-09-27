# pycom-gps-logger

Basic code to use the [pytrack](https://pycom.io/product/pytrack/) board and a [LoPy](https://pycom.io/product/lopy/) (will potentially also work with the [Fipy](https://pycom.io/product/fipy/)).  If a µSD card is present it will also log co-ordinates to file.

## Device Debug Information
Some output is printed to the console otherwise the RGB LED is used to show various states

| Colour | Type | When | Meaning | 
|--------|------|------|---------|
| Yellow | Flash| Boot | SD card Mounted|
| Red    | Steady| Anytime | No GPS Lock|
| Blue   | Flash | Anytime | Search for LoRaWAN|
| Blue   | Steady | Anytime | Joined LoRaWAN network|
| Yellow | Flash | Anytime | Written to file|
| Green  | Flash | Anytime | Sent LoRaWAN message | 
| Red |Double Flash | Anytime | Write to SD card failed | 

Multiple LEDs can be lit at the same time so Purple means on LoRaWAN network but no GPS.

## Client
Utilities to recieve MQTT messages and display / record into mongo database for later analysis.
