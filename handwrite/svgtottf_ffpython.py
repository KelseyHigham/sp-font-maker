
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


class SVGtoTTF:

     #              ▄                                           ▄    ▀
     # ▄▀▀▄  ▄▀▀▄  ▀█▀       █▀▀▄  █▄▀  ▄▀▀▄  █▀▀▄  ▄▀▀▄  █▄▀  ▀█▀  ▀█  ▄▀▀▄  ▄▀▀▄
     #  ▀▄   █▄▄█   █        █  █  █    █  █  █  █  █▄▄█  █     █    █  █▄▄█   ▀▄
     # ▀▄▄▀  ▀▄▄    ▀▄       █▄▄▀  █    ▀▄▄▀  █▄▄▀  ▀▄▄   █     ▀▄   █  ▀▄▄   ▀▄▄▀
     #                       █                █

    def set_properties(self, version_major, version_minor, version_patch):
        """Set metadata of the font from config."""
        props = self.config["props"]
        sfnt_names = self.config["sfnt_names"]
        lang = props.get("lang", "English (US)")
        fontname = self.cli_args.get("filename", None) or props.get(
            "filename", "Example"
        )
        family = self.cli_args.get("family", None) or fontname
        style = props.get("style", "Regular")
        designer = self.cli_args.get("designer", None) or props.get("designer", "jan pi toki pona")
        license = self.cli_args.get("license", None) or sfnt_names.get("License", "All rights reserved")
        licenseurl = self.cli_args.get("licenseurl", None) or sfnt_names.get("License URL", "")

        self.font.familyname = fontname
        self.font.fontname = fontname + "-" + style
        self.font.fullname = fontname + " " + style
        self.font.encoding = props.get("encoding", "UnicodeFull")

        # OS/2 fields - https://learn.microsoft.com/en-us/typography/opentype/spec/os2
        #             - https://fontforge.org/docs/scripting/python/fontforge.html#fontforge.font.os2_codepages
        self.font.os2_vendor = "SPFM"

        self.font.os2_typoascent_add  = False # "Is Offset" checkbox in FontForge
        self.font.os2_typodescent_add = False
        self.font.os2_typolinegap     = 0
        self.font.hhea_ascent_add     = False
        self.font.hhea_descent_add    = False
        self.font.hhea_linegap        = 0

        pixel = self.cli_args.get("pixel") or False
        if version_major < 4 and not pixel: # apply the new metrics to pixel fonts retroactively, to combat blurring
            self.font.ascent  = 800
            self.font.descent = 200
            self.font.os2_typoascent  = 1050
            self.font.os2_typodescent = -450
            self.font.hhea_ascent     = 1050
            self.font.hhea_descent    = -450
            self.font.uwidth = 62.5          # underline thickness is 1/16em
            self.font.upos   = -200 - 62.5/2 # positioned outside of, and touching, the em square
        else:
            self.font.ascent  = 875
            self.font.descent = 125
            self.font.os2_typoascent  = 1125 
            self.font.os2_typodescent = -375
            self.font.hhea_ascent     = 1125
            self.font.hhea_descent    = -375
            self.font.uwidth = 62.5
            self.font.upos   = -125 - 62.5/2
        for k, v in props.items():
            if hasattr(self.font, k):
                if isinstance(v, list):
                    v = tuple(v)
                setattr(self.font, k, v)

        # replace default.json values with CLI-provided values
        if self.config.get("sfnt_names", None):
            # String fields built-in to the ffpython API: ['Copyright', 'Family', 'UniqueID', 'Fullname', 'Version', 'PostScriptName', 'License', 'License URL']
            self.config["sfnt_names"]["Family"] = family
            self.config["sfnt_names"]["Fullname"] = family + " " + style
            self.config["sfnt_names"]["PostScriptName"] = family.replace(" ", "-") + "-" + style
            self.config["sfnt_names"]["SubFamily"] = style
            self.config["sfnt_names"]["Designer"] = designer
            self.config["sfnt_names"]["Copyright"] = "(C) Copyright " + designer + ", " + str(datetime.datetime.now().year)
            self.config["sfnt_names"]["License"] = license
            self.config["sfnt_names"]["License URL"] = licenseurl
            if license == "ofl":
                self.config["sfnt_names"]["License"] = "SIL Open Font License, Version 1.1"
                self.config["sfnt_names"]["License URL"] = "https://openfontlicense.org"
            if license == "cc0":
                self.config["sfnt_names"]["License"] = "CC0 1.0 Universal"
                self.config["sfnt_names"]["License URL"] = "https://creativecommons.org/publicdomain/zero/1.0/"
            if license == "arr":
                self.config["sfnt_names"]["License"] = "All rights reserved"

            # Numbered fields - https://learn.microsoft.com/en-us/typography/opentype/spec/name
            # 8: Manufacturer
            self.config["sfnt_names"][8] = "SP Font Maker - https://wasokeli.github.io/sp-font-maker"
            # 11: Vendor URL
            self.config["sfnt_names"][11] = "https://wasokeli.github.io/sp-font-maker"

        self.config["sfnt_names"]["UniqueID"] = family + " " + str(uuid.uuid4())

        for k, v in self.config.get("sfnt_names", {}).items():
            self.font.appendSFNTName(str(lang), k, v)









    #          █     █             █              █
    #  ▀▀▄  ▄▀▀█  ▄▀▀█       ▄▀▀█  █  █  █  █▀▀▄  █▀▀▄  ▄▀▀▄
    # ▄▀▀█  █  █  █  █       █  █  █  █  █  █  █  █  █   ▀▄
    # ▀▄▄█  ▀▄▄█  ▀▄▄█       ▀▄▄█  █  ▀▄▄█  █▄▄▀  █  █  ▀▄▄▀
    #                         ▄▄▀      ▄▄▀  █

    def add_glyphs(self, debug_dir, version_major, version_minor, version_patch):
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
        for glyph_object in self.config["glyphs-fancy"]:
            if 'name' in glyph_object:
                name = glyph_object['name']
                if 'codepoint' in glyph_object:
                    cp = int(glyph_object['codepoint'], 16)
                else:
                    cp = 0

                # Create character glyph
                if cp == 0:
                    g = self.font.createChar(-1, name)
                else:
                    g = self.font.createChar(cp, name)

                # Create stacking glyphs
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
                        g_bottom = self.font.createChar(-1, name + ".bottom")
                        g_top    = self.font.createChar(-1, name + ".top")

                # Get outlines
                src = "{}/{}.svg".format(name, name)
                src = debug_dir + os.sep + src

                # importOutlines() will print FontForge errors for blank glyphs.
                # Prepend what glyph they refer to.
                print("", end=("\r" + (" " + name + " ").ljust(11, " ") + " - "))
                g.importOutlines(src, ("removeoverlap", "correctdir"))
                g.removeOverlap()
                if stacking:
                    print("", end=("\r" + (" " + name + "-").ljust(11, " ") + " - "))
                    g_bottom.importOutlines(src, ("removeoverlap", "correctdir"))
                    g_bottom.removeOverlap()
                    print("", end=("\r" + ("-" + name + " ").ljust(11, " ") + " - "))
                    g_top   .importOutlines(src, ("removeoverlap", "correctdir"))
                    g_top   .removeOverlap()

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
                if stacking:
                    g_bottom.transform(psMat.translate(-bs_scan_hor_padding, 0))
                    g_top   .transform(psMat.translate(-bs_scan_hor_padding, 0))

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

                pixel = self.cli_args.get("pixel") or False

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
                            self.font.ascent - top - ((self.font.ascent + self.font.descent) - (top - bottom)) / 2
                        ))
                        if stacking:
                            bottom = g_bottom.boundingBox()[1]
                            top    = g_bottom.boundingBox()[3]
                            g_bottom.transform(psMat.translate(0, self.font.ascent - top - ((self.font.ascent + self.font.descent) - (top - bottom)) / 2))
                            bottom = g_top   .boundingBox()[1]
                            top    = g_top   .boundingBox()[3]
                            g_top   .transform(psMat.translate(0, self.font.ascent - top - ((self.font.ascent + self.font.descent) - (top - bottom)) / 2))
                        pass

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
                            bs_glyph_wh - right - (bs_glyph_wh - width) / 2, 
                            0
                        ))
                        if stacking:
                            left  = g_bottom.boundingBox()[0]
                            right = g_bottom.boundingBox()[2]
                            width = right - left
                            g_bottom.transform(psMat.translate(bs_glyph_wh - right - (bs_glyph_wh - width) / 2, 0))
                            left  = g_top   .boundingBox()[0]
                            right = g_top   .boundingBox()[2]
                            width = right - left
                            g_top   .transform(psMat.translate(bs_glyph_wh - right - (bs_glyph_wh - width) / 2, 0))
                        pass

                # Scale everything up so that the glyphs are 1em tall, instead of the cartouches
                # The scaling center is the baseline, far left

                # move glyphs to where rescaling happens:
                # the left side of the glyph, at the height of the baseline
                if version_major < 4 and not pixel:
                    g.transform(psMat.translate(
                        -bs_glyph_wh / 2,
                        200-500 # 200 is the descent. 500 is half the glyph's height.
                    ))
                    if stacking:
                        g_bottom.transform(psMat.translate(-bs_glyph_wh / 2, 200-500))
                        g_top   .transform(psMat.translate(-bs_glyph_wh / 2, 200-500))
                else:
                    g.transform(psMat.translate(
                        -bs_glyph_wh / 2,
                        125-500 # 125 is the descent. 500 is half the glyph's height.
                    ))
                    if stacking:
                        g_bottom.transform(psMat.translate(-bs_glyph_wh / 2, 125-500))
                        g_top   .transform(psMat.translate(-bs_glyph_wh / 2, 125-500))


                g.transform(psMat.scale(1 / bs_glyph_wh * 1000)) # divide by the SAFE area height; multiply by the SCAN area height
                if stacking:
                    g_bottom.transform(psMat.scale(1 / bs_glyph_wh * 1000))
                    g_top   .transform(psMat.scale(1 / bs_glyph_wh * 1000))
                
                if version_major < 4 and not pixel:
                    g.transform(psMat.translate(
                        500, 
                        500-200
                    ))
                    if stacking:
                        g_bottom.transform(psMat.translate(500, 500-200))
                        g_top   .transform(psMat.translate(500, 500-200))
                else:
                    g.transform(psMat.translate(
                        500, 
                        500-125
                    ))
                    if stacking:
                        g_bottom.transform(psMat.translate(500, 500-125))
                        g_top   .transform(psMat.translate(500, 500-125))

                g.width = 1000
                g.vwidth = 1000
                if stacking:
                    # everything above is to keep g, g_bottom, and g_top in sync.
                        # we may be able to clean up the code by just duplicating g at the end.
                    # now, we finally move g_bottom and g_top into place.
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
        for glyph in self.font:
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
        self.font[0xf1992].width = 0
        self.font[0xf1992].transform(psMat.translate(-1000, 0))
        self.font[0x5f].width = 0
        self.font[0x5f].transform(psMat.translate(-1000, 0))

        # later i should move these into default.json
        #   - this would facilitate the overriding that's happening in cli.py#L104-L119
        # spaces
        ideographic_space = self.font.createChar(ord("　"), "ideographicspace")
        ideographic_space.width = 1000
        pipe = self.font.createChar(ord("|"), "pipe")
        pipe.width = 1000
        space = self.font.createChar(ord(" "), "space")
        space.width = 0
        zero_width = self.font.createChar(0x200b, "zerowidth")
        zero_width.width = 0

        # other zero-width
        bang = self.font.createChar(ord("!"), "exclamation")
        bang.width = 1000
        comma = self.font.createChar(ord(","), "comma")
        comma.width = 1000
        question = self.font.createChar(ord("?"), "question")
        question.width = 1000
        semicolon = self.font.createChar(ord(";"), "semicolon")
        semicolon.width = 1000
        hyphen = self.font.createChar(ord("-"), "hyphen")
        hyphen.width = 0
        plus = self.font.createChar(ord("+"), "plus")
        plus.width = 0
        ampersand = self.font.createChar(ord("&"), "ampersand")
        ampersand.width = 0
        opencurly = self.font.createChar(ord("{"), "opencurly")
        opencurly.width = 0
        closecurly = self.font.createChar(ord("}"), "closecurly")
        closecurly.width = 0
        openparen = self.font.createChar(ord("("), "openparen")
        openparen.width = 0
        closeparen = self.font.createChar(ord(")"), "closeparen")
        closeparen.width = 0
        for number, name in enumerate(["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]):
            digit = self.font.createChar(ord(str(number)), name)
            digit.width = 0

        # not zero-width
        slash = self.font.createChar(ord("*"), "asterisk")
        slash.width = 1000
        slash = self.font.createChar(ord('"'), 'doublequote')
        slash.width = 1000
        slash = self.font.createChar(ord("'"), "singlequote")
        slash.width = 1000
        # todo: replace these with rotated lili. it would be cute i think
        north = self.font.createChar(ord("^"), "north")
        north.width = 1000
        west = self.font.createChar(ord("<"), "west")
        west.width = 1000
        east = self.font.createChar(ord(">"), "east")
        east.width = 1000

        # todo: add "start of long pi" as an additional codepoint for the "pi" glyph
        # todo: then add "end of long pi" here
        sp_stacking_joiner = self.font.createChar(0xf1995, "stackJoinTok")
        sp_stacking_joiner.width = 0
        sp_scaling_joiner = self.font.createChar(0xf1996, "nestJoinTok")
        sp_scaling_joiner.width = 0
        zerowidthjoiner = self.font.createChar(0x200d, "zerowidthjoiner")
        zerowidthjoiner.width = 0
        sp_start_of_long_glyph = self.font.createChar(0xf1997)
        sp_start_of_long_glyph.width = 0
        sp_end_of_long_glyph = self.font.createChar(0xf1998)
        sp_end_of_long_glyph.width = 0
        sp_combining_long_glyph_extension = self.font.createChar(0xf1999)
        sp_combining_long_glyph_extension.width = 0
        sp_start_of_reverse_long_glyph = self.font.createChar(0xf199a)
        sp_start_of_reverse_long_glyph.width = 0
        sp_end_of_reverse_long_glyph = self.font.createChar(0xf199b)
        sp_end_of_reverse_long_glyph.width = 0









    #                                    ▄               ▄▀▀              ▄         ▄▀▀  ▀  █
    # ▄▀▀█  ▄▀▀▄  █▀▀▄  ▄▀▀▄  █▄▀  ▀▀▄  ▀█▀  ▄▀▀▄       ▀█▀  ▄▀▀▄  █▀▀▄  ▀█▀       ▀█▀  ▀█  █  ▄▀▀▄
    # █  █  █▄▄█  █  █  █▄▄█  █   ▄▀▀█   █   █▄▄█        █   █  █  █  █   █         █    █  █  █▄▄█
    # ▀▄▄█  ▀▄▄   █  █  ▀▄▄   █   ▀▄▄█   ▀▄  ▀▄▄         █   ▀▄▄▀  █  █   ▀▄        █    █  █  ▀▄▄
    #  ▄▄▀

    def generate_font_file(self, filename, out_dir, default_json, debug_dir):
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
        self.font.generate(outfile)
        self.font.save(outfile[0:-4] + ".sfd")









    #                                      ▄                        ▀
    # ▄▀▀▄  ▄▀▀▄  █▀▀▄  █   █  ▄▀▀▄  █▄▀  ▀█▀         █▀▄▀▄   ▀▀▄  ▀█  █▀▀▄
    # █     █  █  █  █   █ █   █▄▄█  █     █          █ █ █  ▄▀▀█   █  █  █
    # ▀▄▄▀  ▀▄▄▀  █  █    █    ▀▄▄   █     ▀▄         █ █ █  ▀▄▄█   █  █  █
    #                                         ▄▄▄▄▄▄▄
    def convert_main(self, default_json, debug_dir, out_dir, cli_args, v_major, v_minor, v_patch):
        try:
            self.font = fontforge.font()
        except:
            import fontforge
            import psMat

        with open(default_json) as f:
            self.config = json.load(f)
        self.cli_args = json.loads(cli_args) or {}

        self.font = fontforge.font()
        self.set_properties(int(v_major), int(v_minor), int(v_patch))
        self.add_glyphs(debug_dir, int(v_major), int(v_minor), int(v_patch))

        # Generate font and save as a .ttf file
        filename = self.cli_args.get("filename", None) or self.config["props"].get(
            "filename", None
        )
        self.generate_font_file(str(filename), out_dir, default_json, debug_dir)


if __name__ == "__main__":
    if len(sys.argv) != 8:
        raise ValueError("Incorrect call to SVGtoTTF")
    SVGtoTTF().convert_main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
