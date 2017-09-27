"""
Configuration details for the pytrack based GPS logger/tracker
@author Philip Basford P.J.Basford@soton.ac.uk
"""
APP_KEY = "C114885A2E6195E12E312A1C6918149C" #Application key from the things network
APP_EUI = "70B3D57ED00073A0"                 #The EUI for the app
JOIN_TIMEOUT = 0                             #passed to the LoRaWAN join function
GPS_TIMEOUT = 30                             #How long to wait for a GPS reading per attempt
POST_MESSAGE_SLEEP = 30 #How long to wait between messages - affects GPS sample rate when connected
GPS_READ_INTERVAL = 10  #How often to read the GPS if not on the LoRaWAN network
