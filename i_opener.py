#------------------------------------------------------------------------------#
# A plugin to make opening files in Sublime Text a little bit less painless.
# Lisenced under GPL V2.
#
# Written by Ross Hemsley, 2013.
#------------------------------------------------------------------------------#
import sublime, sublime_plugin, time
from os.path import isdir,   expanduser, split, relpath, join, commonprefix
from os      import listdir, sep

# Here is where we store hsitory
HISTORY_FILE    = 'i_opener_history.sublime-settings'
HISTORY_ENTRIES = 30
HISTORY_ENABLED = True

#------------------------------------------------------------------------------#
# This class encapsulates the behaviours relating to the file open panel
# used by the plugin.

class Input_Panel():
    # Cache the list of paths passed to an open dialog.
    path_cache    = None
    history_cache = None
    history_index = None

    #----------------------------------------------------------------------#
    # Class initialisation.
    
    def __init__(self):
        active_window      = sublime.active_window()
        path               = path_mangler.get_current_path()        
        
        # We only reload the history each time the input window is opened.
        self.history_cache = self.get_history()[0]
        
        # Store default at end of history cache.
        self.history_cache.append(path)        
        self.history_index = len(self.history_cache)-1
        self.view          = active_window.show_input_panel(
            "Find file: ", 
            path, 
            self.open_file, 
            None, 
            self.cancel
        )

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
        print ("adding", path, "to history")
        file_history, history_settings = self.get_history()
        file_history = file_history[-(HISTORY_ENTRIES-1):]
        file_history.append(path)     
        history_settings.set("file_history", file_history)
        sublime.save_settings(HISTORY_FILE)

    #----------------------------------------------------------------------#

    def get_history(self):
        history_settings = sublime.load_settings(HISTORY_FILE)
        file_history     = history_settings.get("file_history")
        if not file_history: file_history = []
        print ("loaded history: ", file_history)
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
        if (isdir(expanduser(path))):
            # Open directory in a new window (mirror behaviour of ST).
            sublime.run_command("new_window")            
            data = {"folders":[]}
            data["folders"].append({'follow_symlinks': True, 'path': path})
            sublime.active_window().set_project_data(data)
        else:
            sublime.active_window().open_file(path)

        self.add_to_history(path)
        iOpenerCommand.input_panel = None

    #----------------------------------------------------------------------#
    # Set the text in the file open input panel.

    def set_text(self, s):
        self.view.run_command("i_opener_update", {"append": False, "text":s})

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
            # Kill what was there before.
            directory, filename = split( self.get_text() )

            new_path = join(directory, self.path_cache[i])            
            
            if (isdir(expanduser(new_path))):
                new_path = new_path + sep
            
            self.set_text(new_path)
            self.path_cache = None
            sublime.active_window().focus_view(self.view)
        sublime.active_window().focus_view(self.view)

    #----------------------------------------------------------------------#

    def append_text(self, s):
        self.view.run_command("i_opener_update", {"append": True, "text":s})

#------------------------------------------------------------------------------#
# Defines the behaviour of the paths.

class path_mangler():
    
    #----------------------------------------------------------------------#

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

    #----------------------------------------------------------------------#
    
    def get_completion(path):

        # We complete directories by simply adding a '/'
        if isdir(expanduser(path)):
            if len(path)>0 and path[-1]!= sep:
                return sep

        directory, filename = split(path)
        files = listdir(expanduser(directory))    
        completion = path_mangler.path_complete(filename, files)[len(filename):]

        if (len(completion) == 0): 
            return ""
        
        if isdir(expanduser(path+completion)):
            return completion + sep
        else:
            return completion

    #----------------------------------------------------------------------#
    # If this is an ancestor of '~/', truncate and add '~/'. Else, return
    # relative to '/'.

    def simplify_path(path):
        pass

    #----------------------------------------------------------------------#
        
    def get_current_path():
        home = expanduser("~")
        view = sublime.active_window().active_view()
        data = sublime.active_window().project_data()
        here = None

        if data and len(data["folders"]) == 1:
            here = data["folders"][0]["path"]            
        elif(view != None and view.file_name() != None): 
            here = split(view.file_name())[0] + sep
        else:
            here = "~" + sep
                
        # Return path relative to home if applicable.
        if len(commonprefix([home, here])) > 1:
            return join("~", relpath(here,home))
        else:
            return here

    #----------------------------------------------------------------------#

    def get_history_path(i):
        pass

#------------------------------------------------------------------------------#
# This event listener gives allows us to check when the 'tab' key should be 
# handled by the plugin or not.

class iOpenerEventListener(sublime_plugin.EventListener):    
    def on_query_context(self, view, key, operator, operand, match_all):
        return  (
                 key                              ==  'i_opener'  
            and  iOpenerCommand.input_panel       !=  None
            and  iOpenerCommand.input_panel.view  ==  view
        )
        
#------------------------------------------------------------------------------#
# The edit command used for editing the open input panel.

class iOpenerUpdateCommand(sublime_plugin.TextCommand):
    def run(self, edit, append, text):  
        # Remember that we succeeded.
        if text != "": iOpenerCompleteCommand.last_time = None
        if append:     self.view.insert(edit, self.view.size(), text)
        else: self.view.replace(edit, sublime.Region(0,self.view.size()), text)

#------------------------------------------------------------------------------#
# The command called by tapping tab in the open panel.

class iOpenerCompleteCommand(sublime_plugin.WindowCommand):    
    # Store the time, so that we can detect double presses of tab.
    last_time = None

    def run(self):
        input_panel = iOpenerCommand.input_panel        
        last_time   = iOpenerCompleteCommand.last_time
        if(last_time != None and time.time() - last_time < 0.3):
            input_panel.show_completions()
        else:
            iOpenerCompleteCommand.last_time = time.time()

        input_panel.append_text(
            path_mangler.get_completion( input_panel.get_text() )
        )

#------------------------------------------------------------------------------#
# Receive requests to cycle history.

class iOpenerCycleHistoryCommand(sublime_plugin.WindowCommand):
    def run(self, direction):
        if direction == "up":
            iOpenerCommand.input_panel.goto_prev_history()
        elif direction == "down":
            iOpenerCommand.input_panel.goto_next_history()

#------------------------------------------------------------------------------#
# This is the command caled by the UI.
# We check if input_panel is None to check whether or not the plugin is active.

class iOpenerCommand(sublime_plugin.WindowCommand):
    input_panel  = None

    def run(self):    
        # Create a new input panel, it will display itself.
        iOpenerCommand.input_panel = Input_Panel()

#------------------------------------------------------------------------------#