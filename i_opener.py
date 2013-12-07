#------------------------------------------------------------------------------#
# A plugin to make opening files in Sublime Text a little bit less painless.
# Lisenced under GPL V2.
#
# Written by Ross Hemsley, 2013.
#------------------------------------------------------------------------------#
import sublime, sublime_plugin, time
from   os.path import isdir,   expanduser, split, relpath, join, commonprefix
from   os      import listdir, sep

# Here is where we store hsitory
HISTORY_FILE    = 'i_opener_history.sublime-settings'
HISTORY_ENTRIES = 30

#------------------------------------------------------------------------------#
# Function to find and return longest possile completion for a path p from a
# list of candidates l.

def path_complete(p, l):        
    i       = 0
    matches = []
    for i in range(len(p)):
        matches = list ( filter( lambda x: x.startswith(p), l ) )
        if len(matches) == 1:  return matches[0]
        if len(matches) == 0:  return p[:i]
    if len(matches) !=0:
        return commonprefix(matches)
    return ""

#------------------------------------------------------------------------------#
# Try to complete the given path.

def get_completion(path):

    # We complete directories by simply adding a '/'
    if isdir(expanduser(path)):
        if len(path)>0 and path[-1]!= sep:
            return sep

    directory, filename = split(path)
    if not isdir(expanduser(directory)):        
        sublime.status_message("Error: Path does not exist.")
        return ""
    else:
        files      = listdir(expanduser(directory))    
        completion = path_complete(filename, files)[len(filename):]

        if len(completion) == 0:                return ""        
        if isdir(expanduser(path+completion)):  return completion + sep
        else:                                   return completion

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

    if data and len(data["folders"]) == 1:
        here = data["folders"][0]["path"]            
    elif view != None and view.file_name() != None: 
        here = split(view.file_name())[0] + sep
    else:
        here = "~" + sep

    # Return path relative to home if applicable.
    if len(commonprefix([home, here])) > 1:
        relative_path = relpath(here,home)
        if len(relative_path) > 1:
            return join("~", relpath(here,home))
        else:
            return "~" + sep
    else:
        return here

#------------------------------------------------------------------------------#
# This class encapsulates the behaviours relating to the file open panel
# used by the plugin. We create an instance when the panel is open, and destroy
# it when the panel is closed.
#------------------------------------------------------------------------------#

class Input_Panel():
    
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
        self.history_index -=1
        if self.history_index < 0:
            sublime.status_message("Reached start of history")
            self.history_index = 0
        self.set_text( self.history_cache [ self.history_index] )

    #----------------------------------------------------------------------#

    def goto_next_history(self):
        # Temporarily store any changes in cache, as bash does.
        self.history_cache[self.history_index] = self.get_text()
        self.history_index +=1
        if self.history_index == len(self.history_cache):
            sublime.status_message("Reached end of history")
            self.history_index = len(self.history_cache)-1
        self.set_text( self.history_cache [ self.history_index] )

    #----------------------------------------------------------------------#

    def add_to_history(self,path):        
        file_history, history_settings = self.get_history()
        
        # Trim the history to the correct length and add latest entry.
        file_history = file_history[-(HISTORY_ENTRIES-1):]
        file_history.append(path)

        # Save updated history.
        history_settings.set("file_history", file_history)
        sublime.save_settings(HISTORY_FILE)

    #----------------------------------------------------------------------#

    def get_history(self):
        history_settings = sublime.load_settings(HISTORY_FILE)
        file_history     = history_settings.get("file_history")
        if not file_history: file_history = []
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

        # For cross-platform compatibility, make sure '~' is removed.
        path = expanduser(path)

        if (isdir(expanduser(path))):
            # Open directory in a new window (mirror behaviour of ST).
            sublime.run_command("new_window")            
            data = {"folders":[]}
            data["folders"].append({'follow_symlinks': True, 'path': path})
            sublime.active_window().set_project_data(data)
        else:
            sublime.active_window().open_file(path)
        iOpenerCommand.input_panel = None

    #----------------------------------------------------------------------#
    # Set the text in the file open input panel.

    def set_text(self, s):
        self.view.run_command("i_opener_update", {"append": False, "text": s})

    #----------------------------------------------------------------------#
    # Show a quick panel containing the possible completions.

    def show_completions(self):
        active_window    = sublime.active_window()  
        directory        = split(self.get_text())[0]
        self.path_cache  = listdir(expanduser(directory))
        if len(self.path_cache) == 0:
            sublime.status_message("Directory is empty")
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
            completion = get_completion( input_panel.get_text() )
            if completion == "":
                input_panel.last_completion_failed = True
            else:
                input_panel.last_completion_failed = False
                input_panel.append_text(completion)

#------------------------------------------------------------------------------#
# Receive requests to cycle history.

class iOpenerCycleHistoryCommand(sublime_plugin.WindowCommand):
    def run(self, direction):
        if   direction == "up":   iOpenerCommand.input_panel.goto_prev_history()
        elif direction == "down": iOpenerCommand.input_panel.goto_next_history()

#------------------------------------------------------------------------------#
# This is the command caled by the UI.
# input_panel contains an instance of the class Input_Panel when the input is
# active, otherwise it contains None.

class iOpenerCommand(sublime_plugin.WindowCommand):
    input_panel  = None

    def run(self):    
        # Create a new input panel, it will display itself.
        iOpenerCommand.input_panel = Input_Panel()

#------------------------------------------------------------------------------#