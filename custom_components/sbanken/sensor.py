"""
Sbanken accounts sensor 

For more details about this platform, please refer to the documentation at
https://github.com/sepodele/home-assistant-sbanken

"""

import asyncio
import logging
import voluptuous as vol

from random import randrange

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_interval
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_SCAN_INTERVAL)

from datetime import datetime, timedelta

REQUIREMENTS = ['oauthlib==3.0.2', 'requests-oauthlib==1.2.0']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'sbanken'

SCAN_INTERVAL = timedelta(minutes=20)

ATTR_AVAILABLE = 'available'
ATTR_BALANCE = 'balance'
ATTR_ACCOUNT_NUMBER = 'account_number'
ATTR_NAME = 'name'
ATTR_ACCOUNT_TYPE = 'account_type'
ATTR_ACCOUNT_LIMIT = 'credit_limit'
ATTR_ACCOUNT_ID = 'account_id'
ATTR_LAST_UPDATE = 'last_update'

ATTR_TRANSACTIONS = 'transactions'
ATTR_PAYMENTS = 'payments'

CONF_CLIENT_ID = 'client_id'
CONF_SECRET = 'secret'
CONF_NUMBER_OF_TRANSACTIONS = 'numberOfTransactions'
CONF_NUMBER_OF_PAYMENTS = 'numberOfPayments'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_SECRET): cv.string,
    vol.Optional(CONF_NUMBER_OF_TRANSACTIONS, default=3): cv.string,
    vol.Optional(CONF_NUMBER_OF_PAYMENTS, default=100): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""

    _LOGGER.info("Setting up Sbanken Sensor Platform.")

    api = SbankenApi(config.get(CONF_CLIENT_ID), config.get(CONF_SECRET), config)
    session = api.create_session()
    accounts = api.get_accounts(session) 
    sensors = [SbankenSensor(account, config, api) for account in accounts] 

    add_devices(sensors, update_before_add=True)
    
    return True
    
    
class SbankenSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, account, config, api):
        """Initialize the sensor."""
        self.config = config
        self.api = api
        self._account = account
        self._transactions = []
        self._payments = []
        self._state = account['available']

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._account['accountNumber']

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._account['name'] + ' (' + self._account['accountNumber'] + ')'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'kr'

    @property
    def should_poll(self):
        """Camera should poll periodically."""
        return True

    @property    
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:cash'

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ACCOUNT_ID: self._account['accountId'], 
            ATTR_AVAILABLE: self._account['available'], 
            ATTR_BALANCE: self._account['balance'], 
            ATTR_ACCOUNT_NUMBER: self._account['accountNumber'], 
            ATTR_NAME: self._account['name'], 
            ATTR_ACCOUNT_TYPE: self._account['accountType'], 
            ATTR_ACCOUNT_LIMIT: self._account['creditLimit'],
            ATTR_LAST_UPDATE: datetime.now().strftime("%d/%m/%Y %H:%M:%S"),              
            ATTR_TRANSACTIONS: self._transactions,     
            ATTR_PAYMENTS: self._payments          
            }

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        session = self.api.create_session()
        account = self.api.get_account(session, self._account['accountId'])
        transactions = self.api.get_transactions(session, self._account["accountId"])
        payments = self.api.get_payments(session, self._account["accountId"]) 
        self._transactions = transactions
        self._payments = payments
        self._account = account
        self._state = account['available']
        _LOGGER.info("Updating Sbanken Sensors.")

class SbankenApi(object):
    """Get the latest data and update the states."""

    def __init__(self, client_id, secret, config):
        """Initialize the data object."""

        self.client_id = client_id
        self.secret = secret
        self.session = self.create_session()
        self.config = config
 
    def create_session(self):

        from requests_oauthlib import OAuth2Session
        from oauthlib.oauth2 import BackendApplicationClient
        import urllib.parse
        
        oauth2_client = BackendApplicationClient(client_id=urllib.parse.quote(self.client_id))
        session = OAuth2Session(client=oauth2_client)
        session.fetch_token(
            token_url='https://auth.sbanken.no/identityserver/connect/token',
            client_id=urllib.parse.quote(self.client_id),
            client_secret=urllib.parse.quote(self.secret)
        )
        return session

    def get_customer_information(self, session):
        response = session.get(
            "https://publicapi.sbanken.no/apibeta/api/v1/Customers/").json()

        if not response["isError"]:
            return response["item"]
        else:
            raise RuntimeError("{} {}".format(response["errorType"], response["errorMessage"]))

    def get_accounts(self, session):
        response = session.get(
            "https://publicapi.sbanken.no/apibeta/api/v1/Accounts/").json()

        if not response["isError"]:
            return response["items"]
        else:
            raise RuntimeError("{} {}".format(response["errorType"], response["errorMessage"]))

    def get_account(self, session, accountId):
        response = session.get(
            "https://publicapi.sbanken.no/apibeta/api/v1/Accounts/{}".format(accountId)).json()

        if not response["isError"]:
            return response['item']
        else:
            raise RuntimeError("{} {}".format(response["errorType"], response["errorMessage"]))

    def get_transactions(self, session, accountId):
        response = session.get(
            "https://publicapi.sbanken.no/apibeta/api/v1/Transactions/" + accountId + '?length=' + self.config.get(CONF_NUMBER_OF_TRANSACTIONS)).json()
        
        if not response["isError"]:
            return response["items"]
        else:
            raise RuntimeError("{} {}".format(response["errorType"], response["errorMessage"]))   
            
    def get_payments(self, session, accountId):
        response = session.get(
            "https://publicapi.sbanken.no/apibeta/api/v1/Payments/" + accountId + '?length=' + self.config.get(CONF_NUMBER_OF_PAYMENTS)).json()
    
        if not response["isError"]:
            return response["items"]
        else:
            raise RuntimeError("{} {}".format(response["errorType"], response["errorMessage"]))  
