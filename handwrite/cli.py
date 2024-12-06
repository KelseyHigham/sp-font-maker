import os
import shutil
import argparse
import tempfile
import json

from handwrite import SHEETtoPNG
from handwrite import PNGtoSVG
from handwrite import SVGtoTTF


def run(sheet, output_directory, characters_dir, config, metadata, other_words_string):
    SHEETtoPNG().convert(sheet, characters_dir, config, metadata)
    PNGtoSVG().convert(metadata, directory=characters_dir)
    SVGtoTTF().convert(characters_dir, output_directory, config, metadata, other_words_string)


def converters(sheet, output_directory, directory=None, config=None, metadata=None, other_words_string=None):
    # debug/temp directory
    if not directory:
        directory = tempfile.mkdtemp()
        isTempdir = True
    else:
        isTempdir = False
    if not os.path.isdir(directory):
        print("Debug directory does not exist. Creating it at", directory)
        os.makedirs(directory, exist_ok=True)

    if config is None:
        default_config = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "default.json"
        )
        config = default_config
    shutil.copy(config, directory)
    config = os.path.join(directory, os.path.basename(config))

    with open(config, "r") as file:
        font_data = json.load(file)

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
                    if letter == "-": letters[letter_index] = "hyphen"
                    if letter == "+": letters[letter_index] = "plus"
                    if letter == "^": letters[letter_index] = "caret"
                    if letter == "&": letters[letter_index] = "ampersand"
                    if letter == ",": letters[letter_index] = "comma"
                    if letter == "!": letters[letter_index] = "exclamation"
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

                # todo, fix bug: since i'm NOT running this line of code, we can end up with -+^&,!? in filenames.
                # but if i run it, we'll end up with glyph names like "tokihyphenponaTok", which is weird.
                # also "one" and "nine" are valid toki pona, and may rarely cause name collisions.
                # word = "".join(letters)

                glyph_json = font_data['glyphs-fancy']

                if   word == "apeja":
                    glyph_json[blank_cells[position]] = {"name": word + "Tok", "ligature": " ".join(letters), "codepoint": "0xf19a1"}
                elif word == "kokosila":
                    glyph_json[blank_cells[position]] = {"name": word + "Tok", "ligature": " ".join(letters), "codepoint": "0xf1984"}
                elif word == "pake":
                    glyph_json[blank_cells[position]] = {"name": word + "Tok", "ligature": " ".join(letters), "codepoint": "0xf19a0"}
                elif word == "powe":
                    glyph_json[blank_cells[position]] = {"name": word + "Tok", "ligature": " ".join(letters), "codepoint": "0xf19a3"}
                else:
                    # check if it's a redraw of an existing sheet glyph
                    for default_glyph in glyph_json:
                        if 'name' in default_glyph:
                            if default_glyph['name'] == word + "Tok":
                                if 'codepoint' in default_glyph:
                                    glyph_json[blank_cells[position]]['codepoint'] = default_glyph['codepoint']
                                    del default_glyph['codepoint']
                                del default_glyph['name']
                                if 'ligature' in default_glyph:
                                    del default_glyph['ligature']
                                # todo: replace ASCII A E N O, too
                                    # lowercase seems to work already
                                # todo: remove redundant glyphs from the preview web page
                                # probably never: allow replacing anything from row[6]
                    glyph_json[blank_cells[position]]['name'] = word + "Tok"
                    glyph_json[blank_cells[position]]['ligature'] = " ".join(letters)

    with open(config, "w") as file:
        json.dump(font_data, file, indent=4)

    if os.path.isdir(config):
        raise IsADirectoryError("Config parameter should not be a directory.")

    if os.path.isdir(sheet):
        raise IsADirectoryError("Sheet parameter should not be a directory.")
    else:
        run(sheet, output_directory, directory, config, metadata, other_words_string)

    if isTempdir:
        shutil.rmtree(directory)


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

    args = parser.parse_args()
    metadata = {
        "filename": args.filename, 
        "family": args.family, 
        "designer": args.designer, 
        "license": args.license, 
        "licenseurl": args.license_url, 
        "sheetversion": args.sheet_version
    }
    converters(
        args.input_path, args.output_directory, args.debug_directory, None, metadata, args.other_words
    ) 
