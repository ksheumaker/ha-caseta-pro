"""
Platform for Caseta lights.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/light.caseta/
"""
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_TRANSITION, SUPPORT_BRIGHTNESS, SUPPORT_TRANSITION, Light)
from homeassistant.const import (CONF_NAME, CONF_ID, CONF_DEVICES, CONF_HOST, CONF_TYPE)
import homeassistant.helpers.config_validation as cv

from custom_components import caseta

import voluptuous as vol
import asyncio
import logging

DEFAULT_TYPE = "dimmer"

_LOGGER = logging.getLogger(__name__)

class CasetaData:
    def __init__(self, caseta):
        self._caseta = caseta
        self._devices = []

    @property
    def devices(self):
        return self._devices

    @property
    def caseta(self):
        return self._caseta

    def setDevices(self, devices):
        self._devices = devices

    @asyncio.coroutine
    def readOutput(self, mode, integration, action, value):
        # find integration in devices
        if mode == caseta.Caseta.OUTPUT:
            _LOGGER.debug("Got light caseta value: %s %d %d %f", mode, integration, action, value)
            for device in self._devices:
                if device.integration == integration:
                    if action == caseta.Caseta.Action.SET:
                        _LOGGER.info("Found light device, updating value")
                        device._update_state(value)
                        yield from device.async_update_ha_state()
                        break

def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Setup the platform."""
    if discovery_info == None:
        return
    bridge = caseta.Caseta(discovery_info[CONF_HOST])
    yield from bridge.open()

    data = CasetaData(bridge)
    devices = [CasetaLight(light, data) for light in discovery_info[CONF_DEVICES]]
    data.setDevices(devices)

    for device in devices:
        yield from device.query()

    async_add_devices(devices)

    bridge.register(data.readOutput)
    bridge.start(hass)

    return True

class CasetaLight(Light):
    """Representation of a Caseta Light."""

    def __init__(self, light, data):
        """Initialize a Caseta Light."""
        self._data = data
        self._name = light["name"]
        self._integration = int(light["id"])
        self._is_dimmer = light["type"] == "dimmer"
        self._is_on = False
        self._brightness = 0

    @asyncio.coroutine
    def query(self):
        yield from self._data.caseta.query(caseta.Caseta.OUTPUT, self._integration, caseta.Caseta.Action.SET)

    @property
    def integration(self):
        return self._integration

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Brightness of the light (an integer in the range 1-255)."""
        return (self._brightness / 100) * 255

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._is_on

    @property
    def supported_features(self):
        """Flag supported features."""
        return (SUPPORT_BRIGHTNESS | SUPPORT_TRANSITION) if self._is_dimmer else 0

    def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        value = 100
        transition = None
        if self._is_dimmer:
            if ATTR_BRIGHTNESS in kwargs:
                value = (kwargs[ATTR_BRIGHTNESS] / 255) * 100
            if ATTR_TRANSITION in kwargs:
                transition = ":" + str(kwargs[ATTR_TRANSITION])
        _LOGGER.debug("Writing caseta value: %d %d %d %s", self._integration, caseta.Caseta.Action.SET, value, str(transition))
        yield from self._data.caseta.write(caseta.Caseta.OUTPUT, self._integration, caseta.Caseta.Action.SET, value, transition)

    def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        transition = None
        if self._is_dimmer:
            if ATTR_TRANSITION in kwargs:
                transition = ":" + str(kwargs[ATTR_TRANSITION])
        _LOGGER.debug("Writing caseta value: %d %d off %s", self._integration, caseta.Caseta.Action.SET, str(transition))
        yield from self._data.caseta.write(caseta.Caseta.OUTPUT, self._integration, caseta.Caseta.Action.SET, 0, transition)

    def _update_state(self, brightness):
        """Update brightness value."""
        if self._is_dimmer:
            self._brightness = brightness
        self._is_on = brightness > 0
