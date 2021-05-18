from talon import skia
import os
from user.talon_hud.utils import hex_to_ints

semantic_directory = os.path.dirname(os.path.abspath(__file__))

# Contains all the values related to styling ( images, colours etc )
class HeadUpDisplayTheme:

    name = ''
    image_dict = {}
    values = {}

    def __init__(self, theme_name):
        self.name = theme_name
        theme_dir = semantic_directory + "/themes/" + theme_name
        theme_config_file = theme_dir + "/theme.csv"
        
        # Load in values from the CSV - Otherwise, error
        if (os.path.exists(theme_config_file)):
            fh = open(theme_config_file, "r")
            lines = fh.readlines()
            for index,line in enumerate(lines):
                split_line = line.strip('\n').split(',')
                self.values[split_line[0]] = split_line[1]
            fh.close()
            
        # Load in the images available in the theme directory
        files = os.listdir(theme_dir)
        for index, filename in enumerate(files):
            if (filename.endswith(".png")):
                filename_len = len(filename)
                self.image_dict[filename[:filename_len - 4]] = skia.Image.from_file(theme_dir + "/" + filename)                

    def get_image(self, image_name):
        if (image_name in self.image_dict):
            return self.image_dict[image_name]
        else:
            return None

    def get_colour(self, colour, default_colour='000000'):
        if (colour in self.values):
            return self.values[colour]
        else:
            return default_colour

    def get_opacity(self, opacity_name, default_opacity=1.0):
        if (opacity_name in self.values):
            return int( float(self.values[opacity_name]) * 255 )
        else:
            return int(default_opacity * 255)
        
    def get_colour_as_ints(self, colour):
        return hex_to_ints(self.get_colour(colour))