
#    █▀▀▀               ▄   █▀▀▀                              █▀▀▀▄         ▄   █
#    █▄▄   ▄▀▀▄  █▀▀▄  ▀█▀  █▄▄   ▄▀▀▄  █▄▀  ▄▀▀█  ▄▀▀▄       █   █  █  █  ▀█▀  █▀▀▄  ▄▀▀▄  █▀▀▄
#    █     █  █  █  █   █   █     █  █  █    █  █  █▄▄█       █▀▀▀   █  █   █   █  █  █  █  █  █
#    █     ▀▄▄▀  █  █   ▀▄  █     ▀▄▄▀  █    ▀▄▄█  ▀▄▄        █      ▀▄▄█   ▀▄  █  █  ▀▄▄▀  █  █
#                                             ▄▄▀                     ▄▄▀
# This file is run with the Python distribution that's bundled with FontForge.

import sys
import os
import json
import uuid
import datetime


#              ▄                                           ▄    ▀
# ▄▀▀▄  ▄▀▀▄  ▀█▀       █▀▀▄  █▄▀  ▄▀▀▄  █▀▀▄  ▄▀▀▄  █▄▀  ▀█▀  ▀█  ▄▀▀▄  ▄▀▀▄
#  ▀▄   █▄▄█   █        █  █  █    █  █  █  █  █▄▄█  █     █    █  █▄▄█   ▀▄
# ▀▄▄▀  ▀▄▄    ▀▄       █▄▄▀  █    ▀▄▄▀  █▄▄▀  ▀▄▄   █     ▀▄   █  ▀▄▄   ▀▄▄▀
#                       █                █

def set_properties(font, cli_args, version_major, version_minor, version_patch):
        """Set metadata of the font."""
        sfnt_names = {}
        lang = "English (US)" # `sfnt_names` are stored under the language
        fontname = cli_args.get("filename", "Untitled")
        family = cli_args.get("family", None) or fontname
        style = "Regular"
        designer = cli_args.get("designer", "jan pi toki pona")
        license = cli_args.get("license", "All rights reserved")
        licenseurl = cli_args.get("licenseurl", "")

        font.familyname = fontname
        font.fontname = fontname + "-" + style
        font.fullname = fontname + " " + style
        font.encoding = "UnicodeFull"

        # OS/2 fields - https://learn.microsoft.com/en-us/typography/opentype/spec/os2
        #             - https://fontforge.org/docs/scripting/python/fontforge.html#fontforge.font.os2_codepages
        font.os2_vendor = "SPFM"

        font.os2_typoascent_add  = False # "Is Offset" checkbox in FontForge
        font.os2_typodescent_add = False
        font.os2_typolinegap     = 0
        font.hhea_ascent_add     = False
        font.hhea_descent_add    = False
        font.hhea_linegap        = 0

        pixel = cli_args.get("pixel") or False
        if version_major < 4 and not pixel: # apply the new metrics to pixel fonts retroactively, to combat blurring
            font.ascent  = 800
            font.descent = 200
            font.os2_typoascent  = 1050
            font.os2_typodescent = -450
            font.hhea_ascent     = 1050
            font.hhea_descent    = -450
            font.uwidth = 62.5          # underline thickness is 1/16em
            font.upos   = -200 - 62.5/2 # positioned outside of, and touching, the em square
        else:
            font.ascent  = 875
            font.descent = 125
            font.os2_typoascent  = 1125 
            font.os2_typodescent = -375
            font.hhea_ascent     = 1125
            font.hhea_descent    = -375
            font.uwidth = 62.5
            font.upos   = -125 - 62.5/2

        # String fields built-in to the ffpython API: ['Copyright', 'Family', 'UniqueID', 'Fullname', 'Version', 'PostScriptName', 'License', 'License URL']
        sfnt_names["Family"] = family
        sfnt_names["Fullname"] = family + " " + style
        sfnt_names["PostScriptName"] = family.replace(" ", "-") + "-" + style
        sfnt_names["SubFamily"] = style
        sfnt_names["Designer"] = designer
        sfnt_names["Copyright"] = "(C) Copyright " + designer + ", " + str(datetime.datetime.now().year)
        sfnt_names["License"] = license
        sfnt_names["License URL"] = licenseurl
        if license == "ofl":
            sfnt_names["License"] = "SIL Open Font License, Version 1.1"
            sfnt_names["License URL"] = "https://openfontlicense.org"
        if license == "cc0":
            sfnt_names["License"] = "CC0 1.0 Universal"
            sfnt_names["License URL"] = "https://creativecommons.org/publicdomain/zero/1.0/"
        if license == "arr":
            sfnt_names["License"] = "All rights reserved"

        # Numbered fields - https://learn.microsoft.com/en-us/typography/opentype/spec/name
        # 8: Manufacturer
        sfnt_names[8] = "SP Font Maker - https://wasokeli.github.io/sp-font-maker"
        # 11: Vendor URL
        sfnt_names[11] = "https://wasokeli.github.io/sp-font-maker"

        # probably best to omit this, so that the generated binaries are actually comparable
        # ...actually fontforge stores a modification date in the `FFTM` and `head` tables, so i'd need to figure out how to get rid of those anyway
        sfnt_names["UniqueID"] = family + " " + str(uuid.uuid4())

        for k, v in sfnt_names.items():
            font.appendSFNTName(str(lang), k, v)









    #          █     █             █              █
    #  ▀▀▄  ▄▀▀█  ▄▀▀█       ▄▀▀█  █  █  █  █▀▀▄  █▀▀▄  ▄▀▀▄
    # ▄▀▀█  █  █  █  █       █  █  █  █  █  █  █  █  █   ▀▄
    # ▀▄▄█  ▀▄▄█  ▀▄▄█       ▀▄▄█  █  ▀▄▄█  █▄▄▀  █  █  ▀▄▄▀
    #                         ▄▄▀      ▄▄▀  █

def add_glyphs(font, config, cli_args, debug_dir, version_major, version_minor, version_patch):
        """Read and add SVG images as glyphs to the font.

        Walks through the provided directory and uses each ord(character).svg file
        as glyph for the character. Then using the provided config, set the font
        parameters and export TTF and SFD, without ligatures yet, to debug_dir.

        Parameters
        ----------
        debug_dir : str
            Path to directory with SVGs to be converted.
        """

        # print("Note: If you leave a glyph blank, you'll get a FontForge error like \"I'm")
        # print("      sorry this file is too complex for me to understand (or is erroneous)\".")
        # print("      It's fine, the font still works!")

        import psMat
        for glyph_object in config["glyphs-fancy"] + config["glyphs"]["ligature-base-glyphs"]:
            if 'name' in glyph_object:
                name = glyph_object['name']
                if 'codepoint' in glyph_object:
                    cp = glyph_object['codepoint']
                else:
                    cp = 0

                # Create character glyph
                if cp == 0:
                    g = font.createChar(-1, name)
                else:
                    g = font.createChar(cp, name)

                # Get outlines
                src = "{}/{}.svg".format(name, name)
                src = debug_dir + os.sep + src

                # importOutlines() will print FontForge errors for blank glyphs.
                # Prepend what glyph they refer to.
                print("", end=("\r" + (" " + name + " ").ljust(11, " ") + " - "))
                g.importOutlines(src, ("removeoverlap", "correctdir"))
                g.removeOverlap()

                if version_major <3:
                    # SHEET VERSION 2 metrics, before scaling (BS) up so that the glyph is the full em height
                    # the 8x10gu SVG is scaled to .8x1em, with padding on the sides to make it 1x1em square.
                    # in sv2, the imported SVG spans -200 to 800 vertically.
                    bs_scan_hor_padding = 50
                    bs_glyph_wh = 700
                else:
                    # SHEET VERSION 3 metrics, before scaling (BS) up so that the glyph is the full em height
                    # the 6x8gu SVG is scaled to .75x1em, with padding on the sides to make it 1x1em square.
                    # in sv3, the imported SVG spans -200 to 800 vertically.
                    # in sv4, the imported SVG spans -125 to 875 vertically.
                    bs_scan_hor_padding = 125
                    bs_glyph_wh = 500

                # shift by the left margin, to remove the squaring padding.
                g.transform(psMat.translate(-bs_scan_hor_padding, 0))

                def debug_metrics(word_to_debug, note=""):
                    if name == word_to_debug:
                        print("\n", g.width, g.vwidth)
                        bottom = g.boundingBox()[1] # these numbers talk about the glyph that's actually drawn
                        top    = g.boundingBox()[3] # so i can manipulate them with drawing
                        print(
                            note,
                            "top", int(top),
                            "bottom", int(bottom),
                            "sum", int(top-bottom)
                        )

                # debug_metrics("aTok", "before scaling")

                pixel = cli_args.get("pixel") or False





                # SCALING

                # Scale everything up so that the glyphs are 1em tall, instead of the cartouches
                # The scaling center is the baseline, far left

                # move glyphs to where rescaling happens:
                # the left side of the glyph, at the height of the baseline
                if version_major < 4 and not pixel:
                    g.transform(psMat.translate(
                        -bs_glyph_wh / 2,
                        200-500 # 200 is the descent. 500 is half the glyph's height.
                    ))
                else:
                    g.transform(psMat.translate(
                        -bs_glyph_wh / 2,
                        125-500 # 125 is the descent. 500 is half the glyph's height.
                    ))

                g.transform(psMat.scale(1 / bs_glyph_wh * 1000)) # divide by the SAFE area height; multiply by the SCAN area height
                
                if version_major < 4 and not pixel:
                    g.transform(psMat.translate(
                        500, 
                        500-200
                    ))
                else:
                    g.transform(psMat.translate(
                        500, 
                        500-125
                    ))

                g.width = 1000
                g.vwidth = 1000





                # create rotated glyphs

                rotated_glyph_set = [g] # later we'll iterate through these to generate `.top` and `.bottom` versions
                if 'rotate' in glyph_object:
                    def rotate(flip, degrees_ccw, suffix):
                        rotated_glyph = font.createChar(-1, name + suffix)
                        font.selection.select(g)
                        font.copy()
                        font.selection.select(rotated_glyph)
                        font.paste()
                        rotated_glyph_set.append(rotated_glyph)

                        to_center_x = -500
                        if version_major < 4 and not pixel:
                            to_center_y = -500 + 200
                        else:
                            to_center_y = -500 + 125

                        if pixel:
                            # For pixel fonts, rotate around the assumed center pixel,
                            # with assumed 1px space between glyphs.
                            pixel_size = config.get("pixel-size", 8)
                            if pixel_size % 4 == 0:
                                # If the em size is a multiple of 4, then the total scan width is even. 
                                # Normal case. Assume that there's 1px empty space on the right.
                                to_center_x = -1000/pixel_size * (pixel_size-1)/2
                            else:
                                # If the total scan width is *odd*, then we've arbitrarily chosen to put the
                                # extra 1px padding on the left, balancing out the 1px empty space on the right.
                                # Happens with 6px and 10px fonts. 
                                # Weird case. Assume that the glyph is perfectly centered.
                                to_center_x = -1000/pixel_size * pixel_size/2
                            # Regardless, the vertical scan area is even, so we assume
                            # there's 1px empty space on the bottom.
                            to_center_y = -1000/pixel_size * (pixel_size+1)/2 + 125

                        rotated_glyph.transform(psMat.translate(to_center_x, to_center_y))
                        if flip:
                            rotated_glyph.transform(psMat.scale(-1, 1))
                        import math
                        rotated_glyph.transform(psMat.rotate(degrees_ccw /360 *math.pi*2))
                        rotated_glyph.transform(psMat.translate(-to_center_x, -to_center_y))

                    if 'direction' in glyph_object:
                        if glyph_object['direction'] == 'up':     # akesi, pipi
                            rotate(False,  45, ".NW")
                            rotate(False,  90, ".W")
                            rotate(False, 135, ".SW")
                            rotate(False, 180, ".S")
                            rotate(False, 225, ".SE")
                            rotate(False, 270, ".E")
                            rotate(False, 315, ".NE")
                        elif glyph_object['direction'] == 'down': # ni
                            rotate(False,  45, ".SE")
                            rotate(False,  90, ".E")
                            rotate(False, 135, ".NE")
                            rotate(False, 180, ".N")
                            rotate(False, 225, ".NW")
                            rotate(False, 270, ".W")
                            rotate(False, 315, ".SW")
                        elif glyph_object['direction'] == 'left': # theoretically si
                            rotate(False,  45, ".SW")             #                i
                            rotate(False,  90, ".S")              #                ilapa, spoon moku, dab epiku
                            rotate(True,  315, ".SE")
                            rotate(True,    0, ".E")
                            rotate(True,   45, ".NE")
                            rotate(False, 270, ".N")
                            rotate(False, 315, ".NW")
                        # right. redundant with the below.
                        else:                                     # kala, kijetesantakalu, soweli, waso
                            rotate(False,  45, ".NE")
                            rotate(False,  90, ".N")
                            rotate(True,  315, ".NW")
                            rotate(True,    0, ".W")
                            rotate(True,   45, ".SW")
                            rotate(False, 270, ".S")
                            rotate(False, 315, ".SE")
                    # if direction isn't specified, then assume 'right'
                    else:                                         # kala, kijetesantakalu, soweli, waso
                        rotate(False,  45, ".NE")
                        rotate(False,  90, ".N")
                        rotate(True,  315, ".NW")
                        rotate(True,    0, ".W")
                        rotate(True,   45, ".SW")
                        rotate(False, 270, ".S")
                        rotate(False, 315, ".SE")





                # Center glyphs (including, but not limited to, rotated ones)
                for g in rotated_glyph_set:

                    # Horizontally center sitelen pona, middot, colon, letters
                    # Do NOT center cartouches, long pi, te/to, (period?)
                    if not (
                        cp == 0xf1990 or cp == 0x5b or   # cartouche start
                        cp == 0xf1991 or cp == 0x5d or   # cartouche end
                        cp == 0xf1992 or cp == 0x5f or   # cartouche middle
                        cp == 0x300c or                  # te (open quote)
                        cp == 0x300d                     # to (close quote)
                        # or cp == 0xf199c or cp == 0x2e   # period
                        # or cp == 0xf199d or cp == 0x3a   # colon
                    ):                
                        if not pixel:
                            left  = g.boundingBox()[0]
                            right = g.boundingBox()[2]
                            width = right - left
                            g.transform(psMat.translate(
                                -right + width/2 + 500,
                                0
                            ))

                    # Vertically center sitelen pona, middot, colon
                    # Do NOT center a-z, cartouches, long pi, te/to, (period?)
                    if not (
                        (0x41 <= cp <= 0x5a              # A-Z
                            and cp != 0x41                   # A
                            and cp != 0x45                   # E
                            and cp != 0x4e                   # N
                            and cp != 0x4f) or               # O
                        (0x61 <= cp <= 0x7a              # a-z
                            and cp != 0x61                   # a
                            and cp != 0x65                   # e
                            and cp != 0x6e                   # n
                            and cp != 0x6f) or               # o
                        cp == 0xf1990 or cp == 0x5b or   # cartouche start
                        cp == 0xf1991 or cp == 0x5d or   # cartouche end
                        cp == 0xf1992 or cp == 0x5f or   # cartouche middle
                        cp == 0x300c or                  # te (open quote)
                        cp == 0x300d                     # to (close quote)
                        # or cp == 0xf199c or cp == 0x2e   # period
                    ):
                        if not pixel:
                            bottom = g.boundingBox()[1]
                            top    = g.boundingBox()[3]
                            g.transform(psMat.translate(
                                0, 
                                font.ascent - top - ((font.ascent + font.descent) - (top - bottom)) / 2
                            ))

                    g.width = 1000
                    g.vwidth = 1000




                # Create stacking glyphs (including rotated ones)
                for glyph in rotated_glyph_set:
                    stacking = False
                    if 'ligature' in glyph_object:
                        if (name != "cartoucheStartTok" and
                            name != "cartoucheEndTok" and
                            name != "middotTok" and
                            name != "colonTok" and
                            name != "teTok" and
                            name != "toTok"
                        ):
                            stacking = True
                            g_bottom = font.createChar(-1, glyph.glyphname + ".bottom")
                            g_top    = font.createChar(-1, glyph.glyphname + ".top")

                    if stacking:
                        font.selection.select(glyph)
                        font.copy()
                        font.selection.select(g_bottom, g_top)
                        font.paste()
                        g_bottom.width = 1000
                        g_bottom.vwidth = 1000
                        g_top   .width = 0
                        g_top   .vwidth = 1000
                        if version_major < 4 and not pixel:
                            # move up, so that the origin is in the bottom left
                            g_bottom.transform(psMat.translate(0, 200))
                            g_top   .transform(psMat.translate(0, 200))
                            # scale down to 4:3
                            g_bottom.transform(psMat.scale(1, 0.75))
                            g_top   .transform(psMat.scale(1, 0.75))
                            # reposition
                            g_bottom.transform(psMat.translate(0,    -250 - 200))
                            g_top   .transform(psMat.translate(-1000, 500 - 200))
                        else:
                            # move up, so that the origin is in the bottom left
                            g_bottom.transform(psMat.translate(0, 125))
                            g_top   .transform(psMat.translate(0, 125))
                            # scale down to 4:3
                            g_bottom.transform(psMat.scale(1, 0.75))
                            g_top   .transform(psMat.scale(1, 0.75))
                            # reposition
                            g_bottom.transform(psMat.translate(0,    -250 - 125))
                            g_top   .transform(psMat.translate(-1000, 500 - 125))



                        

        # get rid of stray metrics
        print("\r                                                ")

        # originally 800x1000, minus 50 margin on each side for scanning margin
        # ...though the vertical situation might be more complicated?
        for glyph in font:
            # self.font[glyph].width = 700
            # self.font[glyph].vwidth = 900  # used in vertical writing. might need to revise
            # self.font[glyph].width = 1000
            # self.font[glyph].vwidth = 1000  # used in vertical writing. might need to revise
            pass

            # # Test centering
            # g = self.font[glyph]
            # # "If the glyph is not in the font’s encoding then a number will be returned beyond the encoding size (or in some cases -1 will be returned)."
            # # https://fontforge.org/docs/scripting/python/fontforge.html#fontforge.glyph.encoding
            # if 0 < g.encoding < 0x110000:
            #     cp = g.encoding
            # else:
            #     cp = 0
            # print(chr(cp), g.glyphname.ljust(9), "- " \
            # #     -50ish                             750ish
            #       "left",   int(g.boundingBox()[0]), "right", int(g.boundingBox()[2]), \
            # #     -200ish                            800ish
            #       "bottom", int(g.boundingBox()[1]), "top",   int(g.boundingBox()[3]))

        # combining cartouche extension (the middle of the cartouche)
        font[0xf1992].width = 0
        font[0xf1992].transform(psMat.translate(-1000, 0))
        font[0x5f].width = 0
        font[0x5f].transform(psMat.translate(-1000, 0))



        # later i should move these into default.json
        #   - this would facilitate the overriding that's happening in cli.py#L104-L119

        # support default ASCII ligatures
        pipe = font.createChar(ord("|"), "pipe")
        pipe.width = 1000
        space = font.createChar(ord(" "), "space")
        space.width = 0
        hyphen = font.createChar(ord("-"), "hyphen")
        hyphen.width = 0
        for number, name in enumerate(["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]):
            digit = font.createChar(ord(str(number)), name)
            digit.width = 0
        north = font.createChar(ord("^"), "north") # todo: replace these three, and `v`, with rotated lili. it would be cute i think
        north.width = 1000
        west = font.createChar(ord("<"), "west")
        west.width = 1000
        east = font.createChar(ord(">"), "east")
        east.width = 1000

        # fallback for unsupported SP features
        plus = font.createChar(ord("+"), "plus")
        plus.width = 0
        ampersand = font.createChar(ord("&"), "ampersand")
        ampersand.width = 0
        opencurly = font.createChar(ord("{"), "opencurly")
        opencurly.width = 0
        closecurly = font.createChar(ord("}"), "closecurly")
        closecurly.width = 0
        openparen = font.createChar(ord("("), "openparen")
        openparen.width = 0
        closeparen = font.createChar(ord(")"), "closeparen")
        closeparen.width = 0
        slash = font.createChar(ord("*"), "asterisk")
        slash.width = 1000
        slash = font.createChar(ord('"'), 'doublequote')
        slash.width = 1000
        comma = font.createChar(ord(","), "comma")
        comma.width = 1000
        slash = font.createChar(ord("'"), "singlequote")
        slash.width = 1000

        # fallback for text intended as sitelen Lasina
        bang = font.createChar(ord("!"), "exclamation")
        bang.width = 1000
        question = font.createChar(ord("?"), "question")
        question.width = 1000
        semicolon = font.createChar(ord(";"), "semicolon")
        semicolon.width = 1000

        # UCSUR features
        ideographic_space = font.createChar(ord("　"), "ideographicspace")
        ideographic_space.width = 1000
        zero_width = font.createChar(0x200b, "zerowidth")
        zero_width.width = 0
        sp_stacking_joiner = font.createChar(0xf1995, "stackJoinTok")
        sp_stacking_joiner.width = 0

        # fallback for unsupported UCSUR features
        sp_scaling_joiner = font.createChar(0xf1996, "nestJoinTok")
        sp_scaling_joiner.width = 0
        zerowidthjoiner = font.createChar(0x200d, "zerowidthjoiner")
        zerowidthjoiner.width = 0
        sp_start_of_long_glyph = font.createChar(0xf1997)
        sp_start_of_long_glyph.width = 0
        sp_end_of_long_glyph = font.createChar(0xf1998)
        sp_end_of_long_glyph.width = 0
        sp_combining_long_glyph_extension = font.createChar(0xf1999)
        sp_combining_long_glyph_extension.width = 0
        sp_start_of_reverse_long_glyph = font.createChar(0xf199a)
        sp_start_of_reverse_long_glyph.width = 0
        sp_end_of_reverse_long_glyph = font.createChar(0xf199b)
        sp_end_of_reverse_long_glyph.width = 0
        # todo: add "start of long pi" as an additional codepoint for the "pi" glyph
        # todo: then add "end of long pi" here









    #                                    ▄               ▄▀▀              ▄         ▄▀▀  ▀  █
    # ▄▀▀█  ▄▀▀▄  █▀▀▄  ▄▀▀▄  █▄▀  ▀▀▄  ▀█▀  ▄▀▀▄       ▀█▀  ▄▀▀▄  █▀▀▄  ▀█▀       ▀█▀  ▀█  █  ▄▀▀▄
    # █  █  █▄▄█  █  █  █▄▄█  █   ▄▀▀█   █   █▄▄█        █   █  █  █  █   █         █    █  █  █▄▄█
    # ▀▄▄█  ▀▄▄   █  █  ▀▄▄   █   ▀▄▄█   ▀▄  ▀▄▄         █   ▀▄▄▀  █  █   ▀▄        █    █  █  ▀▄▄
    #  ▄▄▀

def generate_font_file(font, filename, out_dir, default_json, debug_dir):
        """Output TTF file.

        Additionally checks for multiple outputs and duplicates.

        Parameters
        ----------
        filename : str
            Output filename.
        out_dir : str
            Path to output directory.
        default_json : str
            Path to config file.
        """
        if filename is None:
            raise NameError("filename not found in config file.")

        outfile = str(
            debug_dir
            + os.sep
            # + (filename + ".ttf" if not filename.endswith(".ttf") else filename)
            + (filename + " without ligatures.ttf")
        )

        # while os.path.exists(outfile):
        #     outfile = os.path.splitext(outfile)[0] + " (1).ttf"

        # Generate font, but without ligatures yet, to temporary directory
        # sys.stderr.write("\nCreating %s\n" % outfile)
        font.generate(outfile)
        font.save(outfile[0:-4] + ".sfd")









    #                                      ▄                        ▀
    # ▄▀▀▄  ▄▀▀▄  █▀▀▄  █   █  ▄▀▀▄  █▄▀  ▀█▀         █▀▄▀▄   ▀▀▄  ▀█  █▀▀▄
    # █     █  █  █  █   █ █   █▄▄█  █     █          █ █ █  ▄▀▀█   █  █  █
    # ▀▄▄▀  ▀▄▄▀  █  █    █    ▀▄▄   █     ▀▄         █ █ █  ▀▄▄█   █  █  █
    #                                         ▄▄▄▄▄▄▄
def convert_main(default_json, debug_dir, out_dir, cli_args, v_major, v_minor, v_patch):
        try:
            font = fontforge.font()
        except:
            import fontforge
            import psMat

        with open(default_json) as f:
            config = json.load(f)
        cli_args_dict = json.loads(cli_args) or {}

        font = fontforge.font()
        set_properties(font, cli_args_dict, int(v_major), int(v_minor), int(v_patch))
        add_glyphs(font, config, cli_args_dict, debug_dir, int(v_major), int(v_minor), int(v_patch))

        # Generate font and save as a .ttf file
        filename = cli_args_dict.get("filename", "Untitled")
        generate_font_file(font, str(filename), out_dir, default_json, debug_dir)


if __name__ == "__main__":
    if len(sys.argv) != 8:
        raise ValueError("Incorrect call to SVGtoTTF")
    convert_main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
