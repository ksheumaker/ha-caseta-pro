# Home-assistant caseta pro support

This re-packages the caseta code from this repo: https://github.com/jhanssen/home-assistant/tree/caseta-0.40 and makes it work in a custom_components directory

## Install

Copy the directory and files in this repo into your home assistant config/custom_components directory

## Configure

```
caseta:
  bridges:
    - host: XXX.XXX.XXX.XXX
      devices:
        - id: 2
          type: dimmer
        - id: 3
          type: switch
        - id: 4
          type: remote
```
