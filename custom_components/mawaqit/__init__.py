"""The mawaqit_prayer_times component."""
from datetime import timedelta
import logging
import os
import json
import sys
from datetime import datetime
#from mawaqit_times_calculator import MawaqitClient, exceptions
from .mawaqit import MawaqitClient, BadCredentialsException

from requests.exceptions import ConnectionError as ConnError
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_point_in_time
import homeassistant.util.dt as dt_util
from homeassistant.helpers import aiohttp_client


from .const import (
    API,
    CONF_CALC_METHOD,
    DATA_UPDATED,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    USERNAME,
    PASSWORD,
)

from .mosq_list import (
    CALC_METHODS,
)

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_TOKEN


_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {
            DOMAIN: {
                vol.Optional(CONF_CALC_METHOD, default=DEFAULT_CALC_METHOD): vol.In(
                    CALC_METHODS
                ),
            }
        },
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Import the Mawaqit Prayer component from config."""
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )

    return True


async def async_setup_entry(hass, config_entry):
    """Set up the Mawaqit Prayer Component."""
    
    

    client = MawaqitPrayerClient(hass, config_entry)

    if not await client.async_setup():
        return False

    hass.data.setdefault(DOMAIN, client)

    return True




async def async_unload_entry(hass, config_entry):
    """Unload Mawaqit Prayer entry from config_entry."""
    if hass.data[DOMAIN].event_unsub:
        hass.data[DOMAIN].event_unsub()
    hass.data.pop(DOMAIN)
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


class MawaqitPrayerClient:
    """Mawaqit Prayer Client Object."""

    def __init__(self, hass, config_entry):
        """Initialize the Mawaqit Prayer client."""
        self.hass = hass
        self.config_entry = config_entry
        self.prayer_times_info = {}
        self.available = True
        self.event_unsub = None



    @property
    def calc_method(self):
        """Return the calculation method."""
        return self.config_entry.options[CONF_CALC_METHOD]

    def get_new_prayer_times(self):
        """Fetch prayer times for today."""
        mawaqit_login = self.config_entry.data.get("username")
        mawaqit_password = self.config_entry.data.get("password")
        mawaqit_latitude = self.config_entry.data.get("latitude") # self.hass.config.latitude
        mawaqit_longitude = self.config_entry.data.get("longitude") #self.hass.config.longitude

        mosquee = self.config_entry.options.get("calculation_method")





        current_dir = os.path.dirname(os.path.realpath(__file__))

       

        name_servers=[]
        uuid_servers=[]
        CALC_METHODS=[]
        with open('{}/data/all_mosquee_NN.txt'.format(current_dir), "r") as f:
          distros_dict = json.load(f)
        for distro in distros_dict:
          name_servers.extend([distro["label"]])
          uuid_servers.extend([distro["uuid"]])
          CALC_METHODS.extend([distro["label"]])



 
        if mosquee=="nearest" or mosquee=="no mosque in neighborhood" :
            indice = 0
        else:
            indice = name_servers.index(mosquee)
        mosque_id = uuid_servers[indice]


        #update my_mosque file whenever the user changes it in the option
        f = open('{dir}/data/all_mosquee_NN.txt'.format(dir=current_dir ))
        data = json.load(f)
        text_file = open('{}/data/my_mosquee_NN.txt'.format(current_dir), "w")
        json.dump(data[indice], text_file)
        text_file.close()
        
        #readiding prayer times 
        f = open('{dir}/data/pray_time_{name}.txt'.format(dir=current_dir, name=mosque_id ))
        data = json.load(f)
        calendar = data["calendar"]
        today = datetime.today()
        index_month = month = today.month -1
        month_times = calendar[index_month]
        index_day = today.day
        day_times = month_times[str(index_day)]
        salat_name = ["Fajr", "Shurouq", "Dhuhr", "Asr", "Maghrib", "Isha" ]
        res = {salat_name[i]: day_times[i] for i in range(len(salat_name))}
        res['Midnight']=(datetime.strptime(day_times[5], '%H:%M') + timedelta(minutes=1)).strftime("%H:%M") #1 minutes after isha to update 
        # if call of the integration is done after isha time, provide d+1 data
        maintenant  = today.time().strftime("%H:%M")
        if datetime.strptime(day_times[5], '%H:%M') < datetime.strptime(maintenant, '%H:%M'):
            index_day = today.day + 1
            day_times = month_times[str(index_day)]
            res = {salat_name[i]: day_times[i] for i in range(len(salat_name))}
            res['Midnight']=(datetime.strptime(day_times[5], '%H:%M') + timedelta(minutes=1)).strftime("%H:%M") #1 minutes after isha to update 
        # complete the dic with mosque detail
        res['Mosque_name']=data["label"]
        res['Mosque_address']=data["localisation"]
        res['Mosque_site']=data["url"]    
        res['Mosque_image']=data["image"]

        #Iqama timing
        iqamaCalendar = data["iqamaCalendar"]
        iqama= iqamaCalendar[index_month][str(index_day)]
        iqama=[int(s.replace("+", "")) for s in iqama]
        salat=[datetime.strptime(s, '%H:%M') for s in day_times]
        del salat[1] #no iqama for shurouq
        iqama_list = []
        for (item1, item2) in zip(salat, iqama):
            iqama_list.append((item1+ timedelta(minutes=item2)).strftime("%H:%M"))             
        iqama_name = ["Fajr_Iqama", "Dhuhr_Iqama", "Asr_Iqama", "Maghrib_Iqama", "Isha_Iqama" ]
        res1 = {iqama_name[i]: iqama_list[i] for i in range(len(iqama_name))}
        res2 = {**res, **res1}
        return res2

        

    



    async def async_schedule_future_update(self):
        """Schedule future update for sensors.

        Midnight is a calculated time.  The specifics of the calculation
        depends on the method of the prayer time calculation.  This calculated
        midnight is the time at which the time to pray the Isha prayers have
        expired.

        Calculated Midnight: The Mawaqit midnight.
        Traditional Midnight: Isha time + 1 minute

        Update logic for prayer times:

        If the Calculated Midnight is before the traditional midnight then wait
        until the traditional midnight to run the update.  This way the day
        will have changed over and we don't need to do any fancy calculations.

        If the Calculated Midnight is after the traditional midnight, then wait
        until after the calculated Midnight.  We don't want to update the prayer
        times too early or else the timings might be incorrect.

        Example:
        calculated midnight = 11:23PM (before traditional midnight)
        Update time: 12:00AM

        calculated midnight = 1:35AM (after traditional midnight)
        update time: 1:36AM.

        """
        _LOGGER.debug("Scheduling next update for Mawaqit prayer times")

        now = dt_util.utcnow()

        midnight_dt = self.prayer_times_info["Midnight"]

        if now > dt_util.as_utc(midnight_dt):
            next_update_at = midnight_dt + timedelta(days=0, minutes=1)
            _LOGGER.debug(
                "Midnight is after day the changes so schedule update for after Midnight the next day"
            )
        else:
            _LOGGER.debug(
                "Midnight is before the day changes so schedule update for the next start of day"
            )
            next_update_at = dt_util.start_of_local_day(now + timedelta(days=1))

        _LOGGER.info("Next update scheduled for: %s", next_update_at)

        self.event_unsub = async_track_point_in_time(
            self.hass, self.async_update, next_update_at
        )

    async def async_update(self, *_):
        """Update sensors with new prayer times."""
        try:
            prayer_times = await self.hass.async_add_executor_job(
                self.get_new_prayer_times
            )
            self.available = True
        except (BadCredentialsException, ConnError):
            self.available = False
            _LOGGER.debug("Error retrieving prayer times")
            async_call_later(self.hass, 60, self.async_update)
            return

        for prayer, time in prayer_times.items():
            self.prayer_times_info[prayer] = dt_util.parse_datetime(
                f"{dt_util.now().date()} {time}"
            )
        await self.async_schedule_future_update()

        _LOGGER.debug("New prayer times retrieved. Updating sensors")
        async_dispatcher_send(self.hass, DATA_UPDATED)

    async def async_setup(self):
        """Set up the Mawaqit prayer client."""
        await self.async_add_options()

        try:
            await self.hass.async_add_executor_job(self.get_new_prayer_times)
        except (BadCredentialsException, ConnError) as err:
            raise ConfigEntryNotReady from err


        await self.async_update()
        self.config_entry.add_update_listener(self.async_options_updated)

        self.hass.config_entries.async_setup_platforms(self.config_entry, PLATFORMS)

        return True

    async def async_add_options(self):
        """Add options for entry."""
        if not self.config_entry.options:
            data = dict(self.config_entry.data)
            calc_method = data.pop(CONF_CALC_METHOD, DEFAULT_CALC_METHOD)

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=data, options={CONF_CALC_METHOD: calc_method}
            )

    @staticmethod
    async def async_options_updated(hass, entry):
        """Triggered by config entry options updates."""
        if hass.data[DOMAIN].event_unsub:
            hass.data[DOMAIN].event_unsub()
        await hass.data[DOMAIN].async_update()
