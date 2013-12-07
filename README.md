iOpener
=======

A Sublime Text 3 package to make locating and opening files much faster.
Behaviour mostly emulates emacs' find-file. With auto-completion, directory
listings and history. 

Use
---
Tap "super+o" or "cntl-o" as usual (or use the Command Pallete, and select the
command "Find File"). You will be greeted with an input panel that allows you to
type in file paths. Note the following:
- Pressing tab will cause completion to occur.
- Double-tapping tab will allow you to search a current directory.
- Up/down allow you to navigate history.
- Opening a folder will work by opening the folder in a new window. 
- Attempting to open a path that doesn't exist will give a message asking
  whether or not to create the path. 

Note
----
- This plugin will take over your default 'open file' shortcut. If you want to
  use your system file-open dialog, use 'super+shift+o' or 'ctrl+shift+o'
  depending on your OS.
- The open panel will not show when no window is open. You will need to use
  "cntl+n" or "super+n" to open a new window first.


Installing
----------
Installation is easiest using Package Control. For now you need to add
this repositry to the repsitory list. In the Command Pallette, 
type: "Add Repository" enter this git repository and then install as normal.

Credits
-------
I looked at lots of other people's code to write this, including in particular
SublimeMRU and FuzzyFileNav. Thanks for your inspiration!