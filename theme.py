from talon import skia, app
import os
import random
from .utils import hex_to_ints

semantic_directory = os.path.dirname(os.path.abspath(__file__))

# Contains all the values related to styling ( images, colours etc )
class HeadUpDisplayTheme:

    name = ''
    image_dict = {}
    audio_dict = {}
    values = {}
    theme_dir = ''

    def __init__(self, theme_name, theme_dir=None):
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
        if (os.path.exists(theme_config_file)):
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
                    self.image_dict[filename[:filename_len - 4]] = skia.Image.from_file(abspath)
            
        # Load in the audio available in the theme directory
        audio_dir = os.path.join(theme_dir, "audio")
        if os.path.exists(audio_dir) and os.path.isdir(audio_dir):
            audio_files = os.listdir(audio_dir)
            for index, filename in enumerate(audio_files):
                abspath = os.path.join(audio_dir, filename)
                if (filename.endswith(".wav")):
                    filename_len = len(filename)
                    self.audio_dict[filename[:filename_len - 4]] = abspath
                    
                # Randomized audio cues are possible too
                elif os.path.isdir(abspath):
                    options = []
                    subfiles = os.listdir(abspath)
                    for subindex, subfilename in enumerate(subfiles):
                        if (subfilename.endswith(".wav")):
                            filename_len = len(filename)
                            options.append(os.path.join(abspath, subfilename))
                    
                    if len(options) > 0:
                        self.audio_dict[filename] = options

    def get_image(self, image_name, width = None, height = None):
        full_image_name = image_name
        if width is not None:
            full_image_name += "w" + str(width)
        if height is not None:
            full_image_name += "h" + str(height)
    
        # Use cached full image name
        if (full_image_name in self.image_dict):
            return self.image_dict[full_image_name]
            
        # Scale existing image in our cache
        elif (image_name in self.image_dict and full_image_name not in self.image_dict):
            image = self.image_dict[image_name]
            self.image_dict[full_image_name] = self.resize_image(image, width, height)
            return self.image_dict[full_image_name]
            
        # Load the image from the file system
        else:
            # Load in images from other directories
            if "/" in image_name or "\\" in image_name:
                if os.path.isfile(image_name):
                    image_name_len = len(image_name)
                    self.image_dict[image_name] = skia.Image.from_file(image_name)
                    if full_image_name != image_name:
                        return self.get_image(image_name, width, height)
                    else:
                        return self.image_dict[image_name]
            return None

    def get_audio_path(self, filename, default=""):
        if filename in self.audio_dict:
            if isinstance(self.audio_dict[filename], list):
                random_audio_index = random.randint(0, len(self.audio_dict[filename]) - 1)
                return self.audio_dict[filename][random_audio_index]
            else:
                return self.audio_dict[filename]
        else:
            return default

    def resize_image(self, image, width, height):
        aspect_ratio = image.width / image.height
        
        # Resize only if the image width is larger than the given width
        if width is None or image.width < width:
            width = image.width
            
        # Resize only if the image height is larger than the given height
        if height is None or image.height < height:
            height = image.height
            
        width = max(width, 1)
        height = max(height, 1)
        
        # Preserve the aspect ratio of the image at all costs using the smallest dimension to work from
        new_aspect_ratio = width / height
        if new_aspect_ratio > aspect_ratio:
            height = image.width * aspect_ratio
        elif new_aspect_ratio < aspect_ratio:
            width = image.height / aspect_ratio
        
        return image.reshape(int(width), int(height))

    def get_colour(self, colour, default_colour="000000"):
        if (colour in self.values):
            return self.values[colour]
        else:
            return default_colour

    def get_opacity(self, opacity_name, default_opacity=1.0):
        if (opacity_name in self.values):
            return int( float(self.values[opacity_name]) * 255 )
        else:
            return int(default_opacity * 255)
            
    def get_float_value(self, name, default_value=1.0):
        if (name in self.values):
            return float(self.values[name])
        else:
            return default_value
            
    def get_int_value(self, name, default_value=1):
        if (name in self.values):
            return int(self.values[name])
        else:
            return default_value
            
    def get_colour_as_ints(self, colour):
        return hex_to_ints(self.get_colour(colour))