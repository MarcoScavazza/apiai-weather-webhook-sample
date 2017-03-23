#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import time
import locale
import os

from flask import Flask
from flask import request
from flask import make_response

from flask.ext.mail import Mail
from flask.ext.mail import Message


# Flask app should start in global layout
app = Flask(__name__)

app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_TLS = False,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = 'giulio.scavazza2@gmail.com',
    MAIL_PASSWORD = 'lanugine',
))

mail = Mail(app)
msg = Message(
          'Hello',
       sender = 'xxx@xxx.com',
       recipients = ['xxx@xxx.com'])
msg.body = "This is the email body"
msg.html = '<b>HTML</b> body 1234'



@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    print("PARAMETRO ---- " + req.get("result").get("action"))
    if req.get("result").get("action") == "yahooWeatherForecast":
        baseurl = "https://query.yahooapis.com/v1/public/yql?"
        yql_query = makeYqlQuery(req)
        if yql_query is None:
            return {}
        yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
        result = urlopen(yql_url).read()
        data = json.loads(result)
        print(data)
        res = makeWebhookResult(data)
        return res
    if req.get("result").get("action") == "test":
        locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
        oggi = str(time.strftime("%A %d %B %Y"))
        frase="Amicone oggi e' " +oggi
        with app.app_context():
            mail.send(msg)
        return fakeWebhookResult(frase)



def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None
    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u='c'"


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    #celsius = int(condition.get('temp')) - 32) / 1.8
    #speech = "Oggi ad " + location.get('city') + ": " + condition.get('text') + \
    #         ", la temperatura: " + celsius + " " + units.get('temperature')


    speech = "Oggi ad " + location.get('city') + ": " + condition.get('text') + \
    ", la temperatura: " + condition.get('temp') + " gradi"

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


def fakeWebhookResult(frase):


    return {
        "speech": frase,
        "displayText": frase,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')
