import os
import shutil
import argparse
import tempfile
import json
import tomllib

from handwrite.sheettopng import sheet_to_png
from handwrite.pngtosvg import png_to_svg
from handwrite.svgtottf import svg_to_ttf
from handwrite.add_ligatures import add_ligatures
from handwrite.create_toml_html import create_toml_html


def run(sheet, output_directory, debug_dir, default_json, cli_args, other_words_string):
    create_toml_html(debug_dir, output_directory, cli_args, other_words_string)
    sheet_to_png(sheet, debug_dir, default_json, cli_args, other_words_string)
    png_to_svg(cli_args, debug_dir=debug_dir)
    svg_to_ttf(debug_dir, output_directory, default_json, cli_args, other_words_string)
    add_ligatures(debug_dir, output_directory, default_json, cli_args, other_words_string)


def converters(sheet, output_directory, debug_dir=None, default_json=None, cli_args=None, other_words_string=None):
    # debug/temp directory
    if not debug_dir:
        debug_dir = tempfile.mkdtemp()
        isTempdir = True
    else:
        isTempdir = False
    if not os.path.isdir(debug_dir):
        print("Debug directory does not exist. Creating it at", debug_dir)
        os.makedirs(debug_dir, exist_ok=True)

    if default_json is None:
        default_config = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "default.toml"
        )
        default_json = default_config
    
    # read initial config data from TOML
    with open(default_json, "rb") as file:
        font_data = tomllib.load(file)
    
    # save as JSON in debug directory. we'll edit it to add custom words.
    # extra config sheets should be merged into the same working JSON file.
    # ...we do this exact thing again after populating other_words... this is redundant.
    json_path = os.path.join(debug_dir, "default.json")
    with open(json_path, "w") as file:
        json.dump(font_data, file, indent=4)
    default_json = json_path

    if other_words_string:
        other_words = other_words_string.split()
        print(other_words[0:4])
        print(other_words[4:12])
        print(other_words[12:25])
        blank_cells = [ # default.json indices of the blank cells on the page
                                                         136, 137, 138, 139, # 4 cells
                                     152, 153, 154, 155, 156, 157, 158, 159, # 8 cells
            167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179  # 13 cells
        ]

        for position, word in enumerate(other_words):
            if word != "_":
                letters = list(word)
                for letter_index, letter in enumerate(letters):
                    # consider switching to the official Adobe names for these special characters
                    # https://github.com/adobe-type-tools/agl-aglfn/
                    # https://en.wikipedia.org/wiki/Adobe_Glyph_List
                    if letter == "-": letters[letter_index] = "hyphen"
                    if letter == "+": letters[letter_index] = "plus"
                    if letter == "^": letters[letter_index] = "north"       # asciicircum
                    if letter == "<": letters[letter_index] = "west"        # less
                    if letter == ">": letters[letter_index] = "east"        # greater
                    if letter == "&": letters[letter_index] = "ampersand"
                    if letter == ",": letters[letter_index] = "comma"
                    if letter == "!": letters[letter_index] = "exclamation" # exclam
                    if letter == "?": letters[letter_index] = "question"
                    if letter == "0": letters[letter_index] = "zero"
                    if letter == "1": letters[letter_index] = "one"
                    if letter == "2": letters[letter_index] = "two"
                    if letter == "3": letters[letter_index] = "three"
                    if letter == "4": letters[letter_index] = "four"
                    if letter == "5": letters[letter_index] = "five"
                    if letter == "6": letters[letter_index] = "six"
                    if letter == "7": letters[letter_index] = "seven"
                    if letter == "8": letters[letter_index] = "eight"
                    if letter == "9": letters[letter_index] = "nine"
                    if letter == "{": letters[letter_index] = "opencurly"   # braceleft
                    if letter == "}": letters[letter_index] = "closecurly"  # braceright
                    if letter == "(": letters[letter_index] = "openparen"   # parenleft
                    if letter == ")": letters[letter_index] = "closeparen"  # parenright
                    if letter == "[": letters[letter_index] = "bracketleft"
                    if letter == "]": letters[letter_index] = "bracketright"
                    if letter == ";": letters[letter_index] = "semicolon"
                    if letter == "|": letters[letter_index] = "pipe"        # bar
                    if letter == "*": letters[letter_index] = "asterisk"
                    if letter == '"': letters[letter_index] = 'doublequote' # quotedbl
                    if letter == "'": letters[letter_index] = "singlequote" # quotesingle

                # todo: we don't differentiate letters from renamed special characters, we just concatenate them.
                # so we end up with glyph names like "tokihyphenponaTok", which is nonstandard and hard to read.
                    # standard is to use _ for concatenating characters, and . for variants
                    # https://github.com/adobe-type-tools/agl-specification?tab=readme-ov-file#3-examples
                # also "one" and "nine" are valid toki pona, and may rarely cause name collisions, e.g. "an1" -> "anone"
                # ideal would be "tokiTok_hyphen_ponaTok", because the convention is like "f_f_i.liga"
                # next best thing would be "toki_hyphen_ponaTok"
                # or "tokiHYPHENponaTok", which requires allcapsing HYPHEN, PLUS, and AMPERSAND in a few places in the code
                word = "".join(letters)

                glyph_json = font_data.get("glyphs", {}).get("sheet", {})

                # TODO:
                # here we start adding data based on hardcoded UCSUR data.
                # this logic should be reworked to read from default_json instead.
                # for unused_ucsur_word in default_json:
                    # if glyph["name"] == unused_ucsur_word:
                        # do the things
                if   word == "apeja":
                    glyph_json[blank_cells[position]] = {"name": word + "Tok", "ligature": " ".join(letters), "codepoint": 0xf19a1}
                elif word == "kokosila":
                    glyph_json[blank_cells[position]] = {"name": word + "Tok", "ligature": " ".join(letters), "codepoint": 0xf1984}
                elif word == "pake":
                    glyph_json[blank_cells[position]] = {"name": word + "Tok", "ligature": " ".join(letters), "codepoint": 0xf19a0}
                elif word == "powe":
                    glyph_json[blank_cells[position]] = {"name": word + "Tok", "ligature": " ".join(letters), "codepoint": 0xf19a3}
                else:

                    # check if it's a redraw of an existing sheet glyph
                    redraw = False
                    for default_glyph in glyph_json:
                        if 'name' in default_glyph:
                            if default_glyph['name'] == word + "Tok":
                                redraw = True
                                # todo: remove redundant glyphs from the preview web page

                    if not redraw:
                        # finally, the common case of a custom word
                        glyph_json[blank_cells[position]]['name'] = word + "Tok"
                        glyph_json[blank_cells[position]]['ligature'] = " ".join(letters)

    with open(default_json, "w") as file:
        json.dump(font_data, file, indent=4)

    if os.path.isdir(default_json):
        raise IsADirectoryError("Config parameter should not be a directory.")

    if os.path.isdir(sheet):
        raise IsADirectoryError("Sheet parameter should not be a directory.")
    else:
        run(sheet, output_directory, debug_dir, default_json, cli_args, other_words_string)

    if isTempdir:
        shutil.rmtree(debug_dir)


def main():
    print("If you get errors, try `handwrite --help`. Also check the analysis PNGs in the debug directory.")
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", help="Path to sample sheet")
    parser.add_argument("output_directory", help="Directory Path to save font output")
    parser.add_argument("--debug-directory", help="Generate in-progress PNGs, BMPs, SVGs, SFDs, and TTFs to this path \
        (Temp by default)", default=None)
    parser.add_argument("--filename", help="Font File name (\"MyFont\" by default)", default=None)
    parser.add_argument("--family", help="Font Family name (filename by default)", default=None)
    parser.add_argument("--designer", help="Font Designer name (\"me\" by default)", default=None)
    parser.add_argument("--license", help="Font License. \
        (`--license ofl` and `--license cc0` will populate License and LicenseURL appropriately. \
        IMPORTANT: The command line tool defaults to \"All rights reserved\", even though the sheet defaults to OFL.)", default=None)
    parser.add_argument("--license-url", help="Font License URL (\"\" by default)", default=None)
    parser.add_argument("--sheet-version", help="Sheet version (latest by default)", default=None)
    parser.add_argument("--other-words", help="""List of other words in the custom cells. Use _ to ignore a cell.

        IMPORTANT: Add a _ to the left of every custom row, where the empty space is.

        Example: `--other-words \"\
        _ kiki kokosila usawi \
        _ api Keli melome Pingo penpo poni snoweli \
        _ kan kulijo misa molusa oke pa panke polinpin tona wa wasoweli waken\"`)""", default=None)
    parser.add_argument("--pixel", action='store_true', help="Pixel font (experimental, false by default)", default=False)
    parser.add_argument("--not-new", action='store_true', help="Skip creating a .TOML file (false by default)", default=False)

    args = parser.parse_args()
    # todo: skip recreating the dictionary and just do cli_args = parser.parse_args()
    cli_args = {
        "filename": args.filename, 
        "family": args.family, 
        "designer": args.designer, 
        "license": args.license, 
        "licenseurl": args.license_url, 
        "sheetversion": args.sheet_version,
        "pixel": args.pixel,
        "notnew": args.not_new
    }
    converters(
        args.input_path, args.output_directory, args.debug_directory, None, cli_args, args.other_words
    ) 
