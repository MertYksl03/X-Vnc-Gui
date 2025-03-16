import gi
import atexit
import signal
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # type: ignore

from gui.main_window import MainWindow

from src.dummy import Dummy
from src.virtual_display import VirtualDisplay

import threading
import json
import os
import subprocess

class MyApp(Gtk.Application):
    # Global variables
    ports = []                                              # Holds all the ports the computer has for display 
    port_name = None                                        # Holds the name of the display port of virtual display
    main_port_name = None                                   # Holds the name of the primary display port 
    resolutions = None                                      # All the resolution of the port that vd is connected to
    active_resoultion_vnc = None                            # 

    dummy_instance = None
    virtual_display_instance = None

    def __init__(self):
        super().__init__(application_id="org.gnome.X-Vnc")  # Add an application ID
        # This varibales are private variables
        self.main_window = None
        self.data = None                                    # App's config data stored in config.json             
        

    def do_activate(self):
        if self.initialize_app() == False:
            return
        
            # Register cleanup function for normal exit
        atexit.register(self.clean_up)

        # Register signal handlers for crashes or termination
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

        self.main_window = MainWindow(self)
        self.add_window(self.main_window)
        self.main_window.show_all()

    # LOGIC FUNCTIONS

    def initialize_app(self):
        
        # First check the session type 
        session = self.get_session_type()
        if session != "Xorg":
            self.show_critical_error(f"You are on {session} session\nThis app only works on Xorg")
            return False

        # Read the configuration from config.json
        self.load_data()

        # These variables will be loaded from config.json
        try :
            self.file_path = self.data["user-settings"]["x"]["file_path"]
            self.port_name = self.data["user-settings"]["x"]["default_port"]
        except Exception as e:
            self.show_critical_error(str(e))
            return

        # Initialize Dummy class
        self.dummy_instance = Dummy()
        status = self.dummy_instance.initialize(self.file_path, self.port_name, self.main_port_name)
        if status[0] == False:
            # Display error message and close the app
            # error_message = "Failed to initialize Dummy class. The application will now close."
            error_message = status[1]
            GLib.idle_add(self.show_critical_error, error_message)
            return  # Stop further execution
        
        # self.main_port_name = self.dummy_instance.main_port

        # fetch the infos from xrandr command and set them
        self.set_xrandr_info()

        # Create the vd instance
        self.virtual_display_instance = VirtualDisplay()
        # Give all the resolutions to vd
        self.virtual_display_instance.resolutions = self.resolutions
        # Check and assign the status of vd
        self.virtual_display_instance.status = self.check_vd_status()
        
        # Initiliaze the vd with data from config.json
        try :
            self.virtual_display_instance.resolution = self.data["user-settings"]["virtual-display"]["resolution"]
            self.virtual_display_instance.position = self.data["user-settings"]["virtual-display"]["position"]
        except Exception as e:
            self.show_critical_error(str(e))
            return
        
        # if initialize is succesfull then return true
        return True
    
    def restore_defaults(self):
        self.data["user-settings"] = self.data["default"]

        self.save_user_settings()
        
        return self.initialize_app()

    def get_session_type(self):
        if os.getenv('WAYLAND_DISPLAY'):
            return 'Wayland'
        elif os.getenv('DISPLAY'):
            return 'Xorg'
        else:
            return 'Unknown'

    def clean_up(self):
        # This function will be called when the program closes or crahes
        # Check the virtual display is connected or not
        if self.virtual_display_instance.status == True:
            # Unlug the virtual display
            self.virtual_display_instance.unplug_virtual_display()

        super().do_shutdown(self) # Call the parent class's shutdown method

    def handle_signal(self, signum, frame):
        self.clean_up()
        sys.exit(0)

    # UI FUNCTIONS

    def show_info_message(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window if self.main_window else None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()
        
    def show_error_message(self, message):
        "Show a error message to the user"
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window if self.main_window else None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error",
        )
        dialog.format_secondary_text(message)

        # Run the dialog and wait for user response
        response = dialog.run()

        # Destroy the dialog after the user responds
        dialog.destroy()

    def show_critical_error(self, message):
        """
        Show a critical error dialog and close the app when the user presses OK.
        """
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window if self.main_window else None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Critical Error",
        )
        dialog.format_secondary_text(message)  # Add detailed error message

        # Run the dialog and wait for user response
        response = dialog.run()

        # Destroy the dialog after the user responds
        dialog.destroy()

        # Close the application if the user presses OK
        if response == Gtk.ResponseType.OK:
            self.quit()  # Close the program

    # NON-UI FUNCTIONS
    
    def load_data(self):
        try:
            # Path to the JSON file
            json_path = os.path.join(os.path.dirname(__file__), "src/config.json")

            # Load the JSON file
            with open(json_path, "r") as file:
                self.data = json.load(file)
        except FileNotFoundError:
            self.show_critical_error("Error: JSON file not found.")
            self.data = {}  # Fallback to an empty dictionary
        except json.JSONDecodeError:
            self.show_critical_error("Error: Invalid JSON format.")
            self.data = {}  # Fallback to an empty dictionary

    def set_xrandr_info(self):
        port_name = self.port_name
        # Run the xrandr command and capture the output
        result = subprocess.run(['xrandr'], stdout=subprocess.PIPE, text=True)
        output = result.stdout

        # Extract valid port names (lines that start with a port name)
        found_port = False
        resolutions = []
        ports = []
        for line in output.splitlines():
            # Get the main(primary) port name
            if " connected " in line and " primary " in line:
                main_port = line.split()[0] # The first word is the port name 

            # Get the ports 
            if " connected" in line or " disconnected" in line:
                # Skip the main port
                if main_port in line:
                    continue
                port = line.split()[0]  # The first word is the port name
                ports.append(port)
            
            # Find the port
            if port_name in line and 'connected' in line:
                found_port = True
                continue  # Move to the next line to start parsing resolutions
            
            # If we're in the correct display port section, look for resolutions
            if found_port:
                # Stop processing if we reach another display port section
                if 'connected' in line:
                    found_port = False
                
                # Extract resolution if the line contains a resolution like "1920x1080"
                if 'x' in line and '+' not in line:
                    resolution = line.strip().split()[0]
                    resolutions.append(resolution)

        # Set the data into relevant variables
        self.main_port_name = main_port
        self.ports = ports
        self.resolutions = resolutions
        return

    def check_vd_status(self):
        port_name = self.port_name
        # Run the xrandr command and capture the output
        command = "xrandr --listmonitors"
        result = subprocess.run(command.split(), stdout=subprocess.PIPE, text=True)
        output = result.stdout

        for line in output.splitlines():
            if port_name in line:
                return True
            
        return False

    def on_config_saved_dmy(self, file_path, port_name):
        status = self.dummy_instance.initialize(file_path, port_name, self.main_port_name)
        if status[0] == False:
            error_message = status[1]
            GLib.idle_add(self.show_error_message, error_message)
            return False # Return false, so user can enter a valid filepath
        else:
            self.data["user-settings"]["x"]["file_path"] = file_path
            self.data["user-settings"]["x"]["default_port"] = port_name

            # Write the new json file 
            return self.save_user_settings()
            
    def on_config_save_vd(self, resolution, position):
        # Assign the width, height and position
        self.virtual_display_instance.resolution = resolution
        self.virtual_display_instance.position = position

        # save the configuration to json file
        self.data["user-settings"]["virtual-display"]["resolution"] = resolution
        self.data["user-settings"]["virtual-display"]["position"] = position
        
        self.save_user_settings()
    
    def save_user_settings(self): # By writing into config.json file 
        try:
            with open("src/config.json", 'w') as json_file:
                json.dump(self.data, json_file, indent=4)  # indent=4 for pretty-printing
                return True
        except Exception as e:
            self.main_window.show_error_dialog(str(e))
            return False



