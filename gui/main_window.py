import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk #type: ignore

from gui.configure_window import ConfigWindow

WIDTH = 1280
HEIGHT = 720

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(title = "X-vnc")
        self.set_default_size(WIDTH, HEIGHT)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(10)
        self.app = app

        # Load external CSS
        provider = Gtk.CssProvider()
        provider.load_from_path("styles/style.css")  # Load the CSS file

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(box_outer)


        box_upper = self.box_upper().get_box()
        # grid_outer.attach(box_upper, 0, 0, 1, 1)
        box_outer.pack_start(box_upper, True, True, 0)


        box_lower = self.lower_box().get_box()
        box_outer.pack_start(box_lower, True, True, 0)
        
    def on_configure_clicked(self, button):
        # Open the configuration window
        config_window = ConfigWindow(self, self.app.on_config_saved, self.app.get_ports)
        config_window.show_all()


    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()
     

    class box_upper:

        def __init__(self):
            self.box_upper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

            # First Box: About xconf.d configs
            box_1 = self.box_1().get_box()

            label = Gtk.Label(" ") # TEMPORARY
            label1 = Gtk.Label(" ") # TEMPORARY
            label2 = Gtk.Label(" ") # TEMPORARY

            # Second Box: The settings about the virtual display(resolution etc.)
            box_2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

            # Third Box: The settings and status about ADB server
            box_3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

            # Fourth Box: The settings and status about VNC server
            box_4 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            
            box_2.add(label)
            box_3.add(label1)
            box_4.add(label2)
            
            # Add small boxes to the main box
            self.box_upper.pack_start(box_1, True, True, 0)
            self.box_upper.pack_start(box_2, True, True, 0)
            self.box_upper.pack_start(box_3, True, True, 0)
            self.box_upper.pack_start(box_4, True, True, 0)
    
            
        def get_box(self):
            return self.box_upper
        
         # First Box: About xconf.d configs
        class box_1:

            def __init__(self):
                self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

                # User should see and know what this part about
                label_title = Gtk.Label("DUMMY CONFIG")
                self.box.pack_start(label_title, True, True, 10)

                # The label about the status. This label will be dynamicly changes and displays the status of dummy config
                label_status = Gtk.Label("Ready")
                self.box.pack_start(label_status, True, True, 10)
                
                button_configure = Gtk.Button(label="Configure")
                self.box.pack_start(button_configure, False, False, 10)
                
                button_activate = Gtk.Button(label="Save")
                self.box.pack_start(button_activate, False, False, 10)

            def get_box(self):
                return self.box
                

        
    class lower_box:
        def __init__(self):

            self.box_outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

            # Using these empty labels as spacers
            spacer_left = Gtk.Label(" ")
            spacer_right = Gtk.Label(" ")

            box_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            box_main.set_name("asd")
            
            status = Gtk.Label("DISCONNECTED")
            status.set_name("lower_box_status")
            box_main.pack_start(status, True, False, 0)


            # Grid for IP and other details
            grid = Gtk.Grid()
            grid.set_column_spacing(20)
            grid.set_row_spacing(20)
            box_main.pack_end(grid, True, True, 0)

            # Center the grid horizontally
            grid.set_halign(Gtk.Align.CENTER)

            # Add informational label at the top (row 0)
            info = """You can connect the VNC server with this ip """
            info = Gtk.Label(label=info)
            grid.attach(info, 0, 0, 2, 1)  # Span across 2 columns

            # Add IP label and value (row 1)
            label1 = Gtk.Label(label="Ip: ")
            label2 = Gtk.Label(label="127.0.0.1:5900")
            label2.set_selectable(True)  # Allow text selection
            grid.attach(label1, 0, 1, 1, 1)  # Attach label1 at (0, 1)
            grid.attach(label2, 1, 1, 1, 1)  # Attach label2 at (1, 1)


            self.box_outer.pack_start(spacer_left, True, True, 0)
            self.box_outer.pack_start(box_main, True, True, 0)
            self.box_outer.pack_start(spacer_right, True, True, 0)

        def get_box(self):
            return self.box_outer
        
