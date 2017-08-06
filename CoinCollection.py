#!/usr/bin/env python
import calendar
import time
import json
import logging

logger = logging.getLogger("tango")
logger.setLevel(logging.DEBUG)

class CoinCollection():
    activeCoins = {}

    coinParamValues = {
        'bitcoin': 'BTC',
        'bitcoin cash': 'BCH',
        'ethereum': 'ETH',
        'litecoin': 'LTC',
    }

    def __init__(self):
        self.activeCoins = {
            'bitcoin': False,
            'bitcoin cash': False,
            'ethereum': False,
            'litecoin': False,
        }

    def isValid(self, coinType):
        if coinType in self.coinParamValues:
            return True
        return False

    def toggleCoin(self, coin):
        logger.debug("Toggle request made for: " + coin)
        coin = self.inflateName(coin)
        for k,v in self.activeCoins.iteritems():
            if k == coin:
                self.activeCoins[coin] = not self.activeCoins[coin]

    def activateCoin(self, coin):
        self.activeCoins[coin] = True

    def deactivateCoin(self, coin):
        self.activeCoins[coin] = False

    def getActiveCoins(self):
        return [x for x in self.activeCoins if self.activeCoins[x] == True]

    def getActiveCoinTypes(self):
        types = []
        for coin in self.getActiveCoins():
            types.append(self.coinParamValues[coin])
        return types

    def getParams(self):
        params = ''
        for coin in self.getActiveCoins():
            params = params + self.coinParamValues[coin] + ','
        return params

    def inflateName(self, inName):
        for name, short in self.coinParamValues.iteritems():
            if short == inName:
                return name
            elif name == inName:
                return name
        return "unknown"

class ValueRecord():
    coinType = ''
    fiat = {
        'USD': 0.0,
    }

    def __init__(self, coinType, fiatName, fiatValue):
        self.asof = calendar.timegm(time.gmtime())
        self.coinType = coinType
        self.fiat = {}
        self.fiat[fiatName] = fiatValue


    def getDisplayFiatValue(self,fiatName):
        return str(self.fiat[fiatName])

    def getCoinType(self):
        return self.coinType

    def expired(self):
        current = calendar.timegm(time.gmtime())
        fromCurrent = current - self.asof
        if fromCurrent >= 60:
            return True
        return False

    def stringify(self):
        display =  "As of: " + str(self.asof) + " type: " + self.coinType
        for k,v in self.fiat.iteritems():
            display = display + " fiat type: " + k + " value: " + str(v)
        display = display + " expired: " + str(self.expired())
        return display

    def serialize(self):
        attrs = {
            'coin_type': self.coinType,
            'fiat': self.fiat,
            'asof': self.asof
        }
        return json.dumps(attrs)

    def fromJSON(self, jsonRep):
        attrs = json.loads(jsonRep)
        vr = ValueRecord(attrs['coin_type'], 'USD', attrs['fiat']['USD'])
        vr.asof = attrs['asof']
        vr.fiat = attrs['fiat']
        return vr
