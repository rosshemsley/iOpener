#------------------------------------------------------------------------------#
# A plugin to make opening files in Sublime Text 3 a little bit less painfull.
# Lisenced under GPL V2.
#
# Written by Ross Hemsley, 2013.
#------------------------------------------------------------------------------#
import sublime, sublime_plugin, time
from os.path import isdir, isfile, expanduser, split, relpath, join, commonprefix, normpath, isabs
from os      import listdir, sep, makedirs

# Locations of settings files.
HISTORY_FILE     = 'i_opener_history.sublime-settings'
SETTINGS_FILE    = 'i_opener.sublime-settings'

#------------------------------------------------------------------------------#

def load_settings():
    # We set these globals.
    global USE_PROJECT_DIR
    global HISTORY_ENTRIES
    global CASE_SENSITIVE

    settings = sublime.load_settings(SETTINGS_FILE)

    USE_PROJECT_DIR = settings.get('use_project_dir')
    CASE_SENSITIVE  = settings.get('case_sensitive')
    HISTORY_ENTRIES = settings.get('history_entries')

#------------------------------------------------------------------------------#
# Function to find and return longest possile completion for a path p from a
# list of candidates l. Returns new_path, status, completed.

def get_completion(path):
    # Find filename and directory.
    directory, filename = split(path)

    # Dir doesn't exist
    if not isdir(expanduser(directory)):
        status    = "No match"  
        completed = False
        return path, status, completed

    # Get all matching files relating to this path.
    f_list = listdir(expanduser(directory))
    
    matches  = []

    # Case sensitivity test. 
    if CASE_SENSITIVE:        
        matches = [ f for f in f_list if f.startswith(filename) ]
    else:
        matches = [ f for f in f_list if f.lower().startswith(filename.lower())]

    ## Handle filename completion. ##

    # If this match is not unique.
    if len(matches) >  1:
        # We can do this more efficiently later.
        # Get the longest prefix, ignoring case.
        prefix_length = len( commonprefix([ s.lower() for s in matches ]) )        
        new_filename  = filename + matches[0][len(filename):prefix_length] 
        status        = "Complete, but not unique"
        completed     = False
    elif len(matches) == 1:  
        new_filename  = matches[0]
        # If we completed a directory
        if isdir(expanduser(join(directory, new_filename))):
            new_filename += sep
        status        = None
        completed     = True        
    else:
        new_filename  = filename
        status        = "No match"
        completed     = False

    return join(directory, new_filename), status, completed
    
#------------------------------------------------------------------------------#
# Try to give a sensible estimate for 'current directory'.
# If there is a single folder open, we return that. 
# Else, if there is an active file, return its path. 
# If all else fails, return the home directory.

def get_current_path():
    home = expanduser("~")
    view = sublime.active_window().active_view()
    data = sublime.active_window().project_data()
    here = None

    if USE_PROJECT_DIR and data and "folders" in data and len(data["folders"]) == 1:
        specified_path = data["folders"][0]["path"]
        if isabs(specified_path):
            here = specified_path+sep
        else:
            project_file_name = sublime.active_window().project_file_name()
            project_file_dir = split(project_file_name)[0]
            here = normpath(join(project_file_dir, specified_path))+sep

    elif view != None and view.file_name() != None:        
        here = split(view.file_name())[0]
        if here != sep: here += sep
    else:
        here = "~" + sep

    # Return path relative to home if applicable.
    if len(commonprefix([home, here])) > 1:
        relative_path = relpath(here,home)
        if len(relative_path) > 1:
            return join("~", relpath(here,home)) + sep
        else:
            return "~" + sep
    else:
        return here

#------------------------------------------------------------------------------#
# This class encapsulates the behaviours relating to the file open panel
# used by the plugin. We create an instance when the panel is open, and destroy
# it when the panel is closed.
#------------------------------------------------------------------------------#

class Path_input():
    
    #----------------------------------------------------------------------#
    # Class initialisation.
    
    def __init__(self):
        # If the user presses tab, and nothing happens, remember it.
        # If they press tab again, we show them a list of files.
        self.last_completion_failed = False
        self.path_cache             = None
        active_window               = sublime.active_window()
        path                        = get_current_path()

        # We only reload the history each time the input window is opened.
        self.history_cache = self.get_history()[0]
        
        # Store default at end of history cache and 'select' it.
        self.history_cache.append(path)        
        self.history_index = len(self.history_cache)-1

        self.view          = active_window.show_input_panel(
            "Find file: ", 
            path, 
            self.open_file, 
            self.update, 
            self.cancel
        )

    #----------------------------------------------------------------------#
    # If the user updates the input, reset the 'failed completion' flag.

    def update(self,text):
        self.last_completion_failed = False    

    #----------------------------------------------------------------------#

    def goto_prev_history(self):
        # Temporarily store any changes in cache, as bash does.
        self.history_cache[self.history_index] = self.get_text()
        self.history_index -= 1
        if self.history_index < 0:
            sublime.status_message("Reached start of history")
            self.history_index = 0
        self.set_text( self.history_cache [ self.history_index] )

    #----------------------------------------------------------------------#

    def goto_next_history(self):
        # Temporarily store any changes in cache, as bash does.
        self.history_cache[self.history_index] = self.get_text()
        self.history_index += 1
        if self.history_index == len(self.history_cache):
            sublime.status_message("Reached end of history")
            self.history_index = len(self.history_cache)-1
        self.set_text( self.history_cache [ self.history_index] )

    #----------------------------------------------------------------------#

    def add_to_history(self,path):        
        file_history, history_settings = self.get_history()

        # Trim the history to the correct length and add latest entry.        
        if HISTORY_ENTRIES > 1:
            file_history = file_history[-HISTORY_ENTRIES+1:]
            file_history.append(path)
        elif HISTORY_ENTRIES == 1:
            file_history = [path]
        elif HISTORY_ENTRIES == 0:
            file_history = []            

        # Save updated history.
        history_settings.set("file_history", file_history)
        sublime.save_settings(HISTORY_FILE)

    #----------------------------------------------------------------------#

    def get_history(self):        
        history_settings = sublime.load_settings(HISTORY_FILE)
        file_history     = history_settings.get("file_history")
        # Trim history.
        if not file_history: 
            file_history = []
        else:
            file_history = file_history[ -HISTORY_ENTRIES :]
        return file_history, history_settings        
    
    #----------------------------------------------------------------------#
    # Method called when we exit from the input panel without opening a file.

    def cancel(self):
        # Cancel implies removing panel object.
        iOpenerCommand.input_panel = None

    #----------------------------------------------------------------------
    # Get current text being displayed by input panel.

    def get_text(self):
        return self.view.substr(sublime.Region(0, self.view.size()))
    
    #----------------------------------------------------------------------#
    # Open the given path. Can be a directory OR a file.

    def open_file(self, path):
        self.add_to_history(path)

        path = expanduser(path)

        # Ignore empty paths.
        if len(path) == 0: 
            sublime.status_message("Warning: Ignoring empty path.")
            return

        directory = ""
        filename  = ""

        # If the user enters a path without a filename.
        if path[-1] == sep:  directory = path
        else:                directory,filename = split(path)

        # Path doesn't exist, ask the user if they want to create it.
        if not isdir(directory):
            create = sublime.ok_cancel_dialog(
                "The path you entered does not exist, create it?","Yes"
            )
            # The user cancelled.
            if not create: return
            else:
                try: makedirs(directory)
                except OSError as e:
                    sublime.error_message(
                        "Failed to create path with error: "+str(e)
                    )
                    return

        if filename == "":
            # Open directory in a new window (mirror behaviour of ST).
            sublime.run_command("new_window")            
            data = {"folders":[]}
            data["folders"].append({'follow_symlinks': True, 'path': path})
            sublime.active_window().set_project_data(data)
        else:
            # If file doesn't exist, add a message in the status bar.
            if not isfile(path):
                sublime.status_message("Created new buffer '"+filename+"'")
            sublime.active_window().open_file(path)
        iOpenerCommand.input_panel = None

    #----------------------------------------------------------------------#
    # Set the text in the file open input panel.

    def set_text(self, s):
        self.view.run_command("i_opener_update", {"append": False, "text": s})

    #----------------------------------------------------------------------#
    # Show a quick panel containing the possible completions.

    def show_completions(self):
        active_window      = sublime.active_window()  
        directory,filename = split(self.get_text())
        
        dir_list = listdir(expanduser(directory))

        if CASE_SENSITIVE:
            self.path_cache = [x for x in dir_list if x.startswith(filename)]
        else:
            f  = filename.lower()
            self.path_cache = [x for x in dir_list if x.lower().startswith(f)]
        
        if len(self.path_cache) == 0:
            sublime.status_message("No match")
        else:
            active_window.show_quick_panel(self.path_cache, self.on_done)

    #----------------------------------------------------------------------#

    def on_done(self, i):
        if (self.path_cache == None):  return
        
        if (i!=-1):
            # Remove what was there before.
            directory = split( self.get_text() )[0]
            new_path  = join(directory, self.path_cache[i])            
            
            if (isdir(expanduser(new_path))):
                new_path = new_path + sep
            
            self.set_text(new_path)
            self.path_cache = None
            sublime.active_window().focus_view(self.view)
        sublime.active_window().focus_view(self.view)

    #----------------------------------------------------------------------#

    def append_text(self, s):
        self.view.run_command("i_opener_update", {"append": True, "text": s})

#------------------------------------------------------------------------------#
# Commands and listeners.
#------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
# Event listener to allow querying of context. All our events (for now) only
# need to know if the plugin is active. If so, Sublime Text calls the correct
# commands.

class iOpenerEventListener(sublime_plugin.EventListener):    
    def on_query_context(self, view, key, operator, operand, match_all):
        return  (
                 key                              ==  'i_opener'  
            and  iOpenerCommand.input_panel       !=  None
            and  iOpenerCommand.input_panel.view  ==  view
        )
        
#------------------------------------------------------------------------------#
# The edit command used for editing the text in the input panel.

class iOpenerUpdateCommand(sublime_plugin.TextCommand):
    def run(self, edit, append, text):
        if append: self.view.insert(edit, self.view.size(), text)
        else: self.view.replace(edit, sublime.Region(0,self.view.size()), text)

#------------------------------------------------------------------------------#
# The command called by tapping tab in the open panel.

class iOpenerCompleteCommand(sublime_plugin.WindowCommand):    

    def run(self):
        input_panel = iOpenerCommand.input_panel        
        
        if(input_panel.last_completion_failed):
            input_panel.last_completion_failed = False

            # Show the contents of this directory (if it exists).
            input_panel.show_completions()
        else:
            # Do path completion.            
            path, status, complete = get_completion( input_panel.get_text() )
            if (status != None):
                sublime.status_message(status)
            input_panel.set_text(path)
            input_panel.last_completion_failed = not complete

#------------------------------------------------------------------------------#
# Receive requests to cycle history.

class iOpenerCycleHistoryCommand(sublime_plugin.WindowCommand):
    def run(self, direction):
        if   direction == "up":   iOpenerCommand.input_panel.goto_prev_history()
        elif direction == "down": iOpenerCommand.input_panel.goto_next_history()

#------------------------------------------------------------------------------#
# This is the command caled by the UI.
# input_panel contains an instance of the class Path_input when the input is
# active, otherwise it contains None.

class iOpenerCommand(sublime_plugin.WindowCommand):
    input_panel  = None

    def run(self):
        # Re-load the settings file, which may have changed since last run.
        load_settings()

        # Create a new input panel, it will display itself.
        iOpenerCommand.input_panel = Path_input()

#------------------------------------------------------------------------------#
