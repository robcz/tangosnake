#!/usr/bin/env python
import sys
import time
import logging
from CoinCollection import CoinCollection
from CryptoCompare import CCAPI
from TangoServices import Cache

cache = Cache()
logger = logging.getLogger("tango")
logger.setLevel(logging.DEBUG)

def handler(jsonArgs, context):
    args = []
    try:
        coinType = jsonArgs['request']['intent']['slots']['coin']['value']
        # if the coinType is recognized as valid then we don't need to worry about name resolution
        if not CoinCollection().isValid(coinType):
            resolveSlot(jsonArgs, args)
        else:
            args.append(coinType)
        return successResponse(coinType, goFetch(args))
    except (KeyError, ValueError) as ke:
        return errorResponse(ke)

def resolveSlot(jsonArgs, fetchArgs):
    try:
        resolutions = jsonArgs['request']['intent']['slots']['coin']['resolutions']['resolutionsPerAuthority']
        for resolution in resolutions:
            resValues = resolution['values']
            for resValue in resValues:
                coinType = resValue['value']['name']
                logger.debug("Resolved type: " + coinType)
                fetchArgs.append(coinType)
    except KeyError as ke:
        logger.error("Resolution error with key: " + str(ke))
    return fetchArgs

def goFetch(args):
    activeCoins = CoinCollection()
    for arg in args:
        activeCoins.toggleCoin(arg)
    try:
        logger.debug("Fetching for active coin params: " + activeCoins.getParams())
        currencyStatement = CCAPI(cache).getCurrencyValueStatement(activeCoins)
        return currencyStatement
    except ValueError as ve:
        raise ValueError("Error occurred fetching value for requested coin")

# TODO: Build valid response object
def errorResponse(errorValue):
    response = "An error occurred\n" + str(errorValue)
    return response

# TODO: Build valid response object
def successResponse(coinType, narrative):
    narrative = narrative.rstrip()
    response = {}
    response['version'] = "1.0"
    response['response'] = {}
    response['response']['outputSpeech'] = buildOutputSpeech(narrative)
    response['response']['card'] = buildCard(coinType, narrative)
    response['response']['shouldEndSession'] = True
    return response

def buildOutputSpeech(narrative):
    outputSpeech = {}
    outputSpeech['type'] = "PlainText"
    outputSpeech['text'] = narrative
    return outputSpeech

def buildCard(coinType, narrative):
    card = {}
    card['type'] = "Simple"
    card['title'] = "Tango fetched for " + coinType + " on " + time.strftime("%d/%m/%Y") + " at " + time.strftime("%I:%M %p %Z")
    card['text'] = narrative
    return card

if __name__ == '__main__':
    # maybe later we do all by default
    if (len(sys.argv) > 1):
        myhandler = logging.StreamHandler()  # writes to stderr
        myformatter = logging.Formatter(fmt='%(levelname)s: %(message)s')
        myhandler.setFormatter(myformatter)
        logger.addHandler(myhandler)
        sys.argv.pop(0)
        print(goFetch(sys.argv))
