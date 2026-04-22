# Handles 4 things:
# 1. Create a .toml to submit to ilo-Linku/sona/fonts/metadata
# 2. Add a line to `wasokeli/wasokeli.github.io/sp-font-maker/generate all fonts.bat`
# 3. Create the web page for previewing the font
# 4. Preview how the font will look with the ilo Linku renderer. (Currently not working
#    and commented out)

import json
import os
import platform
import subprocess
from datetime import datetime

#    ▄            █
#   ▀█▀ ▄▀▄ █▀▄▀▄ █
# ▄  ▀▄ ▀▄▀ █ █ █ █


def create_toml_html(
    debug_dir, out_dir, default_json, cli_args=None, other_words_string=None
):
    cli_args_dict = cli_args

    filename = cli_args_dict.get("filename", "Untitled")
    if filename is None:
        raise NameError("filename not found in config file.")

    family = cli_args_dict.get("family", None) or filename

    filename = filename + ".ttf" if not filename.endswith(".ttf") else filename
    filename_stripped = filename[:-4] if filename.endswith(".ttf") else filename

    designer = cli_args_dict.get("designer", "jan pi toki pona")

    # Only say designer once in web page title
    short_family, short_tan, short_designer = family.partition(" tan ")
    if not short_designer == designer:
        short_family = family

    # For generating the ilo Linku TOML files for each font,
    # we use short license codes from the SPDX License List: https://spdx.org/licenses/
    license = cli_args_dict.get("license", "All rights reserved")
    licenseurl = cli_args_dict.get("license_url", "")
    if license == "ofl":
        license = "OFL-1.1"
        licenseurl = "https://openfontlicense.org"
    if license == "cc0":
        license = "CC0-1.0"
        licenseurl = "https://creativecommons.org/publicdomain/zero/1.0/"

    not_new = cli_args_dict.get("not_new", False)
    if not_new:
        print("\nSkipping ilo Linku .TOML file.\n")
    else:
        s = os.sep
        # If the user has ilo Linku's "sona" repo on their local machine, put the .toml
        # in there for easy updating.
        # Two folders up from /wasokeli.github.io/sp-font-maker/:
        two_levels_up = f"{out_dir}..{s}..{s}sona{s}fonts{s}metadata"
        one_level_up = f"{out_dir}..{s}sona{s}fonts{s}metadata"
        sona_repo_path = ""
        if os.path.isdir(two_levels_up):
            sona_repo_path = two_levels_up
        # Theoretically, some flatter folder:
        elif os.path.isdir(one_level_up):
            sona_repo_path = one_level_up
        if not sona_repo_path == "":
            ilo_linku_toml_file_path = f"{sona_repo_path}{s}{filename_stripped}.toml"
            if os.path.exists(ilo_linku_toml_file_path):
                print(
                    f"\nOverwriting `{ilo_linku_toml_file_path}`, and opening for editing. To skip, add `--not-new`.\n"
                )
            else:
                print(
                    f"\nOpening `{ilo_linku_toml_file_path}` for editing. To skip, add `--not-new`.\n"
                )
        else:
            # Otherwise, just put it in out_dir.
            ilo_linku_toml_file_path = out_dir + os.sep + filename_stripped + ".toml"
            if os.path.exists(ilo_linku_toml_file_path):
                print(
                    f"\nOverwriting ilo Linku .TOML, and opening for editing. To skip, add `--not-new`.\n"
                )
            else:
                # New file in debug folder
                print(
                    f"\nOpening ilo Linku .TOML for editing. To skip, add `--not-new`.\n"
                )
        ilo_linku_toml_file = open(ilo_linku_toml_file_path, "w", encoding="utf-8")
        ilo_linku_toml_file.write(f"""#:schema ../../api/generated/v2/font.json

# To submit your font to ilo Linku, for use with the Discord `/sitelenpona` command:
# 1. Upload your font to a website, like GitHub or Neocities
# 2. Add the URL to your .TTF file at the bottom of this .TOML file
# 3. Fill out the rest of this .TOML file. If you don't have a repo or a webpage, leave those blank
# 4. Submit the .TOML to this page: https://github.com/lipu-linku/sona/tree/main/fonts/metadata
# 5. Ask for help if you need it! Join the Linku Discord, or make a GitHub Issue on lipu-linku/sona.

id        = "{filename_stripped.replace("-", " ")}"
name      = "{family}"
filename  = "{filename}"
author    = ["{designer}"]
license   = "{license}"
ligatures = true
ucsur     = true
writing_system = "sitelen pona" # pick one: sitelen pona, sitelen sitelen, alphabet, syllabary, logography,
                                # tokiponido alphabet, tokiponido syllabary, tokiponido logography

last_updated = "{datetime.now().strftime("%Y-%m")}"
version      = "1"
""")
        other_words = []
        apeja = False
        pake = False
        powe = False
        prefix_nimisin = "# "
        prefix_kokosila = "# "
        prefix_names = "# "
        prefix_variants = "# "
        if other_words_string:
            other_words = other_words_string.split()
            for word_index, word in enumerate(other_words):
                if word == "nimisin":
                    prefix_nimisin = ""
                if word == "kokosila":
                    prefix_kokosila = ""
                if word == "apeja":
                    apeja = True
                if word == "pake":
                    pake = True
                if word == "powe":
                    powe = True
                if word[0].isupper():
                    prefix_names = ""
                if any(char.isdigit() for char in word):
                    prefix_variants = ""
        prefix_ucsur_2022 = "# "
        if prefix_kokosila == "" and apeja and pake and powe:
            prefix_ucsur_2022 = ""

        prefix_handwritten = ""
        prefix_pixelated = "# "
        pixel = cli_args_dict.get("pixel") or False
        if pixel:
            prefix_handwritten = "# "
            prefix_pixelated = ""

        ilo_linku_toml_file.write(f"""
features = [
  "ASCII transcription and codepoints",
  "UCSUR-compliant",
  "cartouches",
  "SP Font Maker words v2.2",        # unless they didn't fill out all the words

  # "incomplete",
  # "variable weight",
  {prefix_names}"name glyphs",
  {prefix_variants}"character variants",
  {prefix_nimisin}"Linku common & uncommon 2024",  # nimisin
  {prefix_kokosila}"all ku suli",                   # kokosila
  {prefix_ucsur_2022}"all UCSUR 2022 words",          # kokosila, apeja, pake, powe
  # "community requested nimisin",

  # Not implemented in SP Font Maker:
  # "long pi",
  # "randomized jaki",
  # "ZWJ sequences",
  # "tuki tiki",
]

# Pick one style, or put multiple comma-separated styles in quotes.
{prefix_handwritten}style = "handwritten"
# style = "alternate design"
# style = "uniform line weight"
{prefix_pixelated}style = "pixelated"
# style = "handdrawn"
# style = "serif"
# style = "sans-serif"
# style = "faux 3d"
# style = "unspecified"

[links]
# Autofilled for Kelly's site. If you're not uploading to Kelly's site, these URLs are inaccurate; upload the font to a website like neocities.org or github.io
# fontfile = "https://wasokeli.github.io/sp-font-maker/{filename.replace(" ", "%20")}"
# webpage  = "https://wasokeli.github.io/sp-font-maker/{filename_stripped.replace(" ", "-")}.html"
# repo     = "https://github.com/wasokeli/wasokeli.github.io/tree/main/sp-font-maker"
""")
        ilo_linku_toml_file.close()

        if platform.system() == "Windows":
            os.startfile(ilo_linku_toml_file_path)
        elif plaform.system() == "Darwin":  # macOS
            try:
                subprocess.run(["open", ilo_linku_toml_file_path])
            except:
                pass
        elif plaform.system() == "Linux":
            try:
                subprocess.run(["xdg-open", ilo_linku_toml_file_path])
            except:
                pass

    print(
        f"🌐 If hosting, give this to {designer}: "
        + f"https://wasokeli.github.io/sp-font-maker/{filename_stripped.replace(' ', '-')}"
    )
    print(
        "🏠 Preview in browser: file://"
        + os.path.abspath(
            out_dir + os.sep + filename_stripped.replace(" ", "-") + ".html"
        ).replace("\\", "/")
        + "\n"
    )

    #   █        ▄
    #   █▀▄ ▄▀█ ▀█▀
    # ▄ █▄▀ ▀▄█  ▀▄

    # Add to `generate_all_fonts.bat`, if it exists.
    bat_path = f"{out_dir}{os.sep}generate all fonts.bat"
    bat_string = ""
    if os.path.exists(bat_path):
        if not not_new:
            bat_file = open(bat_path, "a", encoding="utf-8")
            c = cli_args_dict
            bat_string += f"\nhandwrite --debug-directory ./debug/ "
            if c["sheet_version"]:
                bat_string += f"--sheet-version {c['sheet_version'].ljust(5)} "
            else:
                bat_string += f"                      "
            if c["license"]:
                if len(c["license"]) == 3:
                    bat_string += f"--license {c['license']} "
                else:
                    # Write license later, for alignment.
                    bat_string += f"              "
            else:
                bat_string += f"              "
            if c["designer"]:
                bat_string += f"--designer {f'"{c['designer']}"'.ljust(20)} "
            else:
                bat_string += f"                                "
            if c["family"]:
                bat_string += f"--family {f'"{c['family']}"'.ljust(33)} "
            if c["filename"]:
                # If filename is just family with hyphens, then we can omit it, because
                # the script generates that filename anyway
                if c.get("family", "").replace(" ", "-") != c["filename"]:
                    bat_string += f'--filename "{c["filename"]}" '
            bat_string += f"{c['input_path']} "
            bat_string += f"{c['output_directory']} "
            if c["other_words"]:
                bat_string += f'--other-words "{c["other_words"]}" '
            if c["license"]:
                if len(c["license"]) != 3:
                    bat_string += f'--license "{c["license"]}" '
            if c["license_url"]:
                bat_string += f'--license-url "{c["license_url"]}" '
            if c["pixel"]:
                bat_string += f"--pixel"
            bat_file.write(bat_string)
            print("Nicely-formatted command for Kelly's .bat file:", bat_string)
            print()
            bat_file.close()

    #           █
    # █ █ █ ▄▀▄ █▀▄    █▀▄ ▄▀█ ▄▀█ ▄▀▄
    #  █ █  ▀█▄ █▄▀    █▄▀ ▀▄█ ▀▄█ ▀█▄
    #                  █       ▄▄▀

    example_web_page = open(
        out_dir + os.sep + filename_stripped.replace(" ", "-") + ".html",
        "w",
        encoding="utf-8",
    )

    example_web_page.write(f"""
<meta charset="utf-8" />
<style type=\"text/css\">
    @font-face {{
        font-family: '{family}';
        src: url('{filename}')
    }}
    body {{
        background-color: #334;
        font-size: 48px;
        /*font-size: 32px;*/ /* for slideshow */
        max-width: 960px;    /* 48 x 20 */
        margin: auto;
        /*line-height: 1.5em;*/
        color: white;
        font-family: "Chalkboard SE", "Comic Sans MS", sans-serif;
    }}
    h1 {{
        font-size: 1em;
        /*margin-bottom: 0;*/ /* for slideshow */
    }}
    a {{
        color: white;
    }}
    .tp {{
        font-family: '{family}', 'Chalkboard SE', 'Comic Sans MS', sans-serif;
        font-size: 48px;
    }}
    .word-list {{
        display: flex;
        flex-wrap: wrap;
        align-items: start;
        align-content: flex-start;
    }}
    .word {{
        width: 48px;
        text-align: center;
    }}
    .label {{
        font-family: 'Chalkboard SE', 'Comic Sans MS', sans-serif;
        font-size: 16px;
        min-height: 48px;
        width: 48px;
        display: inline-block;
        opacity: 0.5;
        overflow-wrap: break-word;
    }}
    .hidden.label {{
        display: none;
    }}
    .license-and-checkbox {{
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }}
    .checkbox {{
        font-size: 16px;
        opacity: 0.5;
    }}
    textarea {{
        font-size: 1em;
        width: 20em;
        height: 100%;
        background-color: #223;
        color: white;
        padding: 1em;
    }}
</style>
<h1><a href='{filename}'>{short_family}</a>, tan {designer}</h1>
<!-- vertical test -->
<!-- <p class="tp" style="writing-mode: vertical-rl; font-feature-settings: 'calt';"> -->
<!-- 󱤴󱤑󱦐󱥠󱦜󱤑󱦜󱤧󱦝󱦑<br> -->
<!-- 「󱤴󱥠󱤉󱥁󱥧󱥚󱥩󱤅」<br> -->
<!-- </p> -->
<span class="tp">
    <!-- word list -->
""")

    # Word list
    with open(default_json) as f:
        default_json_data = json.load(f)
    glyphs = default_json_data.get("glyphs", {})
    glyphs_sheet = glyphs.get("sheet", [])
    glyphs_codepoints = (
        glyphs.get("derived", []) + glyphs.get("spaces", []) + glyphs_sheet
    )
    # Dict of glyph name to glyph data, for getting the codepoint from the name
    glyphs_cached = {
        item["name"]: {k: v for k, v in item.items() if k != "name"}
        for item in glyphs_codepoints
        if "name" in item
    }
    word_list = ""
    hyphenations = {
        "kalama": "ka&shy;lama",
        "kepeken": "kepe&shy;ken",
        "kulupu": "ku&shy;lupu",
        "pakala": "pa&shy;kala",
        "pimeja": "pi&shy;meja",
        "sinpin": "sin&shy;pin",
        "kijetesantakalu": "kijete&shy;santa&shy;kalu",
        "lanpan": "lan&shy;pan",
        "misikeke": "misi&shy;keke",
        "monsuta": "mon&shy;suta",
        "namako": "na&shy;mako",
        "jasima": "ja&shy;sima",
        "linluwi": "lin&shy;luwi",
        "majuna": "ma&shy;juna",
        "kokosila": "koko&shy;sila",
        "melome": "me&shy;lome",
        "silapa1": "sila&shy;pa1",
        "silapa2": "sila&shy;pa2",
        "silapa3": "sila&shy;pa3",
        "snoweli": "sno&shy;weli",
        "wasoweli": "waso&shy;weli",
    }
    for glyph in glyphs_sheet:
        # The glyph field doesn't include the unescaped string to type a glyph. For
        # glyphs with ligatures, we convert from the ligature back into the original
        # string.
        #
        # Note that this isn't recursive. It will break with two-layer ligatures. In
        # that case, probably hard-code individual cases.

        word = ""
        word_label = ""
        if "ligature" in glyph:
            # Words, like soweli
            for letter in glyph["ligature"].split(" "):
                letter_string = chr(
                    glyphs_cached.get(letter, {}).get("codepoint", 0x20)
                )
                word += letter_string
                word_label += letter_string
                if letter_string == "-" or letter_string == "+" or letter_string == "&":
                    word_label += "<br>"
            if word.startswith(","):
                # Tally mark. Prepend with a space so that it doesn't combine with the
                # previous character, then insert a combining cartouche extension so
                # that the tally isn't hidden.
                word = "|=" + word
            if word in hyphenations:
                word_label = hyphenations[word]
        else:
            if "name" in glyph:
                # Letters: ijklmpstuw
                word += glyph["name"]
            else:
                # Blank writeins
                word += "|"
                word_label = " "
        word_list += (
            '        <div class="word">'
            + word
            + "<br>"
            + '<span class="hidden label">'
            + (word_label or word)
            + "</span>"
            + "</div>"
            + "\n"
        )

    example_web_page.write('    <div class="word-list">\n' + word_list + "</div>")

    example_web_page.write(
        f"""
</span>

<p class="license-and-checkbox">
    <span>License: <a href='{licenseurl}'>{license}</a></span>
    <span><input type="checkbox" id="labelsCheckbox" onchange="toggleLabels()" class="checkbox"><label for="labelsCheckbox" class="checkbox">Label glyphs</label></span>
</p>

<span class="tp">
<textarea class="tp" title="sina ken pana-wile e kulupu&sitelen lon ni<v">sina ken pana-wile e kulupu&sitelen lon ni<v

</textarea>
</span>

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
| | | li esun e ko jaki | | | | | te a
| | | | | e mu open | | | | | | ike a to

kon pi(kule ala) li tan uta
| | | | li kalama utala lon telo
| | | | li nanpa mute
| | | | li tawa mun
| | | | li pakala nasa e suno sewi
pimeja moli li kama namako e nasin tenpo | | | | | te mi pakala to


pona o kepeken alasa seme
| mani anu unpa
anu pu anu nimi ante li sama kili
| | | | | | tan kasi pi(lipu jelo moli)
te sina wile ala ni
| sina wile mama e musi
| sina wile olin e meli
| | | | e mije e tonsi to | | | | | ona li jo e ilo palisa
| | | | | | | | | | | | | | | | | e sinpin tomo
| | | | | | | | | | | | | | | li pali e lupa
| | | | | | | | | | | | | | telo li kama weka
| | | | | | | | | | | | | | laso li kama walo
| | | | | | | | | | | | | | jan li tawa lupa
| | | | | | | | | | | | | | | li tawa nasin open
| | | | | | | | | | | | | | | li tawa kulupu
| | | | | | | | | | | | | pona kama li wile e wawa
| | | | | | | | | | | | taso laso weka li kama ken e ni


</span></span>
"""
        + """
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



function toggleLabels() {
  const labels = document.querySelectorAll('.label');
  const labelGlyphsCheckbox = document.getElementById('labelsCheckbox');

  labels.forEach(label => {
    if (labelGlyphsCheckbox.checked) {
      label.classList.remove('hidden');
    } else {
      label.classList.add('hidden');
    }
  });
}
</script>
"""
    )
    example_web_page.close()

    # ▀ █        █   ▀     █                          ▀
    # █ █ ▄▀▄    █   █ █▀▄ █▄▀ █ █    █▀▄ █▄▀ ▄▀▄ █ █ █ ▄▀▄ █ █ █
    # █ █ ▀▄▀    █▄▄ █ █ █ █ █ ▀▄█    █▄▀ █   ▀█▄  █  █ ▀█▄  █ █
    #                                 █
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
