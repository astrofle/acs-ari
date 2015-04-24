# **********************************************************************
#
# Copyright (c) 2003-2013 ZeroC, Inc. All rights reserved.
#
# This copy of Ice is licensed to you under the terms described in the
# ICE_LICENSE file included in this distribution.
#
# **********************************************************************
#
# Ice version 3.5.1
#
# <auto-generated>
#
# Generated from file `IceSRTClient.ice'
#
# Warning: do not edit this file.
#
# </auto-generated>
#

import Ice, IcePy

# Start of module SRTClient
_M_SRTClient = Ice.openModule('SRTClient')
__name__ = 'SRTClient'

if '_t_spectrum' not in _M_SRTClient.__dict__:
    _M_SRTClient._t_spectrum = IcePy.defineSequence('::SRTClient::spectrum', (), IcePy._t_float)

if 'stamp' not in _M_SRTClient.__dict__:
    _M_SRTClient.stamp = Ice.createTempClass()
    class stamp(object):
        def __init__(self, name='', timdate='', aznow=0.0, elnow=0.0):
            self.name = name
            self.timdate = timdate
            self.aznow = aznow
            self.elnow = elnow

        def __eq__(self, other):
            if other is None:
                return False
            elif not isinstance(other, _M_SRTClient.stamp):
                return NotImplemented
            else:
                if self.name != other.name:
                    return False
                if self.timdate != other.timdate:
                    return False
                if self.aznow != other.aznow:
                    return False
                if self.elnow != other.elnow:
                    return False
                return True

        def __ne__(self, other):
            return not self.__eq__(other)

        def __str__(self):
            return IcePy.stringify(self, _M_SRTClient._t_stamp)

        __repr__ = __str__

    _M_SRTClient._t_stamp = IcePy.defineStruct('::SRTClient::stamp', stamp, (), (
        ('name', (), IcePy._t_string),
        ('timdate', (), IcePy._t_string),
        ('aznow', (), IcePy._t_float),
        ('elnow', (), IcePy._t_float)
    ))

    _M_SRTClient.stamp = stamp
    del stamp

if 'specs' not in _M_SRTClient.__dict__:
    _M_SRTClient.specs = Ice.createTempClass()
    class specs(object):
        def __init__(self, sampleStamp=Ice._struct_marker, spec=None, avspec=None, avspecc=None, specd=None):
            if sampleStamp is Ice._struct_marker:
                self.sampleStamp = _M_SRTClient.stamp()
            else:
                self.sampleStamp = sampleStamp
            self.spec = spec
            self.avspec = avspec
            self.avspecc = avspecc
            self.specd = specd

        def __eq__(self, other):
            if other is None:
                return False
            elif not isinstance(other, _M_SRTClient.specs):
                return NotImplemented
            else:
                if self.sampleStamp != other.sampleStamp:
                    return False
                if self.spec != other.spec:
                    return False
                if self.avspec != other.avspec:
                    return False
                if self.avspecc != other.avspecc:
                    return False
                if self.specd != other.specd:
                    return False
                return True

        def __ne__(self, other):
            return not self.__eq__(other)

        def __str__(self):
            return IcePy.stringify(self, _M_SRTClient._t_specs)

        __repr__ = __str__

    _M_SRTClient._t_specs = IcePy.defineStruct('::SRTClient::specs', specs, (), (
        ('sampleStamp', (), _M_SRTClient._t_stamp),
        ('spec', (), _M_SRTClient._t_spectrum),
        ('avspec', (), _M_SRTClient._t_spectrum),
        ('avspecc', (), _M_SRTClient._t_spectrum),
        ('specd', (), _M_SRTClient._t_spectrum)
    ))

    _M_SRTClient.specs = specs
    del specs

if '_t_spectrums' not in _M_SRTClient.__dict__:
    _M_SRTClient._t_spectrums = IcePy.defineSequence('::SRTClient::spectrums', (), _M_SRTClient._t_specs)

if 'Client' not in _M_SRTClient.__dict__:
    _M_SRTClient.Client = Ice.createTempClass()
    class Client(Ice.Object):
        def __init__(self):
            if Ice.getType(self) == _M_SRTClient.Client:
                raise RuntimeError('SRTClient.Client is an abstract class')

        def ice_ids(self, current=None):
            return ('::Ice::Object', '::SRTClient::Client')

        def ice_id(self, current=None):
            return '::SRTClient::Client'

        def ice_staticId():
            return '::SRTClient::Client'
        ice_staticId = staticmethod(ice_staticId)

        def message(self, s, current=None):
            pass

        def setup(self, current=None):
            pass

        def trackSource(self, s, current=None):
            pass

        def stopTrack(self, current=None):
            pass

        def __str__(self):
            return IcePy.stringify(self, _M_SRTClient._t_Client)

        __repr__ = __str__

    _M_SRTClient.ClientPrx = Ice.createTempClass()
    class ClientPrx(Ice.ObjectPrx):

        def message(self, s, _ctx=None):
            return _M_SRTClient.Client._op_message.invoke(self, ((s, ), _ctx))

        def begin_message(self, s, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_SRTClient.Client._op_message.begin(self, ((s, ), _response, _ex, _sent, _ctx))

        def end_message(self, _r):
            return _M_SRTClient.Client._op_message.end(self, _r)

        def setup(self, _ctx=None):
            return _M_SRTClient.Client._op_setup.invoke(self, ((), _ctx))

        def begin_setup(self, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_SRTClient.Client._op_setup.begin(self, ((), _response, _ex, _sent, _ctx))

        def end_setup(self, _r):
            return _M_SRTClient.Client._op_setup.end(self, _r)

        def trackSource(self, s, _ctx=None):
            return _M_SRTClient.Client._op_trackSource.invoke(self, ((s, ), _ctx))

        def begin_trackSource(self, s, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_SRTClient.Client._op_trackSource.begin(self, ((s, ), _response, _ex, _sent, _ctx))

        def end_trackSource(self, _r):
            return _M_SRTClient.Client._op_trackSource.end(self, _r)

        def stopTrack(self, _ctx=None):
            return _M_SRTClient.Client._op_stopTrack.invoke(self, ((), _ctx))

        def begin_stopTrack(self, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_SRTClient.Client._op_stopTrack.begin(self, ((), _response, _ex, _sent, _ctx))

        def end_stopTrack(self, _r):
            return _M_SRTClient.Client._op_stopTrack.end(self, _r)

        def checkedCast(proxy, facetOrCtx=None, _ctx=None):
            return _M_SRTClient.ClientPrx.ice_checkedCast(proxy, '::SRTClient::Client', facetOrCtx, _ctx)
        checkedCast = staticmethod(checkedCast)

        def uncheckedCast(proxy, facet=None):
            return _M_SRTClient.ClientPrx.ice_uncheckedCast(proxy, facet)
        uncheckedCast = staticmethod(uncheckedCast)

    _M_SRTClient._t_ClientPrx = IcePy.defineProxy('::SRTClient::Client', ClientPrx)

    _M_SRTClient._t_Client = IcePy.defineClass('::SRTClient::Client', Client, -1, (), True, False, None, (), ())
    Client._ice_type = _M_SRTClient._t_Client

    Client._op_message = IcePy.Operation('message', Ice.OperationMode.Normal, Ice.OperationMode.Normal, False, None, (), (((), IcePy._t_string, False, 0),), (((), IcePy._t_string, False, 0),), None, ())
    Client._op_setup = IcePy.Operation('setup', Ice.OperationMode.Normal, Ice.OperationMode.Normal, False, None, (), (), (((), IcePy._t_string, False, 0),), None, ())
    Client._op_trackSource = IcePy.Operation('trackSource', Ice.OperationMode.Normal, Ice.OperationMode.Normal, False, None, (), (((), IcePy._t_string, False, 0),), (((), _M_SRTClient._t_specs, False, 0),), None, ())
    Client._op_stopTrack = IcePy.Operation('stopTrack', Ice.OperationMode.Normal, Ice.OperationMode.Normal, False, None, (), (), (((), IcePy._t_string, False, 0),), None, ())

    _M_SRTClient.Client = Client
    del Client

    _M_SRTClient.ClientPrx = ClientPrx
    del ClientPrx

# End of module SRTClient
