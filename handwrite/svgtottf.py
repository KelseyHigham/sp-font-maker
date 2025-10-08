
#                           █                  █▀▀▀▄         ▄   █               
#    █▄▀  ▄▀▀▄  ▄▀▀█  █  █  █   ▀▀▄  █▄▀       █   █  █  █  ▀█▀  █▀▀▄  ▄▀▀▄  █▀▀▄
#    █    █▄▄█  █  █  █  █  █  ▄▀▀█  █         █▀▀▀   █  █   █   █  █  █  █  █  █
#    █    ▀▄▄   ▀▄▄█  ▀▄▄█  █  ▀▄▄█  █         █      ▀▄▄█   ▀▄  █  █  ▀▄▄▀  █  █
#                ▄▄▀                                   ▄▄▀

import sys
import os
import json
import datetime


def convert_svg_to_ttf(debug_dir, out_dir, default_json, cli_args=None, other_words_string=None):
    """Convert a directory with SVG images to TrueType Font.

    Calls a subprocess to the run this script with Fontforge Python
    environment, because the FontForge libraries don't work in regular Python.

    Then uses regular Python, and fontTools, to apply ligatures.

    Then outputs a web page with examples of the font.

    Parameters
    ----------
    debug_dir : str
        Path to directory with SVGs to be converted.
    out_dir : str
        Path to output directory.
    default_json : str
        Path to config file.
    cli_args : dict
        Dictionary containing the metadata (filename, family or style)
    """
    print("SVGtoTTF")
    import subprocess
    import platform
    from packaging.version import Version
    sheet_version = cli_args.get("sheetversion") or "99999999.999999.999999"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    svgtottf_ffpython_path = os.path.join(current_dir, 'svgtottf_ffpython.py')

    subprocess.run(
        (
            ["ffpython"]
            if platform.system() == "Windows"
            else ["fontforge", "-script"]
        )
        + [
            svgtottf_ffpython_path,
            default_json,
            debug_dir,
            out_dir,
            json.dumps(cli_args),
            str(Version(sheet_version).major),
            str(Version(sheet_version).minor),
            str(Version(sheet_version).micro)
        ]
    )

    add_ligatures(debug_dir, out_dir, default_json, cli_args, other_words_string)









    # █   ▀               ▄
    # █  ▀█  ▄▀▀█   ▀▀▄  ▀█▀  █  █  █▄▀  ▄▀▀▄  ▄▀▀▄
    # █   █  █  █  ▄▀▀█   █   █  █  █    █▄▄█   ▀▄
    # █   █  ▀▄▄█  ▀▄▄█   ▀▄  ▀▄▄█  █    ▀▄▄   ▀▄▄▀
    #         ▄▄▀

def add_ligatures(debug_dir, out_dir, default_json, cli_args=None, other_words_string=None):
        # Now the font has exported, presumably. 
        # We're back to the `python` environment, not the `ffpython` one, so we can use libraries like fontTools, camelCase.
        import fontTools  # camelCase!

        # `debug_dir` is the temp directory

        cli_args_dict = json.loads(json.dumps(cli_args)) or {}

        with open(default_json) as f:
            default_json_data = json.load(f)

        filename = (cli_args_dict.get("filename", None) or default_json_data["props"].get("filename", None))
        if filename is None:
            raise NameError("filename not found in config file.")

        family = (cli_args_dict.get("family", None) or filename)

        designer = cli_args_dict.get("designer", None) or default_json_data["props"].get("designer", "jan pi toki pona")

        # for generating the ilo Linku TOML files for each font,
        # we use short license codes from the SPDX License List: https://spdx.org/licenses/
        license = cli_args_dict.get("license", None) or default_json_data["sfnt_names"].get("License", "All rights reserved")
        licenseurl = cli_args_dict.get("licenseurl", None) or default_json_data["sfnt_names"].get("License URL", "")
        if license == "ofl":
            license = "OFL-1.1"
            licenseurl = "https://openfontlicense.org"
        if license == "cc0":
            license = "CC0-1.0"
            licenseurl = "https://creativecommons.org/publicdomain/zero/1.0/"

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









# LIGATURES

feature liga {
"""
        list_of_ligs = []
        # cartouchable and stackable glyphs with ligatures
        cartoucheable_and_stackable = []

        # create ligature lines
        with open(default_json) as f:
            glyphs = json.load(f).get("glyphs-fancy", {})
            for k in glyphs:
                if 'ligature' in k:
                    lig = k['ligature']
                    name = k['name']

                    # create tuples of ligature text, followed by ligature length by tokens
                    list_of_ligs.append((
                        f"  sub   {lig.rjust(22)}   by   {name.rjust(13)};",
                        len(lig.split(' '))
                    ))

                    if 'rotate' in k and k['rotate']:
                        def rotated_ligature(lig, lig_suffix, name, name_suffix, extra_length):
                            list_of_ligs.append((
                                f"  sub   {(lig+lig_suffix).rjust(22)}   by   {(name+name_suffix).rjust(13)};",
                                len(lig.split(' ')) + extra_length
                            ))
                        rotated_ligature(lig, " v east",     name, ".SE", 2)
                        rotated_ligature(lig, " east v",     name, ".SE", 2)
                        rotated_ligature(lig, " north east", name, ".NE", 2)
                        rotated_ligature(lig, " east north", name, ".NE", 2)
                        rotated_ligature(lig, " north west", name, ".NW", 2)
                        rotated_ligature(lig, " west north", name, ".NW", 2)
                        rotated_ligature(lig, " v west",     name, ".SW", 2)
                        rotated_ligature(lig, " west v",     name, ".SW", 2)
                        if 'direction' in k:
                            if k['direction'] == 'up':
                                rotated_ligature(lig, " v",     name, ".S", 1)
                                rotated_ligature(lig, " east",  name, ".E", 1)
                                rotated_ligature(lig, " north", name, "",   1) # default dir
                                rotated_ligature(lig, " west",  name, ".W", 1)
                            elif k['direction'] == 'down':
                                rotated_ligature(lig, " v",     name, "",   1) # default dir
                                rotated_ligature(lig, " east",  name, ".E", 1)
                                rotated_ligature(lig, " north", name, ".N", 1)
                                rotated_ligature(lig, " west",  name, ".W", 1)
                            elif k['direction'] == 'left':
                                rotated_ligature(lig, " v",     name, ".S", 1)
                                rotated_ligature(lig, " east",  name, ".E", 1)
                                rotated_ligature(lig, " north", name, ".N", 1)
                                rotated_ligature(lig, " west",  name, "",   1) # default dir
                            else: #right
                                rotated_ligature(lig, " v",     name, ".S", 1)
                                rotated_ligature(lig, " east",  name, "",   1) # default dir
                                rotated_ligature(lig, " north", name, ".N", 1)
                                rotated_ligature(lig, " west",  name, ".W", 1)
                        else: # right again
                            rotated_ligature(lig, " v",     name, ".S", 1)
                            rotated_ligature(lig, " east",  name, "",   1) # default dir
                            rotated_ligature(lig, " north", name, ".N", 1)
                            rotated_ligature(lig, " west",  name, ".W", 1)
                        pass

                    if (k['name'] != "cartoucheStartTok" and
                        k['name'] != "cartoucheEndTok" and
                        k['name'] != "middotTok" and
                        k['name'] != "colonTok" and
                        k['name'] != "teTok" and
                        k['name'] != "toTok"
                    ):
                        cartoucheable_and_stackable.append(k['name']) 

                    if 'rotate' in k and k['rotate']:
                        if 'direction' in k:
                            if k['direction'] == 'up':
                                cartoucheable_and_stackable.append(k['name'] + ".S")
                                cartoucheable_and_stackable.append(k['name'] + ".E")
                                cartoucheable_and_stackable.append(k['name'] + ".W")
                            elif k['direction'] == 'down':
                                cartoucheable_and_stackable.append(k['name'] + ".E")
                                cartoucheable_and_stackable.append(k['name'] + ".N")
                                cartoucheable_and_stackable.append(k['name'] + ".W")
                            elif k['direction'] == 'left':
                                cartoucheable_and_stackable.append(k['name'] + ".S")
                                cartoucheable_and_stackable.append(k['name'] + ".E")
                                cartoucheable_and_stackable.append(k['name'] + ".N")
                            else: # right
                                cartoucheable_and_stackable.append(k['name'] + ".S")
                                cartoucheable_and_stackable.append(k['name'] + ".N")
                                cartoucheable_and_stackable.append(k['name'] + ".W")
                        else: # right again
                            cartoucheable_and_stackable.append(k['name'] + ".S")
                            cartoucheable_and_stackable.append(k['name'] + ".N")
                            cartoucheable_and_stackable.append(k['name'] + ".W")
                        cartoucheable_and_stackable.append(k['name'] + ".SE")
                        cartoucheable_and_stackable.append(k['name'] + ".NE")
                        cartoucheable_and_stackable.append(k['name'] + ".NW")
                        cartoucheable_and_stackable.append(k['name'] + ".SW")

        # candidate for removal later, because 
            # it doesn't play well with HTML
            # it interferes with an alignment style that's easy to read and works across platforms:
                # soweli li wile moku
                # |      li lukin e sewi
                # |      |  |     e ma
                # |      |  |     e poka
                # |      li kama lukin e kili
                # |      |  |    |     | |    lon kasi
                # |      li moku e kili
            # here's that style with the interference:
                # soweli li wile moku
                # | li lukin e sewi
                # | | | e ma
                # | | | e poka
                # | li kama lukin e kili
                # | | | | | | lon kasi
                # | li moku e kili
        # in the future, full-width spaces can be inserted with `|`.
        # this removal may be disruptive, though, and should only be performed with community consensus. 
        list_of_ligs.append(("  sub              space space   by   ideographicspace;", 2))
        list_of_ligs.append(("  sub                   hyphen   by    stackJoinTok;", 1))

        list_of_ligs.append(("  sub              l i n u w i   by      linluwiTok;", 6))
        list_of_ligs.append(("  sub                k e p e n   by      kepekenTok;", 5))

        # sort them by number of tokens
        list_of_ligs.sort(reverse=True, key=lambda x: x[1])

        # add to our cool string
        for line in list_of_ligs:
            ligatures_string += line[0] + "\n"

        ligatures_string += """} liga;









"""


        ligatures_string += """# STACKING

# let's say we have the input string `kala stackJoin lili`, and we want to turn it into `kala.bottom lili.top`

# 0. start:                            kala stackJoin    lili
# 1. we join the bottom:        kala.bottom              lili
# 2. we duplicate the joiner:   kala.bottom    stackJoin lili
# 3. we join the top:           kala.bottom              lili.top



lookup step1_joinBottom {"""
        # sub   kalaTok stackJoinTok   by   kalaTok.bottom;
        for word in cartoucheable_and_stackable:
            ligatures_string += "\n" + "  sub " +     word.rjust(12) + " stackJoinTok   by " +     word.rjust(12) + ".bottom;"
        ligatures_string += """
} step1_joinBottom;



lookup step2_duplicateJoiner {"""
        # sub   kalaTok.bottom   by   kalaTok.bottom stackJoinTok;
        for word in cartoucheable_and_stackable:
            ligatures_string += "\n" + "  sub " +     word.rjust(12) + ".bottom   by " +     word.rjust(12) + ".bottom stackJoinTok;"
        ligatures_string += """
} step2_duplicateJoiner;



lookup step3_joinTop {"""
        # sub   stackJoinTok liliTok   by   liliTok.top;
        for word in cartoucheable_and_stackable:
            ligatures_string += "\n" + "  sub   stackJoinTok " +     word.rjust(12) + "   by " +     word.rjust(12) + ".top;"
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
            ligatures_string += "  " +     word.rjust(12) + "\n"
        for word in cartoucheable_and_stackable:
            ligatures_string += "  " +     word.rjust(12) + ".bottom\n"
        for word in cartoucheable_and_stackable:
            ligatures_string += "  " +     word.rjust(12) + ".top\n"

        cartoucheable_non_words = ["a","e","n","o", "A","E","N","O", 
            "b","B","c","C","d","D","f","F","g","G","h","H",
            "q","Q","r","R","v","V","x","X","y","Y","z","Z",
            "period", "colon", "space", "exclamation",
            "question", "underscore", "ideographicspace", "pipe",
            "middotTok", "colonTok", "teTok", "toTok"]
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
            ligatures_string += "  sub " +     word.rjust(12) + "   by " +     word.rjust(12) + " cartoucheMiddleTok;" + "\n"
        for word in cartoucheable_and_stackable:
            ligatures_string += "  sub " +     word.rjust(12) + ".bottom   by " +     word.rjust(12) + ".bottom cartoucheMiddleTok;" + "\n"
        for word in cartoucheable_and_stackable:
            ligatures_string += "  sub " +     word.rjust(12) + ".top   by " +     word.rjust(12) + ".top cartoucheMiddleTok;" + "\n"
        for non_word in cartoucheable_non_words:
            ligatures_string += "  sub " + non_word.rjust(12) + "   by " + non_word.rjust(12) + " cartoucheMiddleTok;" + "\n"

        ligatures_string += """} add_cartouche_middle;



# idk what keyword to use here. liga, calt, ccmp, something else?
# this might affect whether the font works by default in text editors like LibreOffice and Word...?
feature calt {
  # If a glyph follows a cartouche start, add a cartouche middle after the glyph.
  sub   cartoucheStartTok  [@cartoucheableGlyph]'   lookup add_cartouche_middle;

  # If a glyph follows a cartouche middle, add a cartouche middle after the glyph.
  sub   cartoucheMiddleTok [@cartoucheableGlyph]'   lookup add_cartouche_middle;
  # # (Bug: The following line doesn't do anything? So instead, we draw the cartouche middle twice, making cartouche middles too thick.)
  # sub   cartoucheMiddleTok space [@cartoucheableGlyph]'   lookup add_cartouche_middle;

  # # Stacked glyphs
  # # (Bug: The following lines don't do anything? So instead, we draw the cartouche middle twice, making cartouche middles too thick.)
  # sub   cartoucheStartTok [@stackableBottom] [@stackableTop]'   lookup add_cartouche_middle;
  # sub   cartoucheMiddleTok [@stackableBottom] [@stackableTop]'   lookup add_cartouche_middle;
} calt;









"""

        # print(ligatures_string)
        feature_file = open(debug_dir + os.sep + family + ".fea", "w", encoding="utf-8")
        feature_file.write(ligatures_string)
        feature_file.close()

        from fontTools import ttLib  # camelCase!
        tt = ttLib.TTFont(infile)
        from fontTools.feaLib import builder  # camelCase!
        # with `addOpenTypeFeatures          (tt, file,   debug=True)`, the debug info includes the .fea filename.
        # with `addOpenTypeFeaturesFromString(tt, string, debug=True)`, the filename is only reported as `<feature>`.
        builder.addOpenTypeFeaturesFromString(tt, ligatures_string, debug=True)
        sys.stderr.write("Generating %s...\n" % outfile)
        tt.save(outfile)
        print("\a")









        #    ▄                █
        #   ▀█▀  ▄▀▀▄  █▀▄▀▄  █
        #    █   █  █  █ █ █  █
        # ▄  ▀▄  ▀▄▄▀  █ █ █  █
        # generate .toml file

        from datetime import datetime
        ilo_linku_toml_file = open(out_dir + os.sep + family + ".toml", "w", encoding="utf-8")
        ilo_linku_toml_file.write('''#:schema ../../api/generated/font.json
id        = "''' + family + '''"
name      = "''' + family + '''"
filename  = "''' + filename + '''"
creator   = ["''' + designer + '''"]
license   = "''' + license + '''"
ligatures = true
ucsur     = true
writing_system = "sitelen pona" # pick one: sitelen pona, sitelen sitelen, alphabet, syllabary, logography,
                                # tokiponido alphabet, tokiponido syllabary, tokiponido logography

last_updated = "''' + datetime.now().strftime("%Y-%m") + '''"
version      = "1"

features = [
  "ASCII transcription and codepoints",
  "UCSUR-compliant",
  "cartouches",
  "SP Font Maker words v2.2",        # unless they didn't fill out all the words

  # "incomplete",
  # "variable weight",
  # "name glyphs",
  # "character variants",
  # "Linku common & uncommon 2024"   # nimisin
  # "all ku suli",                   # kokosila
  # "all ku suli and UCSUR words",   # kokosila, apeja, pake, powe
  # "community requested nimisin",

  # Not implemented in SP Font Maker:
  # "long pi",
  # "randomized jaki",
  # "ZWJ sequences",
  # "tuki tiki",
]

# Pick one style, or put multiple comma-separated styles in quotes.''')

        pixel = cli_args_dict.get("pixel") or False
        if pixel:
            ilo_linku_toml_file.write('''
# style = "handwritten"
style = "pixelated"''')
        else:
            ilo_linku_toml_file.write('''
style = "handwritten"
# style = "pixelated"''')

        ilo_linku_toml_file.write('''
# style = "alternate design"
# style = "uniform line weight"
# style = "handdrawn"
# style = "serif"
# style = "sans-serif"
# style = "faux 3d"
# style = "unspecified"

[links]
# Autofilled for Kelly's site. If you're not uploading to Kelly's site, these URLs are inaccurate; upload the font to a website like neocities.org or github.io
# fontfile = "https://github.com/wasokeli/wasokeli.github.io/raw/main/sp-font-maker/''' + filename.replace(" ", "%20") + '''"
# repo     = "https://github.com/wasokeli/wasokeli.github.io/tree/main/sp-font-maker"
# webpage  = "https://wasokeli.github.io/sp-font-maker/''' + family.replace(" ", "-") + '''.html"
''')
        # print("Generating " + out_dir + os.sep + family + ".toml for ilo Linku...")
        ilo_linku_toml_file.close()

        print("🌐 If hosting, give this to " + designer + ": https://wasokeli.github.io/sp-font-maker/" + family.replace(" ", "-"))
        print("🏠 Preview in browser: file://" + os.path.abspath(out_dir + os.sep + family.replace(" ", "-") + ".html").replace("\\", "/") + "\n")

        generate_web_page(out_dir, filename, family, designer, license, licenseurl, other_words_string)









    #              █
    # █   █  ▄▀▀▄  █▀▀▄       █▀▀▄   ▀▀▄  ▄▀▀█  ▄▀▀▄
    # █ █ █  █▄▄█  █  █       █  █  ▄▀▀█  █  █  █▄▄█
    #  █ █   ▀▄▄   █▄▄▀       █▄▄▀  ▀▄▄█  ▀▄▄█  ▀▄▄
    #                         █            ▄▄▀

def generate_web_page(out_dir, filename, family, designer, license, licenseurl, other_words_string=None):
        other_words = []
        if other_words_string:
            other_words = other_words_string.split()
            for word_index, word in enumerate(other_words):
                if word == "_":
                    other_words[word_index] = "|"

        example_web_page = open(out_dir + os.sep + family.replace(" ", "-") + ".html", "w", encoding="utf-8")

        # # this fails because i'm feeding it a relative path on the command line... hmm...
        # # and now it fails because the "C:" part doesn't get underlined on the C
        # # also it needs to have forward slashes
        # # uuuggghhhh
        # print("Local web page: file:///" + os.path.abspath(out_dir + os.sep + family.replace(" ", "-") + ".html"))

        example_web_page.write(
"""
<meta charset="utf-8" />
<style type=\"text/css\">
    @font-face {
        font-family: '""" + family + """';
        src: url('""" + filename + """')
    }
    body {
        background-color: #334;
        font-size: 48px;
        /*font-size: 32px;*/ /* for slideshow */
        max-width: 960px;    /* 48 x 20 */
        margin: auto;
        /*line-height: 1.5em;*/
        color: white;
        font-family: "Chalkboard SE", "Comic Sans MS", sans-serif;
    }
    h1 {
        font-size: 1em;
        /*margin-bottom: 0;*/ /* for slideshow */
    }
    a {
        color: white;
    }
    .tp {
        font-family: '""" + family + """', 'Chalkboard SE', 'Comic Sans MS', sans-serif;
        font-size: 48px;
    }
    textarea {
        font-size: 1em; 
        width: 20em; 
        height: 100%; 
        background-color: #223; 
        color: white; 
        padding: 1em;
    }
</style>
<h1>""" + "<a href='" + filename + "'>" + family + "</a>, tan " + designer + """</h1>

<span class="tp">
<!-- word list -->
a akesi ala alasa ale anpa ante anu awen e en esun ijo ike ilo insa jaki jan jelo jo<br>
kala kalama kama kasi ken kepeken kili kiwen ko kon kule kulupu kute la lape laso lawa len lete li<br>
lili linja lipu loje lon luka lukin lupa ma mama mani meli mi mije moku moli monsi mu mun musi<br>
mute nanpa nasa nasin nena ni nimi noka o olin ona open pakala pali palisa pan pana pi pilin pimeja<br>
pini pipi poka poki pona pu sama seli selo seme sewi sijelo sike sin sina sinpin sitelen sona soweli suli<br>
suno supa suwi tan taso tawa telo tenpo toki tomo tu unpa uta utala walo wan waso wawa weka wile<br>
[] . : i j k l m p s t u w te to """ + " ".join(other_words[0:4]) + """<br>
kijetesantakalu kin kipisi ku lanpan leko misikeke monsuta n namako soko tonsi """ + " ".join(other_words[4:12]) + """<br>
epiku jasima linluwi majuna meso oko su """ + " ".join(other_words[12:25]) + """<br>
</span>

<p>License: <a href='""" + licenseurl + """'>""" + license + """</a></p>

<span class="tp">
<span style="white-space: break-spaces">
<!-- telo oko li ken ante e pilin, by jan Ke Tami -->
toki ni li kepeken nimi pu ale

telo oko li ken ante e pilin
tan jan [kiwen en] [tomo anu mi insa]:

| telo li kama 
| | | tan oko loje tu pi(jan wan)
| | li sitelen sike suwi 
| | | lon anpa sinpin 
| ona li wile tawa ma
taso ona li awen lon sijelo
| | li pini 
| | | lon len 
| | li weka
sona la
| waso en kala en pipi 
| en akesi en soweli ale li ken pana sama
taso pilin pi(jan ni) li suli la 
| | | | | | | telo lukin li sin
| | | | | | | | | li wawa
| | | | | | | | | li selo e ijo poka 
| | | | | | | | | | | e tomo e noka e supa moku 
| | | | | | | | | | | e pan e poki kiwen e monsi 
| | | | | | | | | | | e luka e lawa e nena 
| | | | | | | | | | | e kute e linja sewi kin
laso lete ni li lili e seli insa
| | | li lape e ike toki
| | | li open e ante
| | | li esun e ko jaki| | | | | te a
| | | | | e mu open| | | | | | ike a to

kon pi(kule ala) li tan uta 
| | | | li kalama utala lon telo 
| | | | li nanpa mute 
| | | | li tawa mun 
| | | | li pakala nasa e suno sewi
pimeja moli li kama namako e nasin tenpo| | | | | te mi pakala to


pona o kepeken alasa seme
| mani anu unpa 
anu pu anu nimi ante li sama kili 
| | | | | | tan kasi pi(lipu jelo moli)
te sina wile ala ni
| sina wile mama e musi
| sina wile olin e meli 
| | | | e mije e tonsi to| | | | | ona li jo e ilo palisa 
| | | | | | | | | | | | | | | | | e sinpin tomo 
| | | | | | | | | | | | | | | li pali e lupa
| | | | | | | | | | | | | | telo li kama weka
| | | | | | | | | | | | | | laso li kama walo
| | | | | | | | | | | | | | jan li tawa lupa 
| | | | | | | | | | | | | | | li tawa nasin open 
| | | | | | | | | | | | | | | li tawa kulupu
| | | | | | | | | | | | | pona kama li wile e wawa
| | | | | | | | | | | | taso laso weka li kama ken e ni


<textarea class="tp">sina ken sitelen-wile lon ni<v

</textarea>
</span></span>

<script>
/*  workaround for Chromium

    Chrome has a bug where ligatures aren't properly applied at typing-time. 
    for example, if you type "pona", it erroneously shows a p followed by a sideways 6, rather than one smile.
    i work around this by refreshing the textarea after every keystroke.
    i refresh the textarea by changing one property, back and forth between two values that will result in the same appearance on most modern devices.
*/

const textarea = document.querySelector('textarea');
var cssToggle = false;

textarea.addEventListener('input', redrawTextarea);

function redrawTextarea(e) {
  if (cssToggle) {
    textarea.style.fontVariantLigatures = 'normal';
    cssToggle = false;
  } else {
    textarea.style.fontVariantLigatures = 'common-ligatures';
    cssToggle = true;
  }
}
</script>
"""
        )
        example_web_page.close()









        #  ▀  █             █      ▀        █                                         ▀
        # ▀█  █  ▄▀▀▄       █     ▀█  █▀▀▄  █ ▄▀  █  █       █▀▀▄  █▄▀  ▄▀▀▄  █   █  ▀█  ▄▀▀▄  █   █
        #  █  █  █  █       █      █  █  █  █▀▄   █  █       █  █  █    █▄▄█   █ █    █  █▄▄█  █ █ █
        #  █  █  ▀▄▄▀       █▄▄▄   █  █  █  █  █  ▀▄▄█       █▄▄▀  █    ▀▄▄     █     █  ▀▄▄    █ █
        #                                                    █
        # # test ilo Linku rendering
        # # disabled because i don't have RAQM, so i can't test it
        # # and it seems to be hard to install on Windows
        # # and i don't want to bother with WSL
        # # i probably should though...

        # from PIL import Image, ImageDraw, ImageFont
        # from PIL import features

        # # Check if RAQM support is enabled in Pillow
        # if features.check_feature('raqm'):
        #     print("RAQM support is enabled in Pillow.")
        # else:
        #     print("RAQM support is NOT enabled in Pillow. Linku rendering is probably borked.")

        # from typing import Any, Dict, List, Literal
        # BgStyle = Literal["outline"] | Literal["background"]
        # Color = tuple[int, int, int]
        # ColorAlpha = tuple[int, int, int, int]

        # def display(text: str, font_path: str, font_size: int, color: Color, bgstyle: BgStyle):
        #     STROKE_WIDTH = round((font_size / 133) * 5)
        #     LINE_SPACING = round((font_size / 2))

        #     HPAD = round(font_size / 30)
        #     # NOTE: the VPAD is high because keli's font tool produces fonts which cut off on the top otherwise
        #     VPAD = round(font_size / 4) + 5

        #     BLACK: ColorAlpha = (0x36, 0x39, 0x3F, 0xFF)
        #     WHITE: ColorAlpha = (0xF0, 0xF0, 0xF0, 0xFF)
        #     TRANSPARENT: ColorAlpha = (0, 0, 0, 0)

        #     stroke_color = BLACK if True else WHITE
        #     bg_color = stroke_color if bgstyle == "background" else TRANSPARENT

        #     font = ImageFont.truetype(font_path, font_size)
        #     d = ImageDraw.Draw(Image.new("RGBA", (0, 0), (0, 0, 0, 0)))
        #     x, y, w, h = d.multiline_textbbox(
        #         (0, 0),
        #         text=text,
        #         font=font,
        #         spacing=LINE_SPACING,
        #         stroke_width=STROKE_WIDTH,
        #         font_size=font_size,
        #     )
        #     image = Image.new(
        #         mode="RGBA",
        #         size=(w + (HPAD * 2), h + (VPAD * 2)),
        #         color=bg_color,
        #     )
        #     d = ImageDraw.Draw(image)
        #     d.multiline_text(
        #         (HPAD, VPAD),
        #         text,
        #         font=font,
        #         fill=color,
        #         spacing=LINE_SPACING,
        #         stroke_width=STROKE_WIDTH,
        #         stroke_fill=stroke_color,
        #     )
        #     image.save(out_dir + os.sep + "LINKU TEST - " + family + ".png")

        # display(
        #     "󱤴󱥴󱦐󱤗󱤋󱤦󱤎󱦑󱤀", 
        #     out_dir + os.sep + family + ".ttf",
        #     72,
        #     (0x0C, 0xAF, 0xF5),
        #     "outline"
        # )
