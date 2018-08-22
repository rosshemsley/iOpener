"""
A package to make opening files in Sublime Text a little bit less painful.
Licensed under GPL V2.

Written by Ross Hemsley and other collaborators 2013.
"""

import sublime, sublime_plugin, time
from os.path import isdir, isfile, expanduser, split, relpath, join, commonprefix, normpath
from os      import listdir, sep, makedirs

from .matching import complete_path, COMPLETION_TYPE, get_matches
from .paths import get_current_directory, directory_listing_with_slahes

# Locations of settings files.
HISTORY_FILE     = 'i_opener_history.sublime-settings'
SETTINGS_FILE    = 'i_opener.sublime-settings'

STATUS_MESSAGES = {
    COMPLETION_TYPE.CompleteButNotUnique: 'Complete, but not unique',
    COMPLETION_TYPE.NoMatch: 'No match',
    COMPLETION_TYPE.Complete: None,
}

def load_settings():
    # We set these globals.
    global USE_PROJECT_DIR
    global OPEN_FOLDERS_IN_NEW_WINDOW
    global HISTORY_ENTRIES
    global CASE_SENSITIVE

    settings = sublime.load_settings(SETTINGS_FILE)

    USE_PROJECT_DIR = settings.get('use_project_dir')
    OPEN_FOLDERS_IN_NEW_WINDOW = settings.get('open_folders_in_new_window')
    CASE_SENSITIVE  = settings.get('case_sensitive')
    HISTORY_ENTRIES = settings.get('history_entries')


def is_sublime_text_2():
    return 2000 <= int(sublime.version()) <= 2999


def is_sublime_text_3():
    return 3000 <= int(sublime.version()) <= 3999


def get_completion(path):
    """
    Function to find and return longest possile completion for a path p from a
    list of candidates l. Returns new_path, status, completed.
    Find filename and directory.
    """
    directory, filename = split(path)

    if not isdir(expanduser(directory)):
        return path, COMPLETION_TYPE.NoMatch

    directory_listing = listdir(expanduser(directory))
    new_filename, completion_type = complete_path(filename, directory_listing, CASE_SENSITIVE)

    if new_filename != '' and isdir(expanduser(join(directory, new_filename))):
        new_filename += sep

    return join(directory, new_filename), completion_type


class iOpenerPathInput():
    """
    This class encapsulates the behaviors relating to the file open panel
    used by the package. We create an instance when the panel is open, and destroy
    it when the panel is closed.
    """
    def __init__(self):
        # If the user presses tab, and nothing happens, remember it.
        # If they press tab again, we show them a list of files.
        self.last_completion_failed = False
        self.path_cache             = None
        active_window               = sublime.active_window()

        view_filename = active_window.active_view().file_name()
        folders = active_window.folders()

        path = get_current_directory(view_filename, folders, USE_PROJECT_DIR)

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

    def update(self,text):
        """
        If the user updates the input, reset the 'failed completion' flag.
        """
        self.last_completion_failed = False

    def goto_prev_history(self):
        """
        Temporarily store any changes in cache, as bash does.
        """
        self.history_cache[self.history_index] = self.get_text()
        self.history_index -= 1
        if self.history_index < 0:
            sublime.status_message("Reached start of history")
            self.history_index = 0
        self.set_text( self.history_cache [ self.history_index] )

    def goto_next_history(self):
        # Temporarily store any changes in cache, as bash does.
        self.history_cache[self.history_index] = self.get_text()
        self.history_index += 1
        if self.history_index == len(self.history_cache):
            sublime.status_message("Reached end of history")
            self.history_index = len(self.history_cache)-1
        self.set_text( self.history_cache [ self.history_index] )

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

    def get_history(self):
        history_settings = sublime.load_settings(HISTORY_FILE)
        file_history     = history_settings.get("file_history")
        # Trim history.
        if not file_history:
            file_history = []
        else:
            file_history = file_history[ -HISTORY_ENTRIES :]
        return file_history, history_settings

    def cancel(self):
        """
        Method called when we exit from the input panel without opening a file.
        Cancel implies removing panel object.
        """
        iOpenerCommand.input_panel = None

    def get_text(self):
        """
        Get current text being displayed by input panel.
        """
        return self.view.substr(sublime.Region(0, self.view.size()))

    def open_file(self, path):
        """
        Open the given path. Can be a directory OR a file.
        """
        path = expanduser(path)

        # Ignore empty paths.
        if not path:
            sublime.status_message("Warning: Ignoring empty path.")
            return

        self.add_to_history(path)

        directory = ""
        filename  = ""

        # If the user enters a path without a filename.
        if path[-1] == sep:  directory = path
        else:                directory,filename = split(path)

        # Path doesn't exist, ask the user if they want to create it.
        if not isdir(directory):
            create = sublime.ok_cancel_dialog("The path you entered does not exist, create it?",
                                              "Yes")
            if not create:
                return
            else:
                try: makedirs(directory)
                except OSError as e:
                    sublime.error_message("Failed to create path with error: " + str(e))
                    return

        if isdir(path):
            if is_sublime_text_2():
                # Project folders can not be added using the ST2 API.
                sublime.status_message("Warning: Opening folders requires ST v3.")
            elif OPEN_FOLDERS_IN_NEW_WINDOW:
                sublime.run_command("new_window")
                project_data = dict(folders=[dict(follow_symlinks=True, path=path)])
                sublime.active_window().set_project_data(project_data)
            else:
                project_data = sublime.active_window().project_data() or {}
                project_folders = project_data.get('folders') or []

                folder = dict(path=path, follow_symlinks=True, folder_exclude_patterns=['.*'])

                # if project_data == {}, no project is open.
                if project_data == {}:
                    project_data = dict(folders=[dict(follow_symlinks=True, path=path)])
                elif all(folder['path'] != path for folder in project_folders):
                    project_data['folders'].append(folder)
                sublime.active_window().set_project_data(project_data)
        else:
            # If file doesn't exist, add a message in the status bar.
            if not isfile(path):
                sublime.status_message("Created new buffer '"+filename+"'")
            sublime.active_window().open_file(path)
        iOpenerCommand.input_panel = None

    def set_text(self, s):
        """
        Set the text in the file open input panel.
        """
        self.view.run_command("i_opener_update", {"append": False, "text": s})

    def show_completions(self):
        """
        Show a quick panel containing the possible completions.
        """
        active_window      = sublime.active_window()
        directory, filename = split(self.get_text())

        directory_listing = directory_listing_with_slahes(expanduser(directory))
        self.path_cache = get_matches(filename, directory_listing, CASE_SENSITIVE)

        if len(self.path_cache) == 0:
            show_completion_message(COMPLETION_TYPE.NoMatch)
        else:
            active_window.show_quick_panel(self.path_cache, self.on_done)

    def on_done(self, i):
        if self.path_cache is None:
            return

        elif i != -1:
            directory, _ = split(self.get_text())
            new_path  = join(directory, self.path_cache[i])
            self.path_cache = None

            if isdir(expanduser(new_path)):
                self.set_text(new_path)
                sublime.active_window().focus_view(self.view)
            else:
                self.open_file(new_path)
                sublime.active_window().run_command("hide_panel", {"cancel": True})
        else:
            sublime.active_window().focus_view(self.view)

    def append_text(self, s):
        self.view.run_command("i_opener_update", {"append": True, "text": s})


def show_completion_message(completion_type):
    status = STATUS_MESSAGES.get(completion_type)

    if status is not None:
        sublime.status_message(status)


##
# Commands and listeners.
##


class iOpenerEventListener(sublime_plugin.EventListener):
    """
    Event listener to allow querying of context. All our events (for now) only
    need to know if the plugin is active. If so, Sublime Text calls the correct
    commands.
    """
    def on_query_context(self, view, key, operator, operand, match_all):
        return (key                                   ==  'i_opener'
            and iOpenerCommand.input_panel            !=  None
            and iOpenerCommand.input_panel.view.id()  ==  view.id()
        )


class iOpenerUpdateCommand(sublime_plugin.TextCommand):
    """
    The edit command used for editing the text in the input panel.
    """
    def run(self, edit, append, text):
        if append: self.view.insert(edit, self.view.size(), text)
        else: self.view.replace(edit, sublime.Region(0,self.view.size()), text)


class iOpenerCompleteCommand(sublime_plugin.WindowCommand):
    """
    The command called by tapping tab in the open panel.
    """
    def run(self):
        input_panel = iOpenerCommand.input_panel

        if input_panel.last_completion_failed:
            input_panel.last_completion_failed = False
            input_panel.show_completions()
        else:
            completion, completion_type = get_completion(input_panel.get_text())
            show_completion_message(completion_type)
            input_panel.set_text(completion)

            completion_failed = completion_type != COMPLETION_TYPE.Complete
            input_panel.last_completion_failed = completion_failed


class iOpenerCycleHistoryCommand(sublime_plugin.WindowCommand):
    """
    Receive requests to cycle history.
    """
    def run(self, direction):
        if   direction == "up":   iOpenerCommand.input_panel.goto_prev_history()
        elif direction == "down": iOpenerCommand.input_panel.goto_next_history()


class iOpenerCommand(sublime_plugin.WindowCommand):
    """
    This is the command caled by the UI.
    input_panel contains an instance of the class iOpenerPathInput when the input is
    active, otherwise it contains None.
    """
    input_panel  = None

    def run(self):
        if not (is_sublime_text_2() or is_sublime_text_3()):
            print("iOpener plugin is only for Sublime Text v2 and v3.")
        else:
            load_settings()
            iOpenerCommand.input_panel = iOpenerPathInput()
