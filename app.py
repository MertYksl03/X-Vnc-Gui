import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # type: ignore

from gui.main_window import MainWindow

from src.dummy import Dummy

import threading
import json
import os
import subprocess

class MyApp(Gtk.Application):

    def __init__(self):
        super().__init__(application_id="org.gnome.X-Vnc")  # Add an application ID
        self.main_window = None
        self.data = None                                    # App's config data stored in config.json
        self.file_path = None                               # The file path of Xorg config files
        self.port_name = None                               # The port name the virtual display will be connected to
        self.ports = []                                     # All the port the computer has for display
        self.dummy_instance = None                      
        

    def do_activate(self):
        self.main_window = MainWindow(self)
        self.add_window(self.main_window)
        self.main_window.show_all()

        # Initialization in a separate thread
        threading.Thread(target=self.initialize_app, daemon=True).start()

    def initialize_app(self):
        # Read the configuration from config.json
        # GLib.idle_add(self.load_data)
        self.load_data()

        # These variables will be loaded from config.json
        self.file_path = self.data["x"]["file_path"]
        self.port_name = self.data["x"]["default_port"]

        # IDK if this is necessary
        self.ports = self.get_ports()

        # Initialize Dummy class
        self.dummy_instance = Dummy()
        if not self.dummy_instance.initialize(self.file_path, self.port_name):
            # Display error message and close the app
            error_message = "Failed to initialize Dummy class. The application will now close."
            GLib.idle_add(self.show_critical_error, error_message)
            return  # Stop further execution
        
        self.print_()


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


    def on_config_saved(self, file_path, port_name):
        self.file_path = file_path
        self.port_name = port_name
        self.print_()  # FOR DEVELOPMENT PURPOSES
        return self.dummy_instance.initialize(file_path, port_name)
    
    # FOR DEVELOPMENT PURPOSES
    def print_(self):
        print(self.file_path)
        print(self.port_name)

    def get_ports(self):
        # Run the xrandr command and capture the output
        result = subprocess.run(['xrandr'], stdout=subprocess.PIPE, text=True)
        output = result.stdout

        # Extract valid port names (lines that start with a port name)
        ports = []
        for line in output.splitlines():
            if " connected" in line or " disconnected" in line:
                if "eDP" in line:
                    continue
                port = line.split()[0]  # The first word is the port name
                ports.append(port)
        
        return ports 
    
    # def on_config_saved(self, file_path, port_name):
    #     # This function will be called when the "Save" button is clicked
    #     print(f"File Path from app.py: {file_path}")
    #     print(f"Port Name from app.py: {port_name}")


