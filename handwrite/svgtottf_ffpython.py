# █▀▀          ▄  █▀▀                    █▀▄      ▄  █
# █▄  ▄▀▄ █▀▄ ▀█▀ █▄  ▄▀▄ █▄▀ ▄▀█ ▄▀▄    █▄▀ █ █ ▀█▀ █▀▄ ▄▀▄ █▀▄
# █   ▀▄▀ █ █  ▀▄ █   ▀▄▀ █   ▀▄█ ▀█▄    █   ▀▄█  ▀▄ █ █ ▀▄▀ █ █
#                             ▄▄▀            ▄▄▀
# This file is run with the Python distribution that's bundled with FontForge.

import datetime
import json
import math
import os
import re
import sys

import fontforge
import psMat

#          ▄                              ▄  ▀
# ▄▀▀ ▄▀▄ ▀█▀    █▀▄ █▄▀ ▄▀▄ █▀▄ ▄▀▄ █▄▀ ▀█▀ █ ▄▀▄ ▄▀▀
# ▄█▀ ▀█▄  ▀▄    █▄▀ █   ▀▄▀ █▄▀ ▀█▄ █    ▀▄ █ ▀█▄ ▄█▀
#                █           █


def set_properties(font, cli_args, version_major, version_minor, version_patch):
    """Set metadata of the font."""
    sfnt_names = {}
    lang = "English (US)"  # `sfnt_names` are stored under the language
    fontname = cli_args.get("filename", "Untitled")
    family = cli_args.get("family", None) or fontname
    style = "Regular"
    designer = cli_args.get("designer", "jan pi toki pona")
    license = cli_args.get("license", "All rights reserved")
    licenseurl = cli_args.get("license_url", "")

    font.familyname = fontname
    font.fontname = fontname + "-" + style
    font.fullname = fontname + " " + style
    font.encoding = "UnicodeFull"

    # OS/2 fields - https://learn.microsoft.com/en-us/typography/opentype/spec/os2
    #             - https://fontforge.org/docs/scripting/python/fontforge.html#fontforge.font.os2_codepages
    font.os2_vendor = "SPFM"

    font.os2_typoascent_add = False  # "Is Offset" checkbox in FontForge
    font.os2_typodescent_add = False
    font.os2_typolinegap = 0
    font.hhea_ascent_add = False
    font.hhea_descent_add = False
    font.hhea_linegap = 0
    font.hasvmetrics = 1

    pixel = cli_args.get("pixel") or False
    # Apply the new metrics to pixel fonts retroactively, to combat blurring.
    if version_major < 4 and not pixel:
        font.ascent = 800
        font.descent = 200
        font.os2_typoascent = 1050
        font.os2_typodescent = -450
        font.hhea_ascent = 1050
        font.hhea_descent = -450
        # Underline thickness is 1/16em.
        font.uwidth = 62.5
        # Underline is positioned outside of, and touching, the em square.
        font.upos = -200 - 62.5 / 2
    else:
        font.ascent = 875
        font.descent = 125
        font.os2_typoascent = 1125
        font.os2_typodescent = -375
        font.hhea_ascent = 1125
        font.hhea_descent = -375
        font.uwidth = 62.5
        font.upos = -125 - 62.5 / 2

    # String fields built-in to the ffpython API: ['Copyright', 'Family', 'UniqueID',
    # 'Fullname', 'Version', 'PostScriptName', 'License', 'License URL']
    sfnt_names["Family"] = family
    sfnt_names["Fullname"] = family + " " + style
    sfnt_names["PostScriptName"] = family.replace(" ", "-") + "-" + style
    sfnt_names["SubFamily"] = style
    sfnt_names["Designer"] = designer
    sfnt_names["Copyright"] = (
        "(C) Copyright " + designer + ", " + str(datetime.datetime.now().year)
    )
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

    for k, v in sfnt_names.items():
        font.appendSFNTName(str(lang), k, v)


#       █   █        █         █
# ▄▀█ ▄▀█ ▄▀█    ▄▀█ █ █ █ █▀▄ █▀▄ ▄▀▀
# ▀▄█ ▀▄█ ▀▄█    ▀▄█ █ ▀▄█ █▄▀ █ █ ▄█▀
#                ▄▄▀   ▄▄▀ █


def add_glyphs(
    font, config, cli_args, debug_dir, version_major, version_minor, version_patch
):
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
    default_glyphs = config.get("glyphs", {}).get("sheet", [])
    generated_glyphs = config.get("glyphs", {}).get("derived", [])
    ligature_base_glyphs = config.get("glyphs", {}).get("copies", [])
    for glyph_object in default_glyphs + generated_glyphs + ligature_base_glyphs:
        if "name" in glyph_object:

            #  ▄▄  ▄▄  ▄▄  ▄▄ ▄█▄  ▄▄
            # █   █   █▄▀ █ █  █  █▄▀
            #  ▀▀ ▀    ▀▀  ▀▀  ▀▀  ▀▀

            name = glyph_object["name"]
            if "codepoint" in glyph_object:
                cp = glyph_object["codepoint"]
            else:
                cp = 0

            # Create character glyph
            if cp == 0:
                g = font.createChar(-1, name)
            else:
                g = font.createChar(cp, name)

            # Get glyph outlines from SVG.
            src = "{}/{}.svg".format(name, name)
            src = debug_dir + os.sep + src
            # importOutlines() will print FontForge errors for blank glyphs.
            # Prepend what glyph they refer to.
            print("", end=("\r" + (" " + name + " ").ljust(11, " ") + " - "))
            g.importOutlines(src, ("removeoverlap", "correctdir"))
            g.removeOverlap()

            #  ▄▄  ▄▄  ▄▄ █  ▄▄
            # ▀▄▄ █   █ █ █ █▄▀
            # ▀▀   ▀▀  ▀▀ ▀  ▀▀

            if version_major < 3:
                # SHEET VERSION 2 metrics, before scaling (BS) up so that the glyph is
                # the full em height.
                # The 8x10gu SVG is scaled to .8x1em, with padding on the sides to make
                # it 1x1em square.
                # In sv2, the imported SVG spans -200 to 800 vertically.
                bs_scan_hor_padding = 50
                bs_glyph_wh = 700
            else:
                # SHEET VERSION 3 metrics, before scaling (BS) up so that the glyph is
                # the full em height.
                # The 6x8gu SVG is scaled to .75x1em, with padding on the sides to make
                # it 1x1em square.
                # In sv3, the imported SVG spans -200 to 800 vertically.
                # In sv4, the imported SVG spans -125 to 875 vertically.
                bs_scan_hor_padding = 125
                bs_glyph_wh = 500

            # Shift by the left margin, to remove the squaring padding.
            g.transform(psMat.translate(-bs_scan_hor_padding, 0))

            def debug_metrics(word_to_debug, note=""):
                if name == word_to_debug:
                    print("\n", g.width, g.vwidth)
                    # These numbers talk about the illustration itself, so "." will be
                    # smaller than "lipu".
                    bottom = g.boundingBox()[1]
                    top = g.boundingBox()[3]
                    print(
                        note,
                        "top",
                        int(top),
                        "bottom",
                        int(bottom),
                        "sum",
                        int(top - bottom),
                    )

            # debug_metrics("aTok", "before scaling")

            pixel = cli_args.get("pixel") or False

            # SCALING

            # Scale everything up so that the glyphs are 1em tall, instead of the
            # cartouches.
            # The scaling center is the baseline, far left.

            # Move glyphs to where rescaling happens: the left side of the glyph, at the
            # height of the baseline.
            if version_major < 4 and not pixel:
                # 200 is the descent. 500 is half the glyph's height.
                g.transform(psMat.translate(-bs_glyph_wh / 2, 200 - 500))
            else:
                # 125 is the descent. 500 is half the glyph's height.
                g.transform(psMat.translate(-bs_glyph_wh / 2, 125 - 500))

            # Divide by the SAFE area height; multiply by the SCAN area height.
            g.transform(psMat.scale(1 / bs_glyph_wh * 1000))

            if version_major < 4 and not pixel:
                g.transform(psMat.translate(500, 500 - 200))
            else:
                g.transform(psMat.translate(500, 500 - 125))

            #  ▄▄  ▄▄  ▄▄ ▄▄        ▄▄ █▄  ▀ ▄▀ ▄█▄
            # ▀▄▄ █   █ █ █ █ ▀▀▀▀ ▀▄▄ █ █ █ █▀  █
            # ▀▀   ▀▀  ▀▀ ▀ ▀      ▀▀  ▀ ▀ ▀ ▀   ▀▀

            pixel_size = config.get("pixel-size", 8)

            if "scan-shift" in glyph_object:
                if pixel:
                    scan_shift_x = math.ceil(glyph_object["scan-shift"][0] * pixel_size)
                    scan_shift_x = int(scan_shift_x / pixel_size * 1000)
                    scan_shift_y = math.ceil(glyph_object["scan-shift"][1] * pixel_size)
                    scan_shift_y = int(scan_shift_y / pixel_size * 1000)
                else:
                    scan_shift_x = int(glyph_object["scan-shift"][0] * 1000)
                    if version_major < 3:
                        scan_shift_x *= 0.25
                    scan_shift_y = int(glyph_object["scan-shift"][1] * 1000)
                g.transform(psMat.translate(scan_shift_x, scan_shift_y))

            g.width = int(glyph_object.get("width", 1.0) * 1000)
            g.vwidth = int(glyph_object.get("height", 1.0) * 1000)

            #  ▄▄  ▄▄  ▄▄  ▄▄ ▄█▄  ▄▄     ▄▄  ▄  ▄█▄  ▄▄ ▄█▄ ▀  ▄  ▄▄   ▄▄
            # █   █   █▄▀ █ █  █  █▄▀    █   █ █  █  █ █  █  █ █ █ █ █ ▀▄▄
            #  ▀▀ ▀    ▀▀  ▀▀  ▀▀  ▀▀    ▀    ▀   ▀▀  ▀▀  ▀▀ ▀  ▀  ▀ ▀ ▀▀

            to_center_x = -500
            if version_major < 4 and not pixel:
                to_center_y = -500 + 200
            else:  # new handwritten, or any pixel
                to_center_y = -500 + 125

            if pixel:
                # For pixel fonts, rotate around the assumed center pixel,
                # with assumed 1px space between glyphs.
                pixel_size = config.get("pixel-size", 8)
                if pixel_size % 4 == 0:
                    # If the em size is a multiple of 4, then the total scan
                    # width is even.
                    # Normal case. Assume that there's 1px empty space on the
                    # right.
                    to_center_x = -1000 / pixel_size * (pixel_size - 1) / 2
                    if name == "aTok":
                        # print("to_center_x", to_center_x, "to_center_y", to_center_y)
                        pass
                else:
                    # If the total scan width is *odd*, then we've arbitrarily
                    # chosen to put the extra 1px padding on the left, balancing
                    # out the 1px empty space on the right.
                    # Happens with 6px and 10px fonts.
                    # Weird case. Assume that the glyph is perfectly centered.
                    to_center_x = -1000 / pixel_size * pixel_size / 2
                # Regardless, the vertical scan area is even, so we assume
                # there's 1px empty space on the bottom.
                to_center_y = -1000 / pixel_size * (pixel_size + 1) / 2 + 125

            # Create rotated glyphs.
            # Later we'll iterate through rotated_glyph_set[] to generate `.top` and
            # `.bottom` versions of each orientation.
            rotated_glyph_set = [g]
            if "rotate" in glyph_object:

                def rotate(flip, degrees_ccw, suffix):
                    # Todo: add "name" and "g" as params, then pull this function out to
                    # the top.
                    # ...Uhh also return the rotated glyph, so it can be appended to
                    # rotated_glyph_set.
                    # If we pull *that* out, then it's appropriate to use this to
                    # generate rotated cartouche parts.

                    rotated_glyph = font.createChar(-1, name + suffix)
                    font.selection.select(g)
                    font.copy()
                    font.selection.select(rotated_glyph)
                    font.paste()
                    rotated_glyph_set.append(rotated_glyph)

                    rotated_glyph.transform(psMat.translate(to_center_x, to_center_y))
                    if flip:
                        rotated_glyph.transform(psMat.scale(-1, 1))
                    rotated_glyph.transform(psMat.rotate(degrees_ccw / 360 * math.tau))
                    rotated_glyph.transform(psMat.translate(-to_center_x, -to_center_y))

                direction = glyph_object.get("direction", "right")
                if direction == "up":
                    # akesi, pipi
                    rotate(False, 45, ".NW")
                    rotate(False, 90, ".W")
                    rotate(False, 135, ".SW")
                    rotate(False, 180, ".S")
                    rotate(False, 225, ".SE")
                    rotate(False, 270, ".E")
                    rotate(False, 315, ".NE")
                elif direction == "down":
                    # ni
                    rotate(False, 45, ".SE")
                    rotate(False, 90, ".E")
                    rotate(False, 135, ".NE")
                    rotate(False, 180, ".N")
                    rotate(False, 225, ".NW")
                    rotate(False, 270, ".W")
                    rotate(False, 315, ".SW")
                elif direction == "left":
                    rotate(False, 45, ".SW")
                    rotate(False, 90, ".S")
                    rotate(True, 315, ".SE")
                    rotate(True, 0, ".E")
                    rotate(True, 45, ".NE")
                    rotate(False, 270, ".N")
                    rotate(False, 315, ".NW")
                else:  # right
                    # kala, kijetesantakalu, soweli, waso
                    rotate(False, 45, ".NE")
                    rotate(False, 90, ".N")
                    rotate(True, 315, ".NW")
                    rotate(True, 0, ".W")
                    rotate(True, 45, ".SW")
                    rotate(False, 270, ".S")
                    rotate(False, 315, ".SE")

            #  ▄▄  ▄▄ ▄▄  ▄█▄  ▄▄  ▄▄
            # █   █▄▀ █ █  █  █▄▀ █
            #  ▀▀  ▀▀ ▀ ▀  ▀▀  ▀▀ ▀

            def center_horizontally(g):
                if not pixel:
                    left = g.boundingBox()[0]
                    right = g.boundingBox()[2]
                    width = right - left
                    g.transform(psMat.translate(-right + width / 2 + 500, 0))
                g.width = int(glyph_object.get("width", 1.0) * 1000)
                g.vwidth = int(glyph_object.get("height", 1.0) * 1000)

            def center_vertically(g):
                if not pixel:
                    bottom = g.boundingBox()[1]
                    top = g.boundingBox()[3]
                    g.transform(
                        psMat.translate(
                            0,
                            font.ascent
                            - top
                            - ((font.ascent + font.descent) - (top - bottom)) / 2,
                        )
                    )
                g.width = int(glyph_object.get("width", 1.0) * 1000)
                g.vwidth = int(glyph_object.get("height", 1.0) * 1000)

            # Center glyphs (including, but not limited to, rotated ones)
            for ff_glyph in rotated_glyph_set:
                center = glyph_object.get("center", "both")
                if center == "both" or center == "horizontal":
                    center_horizontally(ff_glyph)
                if center == "both" or center == "vertical":
                    center_vertically(ff_glyph)

            # ▄█▄  ▄▄ █ █ ▄ ▄    ▄▄▄▄   ▄▄  ▄▄ █ ▄  ▄▄
            #  █  █ █ █ █ ▀▄█    █ █ █ █ █ █   ██  ▀▄▄
            #  ▀▀  ▀▀ ▀ ▀ ▄▄▀    ▀ ▀ ▀  ▀▀ ▀   ▀ ▀ ▀▀

            # We need to create duplicate tally marks.

            # We do create duplicate ni rotations in this file, so it's probably okay to
            # create duplicate (rotated!) tallies in this file.

            # However, we can't reference cartoucheMiddleTok to paste it in, because it
            # hasn't been created yet.

            # So, split the "add glyphs" loop up a bit more - adding glyphs on the first
            # loop, duplicating glyphs on the second.

            # Doesn't currently do anything
            if glyph_object.get("type", "") == "combining":
                g.width = 0
                g.vwidth = 0
                g.transform(psMat.translate(-1000, 0))

            if glyph_object.get("type", "") == "tally":
                g.width = 0
                g.vwidth = 0
                g.transform(psMat.translate(-1000, 0))
                tally_name = ""
                if glyph_object.get("name", "") == "commaTok":
                    # Writein
                    tally_name = "commaTok"
                if glyph_object.get("name", "") == "tallyTok":
                    # Default sheet
                    tally_name = "tallyTok"
                if tally_name == "tallyTok" or tally_name == "commaTok":
                    for tally_count in range(16):  # 1--15
                        long_tally_name = "tally" + str(tally_count) + "Tok"  # 1--15
                        g = font.createChar(-1, long_tally_name)

                        # Rotational method

                        angle_between_tallies = math.radians(9)

                        def rotate_tally(angle_to_rotate):
                            # Rotate about the center: `to_center_y`
                            # Rotate about the top of the cartouche: `to_center_y - 750`
                            # Rotate about the top of the next cartouche up: `to_center_y - 2250`
                            g.transform(
                                psMat.translate(1000 + to_center_x, to_center_y - 750)
                            )
                            g.transform(psMat.rotate(angle_to_rotate))
                            g.transform(
                                psMat.translate(-1000 - to_center_x, -to_center_y + 750)
                            )

                        def draw_one_tally():
                            font.selection.select(tally_name)
                            font.copy()
                            font.selection.select(long_tally_name)
                            font.pasteInto()

                        def draw_two_tallies():
                            font.selection.select(tally_name)
                            font.copy()
                            font.selection.select(long_tally_name)
                            rotate_tally(-angle_between_tallies / 2)
                            font.pasteInto()
                            rotate_tally(angle_between_tallies)
                            font.pasteInto()
                            rotate_tally(-angle_between_tallies / 2)

                        def draw_three_tallies():
                            font.selection.select(tally_name)
                            font.copy()
                            font.selection.select(long_tally_name)
                            rotate_tally(-angle_between_tallies)
                            font.pasteInto()
                            rotate_tally(angle_between_tallies)
                            font.pasteInto()
                            rotate_tally(angle_between_tallies)
                            font.pasteInto()
                            rotate_tally(-angle_between_tallies)

                        def draw_four_tallies():
                            font.selection.select(tally_name)
                            font.copy()
                            font.selection.select(long_tally_name)
                            rotate_tally(-angle_between_tallies * 1.5)
                            font.pasteInto()
                            rotate_tally(angle_between_tallies)
                            font.pasteInto()
                            rotate_tally(angle_between_tallies)
                            font.pasteInto()
                            rotate_tally(angle_between_tallies)
                            font.pasteInto()
                            rotate_tally(-angle_between_tallies * 1.5)

                        # # Horizontal method

                        # def draw_one_tally():
                        #     font.selection.select(tally_name)
                        #     font.copy()
                        #     font.selection.select(long_tally_name)
                        #     font.pasteInto()

                        # def draw_two_tallies():
                        #     g.transform(psMat.translate(125, 0))
                        #     font.selection.select(tally_name)
                        #     font.copy()
                        #     font.selection.select(long_tally_name)
                        #     font.pasteInto()
                        #     g.transform(psMat.translate(-250, 0))
                        #     font.pasteInto()
                        #     g.transform(psMat.translate(125, 0))

                        # def draw_three_tallies():
                        #     g.transform(psMat.translate(250, 0))
                        #     font.selection.select(tally_name)
                        #     font.copy()
                        #     font.selection.select(long_tally_name)
                        #     font.pasteInto()
                        #     g.transform(psMat.translate(-250, 0))
                        #     font.pasteInto()
                        #     g.transform(psMat.translate(-250, 0))
                        #     font.pasteInto()
                        #     g.transform(psMat.translate(250, 0))

                        # def draw_four_tallies():
                        #     g.transform(psMat.translate(337, 0))
                        #     font.selection.select(tally_name)
                        #     font.copy()
                        #     font.selection.select(long_tally_name)
                        #     font.pasteInto()
                        #     g.transform(psMat.translate(-225, 0))
                        #     font.pasteInto()
                        #     g.transform(psMat.translate(-225, 0))
                        #     font.pasteInto()
                        #     g.transform(psMat.translate(-225, 0))
                        #     font.pasteInto()
                        #     g.transform(psMat.translate(337, 0))
                        #     total_tally_cells = 1.25

                        # If there are more than 4 tallies, split them into groups of 3

                        total_tally_cells = 1

                        if tally_count == 1:
                            draw_one_tally()

                        elif tally_count == 2:
                            draw_two_tallies()

                        elif tally_count == 3:
                            draw_three_tallies()

                        elif tally_count == 4:
                            draw_four_tallies()

                        else:
                            groups_of_three = tally_count // 3
                            # print(
                            #     "tally_count",
                            #     tally_count,
                            #     "groups_of_three",
                            #     groups_of_three,
                            # )
                            total_tally_cells = groups_of_three
                            remaining_tallies = tally_count - groups_of_three * 3
                            if remaining_tallies > 0:
                                total_tally_cells += 1
                            for current_cell in range(groups_of_three):
                                if "cartoucheMiddleTok" in font:
                                    # print("cartoucheMiddleTok is in font")
                                    font.selection.select("cartoucheMiddleTok")
                                    font.copy()
                                    font.selection.select(long_tally_name)
                                    font.pasteInto()
                                else:
                                    # print("cartoucheMiddleTok is not in font")
                                    pass
                                g.transform(psMat.translate(-1000, 0))
                                draw_three_tallies()
                            if remaining_tallies == 1:
                                g.transform(psMat.translate(-1000, 0))
                                draw_one_tally()
                            if remaining_tallies == 2:
                                g.transform(psMat.translate(-1000, 0))
                                draw_two_tallies()
                            g.transform(
                                psMat.translate(1000 * (total_tally_cells - 1), 0)
                            )
                        g.width = (total_tally_cells - 1) * 1000
                        g.vwidth = g.width
                    # Remove outlines from commaTok and tallyTok, so that they're
                    # invisible outside of cartouches. Inside of cartouches, they're
                    # replaced with tally1Tok, tally2Tok, etc., which are visible.
                    g = font[tally_name]
                    g.clear(1)
                    g.width = 1000
                    g.vwidth = 1000
                    # font.createChar(tally_name)
                    # font.paste()

            #  ▄▄  ▄▄  ▄▄  ▄▄ ▄█▄  ▄▄    ▄▄   ▄▄  ▄▄       ▄▄  ▄  ▄▄▄▄  █▄  ▀ ▄▄   ▄▄  ▄█
            # █   █   █▄▀ █ █  █  █▄▀    █ █ █   █▄▀ ▀▀▀▀ █   █ █ █ █ █ █ █ █ █ █ █▄▀ █ █
            #  ▀▀ ▀    ▀▀  ▀▀  ▀▀  ▀▀    █▀  ▀    ▀▀       ▀▀  ▀  ▀ ▀ ▀ ▀▀  ▀ ▀ ▀  ▀▀  ▀▀

            # Todo: Choose glyphs to pre-combine from default.toml
            # Pre-combine nested lipu+toki
            if glyph_object["name"] == "tokiTok":
                lipu_toki_glyph = font.createChar(-1, "lipuTok_nestJoinTok_tokiTok")
                rotated_glyph_set.append(lipu_toki_glyph)

                font.selection.select("tokiTok")
                font.copy()
                font.selection.select("lipuTok_nestJoinTok_tokiTok")
                font.paste()
                g = font["lipuTok_nestJoinTok_tokiTok"]

                g.transform(psMat.translate(to_center_x, to_center_y))
                g.transform(psMat.scale(1 / 3))
                g.transform(psMat.translate(-to_center_x, -to_center_y))

                font.selection.select("lipuTok")
                font.copy()
                font.selection.select("lipuTok_nestJoinTok_tokiTok")
                font.pasteInto()

                g.width = 1000
                g.vwidth = 1000

            # Todo: Choose glyphs to pre-combine from default.toml
            # Pre-combine two-letter Latin word
            if glyph_object["name"] == "kijetesantakaluTok":
                k_u_glyph = font.createChar(-1, "k_zerowidthjoiner_u")
                rotated_glyph_set.append(k_u_glyph)

                letter_size = 3 / 4
                letter_overlap = (letter_size - 1 / 3) * 1000

                font.selection.select("u")
                font.copy()
                font.selection.select("k_zerowidthjoiner_u")
                font.paste()
                g = font["k_zerowidthjoiner_u"]

                g.transform(psMat.translate(1000 - letter_overlap, 0))

                font.selection.select("k")
                font.copy()
                font.selection.select("k_zerowidthjoiner_u")
                font.pasteInto()

                g.transform(psMat.translate(-(2000 - letter_overlap) / 2 + 500, 0))

                g.transform(psMat.translate(to_center_x, to_center_y))
                g.transform(psMat.scale(3 / 4))
                g.transform(psMat.translate(-to_center_x, -to_center_y))

                center_vertically(g)
                center_horizontally(g)

                g.width = 1000
                g.vwidth = 1000

            # Todo: Choose glyphs to pre-combine from default.toml
            # Pre-combine two-letter Latin word
            if glyph_object["name"] == "kijetesantakaluTok":
                s_u_glyph = font.createChar(-1, "s_zerowidthjoiner_u")
                rotated_glyph_set.append(s_u_glyph)

                letter_size = 3 / 4
                letter_overlap = (letter_size - 1 / 3) * 1000

                font.selection.select("u")
                font.copy()
                font.selection.select("s_zerowidthjoiner_u")
                font.paste()
                g = font["s_zerowidthjoiner_u"]

                g.transform(psMat.translate(1000 - letter_overlap, 0))

                font.selection.select("s")
                font.copy()
                font.selection.select("s_zerowidthjoiner_u")
                font.pasteInto()

                g.transform(psMat.translate(-(2000 - letter_overlap) / 2 + 500, 0))

                g.transform(psMat.translate(to_center_x, to_center_y))
                g.transform(psMat.scale(letter_size))
                g.transform(psMat.translate(-to_center_x, -to_center_y))

                center_vertically(g)
                center_horizontally(g)

                g.width = 1000
                g.vwidth = 1000

            #  ▄▄  ▄▄  ▄▄  ▄▄ ▄█▄  ▄▄     ▄▄ ▄█▄  ▄▄  ▄▄ █ ▄ ▀ ▄▄   ▄▄
            # █   █   █▄▀ █ █  █  █▄▀    ▀▄▄  █  █ █ █   ██  █ █ █ █▄█
            #  ▀▀ ▀    ▀▀  ▀▀  ▀▀  ▀▀    ▀▀   ▀▀  ▀▀  ▀▀ ▀ ▀ ▀ ▀ ▀ ▄▄▀

            # Create stacking glyphs (including rotated ones)
            for glyph in rotated_glyph_set:
                stacking = False
                if glyph_object.get("cartoucheable-stackable", True):
                    stacking = True
                    g_bottom = font.createChar(-1, glyph.glyphname + ".bottom")
                    g_top = font.createChar(-1, glyph.glyphname + ".top")

                if stacking:
                    font.selection.select(glyph)
                    font.copy()
                    font.selection.select(g_bottom, g_top)
                    font.paste()

                    if version_major < 4 and not pixel:
                        descender_height = 200
                    else:
                        descender_height = 125
                    # move up, so that the origin is in the bottom left
                    g_bottom.transform(psMat.translate(0, descender_height))
                    g_top.transform(psMat.translate(0, descender_height))
                    # scale down to 4:3
                    g_bottom.transform(psMat.scale(1, 0.75))
                    g_top.transform(psMat.scale(1, 0.75))
                    # move back down
                    g_bottom.transform(psMat.translate(0, -descender_height))
                    g_top.transform(psMat.translate(0, -descender_height))

                    # position
                    g_bottom.transform(psMat.translate(0, -250))
                    g_top.transform(psMat.translate(-1000, 500))

                    g_bottom.width = 1000
                    g_bottom.vwidth = 1000
                    g_top.width = 0
                    g_top.vwidth = 1000

            #  ▄▄  ▄▄  ▄▄  ▄▄ ▄█▄  ▄▄    █ ▄ ▄ ▄ █ ▄ ▄ ▄▄  ▄ ▄ ▄▀▄   ▄ ▄ ▄  ▄   ▄▄  ▄█
            # █   █   █▄▀ █ █  █  █▄▀    ██  █ █ █ █ █ █ █ █ █ ▄▀▀▄▀ ▀▄▀▄▀ █ █ █   █ █
            #  ▀▀ ▀    ▀▀  ▀▀  ▀▀  ▀▀    ▀ ▀  ▀▀ ▀  ▀▀ █▀   ▀▀  ▀▀ ▀  ▀ ▀   ▀  ▀    ▀▀

            # Create kulupu'd glyphs (including rotated ones)
            for glyph in rotated_glyph_set:
                kulupu = False
                if glyph_object.get("cartoucheable-stackable", True):
                    kulupu = True
                    g_kulupu = font.createChar(
                        -1, "kulupuTok_zerowidthjoiner_" + glyph.glyphname
                    )

                if kulupu:
                    # Draw
                    font.selection.select(glyph)
                    font.copy()
                    font.selection.select(g_kulupu)
                    font.paste()
                    g_kulupu.transform(psMat.translate(-1000, 0))
                    font.pasteInto()
                    g_kulupu.transform(psMat.translate(500, -1000))
                    font.pasteInto()
                    g_kulupu.transform(psMat.translate(500, 1000))

                    # Scale
                    if version_major < 4 and not pixel:
                        descender_height = 200
                    else:
                        descender_height = 125
                    # move up, so that the origin is in the bottom left
                    g_kulupu.transform(psMat.translate(0, descender_height))
                    # scale down to 3:3
                    g_kulupu.transform(psMat.scale(0.75, 0.75))
                    # move back down
                    g_kulupu.transform(psMat.translate(0, -descender_height))

                    # Position
                    g_kulupu.transform(psMat.translate(0, -250))
                    g_kulupu.width = 1500
                    g_kulupu.vwidth = 1500

    # get rid of stray metrics
    print("\r                                                ")

    #  ▄▄  ▄  ▄▄▄▄  █▄  ▀ ▄▄  ▀ ▄▄   ▄▄
    # █   █ █ █ █ █ █ █ █ █ █ █ █ █ █▄█
    #  ▀▀  ▀  ▀ ▀ ▀ ▀▀  ▀ ▀ ▀ ▀ ▀ ▀ ▄▄▀

    # Combining cartouche extension (the middle of the cartouche)
    # This will also apply to long pi
    default_glyphs = config.get("glyphs", {}).get("sheet", [])
    generated_glyphs = config.get("glyphs", {}).get("derived", [])
    ligature_base_glyphs = config.get("glyphs", {}).get("copies", [])
    for glyph_object in default_glyphs + generated_glyphs + ligature_base_glyphs:
        if glyph_object.get("type", "none") == "middle":
            font[glyph_object["name"]].width = 0
            font[glyph_object["name"]].vwidth = 0
            font[glyph_object["name"]].transform(psMat.translate(-1000, 0))

    # Create characters that are rendered as zero-width or ideographic spaces.
    # This includes actual spaces, Latin fallback, placeholders, special characters.
    # Defined in default.toml.
    def create_space(codepoint, name, width):
        if name:
            space = font.createChar(codepoint, name)
        else:
            space = font.createChar(codepoint)
        space.width = int(width * 1000)
        space.vwidth = int(width * 1000)

    spaces = config.get("glyphs", {}).get("spaces", [])
    for space in spaces:
        create_space(
            space.get("codepoint", -1),
            space.get("name", False),
            space.get("width", 1),
        )


#                          ▄         ▄▀          ▄     ▄▀ ▀ █
# ▄▀█ ▄▀▄ █▀▄ ▄▀▄ █▄▀ ▄▀█ ▀█▀ ▄▀▄    █▀ ▄▀▄ █▀▄ ▀█▀    █▀ █ █ ▄▀▄
# ▀▄█ ▀█▄ █ █ ▀█▄ █   ▀▄█  ▀▄ ▀█▄    █  ▀▄▀ █ █  ▀▄    █  █ █ ▀█▄
# ▄▄▀


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

    # For reproducible builds, set the NAME table's uniqueID field to:
    #     `    en FontForge 2.0 : FontName Regular : 1-1-1970`
    os.environ["SOURCE_DATE_EPOCH"] = "0"

    # SFD
    sfd_path = outfile[0:-4] + ".sfd"
    font.save(sfd_path)

    # For reproducible builds, modify SFD to remove `CreationTime` metadata, which goes
    # into the HEAD table's "created" field
    with open(sfd_path, "r") as file:
        content = file.read()
    # Replace any number after "CreationTime: " with 0
    content = re.sub(r"(CreationTime: )\d+", r"\g<1>0", content)
    content = re.sub(r"(ModificationTime: )\d+", r"\g<1>0", content)
    with open(sfd_path, "w") as file:
        file.write(content)

    # Generate font, but without ligatures yet, to temporary directory
    # sys.stderr.write("\nCreating %s\n" % outfile)
    # TTF
    font = fontforge.open(sfd_path)
    # For reproducible builds; FFTM table stores a timestamp
    font.generate(outfile, flags=("no-FFTM-table"))


#                          ▄                 ▀
# ▄▀▀ ▄▀▄ █▀▄ █ █ ▄▀▄ █▄▀ ▀█▀      █▀▄▀▄ ▄▀█ █ █▀▄
# ▀▄▄ ▀▄▀ █ █  █  ▀█▄ █    ▀▄      █ █ █ ▀▄█ █ █ █
#                             ▀▀▀▀


def convert_main(default_json, debug_dir, out_dir, cli_args, v_major, v_minor, v_patch):
    try:
        font = fontforge.font()
    except:
        pass

    with open(default_json) as f:
        config = json.load(f)
    cli_args_dict = json.loads(cli_args) or {}

    font = fontforge.font()
    set_properties(font, cli_args_dict, int(v_major), int(v_minor), int(v_patch))
    add_glyphs(
        font, config, cli_args_dict, debug_dir, int(v_major), int(v_minor), int(v_patch)
    )

    # Generate font and save as a .ttf file
    filename = cli_args_dict.get("filename", "Untitled")
    generate_font_file(font, str(filename), out_dir, default_json, debug_dir)


if __name__ == "__main__":
    if len(sys.argv) != 8:
        raise ValueError("Incorrect call to SVGtoTTF")
    convert_main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4],
        sys.argv[5],
        sys.argv[6],
        sys.argv[7],
    )
