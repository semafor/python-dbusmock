'''powerd D-BUS mock template'''

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option) any
# later version.  See http://www.gnu.org/copyleft/lgpl.html for the full text
# of the license.

"""node /com/canonical/powerd {
  interface com.canonical.powerd {
    methods:
      requestSysState(in  s name, in  i state, out s cookie);
      clearSysState(in  s cookie);
      requestWakeup(in  s name, in  t time, out s cookie);
      enableProximityHandling(in  s name);
      disableProximityHandling(in  s name);
      clearWakeup(in  s cookie);
      registerClient(in  s name);
      unregisterClient(in  s name);
      ackStateChange(in  i state);
      userAutobrightnessEnable(in  b enable);
      getBrightnessParams(out (iiiib) params);
      setUserBrightness(in  i brightness);
      listSysRequests(out a(ssi) requestList);
      getSysRequestStats(out a(ssuttt) requestStats);
    signals:
      SysPowerStateChange(i sysState);
      Wakeup();
    properties:
      readonly i brightness = -1;
  };
};
"""
import time as timelib
import dbus
import dbusmock
import threading
import uuid

from dbusmock import MOCK_IFACE


__author__ = 'Jonas G. Drange'
__email__ = 'jonas.drange@canonical.com'
__copyright__ = '(c) 2015 Canonical Ltd.'
__license__ = 'LGPL 3+'

BUS_NAME = 'com.canonical.powerd'
MAIN_IFACE = 'com.canonical.powerd'
MAIN_OBJ = '/com/canonical/powerd'
SYSTEM_BUS = True


class SysPowerStates:
    """States per [1].
    [1] http://bazaar.launchpad.net/
        ~phablet-team/powerd/trunk/view/head:/src/powerd.h
    """
    POWERD_SYS_STATE_SUSPEND = 0,
    POWERD_SYS_STATE_ACTIVE = 1
    POWERD_SYS_STATE_ACTIVE_BLANK_ON_PROXIMITY = 2
    POWERD_NUM_POWER_STATES = 3


def load(mock, parameters):
    global _parameters
    _parameters = parameters

    mock.AddProperties(
        MAIN_IFACE,
        dbus.Dictionary({
            'brightness': _parameters.get('brightness', -1),
        }, signature='sv'))

    mock._state_requests = {}
    mock._wakeup_requests = {}


def wakeup(cookie, time):
    from syslog import syslog
    syslog("powerd: %s requesting wakeup at %d, now is %d." % (
        cookie, time, int(timelib.time()))
    )
    while int(timelib.time()) < time:
        syslog("powerd: %s not ready." % cookie)
        timelib.sleep(1)
    syslog("powerd: %s cleared, calling Wakeup." % cookie)
    obj = dbusmock.get_object(MAIN_OBJ)
    obj.EmitSignal(MAIN_IFACE, 'Wakeup', '', [])


@dbus.service.method(MAIN_IFACE, in_signature='si', out_signature='s')
def requestSysState(self, name, state):
    cookie = str(uuid.uuid4())
    self._state_requests[cookie] = (name, state)
    return cookie


@dbus.service.method(MAIN_IFACE, in_signature='s', out_signature='')
def clearSysState(self, cookie):
    del self._state_requests[cookie]


@dbus.service.method(MAIN_IFACE, in_signature='st', out_signature='s')
def requestWakeup(self, name, time):
    cookie = str(uuid.uuid4())
    self._wakeup_requests[cookie] = (name, time)
    thr = threading.Thread(target=wakeup, args=(cookie, time), kwargs={})
    thr.start()
    return cookie


@dbus.service.method(MAIN_IFACE, in_signature='s', out_signature='')
def enableProximityHandling(self, name):
    pass


@dbus.service.method(MAIN_IFACE, in_signature='s', out_signature='')
def disableProximityHandling(self, name):
    pass


@dbus.service.method(MAIN_IFACE, in_signature='s', out_signature='')
def clearWakeup(self, cookie):
    del self._wakeup_requests[cookie]


@dbus.service.method(MAIN_IFACE, in_signature='s', out_signature='')
def registerClient(self, name):
    pass


@dbus.service.method(MAIN_IFACE, in_signature='s', out_signature='')
def unregisterClient(self, name):
    pass


@dbus.service.method(MAIN_IFACE, in_signature='i', out_signature='')
def ackStateChange(self, state):
    pass


@dbus.service.method(MAIN_IFACE, in_signature='b', out_signature='')
def userAutobrightnessEnable(self, enable):
    pass


@dbus.service.method(MAIN_IFACE, in_signature='', out_signature='(iiiib)')
def getBrightnessParams(self):
    return dbus.Tuple((), signature='(iiiib)')


@dbus.service.method(MAIN_IFACE, in_signature='i', out_signature='')
def setUserBrightness(self, brightness):
    self.SetProperty(self.__dbus_object_path__, MAIN_IFACE, 'brightness',
                     brightness)


@dbus.service.method(MAIN_IFACE, in_signature='', out_signature='a(ssi)')
def listSysRequests(self):
    return dbus.Tuple((), signature='a(ssi)')


@dbus.service.method(MAIN_IFACE, in_signature='', out_signature='a(ssuttt)')
def getSysRequestStats(self):
    return dbus.Tuple((), signature='a(ssuttt)')


@dbus.service.method(MOCK_IFACE,
                     in_signature='sssv', out_signature='')
def SetProperty(self, path, iface, name, value):
    obj = dbusmock.get_object(path)
    obj.Set(iface, name, value)
    obj.EmitSignal(iface, 'PropertiesChanged', 'a{sv}', [{name: value}])
