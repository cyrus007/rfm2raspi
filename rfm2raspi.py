#!/usr/bin/env python

"""
  All code is released under the GNU Affero General Public License.
  See COPYRIGHT.txt and LICENSE.txt.
  ---------------------------------------------------------------------
  Adapted from rfm2pigateway.py
  By Swapan <swapan@yahoo.com>
"""

"""
TODO : 
"""

import serial
import time
import logging, logging.handlers
import re
import signal
import os

"""class RFM2COSM

Monitors the serial port for data from RFM2Pi and sends data to COSM/pachube.

"""
class RFM2COSM():
    
    def __init__(self, port=None):
        """Setup an RFM2COSM gateway."""
        self.handler = {}

        # Store PID in a file to allow SIGINTability
        with open('PID', 'w') as f:
            f.write(str(os.getpid()))

        # Set signal handler to catch SIGINT and shutdown gracefully
        self._exit = False
        signal.signal(signal.SIGINT, self._sigint_handler)
        
        # Initialize logging
        self.log = logging.getLogger('MyLog')
        logfile = logging.handlers.RotatingFileHandler('./rfm2raspi.log', 'a', 50 * 1024, 1)
        logfile.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        self.log.addHandler(logfile)
        self.log.setLevel(logging.DEBUG)
        
        # Read config data from file
        filename = '/home/pi/.rfm2pi.cfg'
        with open(filename, 'r') as f:
            for line in f:
                params = line.split(',')
                self.handler[int(params[0])] = __import__(params[2].strip()[:-3])

        # Open given port
        if( port ):
            self._ser = open(port, 'r')
        else:
            self._ser = self._open_serial_port('/dev/ttyAMA0')
        if self._ser is None:
            self.log.error("Serial port opening failed. Exiting...")
            raise Exception('Serial port opening failed.')
        
        # Initialize serial RX buffer
        self._serial_rx_buf = ''
        
    def run(self):
        """Launch the gateway.
        
        Monitor the serial port and process data.
        Check ettings on a regular basis.

        """

        # Until asked to stop
        while not self._exit:
            
            # Read serial RX
            self._serial_rx_buf = self._serial_rx_buf + self._ser.readline()
        
            # If full line was read, process
            if ((self._serial_rx_buf != '') and 
                (self._serial_rx_buf[len(self._serial_rx_buf)-1] == '\n')):

                # Remove CR,LF
                self._serial_rx_buf = re.sub('\\r\\n', '', self._serial_rx_buf)

                # Log data
                self.log.info("Serial RX: " + self._serial_rx_buf)
                
                # Get an array out of the space separated string
                received = self._serial_rx_buf.strip().split(' ')
                
                # Empty serial_rx_buf
                self._serial_rx_buf = ''
                
                # If information message, discard
                if ((received[0] == '>') or (received[0] == '->')):
                    continue

                # Else,frame should be of the form 
                # [node val1_lsb val1_msb val2_lsb val2_msb ...]
                # with number of elements odd and at least 3
                elif ((not (len(received) & 1)) or (len(received) < 3)):
                    self.log.warning("Misformed RX frame: " + str(received))
                
                # Else, process frame
                else:
                    try:
                        received = [int(val) for val in received]
                    except Exception:
                        self.log.warning("Misformed RX frame: " + str(received))
                    else:
                        # Get node ID
                        node = int(received[0])
                        if (node > 192):
                            node = node - 192
                        supplyV = received[1] + 256 * received[2]
                        
                        # Recombine transmitted chars into signed int
                        values = []
                        for i in range(3,len(received),2):
                            value = received[i] + 256 * received[i+1]
                            if value > 32768:
                                value -= 65536
                            values.append(value)
                        
                        self.log.debug("Node: " + str(node) + " | Voltage: " + str(supplyV))
                        self.log.debug("Values: " + str(values))
            
                        # Add data to send buffers
                        dataset = list(values) # Make a distinct copy: we don't want to modify data
                        self.handler[node].process(node, dataset, self.log)
            
            # Sleep until next iteration
            time.sleep(1);
         
    def close(self):
        """Close gateway. Do some cleanup before leaving."""
        
        # Close serial port
        self.log.debug("Closing serial port.")
        self._ser.close()

        # Delete PID file
        try:
            os.remove('PID')
        except OSError:
            pass
        
        self.log.info("Exiting...")

    def _sigint_handler(self, signal, frame):
        """Catch SIGINT (Ctrl+C)."""
        
        self.log.debug("SIGINT received.")
        # gateway should exit at the end of current iteration.
        self._exit = True

    def _set_rfm2pi_setting(self, setting, value):
        """Send a configuration parameter to the RFM2Pi through serial port.
        
        setting (string): setting to be sent, can be one of the following:
          baseid, frequency, sgroup
        value (string): value for this setting
        """
        
        self.log.info("Setting RFM2Pi | %s: %s" % (setting, value))
        if setting == 'baseid':
            self._ser.write(value+'i')
        elif setting == 'frequency':
            self._ser.write(value+'b')
        elif setting == 'sgroup':
            self._ser.write(value+'g')
        time.sleep(1);
    
    def _open_serial_port(self, filename):
        """Open serial port."""

        self.log.debug("Opening serial port: " + filename)
        
        try:
            ser = serial.Serial(filename, 9600, timeout = 0)
        except serial.SerialException as e:
            self.log.error(e)
        except Exception:
            import traceback
            self.log.error(
                "Couldn't send to server, Exception: " 
                + traceback.format_exc())
        else:
            return ser


if __name__ == "__main__":

    try:
        gateway = RFM2COSM()
    except Exception as e:
        print(e)
    else:    
        gateway.run()
        gateway.close()

