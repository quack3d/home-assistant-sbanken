# Sbanken Sensor Platform for Home Assistant

This sensor platform uses the open API of the norwegian bank Sbanken. 

Every account the customer has in the bank is created as sensor, and updated every 20 minutes. The last transactions will also be shown.

## Installation

To get started download
```
/custom_components/sbanken/__init__.py
/custom_components/sbanken/sensor.py
```
into
```
<config directory>/custom_components/sbanken/
```

Restart your Home Assistant instance to load the component.

## Configuration

1. Start by signing up for the [Sbanken API program](https://sbanken.no/bruke/utviklerportalen/). This is free and the only requirement is that you are over 18.
2. Create an app in the developer portal and select APIBeta as the scope. Store your Client ID somewhere and create a new password (secret).
3. Configure the sensor in Home Assistant.

```yaml
sensor:
    - platform: sbanken
      client_id: yourClientId
      secret: yourSecret
      numberOfTransactions: 5
```

Customer_id (national identity number) is no longer needed.

numberOfTransactions is optional (default is 3).
Update interval can be changed with scan_interval and seconds like this to update every 30 minutes:
```yaml
      scan_interval: 1800
```

For a list of transactions in Lovelace the markdown card can be used with a template like this:
```
{%- for transaction in state_attr('sensor.nameofaccount_21212121212', 'transactions') or [] %}
  {{ transaction.accountingDate[:10] }} | {{ transaction.amount }} kr | {% if (transaction.isReservation == True) %} Reservert: {{ transaction.text[:30] }}  {% else %} {{ transaction.text[:40] }} {% endif %} 
{%- endfor %}
```
The ```[:10]``` shows the first 10 chars of date and ```[:40]``` the first 40 chars of transaction text. 'Reservert:' is added to the text when isReservation == True just like it is displayed on Sbanken.no.


That's it! You can now use your brand new Sbanken sensor.

