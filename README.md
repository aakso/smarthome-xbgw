# Digi XBee Gateway Plugin for Smarthome.py

## Description

This plugin allows you to interface with XBGW's RCI XML API to poll channel
values as well as set them.

Information about XBee Gateway:
http://www.digi.com/products/xbee-rf-solutions/gateways/xbee-gateway

## My use case

I started this project to control my Hotspring Sovereign Spa remotely. In fact
the stock solution for the spa in question uses XBGW and Dia's cloud service to
integrate Spa remote controls to their Android application.

Thus most of the code in this project is applicable to Watkins Spa controls.
However, this plugin can be used to control whatever device that is managed by
the XBGW and exposes it settable/gettable values as RCI channels.

## Installation

My XBGW doesn't allow RCI calls to be made remotely so the included
`rci_httpserver.py` can be used as a proxy script. Just copy it to XBGW and
start is as a regular python script. This can be done from the Web UI.

After this configure the plugin. Example: 
```
[xbgw]
class_name = XBeeGateway
class_path = plugins.xbgw
url = http://xbgwhostname:8080
poll_interval = 60
rci_target = watkins
```

## Item configuration

The plugin recognizes `xbgw_listen` and `xbgw_send` to control which channels
are used to poll/set the item value. The format is `<devicename>.<channelname>`
as XBGW can be used to control multiple devices.

Encoder and decoder are references to a function in `encoders.py` and
`decoders.py` that can be used to mangle the value before sending or receiving
it. The provided files contain few functions I used to encode data for Watkins
Spa controller.

Example:
```
[hottub_set_temp]
name = Hot tub set target temperature
type = num
visu_acl = rw
xbgw_listen = eagle.ctrl_head_set_temperature
xbgw_send = eagle.set_temperature
xbgw_decoder = watkins_str_fahrenheit_to_celcius
xbgw_encoder = watkins_set_temp_relative
```

## Credits

If you find this project useful I'd like to hear about it. When this project was
started there were not many projects out there that integrate with Watkins Spa
controllers or XBGW.

* Anton Aksola <aakso@iki.fi>
* Olli Salo <olli.salo@iki.fi>
