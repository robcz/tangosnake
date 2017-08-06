#!/usr/bin/env python
import urllib2
import json
import logging
from CoinCollection import CoinCollection
from CoinCollection import ValueRecord
from TangoServices import Cache

logger = logging.getLogger("tango")
logger.setLevel(logging.DEBUG)

class CCAPI():
    URL_ROOT = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms='
    URL_FIAT_SUFFIX = '&tsyms=USD'
    valueRecords = []

    def __init__(self, cache):
        self.cache = cache

    def buildURL(self, activeCoins):
        # build coin url params
        coinParams = activeCoins.getParams()
        if len(coinParams) == 0:
            raise ValueError('Unable to make request, no valid active currencies')
        return self.URL_ROOT + coinParams + self.URL_FIAT_SUFFIX

    def requestForCoins(self, activeCoins):
        cacheValid = True
        activeTypes = activeCoins.getActiveCoinTypes()
        self.valueRecords = []
        # grab from cache if younger than one minute from right now
        for coinType in activeTypes:
            logger.debug("Pre-request check for valid cache data on type: " + coinType)
            if self.cache.expired(coinType):
                cacheValid = False
        # if the cache is still valid then we'll load up the value collection from it
        if cacheValid:
            for coinType in activeTypes:
                try:
                    self.valueRecords.append(self.cache.retrieve(coinType))
                except ValueError as verr:
                    cacheValid = False
        if not cacheValid:
            logger.debug("No valid cache, performing API call")
            self.callAPI(activeCoins)
        return self

    def callAPI(self, activeCoins):
        url = self.buildURL(activeCoins)
        # perform call
        logger.debug("Execute request against: " + url)
        jsonResponse = urllib2.urlopen(url).read()
        # decode json
        decodedResponse = json.loads(jsonResponse)
        # cache result
        for k,v in decodedResponse.iteritems():
            coinType = k
            for vfname,vfval in v.iteritems():
                vr = ValueRecord(coinType, vfname, vfval)
                logger.debug("Saving: " + vr.stringify())
                self.valueRecords.append(vr)
                self.cache.stash(coinType,vr)

    def translateResult(self):
        narrative = ""
        # extract currency values, TODO: USD for now -- preference setting for others later
        for vr in self.valueRecords:
            usd = vr.getDisplayFiatValue('USD')
            narrative = narrative + " The current value of " + CoinCollection().inflateName(vr.getCoinType()) + " is " + str(usd) + " US Dollars"
        return narrative

    def getCurrencyValueStatement(self, activeCoins):
        return self.requestForCoins(activeCoins).translateResult()
