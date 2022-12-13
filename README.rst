========================================================
larry-rgb: A larry plugin to change your computer's RGBs
========================================================

.. image:: https://img.youtube.com/vi/PmF4ihCTQks/maxresdefault.jpg
    :alt: larry-rgb demo
    :target: https://www.youtube.com/watch?v=PmF4ihCTQks

Tap on the above image for a video demonstration.

larry-rgb is a plugin for larry that pics colors from your (background) image
and smoothly transitions your LEDs from color to color.

Usage
=====

Make sure you have machine running `OpenRGB <https://openrgb.org>`_.  This
will typically be on the same machine that you'll be running larry on.

1. Install `larry <https://github.com/enku/larry>`_.

Install ``larry-rgb``::

    pip install git+https://github.com/enku/larry-rgb

2. Add ``larry_rgb`` to your list of larry plugins, e.g.::

    # ~/.config/larry.cfg

    [larry]
    ...
    plugins = gnome_shell vim larry_rgb

   In addition you can add configuration for the plugin::

    [plugins:larry_rgb]
    # input is the only required configuration. Normally this will be the same as
    # your larry `input` (or `output`) file
    input = ~/Pictures/larry

    # address[:port] of OpenRGB server
    address = 127.0.0.1:6742

    # How many steps in the transition from color to color
    gradient_steps = 20

    # Maxiumum number of colors to get from the input image
    max_palette_size = 10

    # Measure of processing used to get the best palette colors. 1 is the
    # best/slowest.  Higher numbers are faster but less accurate
    quality = 10

    # Time (in seconds) between color changes when fading
    interval = 0.05

    # Time (in seconds) to pause after fading from one color to the next
    pause_after_fade = 0.0

3. (Re)start larry and enjoy!
