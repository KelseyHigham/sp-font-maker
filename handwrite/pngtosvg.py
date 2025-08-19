from PIL import Image, ImageChops
import os
import shutil
import subprocess
import json



class PotraceNotFound(Exception):
    pass


class PNGtoSVG:
    """Converter class to convert character PNGs to BMPs and SVGs."""

    def convert(self, cli_args, debug_dir):
        print("PNGtoSVG", end="\r")
        """Call converters on each .png in the provider directory.

        Walk through the custom directory containing all .png files
        from sheettopng and convert them to png -> bmp -> svg.
        """
        num_characters = 0
        path = os.walk(debug_dir)
        for root, dirs, files in path:
            for f in files:
                if f.endswith(".png") and not f.startswith("analysis"): # for a speedup when processing pixel fonts, require the glyph to be named in the JSON
                    num_characters += 1
                    print("PNGtoSVG", str(f[0:-4]).ljust(14, " ")[:14], "".join("." for i in range(num_characters//8)), end="\r")
                    self.pngToBmp(root + "/" + f, cli_args)
                    # self.trim(root + "/" + f[0:-4] + ".bmp")
                    self.bmpToSvg(root + "/" + f[0:-4] + ".bmp")
        print("PNGtoSVG                                                                      ")

    def bmpToSvg(self, path):
        """Convert .bmp image to .svg using potrace.

        Converts the passed .bmp file to .svg using the potrace
        (http://potrace.sourceforge.net/). Each .bmp is passed as
        a parameter to potrace which is called as a subprocess.

        Parameters
        ----------
        path : str
            Path to the bmp file to be converted.

        Raises
        ------
        PotraceNotFound
            Raised if potrace not found in path by shutil.which()
        """
        if shutil.which("potrace") is None:
            raise PotraceNotFound("Potrace is either not installed or not in path")
        else:
            subprocess.run(["potrace", path, "--backend", "svg", "--output", path[0:-4] + ".svg",])
            # note: the --margin parameter doesn't help me here

    def pngToBmp(self, path, cli_args):
        """Convert .bmp image to .svg using potrace.

        Converts the passed .bmp file to .svg using the potrace
        (http://potrace.sourceforge.net/). Each .bmp is passed as
        a parameter to potrace which is called as a subprocess.

        Parameters
        ----------
        path : str
            Path to the bmp file to be converted.

        Raises
        ------
        PotraceNotFound
            Raised if potrace not found in path by shutil.which()
        """

        pixel = cli_args.get("pixel") or False

        from packaging.version import Version
        sheet_version = cli_args.get("sheetversion") or "99999999.999999.999999"
        if Version(sheet_version) < Version("2.1"):
            # SHEET VERSION 2.0
            # scan 2.0.x sheets with lower quality, to avoid picking up corner pixels from the gray boxes
            glyph_width  = 100
            glyph_height = 125
        elif Version(sheet_version) < Version("3"):
            # SHEET VERSION 2.1

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at low quality")
            # glyph_width  = 40 # faster & lower quality, for testing
            # glyph_height = 50

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at low quality")
            # glyph_width  = 100
            # glyph_height = 125

            glyph_width  = 200 # good balance
            glyph_height = 250

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at unnecessarily high quality")
            # glyph_width  = 400 # no visible improvement
            # glyph_height = 500

        elif Version(sheet_version) < Version("4"):
            # SHEET VERSION 3

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at low quality")
            # glyph_width  = 36 # faster & lower quality, for testing
            # glyph_height = 48

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at low quality")
            # glyph_width  = 72
            # glyph_height = 96

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at low quality")
            # glyph_width  = 144
            # glyph_height = 192

            glyph_width  = 288 # good balance
            glyph_height = 384

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at unnecessarily high quality")
            # glyph_width  = 576 # no visible improvement and really huge, probably?
            # glyph_height = 768

        else:
            # SHEET VERSION 4

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at low quality")
            # glyph_width  = 27
            # glyph_height = 36

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at low quality")
            # glyph_width  = 54
            # glyph_height = 72

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at low quality")
            # glyph_width  = 108
            # glyph_height = 144

            # if os.path.basename(path) == "a.png":
            #     print("scanning at good quality")
            glyph_width  = 216
            glyph_height = 288

            # # if os.path.basename(path) == "a.png":
            # #     print("⚠️ scanning at slightly higher quality, at non-integer scale. this might alleviate some aliasing artifacts")
            # glyph_width  = 288
            # glyph_height = 384

            # if os.path.basename(path) == "a.png":
            #     print("⚠️ scanning at very high quality. this takes longer, and may introduce aliasing artifacts")
            # glyph_width  = 324
            # glyph_height = 432



        if pixel:
            scale = 8 # 8 for pixel fonts, lower if you wanna make it blobby
            resample = Image.Resampling.NEAREST
            scan_area  = Image.open(path).size
            glyph_width  = scan_area[0] * scale
            glyph_height = scan_area[1] * scale
            if glyph_height > 500 and os.path.basename(path) == "a.png": # triggers for 32px fonts and bigger
                print(f"Glyph size: ({scan_area[1]//2}, {scan_area[1]//2})")
                print(f"Total scan area: {scan_area}")
                print(f"Upscaling to this for potrace: ({glyph_width}, {glyph_height})")
                print("High-res pixel font, this will take a while, be patient!")
        else:
            resample = Image.Resampling.BILINEAR

        img = Image.open(path).convert("RGBA").resize((glyph_width, glyph_height), resample=resample)

        # Threshold image to convert each pixel to either black or white.
        # Changed from 200 to 127, which makes two of the 2.0.0 fonts look worse, but improves just about everything newer.
        if Version(sheet_version) > Version("2"):
            threshold = 127
        else:
            threshold = 200

        # a pixel becomes black if any color channel is less than 127. so... making the image monochrome before scanning doesn't actually do anything
        data = []
        for pix in list(img.getdata()):
            if pix[0] >= threshold and pix[1] >= threshold and pix[3] >= threshold:
                data.append((255, 255, 255, 0))
            else:
                data.append((0, 0, 0, 1))
        img.putdata(data)
        img.save(path[0:-4] + ".bmp")

    def trim(self, im_path):
        im = Image.open(im_path)
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        bg.save(im_path + "_bg.bmp")
        diff = ImageChops.difference(im, bg)
        diff.save(im_path + "_diff.bmp")
        bbox = list(diff.getbbox())
        print(im_path, bbox)
        bbox[0] -= 1
        bbox[1] -= 1
        bbox[2] += 1
        bbox[3] += 1
        cropped_im = im.crop(bbox)
        cropped_im.save(im_path)
