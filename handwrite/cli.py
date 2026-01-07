# 📎

import argparse
import json
import os
import shutil
import tempfile

import tomllib

from handwrite.add_ligatures import add_ligatures
from handwrite.create_toml_html import create_toml_html
from handwrite.pngtosvg import png_to_svg
from handwrite.sheettopng import sheet_to_png
from handwrite.svgtottf import svg_to_ttf


def run(sheet, output_directory, debug_dir, default_json, cli_args, other_words_string):
    create_toml_html(
        debug_dir, output_directory, default_json, cli_args, other_words_string
    )
    sheet_to_png(sheet, debug_dir, default_json, cli_args, other_words_string)
    png_to_svg(cli_args, default_json, debug_dir=debug_dir)
    svg_to_ttf(debug_dir, output_directory, default_json, cli_args, other_words_string)
    add_ligatures(
        debug_dir, output_directory, default_json, cli_args, other_words_string
    )


def converters(
    sheet,
    output_directory,
    debug_dir=None,
    default_json=None,
    cli_args=None,
    other_words_string=None,
):
    # Debug/temp directory:
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

    # Read initial config data from TOML.
    with open(default_json, "rb") as file:
        font_data = tomllib.load(file)

    # Save as JSON in debug directory. We'll edit it to add custom words.
    # Extra config sheets should be merged into the same working JSON file.
    # ...We do this exact thing again after populating other_words... This is redundant.
    json_path = os.path.join(debug_dir, "default.json")
    with open(json_path, "w") as file:
        json.dump(font_data, file, indent=4)
    default_json = json_path

    if other_words_string:
        other_words = other_words_string.split()
        print(other_words[0:4])
        print(other_words[4:12])
        print(other_words[12:25])
        # fmt:off
        blank_cells = [ # default.json indices of the blank cells on the page
                                                         136, 137, 138, 139, # 4 cells
                                     152, 153, 154, 155, 156, 157, 158, 159, # 8 cells
            167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179  # 13 cells
        ]
        # fmt:on

        base_glyphs = font_data.get("glyphs", {}).get("copies", [])
        space_glyphs = font_data.get("glyphs", {}).get("spaces", [])
        derived_glyphs = font_data.get("glyphs", {}).get("derived", [])
        combined_glyphs = base_glyphs + space_glyphs + derived_glyphs
        special_character_names = {
            glyph["writein"]: glyph["name"]
            for glyph in combined_glyphs
            if "writein" in glyph and "name" in glyph
        }
        for position, word in enumerate(other_words):
            if word != "_":
                alias_words = word.split("/")
                word = alias_words[0]
                alias_words = alias_words[1:]

                # Replace special characters in `word`.
                letters = [special_character_names.get(ch, ch) for ch in word]

                # Then identically replace special characters for each alias.
                aliases_letters = []
                for alias in alias_words:
                    aliases_letters.append(
                        [special_character_names.get(ch, ch) for ch in alias]
                    )

                # Todo: We don't differentiate letters from renamed special characters,
                # we just concatenate them.
                # So we end up with glyph names like "tokihyphenponaTok", which is
                # nonstandard and hard to read.
                #     Standard is to use _ for concatenating characters, and . for
                #     variants:
                #     https://github.com/adobe-type-tools/agl-specification?tab=readme-ov-file#3-examples
                # Also "one" and "nine" are valid toki pona, and may rarely cause name
                # collisions, e.g. "an1" -> "anone".
                # Ideal would be "tokiTok_hyphen_ponaTok", because the convention is
                # like "f_f_i.liga".
                # Next best thing would be "toki_hyphen_ponaTok".
                # Or "tokiHYPHENponaTok", which requires allcapsing HYPHEN, PLUS, and
                # AMPERSAND in a few places in the code.
                word = "".join(letters)

                # Write ligature aliases to JSON.
                lig_aliases = font_data.get("ligature-aliases", [])
                for wi, alias in enumerate(alias_words):
                    lig_aliases.append(
                        {
                            "ligature": " ".join(aliases_letters[wi]),
                            "target-name": word + "Tok",
                        }
                    )

                glyphs_json = font_data.get("glyphs", {}).get("sheet", [])

                # Check if it's a redraw of an existing sheet glyph.
                redraw = False
                for default_glyph in glyphs_json:
                    if "name" in default_glyph:
                        if default_glyph["name"] == word + "Tok":
                            redraw = True
                            # Todo: Remove redundant glyphs from the preview web page.

                if not redraw:
                    word_json = glyphs_json[blank_cells[position]]

                    # The common case of a custom word.
                    word_json["name"] = word + "Tok"
                    word_json["ligature"] = " ".join(letters)

                    # If a writein word has default metadata (e.g. codepoint, rotate,
                    # direction), assign it.
                    writein_potential_words = font_data.get("writein-metadata", [])
                    for potential_word in writein_potential_words:
                        if word + "Tok" == potential_word.get("name", ""):
                            for key, val in potential_word.items():
                                word_json.setdefault(key, val)

    with open(default_json, "w") as file:
        json.dump(font_data, file, indent=4)

    if os.path.isdir(default_json):
        raise IsADirectoryError("Config parameter should not be a directory.")

    if os.path.isdir(sheet):
        raise IsADirectoryError("Sheet parameter should not be a directory.")
    else:
        run(
            sheet,
            output_directory,
            debug_dir,
            default_json,
            cli_args,
            other_words_string,
        )

    if isTempdir:
        shutil.rmtree(debug_dir)


def main():
    print(
        "If you get errors, try `handwrite --help`. "
        + "Also check the analysis PNGs in the debug directory."
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", help="Path to sample sheet")
    parser.add_argument("output_directory", help="Directory Path to save font output")
    parser.add_argument(
        "--debug-directory",
        help="Generate in-progress PNGs, BMPs, SVGs, SFDs, and TTFs to this path \
        (Temp by default)",
        default=None,
    )
    parser.add_argument(
        "--filename", help='Font File name ("MyFont" by default)', default=None
    )
    parser.add_argument(
        "--family", help="Font Family name (filename by default)", default=None
    )
    parser.add_argument(
        "--designer", help='Font Designer name ("me" by default)', default=None
    )
    parser.add_argument(
        "--license",
        help='Font License. \
        (`--license ofl` and `--license cc0` will populate License and LicenseURL appropriately. \
        IMPORTANT: The command line tool defaults to "All rights reserved", even though the sheet defaults to OFL.)',
        default=None,
    )
    parser.add_argument(
        "--license-url", help='Font License URL ("" by default)', default=None
    )
    parser.add_argument(
        "--sheet-version", help="Sheet version (latest by default)", default=None
    )
    parser.add_argument(
        "--other-words",
        help="""List of other words in the custom cells. Use _ to ignore a cell.

        IMPORTANT: Add a _ to the left of every custom row, where the empty space is.

        Example: `--other-words \"\
        _ kiki kokosila usawi \
        _ api Keli melome Pingo penpo poni snoweli \
        _ kan kulijo misa molusa oke pa panke polinpin tona wa wasoweli waken\"`)""",
        default=None,
    )
    parser.add_argument(
        "--pixel",
        action="store_true",
        help="Pixel font (experimental, false by default)",
        default=False,
    )
    parser.add_argument(
        "--not-new",
        action="store_true",
        help="Skip creating a .TOML file, and skip writing to `generate all fonts.bat` (false by default)",
        default=False,
    )

    args = parser.parse_args()
    # cli_args = { # The format looks like this:
    #     "filename": args.filename,
    #     "family": args.family,
    #     "designer": args.designer,
    #     "license": args.license,
    #     "license_url": args.license_url,
    #     "sheet_version": args.sheet_version,
    #     "pixel": args.pixel,
    #     "not_new": args.not_new,
    # }
    cli_args = vars(parser.parse_args())

    # Get filename from family
    if cli_args["family"] is not None and cli_args["filename"] is None:
        cli_args["filename"] = cli_args["family"].replace(" ", "-")

    converters(
        args.input_path,
        args.output_directory,
        args.debug_directory,
        None,
        cli_args,
        args.other_words,
    )
