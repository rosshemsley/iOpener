iOpener
=======

A Sublime Text 2/3 package to make finding and opening files less painful.
Keep your hands on the keyboard with smart auto completion, history, and directory listings.

Usage
-----
Use `cmd + o` or `cntl + o` as usual (or choose `Find File` in the command pallete.)

- Pressing tab will cause smart completion to occur (hint: `f1` can complete to `filename1`!)

- Double-pressing tab will give you the directory listing

- Up/down allow you to navigate previously entered paths

- Opening a path that doesn't exist will create a new file or directory

Certain paths are available with shortcuts

- Press `ctrl + h` to auto-fill your home directory

- Press `ctrl + f` to auto-fill the folder of the current file

- Press `ctrl + p` to auto-fill and cycle through the current project folders

- Press `ctrl + u` to auto-fill and cycle through user-defined folders in settings

- Press `ctrl + a` to cycle through all of these, based on the order you specify in settings

- Use `ctrl + up` and `ctrl + down` to cycle through the folder lists

![demo](https://raw.github.com/rosshemsley/iOpener/screenshots/demo.gif)

NB
--
- This plugin will take over your default 'open file' shortcut. To
  use your system default, use `cmd + shift + o` or `ctrl + shift + o`

- The open panel will not show unless a window is open. You will need to use
  `cntl + n` or `cmd + n` to open a new window first


Installing
----------
Installation is easiest using Package Control. In the Command Pallette, select
"Install Package" and then select "iOpener".


Bugs
----
Bugs can be reported on GitHub, https://github.com/rosshemsley/iOpener.
