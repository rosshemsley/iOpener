iOpener
=======

Emulate Emacs' find-file. With completion, listings and history. A Plugin
written for Sublime Text 3.

Use
---
Tap "super+o" or "cntrl-o" depending on your OS. You wil be greeted
with an input panel that allows you to type in file paths.
Note the following:
- Pressing tab will cause completion to occur.
- Double-tapping tab will allow you to search a current directory.
- Up/down allow you to navigate history.
- Opening a folder will work by opening the folder in a new window.
There are a few caveats for now: the open will not work when no window is open,
for example. Bug fixes are on there way!

Installing
----------
- Step 1:
Installation is easiest using Package Control. For now you need to add
this repositry to the repsitory list. In the Command Pallette, 
type: "Add Repository" enter this git repository and the install as normal.

- Step 2:
Add key sequence to run open command.

Credits
-------
I looked at lots of other people's code to write this, including in particular
SublimeMRU and FuzzyFileNav. Thanks for your inspiration!