import tempfile
import webbrowser
from pathlib import Path
from talon import Module, actions
import os
from .theme import HeadUpDisplayTheme

class HeadUpHtmlGenerator:
    temp_dir = None
    theme = None
    focus_manager = None
    
    def __init__(self, theme: HeadUpDisplayTheme, focus_manager):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.theme = theme
        self.focus_manager = focus_manager

    def set_theme(self, theme: HeadUpDisplayTheme):
        self.theme = theme

    def open_help(self):
        pass

    def open_main(self):
        pass

    def open_widget(self, widget):
        pass

    def markdown_to_html(self, markdown_string: str):
        pass

    def save_template(self, template_filename: str, template_body: str):
        if Path.exists(self.temp_dir):
            abs_path = os.path.join(self.temp_dir, template_filename)
            with open(abs_path, 'w') as file:
                file.write(template_body)

    def open_template(self, template_filename: str, id: str = ''):
        abs_path = os.path.join(self.temp_dir, template_filename)
        if Path.exists(abs_path):
            uri = abs_path + "#" + id if id else abs_path
            webbrowser.open(uri)
    
    def replace_template_vars(self, template_string: str, vars):
        for key in vars:
            template_string = template_string.replace(key, vars[key])
        return template_string