"""
Login Screen for IPTV-Saba Android
Kivy-based profile selection and creation
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App


class CreateProfilePopup(Popup):
    """Popup dialog for creating a new profile"""

    def __init__(self, on_create_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "Create New Profile"
        self.size_hint = (0.9, 0.5)
        self.on_create_callback = on_create_callback

        # Build content
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        # Header
        header = Label(
            text="Create Your Profile",
            size_hint_y=0.2,
            font_size=dp(20),
            color=(0.898, 0.035, 0.078, 1),  # Netflix red
            bold=True
        )
        content.add_widget(header)

        # Name input
        self.name_input = TextInput(
            hint_text="Enter Profile Name",
            size_hint_y=0.25,
            multiline=False,
            font_size=dp(16),
            background_color=(0.17, 0.17, 0.17, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[dp(15), dp(15)]
        )
        content.add_widget(self.name_input)

        # URL input
        self.url_input = TextInput(
            hint_text="Enter M3U Playlist URL",
            size_hint_y=0.25,
            multiline=False,
            font_size=dp(16),
            background_color=(0.17, 0.17, 0.17, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[dp(15), dp(15)]
        )
        content.add_widget(self.url_input)

        # Buttons
        buttons_layout = BoxLayout(size_hint_y=0.3, spacing=dp(10))

        create_btn = Button(
            text="Create",
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(16),
            bold=True
        )
        create_btn.bind(on_press=self.create_profile)
        buttons_layout.add_widget(create_btn)

        cancel_btn = Button(
            text="Cancel",
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=dp(16)
        )
        cancel_btn.bind(on_press=self.dismiss)
        buttons_layout.add_widget(cancel_btn)

        content.add_widget(buttons_layout)
        self.content = content

    def create_profile(self, instance):
        """Create profile and dismiss"""
        name = self.name_input.text.strip()
        url = self.url_input.text.strip()

        if name and url:
            self.on_create_callback(name, url)
            self.dismiss()
        else:
            # Show error
            error_popup = Popup(
                title='Error',
                content=Label(text='Please enter both name and URL'),
                size_hint=(0.7, 0.3)
            )
            error_popup.open()


class LoginScreen(Screen):
    """Login screen for profile selection and management"""

    def __init__(self, controller, config_manager, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.config_manager = config_manager
        self.selected_profile = None
        self.auto_login_checkbox = None

        self.build_ui()
        self.load_profiles()

    def build_ui(self):
        """Build the login screen UI"""
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        # Set background
        with main_layout.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # Dark background
            self.bg_rect = Rectangle(size=main_layout.size, pos=main_layout.pos)
        main_layout.bind(size=self._update_bg, pos=self._update_bg)

        # Header
        header = Label(
            text="IPTV Saba",
            size_hint_y=0.15,
            font_size=dp(32),
            color=(0.898, 0.035, 0.078, 1),  # Netflix red
            bold=True
        )
        main_layout.add_widget(header)

        # Subtitle
        subtitle = Label(
            text="Select Your Profile",
            size_hint_y=0.1,
            font_size=dp(18),
            color=(1, 1, 1, 1)
        )
        main_layout.add_widget(subtitle)

        # Profile list container
        self.profile_container = BoxLayout(
            orientation='vertical',
            size_hint_y=0.5,
            spacing=dp(10)
        )

        # Scrollable profile list
        scroll = ScrollView(size_hint_y=1)
        self.profile_list = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None
        )
        self.profile_list.bind(minimum_height=self.profile_list.setter('height'))
        scroll.add_widget(self.profile_list)
        self.profile_container.add_widget(scroll)

        main_layout.add_widget(self.profile_container)

        # Auto-login section
        auto_login_layout = BoxLayout(size_hint_y=0.08, spacing=dp(10))
        self.auto_login_checkbox = CheckBox(size_hint_x=0.1)
        self.auto_login_checkbox.bind(active=self.on_auto_login_changed)
        auto_login_layout.add_widget(self.auto_login_checkbox)

        auto_login_label = Label(
            text="Auto-login with this profile",
            size_hint_x=0.9,
            halign='left',
            valign='middle'
        )
        auto_login_label.bind(size=auto_login_label.setter('text_size'))
        auto_login_layout.add_widget(auto_login_label)
        main_layout.add_widget(auto_login_layout)

        # Load auto-login state
        self.auto_login_checkbox.active = self.config_manager.auto_login_enabled

        # Buttons
        buttons_layout = GridLayout(cols=2, size_hint_y=0.15, spacing=dp(10))

        create_btn = Button(
            text="Create Profile",
            background_color=(0.098, 0.467, 0.949, 1),  # Facebook blue
            font_size=dp(16),
            bold=True
        )
        create_btn.bind(on_press=self.show_create_profile_dialog)
        buttons_layout.add_widget(create_btn)

        delete_btn = Button(
            text="Delete Profile",
            background_color=(0.8, 0.2, 0.2, 1),
            font_size=dp(16),
            bold=True
        )
        delete_btn.bind(on_press=self.delete_profile)
        buttons_layout.add_widget(delete_btn)

        main_layout.add_widget(buttons_layout)

        # Select button
        select_btn = Button(
            text="Select Profile",
            size_hint_y=0.12,
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(18),
            bold=True
        )
        select_btn.bind(on_press=self.select_profile)
        main_layout.add_widget(select_btn)

        self.add_widget(main_layout)

    def _update_bg(self, instance, value):
        """Update background rectangle"""
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def load_profiles(self):
        """Load profiles from profile manager"""
        self.profile_list.clear_widgets()
        profiles = self.controller.list_profiles()

        if not profiles:
            # No profiles message
            no_profiles_label = Label(
                text="No profiles found. Create one to get started!",
                size_hint_y=None,
                height=dp(50),
                color=(0.7, 0.7, 0.7, 1)
            )
            self.profile_list.add_widget(no_profiles_label)
            return

        # Add profile buttons
        for profile in profiles:
            profile_btn = Button(
                text=profile.name,
                size_hint_y=None,
                height=dp(60),
                background_color=(0.2, 0.2, 0.2, 1),
                font_size=dp(16)
            )
            profile_btn.bind(on_press=lambda x, p=profile: self.on_profile_selected(p))
            self.profile_list.add_widget(profile_btn)

    def on_profile_selected(self, profile):
        """Handle profile selection"""
        self.selected_profile = profile

        # Highlight selected profile
        for child in self.profile_list.children:
            if isinstance(child, Button):
                if child.text == profile.name:
                    child.background_color = (0.898, 0.035, 0.078, 1)
                else:
                    child.background_color = (0.2, 0.2, 0.2, 1)

    def select_profile(self, instance):
        """Select profile and navigate to channels"""
        if not self.selected_profile:
            error_popup = Popup(
                title='Error',
                content=Label(text='Please select a profile first'),
                size_hint=(0.7, 0.3)
            )
            error_popup.open()
            return

        # Load profile data
        try:
            self.controller.select_profile(self.selected_profile.name)

            # Save last active profile
            if self.auto_login_checkbox.active:
                self.config_manager.last_active_profile_id = self.selected_profile.name

            # Navigate to channels screen
            App.get_running_app().switch_screen('channels')
        except Exception as e:
            error_popup = Popup(
                title='Error',
                content=Label(text=f'Failed to load profile: {str(e)}'),
                size_hint=(0.8, 0.3)
            )
            error_popup.open()

    def show_create_profile_dialog(self, instance):
        """Show create profile dialog"""
        popup = CreateProfilePopup(on_create_callback=self.create_profile)
        popup.open()

    def create_profile(self, name, url):
        """Create a new profile"""
        try:
            self.controller.create_profile(name, url)
            self.load_profiles()

            # Show success message
            success_popup = Popup(
                title='Success',
                content=Label(text=f'Profile "{name}" created successfully!'),
                size_hint=(0.7, 0.3)
            )
            success_popup.open()
        except Exception as e:
            error_popup = Popup(
                title='Error',
                content=Label(text=f'Failed to create profile: {str(e)}'),
                size_hint=(0.8, 0.3)
            )
            error_popup.open()

    def delete_profile(self, instance):
        """Delete selected profile"""
        if not self.selected_profile:
            error_popup = Popup(
                title='Error',
                content=Label(text='Please select a profile to delete'),
                size_hint=(0.7, 0.3)
            )
            error_popup.open()
            return

        # Confirmation popup
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=f'Delete profile "{self.selected_profile.name}"?'))

        buttons = BoxLayout(spacing=dp(10))
        yes_btn = Button(text='Yes', background_color=(0.8, 0.2, 0.2, 1))
        no_btn = Button(text='No', background_color=(0.3, 0.3, 0.3, 1))
        buttons.add_widget(yes_btn)
        buttons.add_widget(no_btn)
        content.add_widget(buttons)

        confirm_popup = Popup(
            title='Confirm Delete',
            content=content,
            size_hint=(0.7, 0.3)
        )

        def do_delete(instance):
            try:
                self.controller.delete_profile(self.selected_profile.name)
                self.selected_profile = None
                self.load_profiles()
                confirm_popup.dismiss()
            except Exception as e:
                error_popup = Popup(
                    title='Error',
                    content=Label(text=f'Failed to delete profile: {str(e)}'),
                    size_hint=(0.8, 0.3)
                )
                error_popup.open()

        yes_btn.bind(on_press=do_delete)
        no_btn.bind(on_press=confirm_popup.dismiss)
        confirm_popup.open()

    def on_auto_login_changed(self, checkbox, value):
        """Handle auto-login checkbox change"""
        self.config_manager.auto_login_enabled = value
