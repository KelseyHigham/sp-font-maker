import json
import os
import sys

from fontTools import ttLib  # camelCase!
from fontTools.feaLib import builder  # camelCase!

# █ ▀          ▄
# █ █ ▄▀█ ▄▀█ ▀█▀ █ █ █▄▀ ▄▀▄ ▄▀▀
# █ █ ▀▄█ ▀▄█  ▀▄ ▀▄█ █   ▀█▄ ▄█▀
#     ▄▄▀


def add_ligatures(
    debug_dir, out_dir, default_json, cli_args=None, other_words_string=None
):
    # Now the font has exported, presumably.
    # We're back to the `python` environment, not the `ffpython` one, so we can use
    # libraries like fontTools, camelCase.

    # `debug_dir` is the temp directory

    cli_args_dict = cli_args

    with open(default_json) as f:
        default_json_data = json.load(f)

    filename = cli_args_dict.get("filename", "Untitled")
    if filename is None:
        raise NameError("filename not found in config file.")

    family = cli_args_dict.get("family", None) or filename

    # fontTools: input font file
    infile = str(debug_dir + os.sep + (filename + " without ligatures.ttf"))
    # sys.stderr.write("\nAdding ligatures to %s\n" % infile)

    # fontTools: output font file
    filename = filename + ".ttf" if not filename.endswith(".ttf") else filename
    outfile = str(out_dir + os.sep + filename)
    # while os.path.exists(outfile):
    #     filename = os.path.splitext(filename)[0] + " (1).ttf"
    #     outfile = out_dir + os.sep + filename

    ligatures_string = """languagesystem DFLT dflt; # this part is apparently necessary so that
languagesystem latn dflt; # people can edit the font in fontforge after??









# WORDS

feature liga {
"""
    list_of_ligs = []
    # Cartouchable and stackable glyphs with ligatures:
    cartoucheable_and_stackable = []

    # Create ligature lines.
    with open(default_json) as f:
        json_glyphs = json.load(f).get("glyphs", {})
        glyphs_sheet = json_glyphs.get("sheet", [])
        glyphs_derived = json_glyphs.get("derived", [])
        glyphs_spaces = json_glyphs.get("spaces", [])
        glyphs = glyphs_sheet + glyphs_derived + glyphs_spaces
        # Pre-combined glyphs. Todo: Move this line to default.toml
        glyphs.extend(
            [
                {
                    "name": "lipuTok_nestJoinTok_tokiTok",
                    "ligature": "l i p u plus t o k i",
                },
                {"name": "k_zerowidthjoiner_u", "ligature": "k ampersand u"},
                {"name": "s_zerowidthjoiner_u", "ligature": "s ampersand u"},
            ]
        )
        for k in glyphs:
            if "ligature" in k:
                lig = k["ligature"]
                name = k["name"]

                # Create tuples of ligature text, followed by ligature length by tokens.
                list_of_ligs.append(
                    (
                        f"  sub   {lig.rjust(22)}   by   {name.rjust(13)};",
                        len(lig.split(" ")),
                    )
                )

                if "rotate" in k and k["rotate"]:

                    def rotated_ligature(
                        lig, lig_suffix, name, name_suffix, extra_length
                    ):
                        list_of_ligs.append(
                            (
                                f"  sub   {(lig + lig_suffix).rjust(22)}   by   {(name + name_suffix).rjust(13)};",
                                len(lig.split(" ")) + extra_length,
                            )
                        )

                    rotated_ligature(lig, " v east", name, ".SE", 2)
                    rotated_ligature(lig, " east v", name, ".SE", 2)
                    rotated_ligature(lig, " north east", name, ".NE", 2)
                    rotated_ligature(lig, " east north", name, ".NE", 2)
                    rotated_ligature(lig, " north west", name, ".NW", 2)
                    rotated_ligature(lig, " west north", name, ".NW", 2)
                    rotated_ligature(lig, " v west", name, ".SW", 2)
                    rotated_ligature(lig, " west v", name, ".SW", 2)
                    direction = k.get("direction", "right")
                    if direction == "up":
                        rotated_ligature(lig, " v", name, ".S", 1)
                        rotated_ligature(lig, " east", name, ".E", 1)
                        rotated_ligature(lig, " north", name, "", 1)  # default dir
                        rotated_ligature(lig, " west", name, ".W", 1)
                    elif direction == "down":
                        rotated_ligature(lig, " v", name, "", 1)  # default dir
                        rotated_ligature(lig, " east", name, ".E", 1)
                        rotated_ligature(lig, " north", name, ".N", 1)
                        rotated_ligature(lig, " west", name, ".W", 1)
                    elif direction == "left":
                        rotated_ligature(lig, " v", name, ".S", 1)
                        rotated_ligature(lig, " east", name, ".E", 1)
                        rotated_ligature(lig, " north", name, ".N", 1)
                        rotated_ligature(lig, " west", name, "", 1)  # default dir
                    else:  # right
                        rotated_ligature(lig, " v", name, ".S", 1)
                        rotated_ligature(lig, " east", name, "", 1)  # default dir
                        rotated_ligature(lig, " north", name, ".N", 1)
                        rotated_ligature(lig, " west", name, ".W", 1)
                    pass

                if (
                    k["name"] != "cartoucheStartTok"
                    and k["name"] != "cartoucheEndTok"
                    # and k['name'] != "middotTok"
                    # and k['name'] != "colonTok"
                    # and k['name'] != "teTok"
                    # and k['name'] != "toTok"
                    and k["name"] != "stackJoinTok"
                    and k["name"] != "zerowidthjoiner"
                    and k["name"] != "ideographicspace"
                ):
                    cartoucheable_and_stackable.append(k["name"])

                if "rotate" in k and k["rotate"]:
                    direction = k.get("direction", "right")
                    if direction == "up":
                        cartoucheable_and_stackable.append(k["name"] + ".S")
                        cartoucheable_and_stackable.append(k["name"] + ".E")
                        cartoucheable_and_stackable.append(k["name"] + ".W")
                    elif direction == "down":
                        cartoucheable_and_stackable.append(k["name"] + ".E")
                        cartoucheable_and_stackable.append(k["name"] + ".N")
                        cartoucheable_and_stackable.append(k["name"] + ".W")
                    elif direction == "left":
                        cartoucheable_and_stackable.append(k["name"] + ".S")
                        cartoucheable_and_stackable.append(k["name"] + ".E")
                        cartoucheable_and_stackable.append(k["name"] + ".N")
                    else:  # right
                        cartoucheable_and_stackable.append(k["name"] + ".S")
                        cartoucheable_and_stackable.append(k["name"] + ".N")
                        cartoucheable_and_stackable.append(k["name"] + ".W")
                    cartoucheable_and_stackable.append(k["name"] + ".SE")
                    cartoucheable_and_stackable.append(k["name"] + ".NE")
                    cartoucheable_and_stackable.append(k["name"] + ".NW")
                    cartoucheable_and_stackable.append(k["name"] + ".SW")

    # linuwi, kepen, ali, ni-numbers, space space, hyphen
    aliases = default_json_data.get("ligature-aliases", [])
    glyphs = default_json_data.get("glyphs", {}).get("sheet", [])
    for alias in aliases:
        # NOTE: The following logic introduces bugs if someone tries to write in both a
        # special character and its name, e.g. ";/semicolon" or "semicolon/;".

        # If:
        # 1. The ligature alias's target (e.g. "kepekenTok") exists,
        # 2. And we're not redirecting a writein glyph's ligature (e.g. "k e p e n") to
        #    a default glyph, thereby preventing the writein from being written:
        if (
            alias["target-name"] in cartoucheable_and_stackable
            and alias["ligature"].replace(" ", "") + "Tok"
            not in cartoucheable_and_stackable
        ):
            list_of_ligs.append(
                (
                    f"  sub   {(alias['ligature']).rjust(22)}   by   {(alias['target-name']).rjust(13)};",
                    len(alias["ligature"].split(" ")),
                )
            )

    # Sort them by number of tokens.
    list_of_ligs.sort(reverse=True, key=lambda x: x[1])

    # Add to our cool string.
    for line in list_of_ligs:
        ligatures_string += line[0] + "\n"

    ligatures_string += """} liga;









# WRITEIN COMBOS
# (Fill this in later)









"""

    ligatures_string += """# KULUPU COMBOS

feature liga {
"""
    for word in cartoucheable_and_stackable:
        ligatures_string += f"  sub   kulupuTok zerowidthjoiner {word.ljust(12)}   by   kulupuTok_zerowidthjoiner_{word};\n"

    ligatures_string += """
  # While typing, preview kulupu mode by showing a giant kulupu. Remove this if it
  # causes bugs.
  sub   kulupuTok zerowidthjoiner   by   kulupuTok_zerowidthjoiner_ijoTok;
} liga;









"""

    ligatures_string += """# STACKING COMBOS

# let's say we have the input string `kala stackJoin lili`, and we want to turn it into `kala.bottom lili.top`

# 0. start:                            kala stackJoin    lili
# 1. we join the bottom:        kala.bottom              lili
# 2. we duplicate the joiner:   kala.bottom    stackJoin lili
# 3. we join the top:           kala.bottom              lili.top



lookup step1_joinBottom {"""
    # sub   kalaTok stackJoinTok   by   kalaTok.bottom;
    for word in cartoucheable_and_stackable:
        ligatures_string += (
            f"\n  sub {word.rjust(12)}    stackJoinTok   by {word.rjust(12)}.bottom;"
            f"\n  sub {word.rjust(12)} zerowidthjoiner   by {word.rjust(12)}.bottom;"
        )
    ligatures_string += """
} step1_joinBottom;



lookup step2_duplicateJoiner {"""
    # sub   kalaTok.bottom   by   kalaTok.bottom stackJoinTok;
    for word in cartoucheable_and_stackable:
        ligatures_string += f"\n  sub {word.rjust(12)}.bottom   by {word.rjust(12)}.bottom stackJoinTok;"
    ligatures_string += """
} step2_duplicateJoiner;



lookup step3_joinTop {"""
    # sub   stackJoinTok liliTok   by   liliTok.top;
    for word in cartoucheable_and_stackable:
        ligatures_string += (
            f"\n  sub   stackJoinTok {word.rjust(12)}   by {word.rjust(12)}.top;"
        )
    ligatures_string += """
} step3_joinTop ;



feature liga {                    #          kala stackJoin    lili
  lookup step1_joinBottom;        #   kala.bottom              lili
  lookup step2_duplicateJoiner;   #   kala.bottom    stackJoin lili
  lookup step3_joinTop;           #   kala.bottom              lili.top
} liga;









"""

    ligatures_string += """# CARTOUCHES

@cartoucheableGlyph = [
"""
    for word in cartoucheable_and_stackable:
        ligatures_string += "  " + word.rjust(12) + "\n"
    for word in cartoucheable_and_stackable:
        ligatures_string += "  " + word.rjust(12) + ".bottom\n"
    for word in cartoucheable_and_stackable:
        ligatures_string += "  " + word.rjust(12) + ".top\n"

    cartoucheable_non_words = [
        "a",
        "e",
        "n",
        "o",
        "A",
        "E",
        "N",
        "O",
        "b",
        "B",
        "c",
        "C",
        "d",
        "D",
        "f",
        "F",
        "g",
        "G",
        "h",
        "H",
        "q",
        "Q",
        "r",
        "R",
        "v",
        "V",
        "x",
        "X",
        "y",
        "Y",
        "z",
        "Z",
        "period",
        "colon",
        "space",
        "exclamation",
        "question",
        "semicolon",
        "comma",
        "underscore",
        "ideographicspace",
        "pipe",
        "middotTok",
        "colonTok",
        "teTok",
        "toTok",
    ]
    for non_word in cartoucheable_non_words:
        ligatures_string += "  " + non_word.rjust(12) + "\n"

    ligatures_string += """];

"""

    # ligatures_string += """@stackableBottom = [\n"""
    # for word in cartoucheable_and_stackable:
    #     ligatures_string += "  " + word.rjust(12) + ".bottom\n"
    # ligatures_string += """];\n\n"""

    # ligatures_string += """@stackableTop = [\n"""
    # for word in cartoucheable_and_stackable:
    #     ligatures_string += "  " + word.rjust(12) + ".top\n"
    # ligatures_string += """];\n\n\n\n"""

    ligatures_string += """lookup add_cartouche_middle {
  # Add a cartouche middle after the glyph.
  # (The cartouche middle is zero-width and extends to the left,
  #  surrounding the glyph.)
"""
    for word in cartoucheable_and_stackable:
        ligatures_string += (
            f"  sub {word.rjust(12)}   by {word.rjust(12)} cartoucheMiddleTok;\n"
        )
    for word in cartoucheable_and_stackable:
        ligatures_string += f"  sub {word.rjust(12)}.bottom   by {word.rjust(12)}.bottom cartoucheMiddleTok;\n"
    for word in cartoucheable_and_stackable:
        ligatures_string += f"  sub {word.rjust(12)}.top   by {word.rjust(12)}.top cartoucheMiddleTok;\n"
    for non_word in cartoucheable_non_words:
        ligatures_string += f"  sub {non_word.rjust(12)}   by {non_word.rjust(12)} cartoucheMiddleTok;\n"

    ligatures_string += """} add_cartouche_middle;



# idk what keyword to use here. liga, calt, ccmp, something else?
# this might affect whether the font works by default in text editors like LibreOffice and Word...?
feature calt {
  # If a glyph follows a cartouche start, add a cartouche middle after the glyph.
  sub   cartoucheStartTok  [@cartoucheableGlyph]'   lookup add_cartouche_middle;

  # If a glyph follows a cartouche middle, add a cartouche middle after the glyph.
  sub   cartoucheMiddleTok [@cartoucheableGlyph]'   lookup add_cartouche_middle;
  # # (Bug: The following line doesn't do anything? So instead, we draw the cartouche middle twice, making cartouche middles too thick.)
  # # (Try moving this line up!! This is ultimately like a ligature in that it needs to be sorted longest-to-shortest.)
  # sub   cartoucheMiddleTok space [@cartoucheableGlyph]'   lookup add_cartouche_middle;

  # # Stacked glyphs
  # # (Bug: The following lines don't do anything? So instead, we draw the cartouche middle twice, making cartouche middles too thick.)
  # # (Same here!!)
  # sub   cartoucheStartTok [@stackableBottom] [@stackableTop]'   lookup add_cartouche_middle;
  # sub   cartoucheMiddleTok [@stackableBottom] [@stackableTop]'   lookup add_cartouche_middle;
} calt;









"""

    # print(ligatures_string)
    feature_file = open(debug_dir + os.sep + family + ".fea", "w", encoding="utf-8")
    feature_file.write(ligatures_string)
    feature_file.close()

    tt = ttLib.TTFont(infile, recalcTimestamp=False)
    builder.addOpenTypeFeatures(tt, debug_dir + os.sep + family + ".fea", debug=True)
    sys.stderr.write("Generating %s...\n" % outfile)
    tt.save(outfile)
    print("\a")
