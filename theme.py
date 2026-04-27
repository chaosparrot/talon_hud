from talon import skia, app
from talon import ui
import os
import random
import re
from .utils import hex_to_ints
import logging

semantic_directory = os.path.dirname(os.path.abspath(__file__))

# Contains all the values related to styling ( images, colours etc )
class HeadUpDisplayTheme:

    name = ''
    image_dict = None
    template_dict = None    
    values = None
    colours = None
    theme_dir = ''

    def __init__(self, theme_name, theme_dir=None):
        self.image_dict = {}
        self.template_dict = {}        
        self.values = {}
        self.colours = {}
    
        self.name = theme_name
        base_theme_dir = os.path.join(os.path.join(semantic_directory, "themes"), "_base_theme")
        if theme_dir is None:
            theme_dir = os.path.join(os.path.join(semantic_directory, "themes"), theme_name)
        self.theme_dir = theme_dir
        
        # Cascade the theme values by first loading in the base theme
        self.load_dir(base_theme_dir)
        
        # Here, override the base theme values
        self.load_dir(theme_dir)
    
    # Get a list of the directories to watch for changes
    def get_watch_directories(self) -> list[str]:
        base_dir = os.path.join(os.path.join(semantic_directory, "themes"), "_base_theme")
        directories = [base_dir]        
        if self.theme_dir != base_dir:
            directories.append(self.theme_dir)
        
        return directories
                
    def load_dir(self, theme_dir):
        theme_config_file = theme_dir + "/theme.csv"
        if os.path.exists(theme_config_file):
            fh = open(theme_config_file, "r")
            lines = fh.readlines()
            for index,line in enumerate(lines):
                split_line = line.strip("\n").split(",")
                self.values[split_line[0]] = split_line[1]
            fh.close()

        # Load in the images available in the theme directory
        images_dir = os.path.join(theme_dir, "images")
        if os.path.exists(images_dir) and os.path.isdir(images_dir):
            image_files = os.listdir(images_dir)
            for index, filename in enumerate(image_files):
                abspath = os.path.join(images_dir, filename)
                if (filename.endswith(".png")):
                    filename_len = len(filename)
                    self.register_image(filename[:filename_len - 4], skia.Image.from_file(abspath))

        # Load in the templates available in the theme directory
        template_dir = os.path.join(theme_dir, "templates")
        if os.path.exists(template_dir) and os.path.isdir(template_dir):
            template_files = os.listdir(template_dir)
            for index, filename in enumerate(template_files):
                abspath = os.path.join(template_dir, filename)
                if (filename.endswith(".html")):
                    filename_len = len(filename)
                    with open(abspath) as template:
                        self.template_dict[filename[:filename_len - 5]] = template.read()

    def register_image(self, filename, image):
        image_name, image_scale = self.split_image_name_and_scale(filename)

        if image_name not in self.image_dict:
            self.image_dict[image_name] = {}

        if image_scale not in self.image_dict[image_name]:
            self.image_dict[image_name][image_scale] = image

    def split_image_name_and_scale(self, filename):
        match = re.search(r"(.+)@([1-3])x$", filename)
        if match is None:
            return filename, 1

        image_name = match.group(1)
        image_scale = int(match.group(2))
        return image_name, image_scale

    def _resolve_image_variant(self, image_name, target_scale=None):
        if not image_name:
            return None, None

        variants = self.image_dict.get(image_name)
        if variants:
            if target_scale is None:
                image_scale = min(variants)
            else:
                try:
                    image_scale = min(k for k in variants if k >= target_scale)
                except ValueError:
                    image_scale = max(variants)

            return variants[image_scale], image_scale

        else:
            # Load in images from other directories
            if "/" in image_name or "\\" in image_name:
                if os.path.isfile(image_name):
                    image = skia.Image.from_file(image_name)
                    self.register_image(image_name, image)
                    return self.get_image_and_scale(image_name, target_scale)

            return None, None

    def get_image(self, image_name):
        image, _ = self._resolve_image_variant(image_name)
        return image

    def get_image_and_scale(self, image_name, target_scale):
        image, image_scale = self._resolve_image_variant(image_name, target_scale)
        return image, image_scale

    def get_dimensions(self, image, image_scale, width=None, height=None):
        image_width = image.width / image_scale
        image_height = image.height / image_scale
        aspect_ratio = image_width / image_height

        # Resize only if the image width is larger than the given width
        if width is None or image_width < width:
            width = image_width

        # Resize only if the image height is larger than the given height
        if height is None or image_height < height:
            height = image_height

        width = max(width, 1)
        height = max(height, 1)

        # Preserve the aspect ratio of the image at all costs using the smallest dimension to work from
        new_aspect_ratio = width / height
        if new_aspect_ratio > aspect_ratio:
            height = image_width * aspect_ratio
        elif new_aspect_ratio < aspect_ratio:
            width = image_height / aspect_ratio

        return width, height

    def get_scale_for_coord(self, point_x, point_y):
        try:
            screen = ui.screen_containing(point_x, point_y)
        # Can't get screen if the coordinates are off screen (e.g. -10, 82)
        except ValueError:
            screen = ui.main_screen()

        return screen.scale

    def get_template(self, template_name):
        if template_name in self.template_dict:
            return self.template_dict[template_name]

        # Load the template from the file system
        else:
            # Load in templates from other directories
            if "/" in template_name or "\\" in template_name:
                if os.path.isfile(template_name):
                    with open(template_name) as file:
                        self.template_dict[template_name] = file.read()
                    return self.template_dict[template_name]
            return None

    def get_colour(self, colour, default_colour="000000"):
        if colour in self.colours:
            return self.colours[colour]
        else:
            if colour in self.values:
                colour_value = self.values[colour]
                if colour_value.startswith("#"):
                    colour_value = colour_value.replace("#", "")                
                if len(colour_value) != 6 and len(colour_value) != 8:
                    logging.warning( "Talon HUD - " + colour + " has an invalid colour value of " + colour_value + ", using default " + default_colour)                    
                    colour_value = default_colour
                self.colours[colour] = colour_value
            else:
                self.colours[colour] = default_colour
            return self.colours[colour]

    def get_opacity(self, opacity_name, default_opacity=1.0):
        if opacity_name in self.values:
            return int( float(self.values[opacity_name]) * 255 )
        else:
            return int(default_opacity * 255)
            
    def get_float_value(self, name, default_value=1.0):
        if name in self.values:
            return float(self.values[name])
        else:
            return default_value
            
    def get_int_value(self, name, default_value=1):
        if name in self.values:
            return int(self.values[name])
        else:
            return default_value
            
    def get_colour_as_ints(self, colour):
        return hex_to_ints(self.get_colour(colour))
