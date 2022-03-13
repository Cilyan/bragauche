# Bragauche

This little project lets you drive the [DexArm][] using a controller.

## Software Setup

The project is written in [Python][] and uses [Poetry][] to handle
dependencies, so you will need to install these first. Then,

```sh
poetry install
```

## Customization

Currently, the project is configured for an Xbox controller. If you have a
different game controller, you will most likely need to adapt the code so
that your controller is recognised and the right buttons and axis are used.

You will most likely need to adapt `controller:MainLoop.get_joystick` and
`controller:MainLoop.joystick_state`.

To help you with getting the right button and axis indexes, there is a little
debugging program that you can start with

```
poetry run bragauche --joydbg notused
```

## Running

You need to plug an XBox controller and connect the DexArm. The DexArm needs
to be prepared with the rotary module and the pump.

```shell
poetry run bragauche <port>
```

where `<port>` is the DexArm serial port. This program has only been tested
under Linux yet. On this platform `<port>` should most likely be
`/dev/ttyACM0`. Under Windows, `<port>` should be `COM3` or alike. On Mac, this
should be something like `/dev/tty.usbmodem<something>`.

By default, the controller's left stick is used for X (up/down) and Y
(left/right) control, while the right stick is used for Z (up/down) and rotate
(left/right). Button A is to start suction, B is for release and Y is for
blowing. There is currently no mapping for "stopping" (`M1003`).

[Python]: https://www.python.org/
[DexArm]: https://www.rotrics.com/products/dexarm
[Poetry]: https://python-poetry.org/
