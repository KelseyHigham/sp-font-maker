import os
import json
from datetime import datetime






#    ▄                █
#   ▀█▀  ▄▀▀▄  █▀▄▀▄  █
#    █   █  █  █ █ █  █
# ▄  ▀▄  ▀▄▄▀  █ █ █  █
# generate .toml file

def create_toml_html(debug_dir, out_dir, cli_args=None, other_words_string=None):

    cli_args_dict = cli_args

    filename = (cli_args_dict.get("filename", "Untitled"))
    if filename is None:
        raise NameError("filename not found in config file.")

    family = (cli_args_dict.get("family", None) or filename)

    filename = filename + ".ttf" if not filename.endswith(".ttf") else filename

    designer = cli_args_dict.get("designer", "jan pi toki pona")

    # for generating the ilo Linku TOML files for each font,
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
        # If the user has ilo Linku's "sona" repo on their local machine, put the .toml in there for easy updating.
        if os.path.isdir(f"{out_dir}..{s}..{s}sona{s}fonts{s}metadata"): # two folders up from /wasokeli.github.io/sp-font-maker/
            sona_repo_path = f"{out_dir}..{s}..{s}sona{s}fonts{s}metadata"
        elif os.path.isdir(f"{out_dir}..{s}sona{s}fonts{s}metadata"): # theoretically, some flatter folder
            sona_repo_path = f"{out_dir}..{s}sona{s}fonts{s}metadata"
        if sona_repo_path:
            ilo_linku_toml_file_path = f"{sona_repo_path}{s}{family}.toml"
            if os.path.exists(f"{sona_repo_path}{s}{family}.toml"):
                print(f"\nOverwriting `{sona_repo_path}{s}{family}.toml`, and opening for editing. To skip, add `--not-new`.\n")
            else:
                print(f"\nOpening `{sona_repo_path}{s}{family}.toml` for editing. To skip, add `--not-new`.\n")
        else:
            # Otherwise, just put it in out_dir.
            ilo_linku_toml_file_path = out_dir + os.sep + family + ".toml"
            if os.path.exists(f"{out_dir}{s}{family}.toml"):
                print(f"\nOverwriting ilo Linku .TOML, and opening for editing. To skip, add `--not-new`.\n")
            else:
                # New file in debug folder
                print(f"\nOpening ilo Linku .TOML for editing. To skip, add `--not-new`.\n")
        ilo_linku_toml_file = open(ilo_linku_toml_file_path, "w", encoding="utf-8")
        ilo_linku_toml_file.write('''#:schema ../../api/generated/font.json

# To submit your font to ilo Linku, for use with the Discord `/sitelenpona` command:
# 1. Upload your font to a website, like GitHub or Neocities
# 2. Add the URL to your .TTF file at the bottom of this .TOML file
# 3. Fill out the rest of this .TOML file. If you don't have a repo or a webpage, leave those blank
# 4. Submit the .TOML to this page: https://github.com/lipu-linku/sona/tree/main/fonts/metadata
# 5. Ask for help if you need it! Join the Linku Discord, or make a GitHub Issue on lipu-linku/sona.

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
''')
        other_words = []
        apeja = False
        pake  = False
        powe  = False
        prefix_nimisin  = "# "
        prefix_kokosila = "# "
        prefix_names    = "# "
        prefix_variants = "# "
        if other_words_string:
            other_words = other_words_string.split()
            for word_index, word in enumerate(other_words):
                if word == "nimisin":
                    prefix_nimisin  = ""
                if word == "kokosila":
                    prefix_kokosila = ""
                if word == "apeja":
                    apeja = True
                if word == "pake":
                    pake  = True
                if word == "powe":
                    powe  = True
                if word[0].isupper():
                    prefix_names    = ""
                if any(char.isdigit() for char in word):
                    prefix_variants = ""
        prefix_ucsur = "# "
        if prefix_kokosila == "" and apeja and pake and powe:
            prefix_ucsur = ""

        prefix_handwritten = ""
        prefix_pixelated = "# "
        pixel = cli_args_dict.get("pixel") or False
        if pixel:
            prefix_handwritten = "# "
            prefix_pixelated = ""

        ilo_linku_toml_file.write(f'''
features = [
  "ASCII transcription and codepoints",
  "UCSUR-compliant",
  "cartouches",
  "SP Font Maker words v2.2",        # unless they didn't fill out all the words

  # "incomplete",
  # "variable weight",
  {prefix_names}"name glyphs",
  {prefix_variants}"character variants",
  {prefix_nimisin}"Linku common & uncommon 2024"   # nimisin
  {prefix_kokosila}"all ku suli",                   # kokosila
  {prefix_ucsur}"all ku suli and UCSUR words",   # kokosila, apeja, pake, powe
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
# fontfile = "https://wasokeli.github.io/sp-font-maker/''' + filename.replace(" ", "%20") + '''"
# webpage  = "https://wasokeli.github.io/sp-font-maker/''' + family.replace(" ", "-") + '''.html"
# repo     = "https://github.com/wasokeli/wasokeli.github.io/tree/main/sp-font-maker"
''')
        ilo_linku_toml_file.close()

        import platform
        import subprocess
        if platform.system() == 'Windows':
            os.startfile(ilo_linku_toml_file_path)
        elif plaform.system() == 'Darwin': # macOS
            try:
                subprocess.run(['open', ilo_linku_toml_file_path])
            except:
                pass
        elif plaform.system() == 'Linux':
            try:
                subprocess.run(['xdg-open', ilo_linku_toml_file_path])
            except:
                pass

    print("🌐 If hosting, give this to " + designer + ": https://wasokeli.github.io/sp-font-maker/" + family.replace(" ", "-"))
    print("🏠 Preview in browser: file://" + os.path.abspath(out_dir + os.sep + family.replace(" ", "-") + ".html").replace("\\", "/") + "\n")






    #     █            ▄ 
    #     █▀▀▄   ▀▀▄  ▀█▀
    #     █  █  ▄▀▀█   █ 
    #  ▄  █▄▄▀  ▀▄▄█   ▀▄
    #            


    # add to `generate_all_fonts.bat`, if it exists
    bat_path = f"{out_dir}{os.sep}generate all fonts.bat"
    if os.path.exists(bat_path):
        if not not_new:
            bat_file = open(bat_path, "a", encoding="utf-8")
            c = cli_args_dict
            bat_file.write(f"\nhandwrite --debug-directory ./debug/ ")
            if c['sheet_version']:
                bat_file.write(f"--sheet-version {c['sheet_version'].ljust(5)} ")
            else:
                bat_file.write(f"                      ")
            if c['license']:
                if len(c['license']) == 3:
                    bat_file.write(f"--license {c['license']} ")
                else:
                    # Write license later, for alignment.
                    bat_file.write(f"              ")
            else:
                    bat_file.write(f"              ")
            if c['designer']:
                bat_file.write(f'--designer {f'"{c['designer']}"'.ljust(20)} ')
            else:
                bat_file.write(f"                                ")
            if c['filename']:
                bat_file.write(f'--filename "{c['filename']}" ')
            if c['family']:
                bat_file.write(f'--family "{c['family']}" ')
            bat_file.write(f'{c['input_path']} ')
            bat_file.write(f'{c['output_directory']} ')
            if c['other_words']:
                bat_file.write(f'--other-words "{c['other_words']}" ')
            if c['license']:
                if len(c['license']) != 3:
                    bat_file.write(f'--license "{c['license']}" ')
            if c['license_url']:
                bat_file.write(f'--license-url "{c['license_url']}" ')
            if c['pixel']:
                bat_file.write(f"--pixel")
            bat_file.close()







    #              █
    # █   █  ▄▀▀▄  █▀▀▄       █▀▀▄   ▀▀▄  ▄▀▀█  ▄▀▀▄
    # █ █ █  █▄▄█  █  █       █  █  ▄▀▀█  █  █  █▄▄█
    #  █ █   ▀▄▄   █▄▄▀       █▄▄▀  ▀▄▄█  ▀▄▄█  ▀▄▄
    #                         █            ▄▄▀

    other_words = []
    if other_words_string:
        other_words = other_words_string.split()
        for word_index, word in enumerate(other_words):
            if word == "_":
                other_words[word_index] = "|"

    example_web_page = open(out_dir + os.sep + family.replace(" ", "-") + ".html", "w", encoding="utf-8")

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