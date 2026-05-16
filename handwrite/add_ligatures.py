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
    # Default pre-composed tallies, as distinct from writein sequences of tallies:
    default_tallies = []

    # Cartouchable and stackable glyphs with ligatures:
    cartoucheable = []
    stackable = []

    # Disable kulupu combos unless a "kulupuTok" glyph is found in the font, to allow
    # for alternative sheets like tuki tiki
    enable_kulupu_combos = False
    # Disable long pi unless a "longPiStartTok" glyph is found in the font, to allow for
    # older versions of the sheet that didn't include it
    enable_long_pi = False

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

                if k.get("cartoucheable-stackable", True) == True:
                    # Currently excludes:
                    # - cartoucheStartTok
                    # - cartoucheEndTok
                    # - stackJoinTok
                    # - zerowidthjoiner
                    # - ideographicspace
                    cartoucheable.append(k["name"])
                    stackable.append(k["name"])

                if k.get("rotate", False):
                    direction = k.get("direction", "right")

                    if direction == "up":
                        cartoucheable.append(k["name"] + ".S")
                        cartoucheable.append(k["name"] + ".E")
                        cartoucheable.append(k["name"] + ".W")
                    elif direction == "down":
                        cartoucheable.append(k["name"] + ".E")
                        cartoucheable.append(k["name"] + ".N")
                        cartoucheable.append(k["name"] + ".W")
                    elif direction == "left":
                        cartoucheable.append(k["name"] + ".S")
                        cartoucheable.append(k["name"] + ".E")
                        cartoucheable.append(k["name"] + ".N")
                    else:  # right
                        cartoucheable.append(k["name"] + ".S")
                        cartoucheable.append(k["name"] + ".N")
                        cartoucheable.append(k["name"] + ".W")
                    cartoucheable.append(k["name"] + ".SE")
                    cartoucheable.append(k["name"] + ".NE")
                    cartoucheable.append(k["name"] + ".NW")
                    cartoucheable.append(k["name"] + ".SW")

                    if direction == "up":
                        stackable.append(k["name"] + ".S")
                        stackable.append(k["name"] + ".E")
                        stackable.append(k["name"] + ".W")
                    elif direction == "down":
                        stackable.append(k["name"] + ".E")
                        stackable.append(k["name"] + ".N")
                        stackable.append(k["name"] + ".W")
                    elif direction == "left":
                        stackable.append(k["name"] + ".S")
                        stackable.append(k["name"] + ".E")
                        stackable.append(k["name"] + ".N")
                    else:  # right
                        stackable.append(k["name"] + ".S")
                        stackable.append(k["name"] + ".N")
                        stackable.append(k["name"] + ".W")
                    stackable.append(k["name"] + ".SE")
                    stackable.append(k["name"] + ".NE")
                    stackable.append(k["name"] + ".NW")
                    stackable.append(k["name"] + ".SW")

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

                if k.get("name", "") == "kulupuTok":
                    enable_kulupu_combos = True
                if k.get("type", "") == "long-pi-start":
                    enable_long_pi = True
                if k.get("type", "") == "tally":
                    # Check for single tally, as opposed to "tallytallytallyTok"
                    if k.get("name", "") == "tallyTok":
                        tally_name = "tallyTok"
                        for tally_count in range(15):  # 0--14
                            # Create tuples of ligature text, followed by ligature
                            # length by tokens.
                            tally_lig = (tally_name + " cartoucheMiddleTok ") * (
                                tally_count + 1
                            )
                            long_tally_name = "tally" + str(tally_count + 1) + "Tok"
                            default_tallies.append(
                                (
                                    f"  sub   {tally_lig.rjust(22)}   by   {long_tally_name.rjust(13)};",
                                    tally_count + 1,
                                )
                            )
                            cartoucheable.append(long_tally_name)

    # linuwi, kepen, ali, ni-numbers
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
            alias["target-name"] in cartoucheable
            and alias["ligature"].replace(" ", "") + "Tok" not in cartoucheable
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







"""

    # ▄ ▄ ▄  ▄▄ ▀ ▄█▄  ▄▄ ▀ ▄▄      ▄▄  ▄  ▄▄▄▄  █▄   ▄   ▄▄
    # ▀▄▀▄▀ █   █  █  █▄▀ █ █ █    █   █ █ █ █ █ █ █ █ █ ▀▄▄
    #  ▀ ▀  ▀   ▀  ▀▀  ▀▀ ▀ ▀ ▀     ▀▀  ▀  ▀ ▀ ▀ ▀▀   ▀  ▀▀

    ligatures_string += """# WRITEIN COMBOS
# (Fill this in later)
# (E.g. `toki+pona` should also produce `tokiTok nestJoinTok ponaTok`)









"""

    # █ ▄ ▄ ▄ █ ▄ ▄ ▄▄  ▄ ▄ ▄▀▄
    # ██  █ █ █ █ █ █ █ █ █ ▄▀▀▄▀
    # ▀ ▀  ▀▀ ▀  ▀▀ █▀   ▀▀  ▀▀ ▀

    ligatures_string += """# KULUPU COMBOS

feature liga {"""
    ligatures_string += """
  # Sierpinski triangle easter egg
  sub   kulupuTok zerowidthjoiner kulupuTok zerowidthjoiner kulupuTok   by   sierpinskiTriangleKulupuTok;
"""
    for word in stackable:
        ligatures_string += f"  sub   kulupuTok zerowidthjoiner {word.ljust(12)}   by   kulupuTok_zerowidthjoiner_{word};\n"

    ligatures_string += """
  # While typing, preview kulupu mode by showing a giant kulupu. Remove this if it
  # causes bugs.
  sub   kulupuTok zerowidthjoiner   by   kulupuTok_zerowidthjoiner_ijoTok;
} liga;









"""

    #  ▄▄ ▄█▄  ▄▄  ▄▄ █ ▄ ▀ ▄▄   ▄▄
    # ▀▄▄  █  █ █ █   ██  █ █ █ █▄█
    # ▀▀   ▀▀  ▀▀  ▀▀ ▀ ▀ ▀ ▀ ▀ ▄▄▀

    ligatures_string += """# STACKING COMBOS

# let's say we have the input string `kala stackJoin lili`, and we want to turn it into `kala.bottom lili.top`

# 0. start:                            kala stackJoin    lili
# 1. we join the bottom:        kala.bottom              lili
# 2. we duplicate the joiner:   kala.bottom    stackJoin lili
# 3. we join the top:           kala.bottom              lili.top



lookup step1_joinBottom {"""
    # sub   kalaTok stackJoinTok   by   kalaTok.bottom;
    for word in stackable:
        ligatures_string += (
            f"\n  sub {word.rjust(12)}    stackJoinTok   by {word.rjust(12)}.bottom;"
            f"\n  sub {word.rjust(12)} zerowidthjoiner   by {word.rjust(12)}.bottom;"
        )
    ligatures_string += """
} step1_joinBottom;



lookup step2_duplicateJoiner {"""
    # sub   kalaTok.bottom   by   kalaTok.bottom stackJoinTok;
    for word in stackable:
        ligatures_string += f"\n  sub {word.rjust(12)}.bottom   by {word.rjust(12)}.bottom stackJoinTok;"
    ligatures_string += """
} step2_duplicateJoiner;



lookup step3_joinTop {"""
    # sub   stackJoinTok liliTok   by   liliTok.top;
    for word in stackable:
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

    #  ▄▄ ▀  ▄▄ ▄▄  ▄█▄    █▄   ▄▄  ▄▄  ▄█    ▄▄   ▄  ▄ ▄ ▄▄   ▄▄
    # █▄█ █ █ █ █ █  █     █ █ █▄▀ █ █ █ █    █ █ █ █ █ █ █ █ ▀▄▄
    # ▄▄▀ ▀  ▀▀ ▀ ▀  ▀▀    ▀ ▀  ▀▀  ▀▀  ▀▀    ▀ ▀  ▀   ▀▀ ▀ ▀ ▀▀

    ligatures_string += """# BIG NESTING WORDS

# We don't support actual nesting yet, but `soweli++` should produce a big soweli.
# (I'm not sure whether the ASCII Input Standard and UCSUR would prefer `soweli+|` or
# just `soweli+`, so I'm not supporting either yet.)

feature liga {
"""
    for word in stackable:
        ligatures_string += f"  sub   {word.ljust(12)} plus plus   by   {word}.big;\n"

    ligatures_string += """} liga;









"""

    #  ▄▄  ▄▄  ▄▄ ▄█▄  ▄  ▄ ▄  ▄▄ █▄   ▄▄  ▄▄
    # █   █ █ █    █  █ █ █ █ █   █ █ █▄▀ ▀▄▄
    #  ▀▀  ▀▀ ▀    ▀▀  ▀   ▀▀  ▀▀ ▀ ▀  ▀▀ ▀▀

    ligatures_string += """# CARTOUCHES

@cartoucheableGlyph = [
"""
    for word in cartoucheable:
        ligatures_string += "  " + word.rjust(12) + "\n"
    for word in stackable:
        ligatures_string += "  " + word.rjust(12) + ".bottom\n"
    for word in stackable:
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
        "tally",
        "equals",
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
    # for word in stackable:
    #     ligatures_string += "  " + word.rjust(12) + ".bottom\n"
    # ligatures_string += """];\n\n"""

    # ligatures_string += """@stackableTop = [\n"""
    # for word in stackable:
    #     ligatures_string += "  " + word.rjust(12) + ".top\n"
    # ligatures_string += """];\n\n\n\n"""

    ligatures_string += """lookup add_cartouche_middle {
  # Add a cartouche middle after the glyph.
  # (The cartouche middle is zero-width and extends to the left,
  #  surrounding the glyph.)
"""
    for word in cartoucheable:
        ligatures_string += (
            f"  sub {word.rjust(12)}   by {word.rjust(12)} cartoucheMiddleTok;\n"
        )
    for word in stackable:
        ligatures_string += f"  sub {word.rjust(12)}.bottom   by {word.rjust(12)}.bottom cartoucheMiddleTok;\n"
    for word in stackable:
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

    # █  ▄  ▄▄   ▄▄    ▄▄  ▀
    # █ █ █ █ █ █▄█    █ █ █
    # ▀  ▀  ▀ ▀ ▄▄▀    █▀  ▀

    # Currently, long pi and cartouches can't contain each other, because
    # cartoucheEndTok and longPiEndTok are both excluded from @cartoucheableGlyph.

    if enable_long_pi:

        ligatures_string += """# LONG PI

"""

        ligatures_string += """lookup add_long_pi_middle {
  # Add a long pi middle after the glyph.
"""
        ligatures_string += (
            "  sub cartoucheMiddleTok   by   cartoucheMiddleTok longPiMiddleTok;\n"
        )
        for word in cartoucheable:
            ligatures_string += (
                f"  sub {word.rjust(12)}   by {word.rjust(12)} longPiMiddleTok;\n"
            )
        for word in stackable:
            ligatures_string += f"  sub {word.rjust(12)}.bottom   by {word.rjust(12)}.bottom longPiMiddleTok;\n"
        for word in stackable:
            ligatures_string += f"  sub {word.rjust(12)}.top   by {word.rjust(12)}.top longPiMiddleTok;\n"
        for non_word in cartoucheable_non_words:
            ligatures_string += f"  sub {non_word.rjust(12)}   by {non_word.rjust(12)} longPiMiddleTok;\n"

        ligatures_string += """} add_long_pi_middle;



# Same logic as cartouches
feature calt {
  sub   longPiStartTok  [@cartoucheableGlyph]'   lookup add_long_pi_middle;
  sub   longPiMiddleTok [@cartoucheableGlyph]'   lookup add_long_pi_middle;
} calt;









"""

    # ▄█▄  ▄▄ █ █ ▄ ▄    ▄▄▄▄   ▄▄  ▄▄ █ ▄  ▄▄
    #  █  █ █ █ █ ▀▄█    █ █ █ █ █ █   ██  ▀▄▄
    #  ▀▀  ▀▀ ▀ ▀ ▄▄▀    ▀ ▀ ▀  ▀▀ ▀   ▀ ▀ ▀▀

    ligatures_string += """# DEFAULT TALLIES
# (Well after writein tallies)

feature liga {
"""

    # Sort them by number of tokens.
    default_tallies.sort(reverse=True, key=lambda x: x[1])

    # Add to our cool string.
    for line in default_tallies:
        ligatures_string += line[0] + "\n"

    ligatures_string += """} liga;









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
