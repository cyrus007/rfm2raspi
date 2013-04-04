#!/usr/bin/env python
from datetime import datetime
import eeml
import eeml.datastream
import eeml.unit
from eeml.datastream import CosmError

# COSM variables. The API_KEY and FEED are specific to your COSM account and must be changed 
#API_KEY = '5RNOO3ShYJxYiq2V2sgSRtz3112SAKxFQjNDQmNXc0RScz0g'
#FEED = 68872
API_KEY = 'pqPvaWJ5H9zIwwXBoMgoE8aNGpeSAKxRSmhmZWltWmJOND0g'
FEED = 87632

API_URL = '/v2/feeds/{feednum}.xml' .format(feednum = FEED)

def process( node, values, logger ):
  temp = float(values[0])
  temp = temp / 100
  dht_time = datetime.utcnow()

  #setup environment
  metadata = eeml.Environment(title="RPi Home", feed="https://cosm.com/feeds/87632", creator="Cyrus007")
  #setup location
  location = eeml.Location(lat=33.012775, lon=-97.065071, exposure='indoor', domain='physical', disposition='fixed')

  #open up your cosm feed
  pac = eeml.datastream.Cosm(API_URL, API_KEY, env=metadata, loc=location)

  pac.update([
        eeml.Data(5, temp, unit=eeml.unit.Fahrenheit(), at=dht_time)])  #send fahrenheit data

  try:
  #send data to cosm
    pac.put()
#   print pac.geteeml()
  except CosmError, e:
    logger.error('ERROR: pac.put(): {}'.format(e))
  except StandardError:
    logger.error('ERROR: StandardError')
  except:
    logger.error('ERROR: Unexpected error: %s' % sys.exc_info()[0])
