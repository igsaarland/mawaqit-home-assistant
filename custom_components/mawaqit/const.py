"""Constants for the Islamic Prayer component."""
DOMAIN = "mawaqit"
NAME = "Mawaqit Prayer Times"
PRAYER_TIMES_ICON = "mdi:calendar-clock"

SENSOR_TYPES = {
    "Fajr": "Adhan",
    "Shurouq": "Time",
    "Sunrise": "Time",
    "Dhuhr": "Adhan",
    "Asr": "Adhan",
    "Maghrib": "Adhan",
    "Isha": "Adhan",
    "next_mawaqit": "time",
    "Fajr Iqama": "",  
    "Dhuhr Iqama": "",   
    "Asr Iqama": "",    
    "Maghrib Iqama": "",  
    "Isha Iqama": "",
    "Next Salat Time": "",
    "Next Salat Name": "",
    "Next Salat Preparation": "",
    "Mosque_label": "",
    "Mosque_localisation": "",
    "Mosque_url": "",
    "Mosque_image": "",
    "Jumua": "",

    "20 min before Fajr": "",
    "20 min before Dhuhr": "",
    "20 min before Asr": "",
    "20 min before Maghrib": "",
    "20 min before Ishaa": "",



    "20 min after Ishaa": "",
    "20 min before Jumua": "",
    "60 min after Jumua": "",
}


        
CONF_CALC_METHOD = "calculation_method"

CALC_METHODS = ["nearest", "farest"]
DEFAULT_CALC_METHOD = "nearest"

DATA_UPDATED = "Mawaqit_prayer_data_updated"

CONF_SERVER = "server"


USERNAME = "user"

PASSWORD = "password"

API = "api"
CONF_UUID ="uuid"
