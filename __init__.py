#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2016 Anton Aksola <aakso@iki.fi>                            /
#########################################################################
#  This file is part of SmartHome.py.    http://mknx.github.io/smarthome/
#
#  SmartHome.py is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHome.py is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import time
import urllib.request
import threading
import itertools
from collections import deque
from xml.etree import ElementTree as ET
from struct import pack, unpack

from . import encoders
from . import decoders

logger = logging.getLogger('')

class XBeeGateway:
    ITEM_CONF_NS = "xbgw_"
    LISTEN       = ITEM_CONF_NS + "listen"
    SEND         = ITEM_CONF_NS + "send"
    ENCODER      = ITEM_CONF_NS + "encoder"
    DECODER      = ITEM_CONF_NS + "decoder"
    ENCODER_FUNC = "__" + ITEM_CONF_NS + 'encoder'
    DECODER_FUNC = "__" + ITEM_CONF_NS + 'decoder'

    def __init__(self, 
                 smarthome,
                 url='http://localhost:8080',
                 poll_interval=61,
                 write_interval=5,
                 rci_target='',
                 cmd_sleep=1,
                 refresh_sleep=5):

        self._sh = smarthome
        self._rci_target = rci_target
        self._url = url
        self._cmd_sleep = cmd_sleep
        self._refresh_sleep = refresh_sleep
        self.clsname = self.__class__.__name__
        # Item to channel mappings
        self._item_channel_listen = {}
        self._item_channel_send = {}
        # Channels to refresh before poll
        self._channel_refresh = set()

        ## Init periodic tasks
        self._task_lock = threading.Lock()

        # Discover channels and their current values
        smarthome.scheduler.add("{} poll channels".format(self.clsname),
                               self._poll_channels,
                               cycle=poll_interval,
                               offset=20,
                               prio=5)

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False

    def _rci_xml_command(self):
        return ET.Element('do_command', {'target':self._rci_target})

    def _rci_channel_dump(self):
        cmd = self._rci_xml_command()
        cmd.append(ET.Element('channel_dump'))
        resp = ET.fromstring(self._remote_req(ET.tostring(cmd)))
        r = {}
        for device in resp.findall('.//device'):
            for channel in device.findall('channel'):
                name = '{}.{}'.format(device.attrib['name'],
                                      channel.attrib['name'])
                value = channel.attrib['value']
                type = channel.attrib['type']
                try:
                    if type == 'int' or type == 'long':
                        value = int(value)
                    elif type == 'Boolean':
                        value = value.lower() == 'true'
                except Exception as e:
                    logger.debug("{}: Ignored channel {}, cannot parse value: {}".format(self.clsname, name, e))
                    continue
                r[name] = value
        return r

    def _rci_channel_refresh(self, name):
        cmd = self._rci_xml_command()
        cmd.append(ET.Element('channel_refresh', {'name':name}))
        ET.fromstring(self._remote_req(ET.tostring(cmd)))

    def _rci_channel_set(self, name, value):
        cmd = self._rci_xml_command()
        cmd.append(ET.Element('channel_set', {'name':name, 'value':str(value)}))
        ET.fromstring(self._remote_req(ET.tostring(cmd)))

    def _remote_req(self, xml):
        req = urllib.request.Request(self._url)
        req.add_header('Content-Type', 'text/xml')
        resp = urllib.request.urlopen(req, xml)
        body = resp.read()
        if resp.status != 200:
            logger.debug("{}: Error in HTTP Request, body: {}".format(self.clsname, body))
            raise RuntimeError("non-ok response from the server")
        return body

    def _poll_channels(self):
        skip_channels = set()
        with self._task_lock:
            if self._channel_refresh:
                while self._channel_refresh:
                    channel = self._channel_refresh.pop()
                    self._rci_channel_refresh(channel)
                    logger.debug("{}: Refresh channel {}".format(self.clsname, channel))
                    skip_channels.add(channel)
                time.sleep(self._refresh_sleep)
            for channel, value in self._rci_channel_dump().items():
                if channel in skip_channels:
                    continue
                #logger.debug("{}: Poll channels: channel {} = {}".format(self.clsname, channel, value))
                channel_items = (k for k,v in self._item_channel_listen.items() if v == channel)
                for item in channel_items:
                    self._decode_set(item, value)

    def _decode_set(self, item, value):
        if hasattr(item, self.DECODER_FUNC):
            fn = item[self.DECODER_FUNC]
            value = fn(value, item=item)
        if value is not None:
            item(value, self.clsname)

    def _update_item_channel(self, item):
        r_channel = self._item_channel_listen.get(item)
        w_channel = self._item_channel_send.get(item)
        if not w_channel:
            return

        with self._task_lock:
            item_value = item()
            if hasattr(item, self.ENCODER_FUNC):
                fn = item[self.ENCODER_FUNC]
                item_value = fn(item_value, item=item)

            if not isinstance(item_value, list):
                item_value = [item_value]

            for value in item_value:
                try:
                    logger.debug("{}: Set channel {} -> {}"\
                                 .format(self.clsname, w_channel, value))
                    self._rci_channel_set(w_channel, value)
                    time.sleep(self._cmd_sleep)
                    if r_channel:
                        self._channel_refresh.add(r_channel)
                except Exception as e:
                    logger.error("{}: Exception {} while writing to channel {}"\
                                 .format(self.clsname, e, w_channel))

    def parse_item(self, item):
        if any(a.startswith(self.ITEM_CONF_NS) for a in item.conf.keys()):
            listen = item.conf.get(self.LISTEN)
            send = item.conf.get(self.SEND)
            encoder = item.conf.get(self.ENCODER)
            decoder = item.conf.get(self.DECODER)
            if listen:
                self._item_channel_listen[item] = listen
            if send:
                self._item_channel_send[item] = send
            if encoder:
                try:
                    f = getattr(encoders, encoder)
                    item[self.ENCODER_FUNC] = f
                except AttributeError:
                    logger.error("{}: Cannot find encoder: {}"\
                                 .format(self.clsname, encoder))
            if decoder:
                try:
                    f = getattr(decoders, decoder)
                    item[self.DECODER_FUNC] = f
                except AttributeError:
                    logger.error("{}: Cannot find decoder: {}"\
                                 .format(self.clsname, decoder))

            # Return update callback to smarthome
            return self.update_item
        else:
            return None

    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != self.clsname:
            logger.info("{}: update item: {}".format(self.clsname, item.id()))
            self._update_item_channel(item)

