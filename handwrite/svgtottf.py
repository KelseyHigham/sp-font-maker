import sys
import os
import json
import uuid
import datetime


class SVGtoTTF:
    def convert(self, directory, outdir, config, metadata=None, other_words_string=None):
        print("SVGtoTTF")
        """Convert a directory with SVG images to TrueType Font.

        Calls a subprocess to the run this script with Fontforge Python
        environment, because the FontForge libraries don't work in regular Python.

        Then uses regular Python, and fontTools, to apply ligatures.

        Then outputs a web page with examples of the font.

        Parameters
        ----------
        directory : str
            Path to directory with SVGs to be converted.
        outdir : str
            Path to output directory.
        config : str
            Path to config file.
        metadata : dict
            Dictionary containing the metadata (filename, family or style)
        """
        import subprocess
        import platform
        from packaging.version import Version
        sheet_version = metadata.get("sheetversion") or "99999999.999999.999999"

        subprocess.run(
            (
                ["ffpython"]
                if platform.system() == "Windows"
                else ["fontforge", "-script"]
            )
            + [
                os.path.abspath(__file__),
                config,
                directory,
                outdir,
                json.dumps(metadata),
                str(Version(sheet_version).major),
                str(Version(sheet_version).minor),
                str(Version(sheet_version).micro)
            ]
        )

        self.add_ligatures(directory, outdir, config, metadata, other_words_string)



    # █   ▀               ▄
    # █  ▀█  ▄▀▀█   ▀▀▄  ▀█▀  █  █  █▄▀  ▄▀▀▄  ▄▀▀▄
    # █   █  █  █  ▄▀▀█   █   █  █  █    █▄▄█   ▀▄
    # █   █  ▀▄▄█  ▀▄▄█   ▀▄  ▀▄▄█  █    ▀▄▄   ▀▄▄▀
    #         ▄▄▀

    def add_ligatures(self, directory, outdir, config, metadata=None, other_words_string=None):
        # Now the font has exported, presumably. 
        # We're back to the `python` environment, not the `ffpython` one, so we can use libraries like fontTools, camelCase.
        import fontTools  # camelCase!

        # `directory` is the temp directory

        self.metadata = json.loads(json.dumps(metadata)) or {}

        with open(config) as f:
            self.config = json.load(f)

        filename = (self.metadata.get("filename", None) or self.config["props"].get("filename", None))
        if filename is None:
            raise NameError("filename not found in config file.")

        family = (self.metadata.get("family", None) or filename)

        designer = self.metadata.get("designer", None) or self.config["props"].get("designer", "jan pi toki pona")

        # for generating the ilo Linku TOML files for each font,
        # we use short license codes from the SPDX License List: https://spdx.org/licenses/
        license = self.metadata.get("license", None) or self.config["sfnt_names"].get("License", "All rights reserved")
        licenseurl = self.metadata.get("licenseurl", None) or self.config["sfnt_names"].get("License URL", "")
        if license == "ofl":
            license = "OFL-1.1"
            licenseurl = "https://openfontlicense.org"
        if license == "cc0":
            license = "CC0-1.0"
            licenseurl = "https://creativecommons.org/publicdomain/zero/1.0/"

        # fontTools: input font file
        infile = str(directory + os.sep + (filename + " without ligatures.ttf"))
        # sys.stderr.write("\nAdding ligatures to %s\n" % infile)

        # fontTools: output font file
        filename = filename + ".ttf" if not filename.endswith(".ttf") else filename
        outfile = str(outdir + os.sep + filename)
        # while os.path.exists(outfile):
        #     filename = os.path.splitext(filename)[0] + " (1).ttf"
        #     outfile = outdir + os.sep + filename

        ligatures_string = """languagesystem DFLT dflt; # this part is apparently necessary so that people can edit the font in fontforge after??
languagesystem latn dflt;

feature liga {
"""
        list_of_ligs = []
        list_of_cartoucheable_glyphs = []

        # create ligature lines
        with open(config) as f:
            glyphs = json.load(f).get("glyphs-fancy", {})
            for k in glyphs:
                if 'ligature' in k:
                    # create tuples of ligature text, followed by ligature length by tokens
                    list_of_ligs.append((
                        "  sub " + k['ligature'] + " by " + k['name'] + ";", 
                        len(k['ligature'].split(' '))
                    ))
                    # # If you make ligatures of the format `p o n a space`, 
                    # # the spacing is incorrect in every browser on iPhone and iPad, as well as Safari for macOS.
                    # # (The browser correctly renders the ligature, but incorrectly renders an additional space.)
                    # # So I just make the space character zero-width instead,
                    # # which is redundant with `p o n a space` ligatures.
                    # list_of_ligs.append((
                    #     "  sub " + k['ligature'] + " space by " + k['name'] + ";", 
                    #     len(k['ligature'].split(' ')) + 1
                    # ))
                    list_of_cartoucheable_glyphs.append(k['name'])

        list_of_ligs.append(("  sub comma space by zerowidth;", 2))
        list_of_ligs.append(("  sub space space by ideographicspace;", 2))
        list_of_ligs.append(("  sub exclamation space by ideographicspace;", 2))
        list_of_ligs.append(("  sub question space by ideographicspace;", 2))
        list_of_ligs.append(("  sub l i n u w i by linluwiTok;", 6))
        # directional ni: extra ligatures to cover both v> and >v, and niv
        list_of_ligs.append(("  sub n i west v      by niTok.SW;", 4))
        list_of_ligs.append(("  sub n i west north  by niTok.NW;", 4))
        list_of_ligs.append(("  sub n i east north  by niTok.NE;", 4))
        list_of_ligs.append(("  sub n i east v      by niTok.SE;", 4))
        list_of_ligs.append(("  sub n i v by niTok;", 3))
        # directional akesi: extra ligatures to cover both ^> and >^, and akesi^
        list_of_ligs.append(("  sub a k e s i west v      by akesiTok.SW;", 4))
        list_of_ligs.append(("  sub a k e s i west north  by akesiTok.NW;", 4))
        list_of_ligs.append(("  sub a k e s i east north  by akesiTok.NE;", 4))
        list_of_ligs.append(("  sub a k e s i east v      by akesiTok.SE;", 4))
        list_of_ligs.append(("  sub a k e s i north by akesiTok;", 3))
        # directional pipi: extra ligatures to cover both ^> and >^, and pipi^
        list_of_ligs.append(("  sub p i p i west v      by pipiTok.SW;", 4))
        list_of_ligs.append(("  sub p i p i west north  by pipiTok.NW;", 4))
        list_of_ligs.append(("  sub p i p i east north  by pipiTok.NE;", 4))
        list_of_ligs.append(("  sub p i p i east v      by pipiTok.SE;", 4))
        list_of_ligs.append(("  sub p i p i north by pipiTok;", 3))
        # directional kala: extra ligatures to cover both ^> and >^, and kala>
        list_of_ligs.append(("  sub k a l a west v      by kalaTok.SW;", 4))
        list_of_ligs.append(("  sub k a l a west north  by kalaTok.NW;", 4))
        list_of_ligs.append(("  sub k a l a east north  by kalaTok.NE;", 4))
        list_of_ligs.append(("  sub k a l a east v      by kalaTok.SE;", 4))
        list_of_ligs.append(("  sub k a l a east by kalaTok;", 3))
        # directional kijetesantakalu: extra ligatures to cover both ^> and >^, and kijetesantakalu>
        list_of_ligs.append(("  sub k i j e t e s a n t a k a l u west v      by kijetesantakaluTok.SW;", 4))
        list_of_ligs.append(("  sub k i j e t e s a n t a k a l u west north  by kijetesantakaluTok.NW;", 4))
        list_of_ligs.append(("  sub k i j e t e s a n t a k a l u east north  by kijetesantakaluTok.NE;", 4))
        list_of_ligs.append(("  sub k i j e t e s a n t a k a l u east v      by kijetesantakaluTok.SE;", 4))
        list_of_ligs.append(("  sub k i j e t e s a n t a k a l u east by kijetesantakaluTok;", 3))
        # directional soweli: extra ligatures to cover both ^> and >^, and soweli>
        list_of_ligs.append(("  sub s o w e l i west v      by soweliTok.SW;", 4))
        list_of_ligs.append(("  sub s o w e l i west north  by soweliTok.NW;", 4))
        list_of_ligs.append(("  sub s o w e l i east north  by soweliTok.NE;", 4))
        list_of_ligs.append(("  sub s o w e l i east v      by soweliTok.SE;", 4))
        list_of_ligs.append(("  sub s o w e l i east by soweliTok;", 3))
        # directional waso: extra ligatures to cover both ^> and >^, and waso>
        list_of_ligs.append(("  sub w a s o west v      by wasoTok.SW;", 4))
        list_of_ligs.append(("  sub w a s o west north  by wasoTok.NW;", 4))
        list_of_ligs.append(("  sub w a s o east north  by wasoTok.NE;", 4))
        list_of_ligs.append(("  sub w a s o east v      by wasoTok.SE;", 4))
        list_of_ligs.append(("  sub w a s o east by wasoTok;", 3))

        # sort them by number of tokens
        list_of_ligs.sort(reverse=True, key=lambda x: x[1])

        # add to our cool string
        for line in list_of_ligs:
            ligatures_string += line[0] + "\n"

        ligatures_string += "} liga;"
        ligatures_string += """

@cartoucheableGlyph = [
  a e i j k l m n o p s t u w
  period colon space exclamation question underscore
"""
        for word in list_of_cartoucheable_glyphs:
            if (word != "cartoucheStartTok" and
                word != "cartoucheEndTok"
            ):
                ligatures_string += "  " + word + "\n"

        ligatures_string += """];

lookup add_cartouche_middle {
  # Add a cartouche middle after the glyph.
  # (The cartouche middle is zero-width and extends to the left,
  #  surrounding the glyph.)
  sub   @cartoucheableGlyph   by   @cartoucheableGlyph cartoucheMiddleTok;
} add_cartouche_middle;

# idk what keyword to use here. liga, calt, ccmp, something else?
feature calt {
  # If a glyph follows a cartouche start, add a cartouche middle after the glyph.
  sub   cartoucheStartTok  [@cartoucheableGlyph]'   lookup add_cartouche_middle;

  # If a glyph follows a cartouche middle, add a cartouche middle after the glyph.
  sub   cartoucheMiddleTok [@cartoucheableGlyph]'   lookup add_cartouche_middle;
} calt;
"""
        # print(ligatures_string)
        feature_file = open(directory + os.sep + family + ".fea", "w", encoding="utf-8")
        feature_file.write(ligatures_string)
        feature_file.close()

        from fontTools import ttLib  # camelCase!
        tt = ttLib.TTFont(infile)
        from fontTools.feaLib import builder  # camelCase!
        builder.addOpenTypeFeaturesFromString(tt, ligatures_string)
        sys.stderr.write("Generating %s...\n" % outfile)
        tt.save(outfile)



        #    ▄                █
        #   ▀█▀  ▄▀▀▄  █▀▄▀▄  █
        #    █   █  █  █ █ █  █
        # ▄  ▀▄  ▀▄▄▀  █ █ █  █

        from datetime import datetime
        ilo_linku_toml_file = open(directory + os.sep + family + ".toml", "w", encoding="utf-8")
        ilo_linku_toml_file.write('''#:schema ../../api/generated/font.json
id        = "''' + family + '''"
name      = "''' + family + '''"
filename  = "''' + filename + '''"
creator   = ["''' + designer + '''"]
license   = "''' + license + '''"
ligatures = true
ucsur     = true
writing_system = "sitelen pona"

last_updated = "''' + datetime.now().strftime("%Y-%m") + '''"
version      = "1"

features = [
  "ASCII transcription and codepoints",
  "UCSUR-compliant",
  "cartouches",

  # "incomplete",
  # "variable weight",
  # "name glyphs",
  # "character variants",
  # "all ku suli",                   # kokosila
  # "all ku suli and UCSUR words",   # apeja, pake, powe
  # "community requested nimisin",

  # Not implemented in SP Font Maker:
  # "long pi",
  # "randomized jaki",
  # "ZWJ sequences",
  # "tuki tiki",
]

# Pick one style, or put multiple comma-separated styles in quotes.
style = "handwritten"
# style = "alternate design"
# style = "uniform line weight"
# style = "pixelated"
# style = "handdrawn"
# style = "serif"
# style = "sans-serif"
# style = "faux 3d"
# style = "unspecified"

[links]
# Autofilled for Kelly. If you're not Kelly, these URLs are inaccurate; upload the font to a website like neocities.org or github.io
# fontfile = "https://github.com/wasokeli/wasokeli.github.io/raw/main/sp-font-maker/''' + filename.replace(" ", "%20") + '''"
# repo     = "https://github.com/wasokeli/wasokeli.github.io/tree/main/sp-font-maker"
# webpage  = "https://wasokeli.github.io/sp-font-maker/''' + family.replace(" ", "-") + '''.html"
''')
        print("Generating " + directory + os.sep + family + ".toml for ilo Linku...")
        ilo_linku_toml_file.close()

        print("If you're Kelly, give this to " + designer + ": https://wasokeli.github.io/sp-font-maker/" + family.replace(" ", "-") + "\n")

        self.generate_web_page(outdir, filename, family, designer, license, licenseurl, other_words_string)



    #              █
    # █   █  ▄▀▀▄  █▀▀▄       █▀▀▄   ▀▀▄  ▄▀▀█  ▄▀▀▄
    # █ █ █  █▄▄█  █  █       █  █  ▄▀▀█  █  █  █▄▄█
    #  █ █   ▀▄▄   █▄▄▀       █▄▄▀  ▀▄▄█  ▀▄▄█  ▀▄▄
    #                         █            ▄▄▀

    def generate_web_page(self, outdir, filename, family, designer, license, licenseurl, other_words_string=None):
        other_words = []
        if other_words_string:
            other_words = other_words_string.split()
            for word_index, word in enumerate(other_words):
                if word == "_":
                    other_words[word_index] = "　"

        example_web_page = open(outdir + os.sep + family.replace(" ", "-") + ".html", "w", encoding="utf-8")

        # # this fails because i'm feeding it a relative path on the command line... hmm...
        # # and now it fails because the "C:" part doesn't get underlined on the C
        # # also it needs to have forward slashes
        # # uuuggghhhh
        # print("Local web page: file:///" + os.path.abspath(outdir + os.sep + family.replace(" ", "-") + ".html"))

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
    }
    * {
        font-size: 48px;
        /*line-height: 1.5em;*/
        color: white;
    }
    .tp {
        font-family: '""" + family + """', 'Chalkboard SE', 'Comic Sans MS', sans-serif;
    }
    h1, p {
        font-family: "Chalkboard SE", "Comic Sans MS", sans-serif;
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

<!-- Latin test -->
<!-- <h1>Latin test: jelo <span class="tp">ijklmpstuw awen e lipu</span></h1> -->

<span class="tp">
<!-- spacing test -->
<!--a　　akesi　　ala　　alasa　　ale　　anpa　　ante　　anu　　awen　　e　　en　　esun　　ijo　　ike　　ilo　　insa　　jaki　　jan　　jelo　　jo<br>
kala　　kalama　　kama　　kasi　　ken　　kepeken　　kili　　kiwen　　ko　　kon　　kule　　kulupu　　kute　　la　　lape　　laso　　lawa　　len　　lete　　li<br>
lili　　linja　　lipu　　loje　　lon　　luka　　lukin　　lupa　　ma　　mama　　mani　　meli　　mi　　mije　　moku　　moli　　monsi　　mu　　mun　　musi<br>
mute　　nanpa　　nasa　　nasin　　nena　　ni　　nimi　　noka　　o　　olin　　ona　　open　　pakala　　pali　　palisa　　pan　　pana　　pi　　pilin　　pimeja<br>
pini　　pipi　　poka　　poki　　pona　　pu　　sama　　seli　　selo　　seme　　sewi　　sijelo　　sike　　sin　　sina　　sinpin　　sitelen　　sona　　soweli　　suli<br>
suno　　supa　　suwi　　tan　　taso　　tawa　　telo　　tenpo　　toki　　tomo　　tu　　unpa　　uta　　utala　　walo　　wan　　waso　　wawa　　weka　　wile<br>
[　　]　　.　　:　　i　　j　　k　　l　　m　　p　　s　　t　　u　　w　　te　　to<br>
kijetesantakalu　　kin　　kipisi　　ku　　lanpan　　leko　　misikeke　　monsuta　　n　　namako　　soko　　tonsi<br>
epiku　　jasima　　linluwi　　majuna　　meso　　oko　　su<br><br>-->

<!-- cartouche test -->
<!--[<span style="color: red; opacity: .5;">]</span>[.]<br>
[<span style="color: red; opacity: .5;">._</span>][.._.]<br>
[<span style="color: red; opacity: .5;">._</span><span style="color: yellow; opacity: .5;">._</span><span style="color: blue; opacity: .5;">._</span>]<br><br>-->

<!-- word list -->
a akesi ala alasa ale anpa ante anu awen e en esun ijo ike ilo insa jaki jan jelo jo<br>
kala kalama kama kasi ken kepeken kili kiwen ko kon kule kulupu kute la lape laso lawa len lete li<br>
lili linja lipu loje lon luka lukin lupa ma mama mani meli mi mije moku moli monsi mu mun musi<br>
mute nanpa nasa nasin nena ni nimi noka o olin ona open pakala pali palisa pan pana pi pilin pimeja<br>
pini pipi poka poki pona pu sama seli selo seme sewi sijelo sike sin sina sinpin sitelen sona soweli suli<br>
suno supa suwi tan taso tawa telo tenpo toki tomo tu unpa uta utala walo wan waso wawa weka wile<br>
[].:ijklmpst,uw,te to""" + " ".join(other_words[0:4]) + """<br>
kijetesantakalu kin kipisi ku lanpan leko misikeke monsuta n namako soko tonsi""" + " ".join(other_words[4:12]) + """<br>
epiku jasima linluwi majuna meso oko su""" + " ".join(other_words[12:25]) + """<br><br>
</span>
<p class="tp">
<!-- jan [sama olin namako jaki ala] li sitelen e pu kepeken wawa mute. -->
󱤑󱦐󱥖󱥅󱥸󱤐󱤂󱦑󱤧󱥠󱤉󱥕󱤙󱥵󱤼󱦜
</p>
<p>License: <a href='""" + licenseurl + """'>""" + license + """</a></p>
<span class="tp">
<span style="white-space: break-spaces">
<!-- telo oko li ken ante e pilin, by jan Ke Tami -->
󱥬󱥁󱤧󱤙󱥂󱥕󱤄

󱥪󱥺󱤧󱤘󱤆󱤉󱥎
󱥧󱤑󱦐󱤛󱤊󱦑󱦐󱥭󱤇󱤴󱤏󱦑󱦝

　󱥪󱤧󱤖
　　　󱥧󱥺󱤫󱥮󱥍󱦗󱤑󱥳󱦘
　　󱤧󱥠󱥜󱥦
　　　󱤬󱤅󱥟
　󱥆󱤧󱥷󱥩󱤰
󱥨󱥆󱤧󱤈󱤬󱥛
　　󱤧󱥐
　　　󱤬󱤥
　　󱤧󱥶
󱥡󱤡
　󱥴󱤊󱤔󱤊󱥑
　󱤊󱤁󱤊󱥢󱤄󱤧󱤘󱥌󱥖
󱥨󱥎󱥍󱦗󱤑󱥁󱦘󱤧󱥣󱤡
　　　　　　　󱥪󱤮󱤧󱥝
　　　　　　　　　󱤧󱥵
　　　　　　　　　󱤧󱥘󱤉󱤌󱥒
　　　　　　　　　　　󱤉󱥭󱤉󱥃󱤉󱥥󱤶
　　　　　　　　　　　󱤉󱥋󱤉󱥓󱤛󱤉󱤸
　　　　　　　　　　　󱤉󱤭󱤉󱤤󱤉󱥀
　　　　　　　　　　　󱤉󱤠󱤉󱤩󱥚󱥹
󱤣󱤦󱥁󱤧󱤨󱤉󱥗󱤏
　　　󱤧󱤢󱤉󱤍󱥬
　　　󱤧󱥇󱤉󱤆
　　　󱤧󱤋󱤉󱤜󱤐　　　　　「　󱤀
　　　　　󱤉󱤹󱥇　　　　　　󱤀󱦗　　　　　　󱦘　」

󱤝󱥍󱦗󱤞󱤂󱦘󱤧󱥧󱥰
　　　　󱤧󱤕󱥱󱤬󱥪
　　　　󱤧󱤽󱤼
　　　　󱤧󱥩󱤺
　　　　󱤧󱥈󱤾󱤉󱥤󱥚
󱥏󱤷󱤧󱤖󱥸󱤉󱤿󱥫　　　　　「󱤴󱥈」


󱥔󱥄󱤙󱤃󱥙
　󱤲󱤇󱥯
󱤇󱥕󱤇󱥂󱤆󱤧󱥖󱤚
　　　　　　󱥧󱤗󱥍󱦗󱤪󱤒󱤷󱦘
「󱥞󱥷󱤂󱥁
　󱥞󱥷󱤱󱤉󱤻
　󱥞󱥷󱥅󱤉󱤳
　　　　󱤉󱤵󱤉󱥾」　　　　󱥆󱤧󱤓󱤉󱤎󱥊
　　　　　　　　　　　　　　　　　󱤉󱥟󱥭
　　　　　　　　　　　　　　　󱤧󱥉󱤉󱤯
　　　　　　　　　　　　　　󱥪󱤧󱤖󱥶
　　　　　　　　　　　　　　󱤣󱤧󱤖󱥲
　　　　　　　　　　　　　　󱤑󱤧󱥩󱤯
　　　　　　　　　　　　　　　󱤧󱥩󱤿󱥇
　　　　　　　　　　　　　　　󱤧󱥩󱤟
　　　　　　　　　　　　　　󱥔󱤖󱤧󱥷󱤉󱥵
　　　　　　　　　　　　　󱥨󱤣󱥶󱤧󱤖󱤘󱤉󱥁


<textarea class="tp">sina ken sitelen wile lon ni
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
        #     image.save(outdir + os.sep + "LINKU TEST - " + family + ".png")

        # display(
        #     "󱤴󱥴󱦐󱤗󱤋󱤦󱤎󱦑󱤀", 
        #     outdir + os.sep + family + ".ttf",
        #     72,
        #     (0x0C, 0xAF, 0xF5),
        #     "outline"
        # )









     # ▄▀▄  ▄▀▄  ▄▀▄                              █                  █▀▀▀▄         ▄   █                      ▄▀▄  ▄▀▄  ▄▀▄
     #                     █▄▀  ▄▀▀▄  ▄▀▀█  █  █  █   ▀▀▄  █▄▀       █   █  █  █  ▀█▀  █▀▀▄  ▄▀▀▄  █▀▀▄
     #                     █    █▄▄█  █  █  █  █  █  ▄▀▀█  █         █▀▀▀   █  █   █   █  █  █  █  █  █
     #                     █    ▀▄▄   ▀▄▄█  ▀▄▄█  █  ▀▄▄█  █         █      ▀▄▄█   ▀▄  █  █  ▀▄▄▀  █  █
     #                                 ▄▄▀                                   ▄▄▀







# i might be mistaken about this...






     #                           █▀▀▀               ▄   █▀▀▀                              █▀▀▀▄         ▄   █
     # █   █  █   █  █   █       █▄▄   ▄▀▀▄  █▀▀▄  ▀█▀  █▄▄   ▄▀▀▄  █▄▀  ▄▀▀█  ▄▀▀▄       █   █  █  █  ▀█▀  █▀▀▄  ▄▀▀▄  █▀▀▄       █   █  █   █  █   █
     #  █ █    █ █    █ █        █     █  █  █  █   █   █     █  █  █    █  █  █▄▄█       █▀▀▀   █  █   █   █  █  █  █  █  █        █ █    █ █    █ █
     #   █      █      █         █     ▀▄▄▀  █  █   ▀▄  █     ▀▄▄▀  █    ▀▄▄█  ▀▄▄        █      ▀▄▄█   ▀▄  █  █  ▀▄▄▀  █  █         █      █      █
     #                                                                    ▄▄▀                     ▄▄▀






     #              ▄                                           ▄    ▀
     # ▄▀▀▄  ▄▀▀▄  ▀█▀       █▀▀▄  █▄▀  ▄▀▀▄  █▀▀▄  ▄▀▀▄  █▄▀  ▀█▀  ▀█  ▄▀▀▄  ▄▀▀▄
     #  ▀▄   █▄▄█   █        █  █  █    █  █  █  █  █▄▄█  █     █    █  █▄▄█   ▀▄
     # ▀▄▄▀  ▀▄▄    ▀▄       █▄▄▀  █    ▀▄▄▀  █▄▄▀  ▀▄▄   █     ▀▄   █  ▀▄▄   ▀▄▄▀
     #                       █                █

    def set_properties(self):
        """Set metadata of the font from config."""
        props = self.config["props"]
        sfnt_names = self.config["sfnt_names"]
        lang = props.get("lang", "English (US)")
        fontname = self.metadata.get("filename", None) or props.get(
            "filename", "Example"
        )
        family = self.metadata.get("family", None) or fontname
        style = props.get("style", "Regular")
        designer = self.metadata.get("designer", None) or props.get("designer", "jan pi toki pona")
        license = self.metadata.get("license", None) or sfnt_names.get("License", "All rights reserved")
        licenseurl = self.metadata.get("licenseurl", None) or sfnt_names.get("License URL", "")

        self.font.familyname = fontname
        self.font.fontname = fontname + "-" + style
        self.font.fullname = fontname + " " + style
        self.font.encoding = props.get("encoding", "UnicodeFull")

        self.font.os2_typoascent_add  = 0  
        self.font.os2_typodescent_add = 0 
        self.font.os2_typoascent      = 1200
        self.font.os2_typodescent     = -300
        self.font.os2_typolinegap     = 0

        self.font.hhea_ascent_add  = 0
        self.font.hhea_descent_add = 0
        self.font.hhea_ascent      = 1200
        self.font.hhea_descent     = -300
        self.font.hhea_linegap     = 0

        for k, v in props.items():
            if hasattr(self.font, k):
                if isinstance(v, list):
                    v = tuple(v)
                setattr(self.font, k, v)

        # idk where the list of string IDs is actually documented
        # if i can't find a string ID, i can use a numeric ID instead:
        # https://learn.microsoft.com/en-us/typography/opentype/otspec140/name#name-ids
        if self.config.get("sfnt_names", None):
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

        self.config["sfnt_names"]["UniqueID"] = family + " " + str(uuid.uuid4())

        for k, v in self.config.get("sfnt_names", {}).items():
            self.font.appendSFNTName(str(lang), k, v)



    #          █     █             █              █
    #  ▀▀▄  ▄▀▀█  ▄▀▀█       ▄▀▀█  █  █  █  █▀▀▄  █▀▀▄  ▄▀▀▄
    # ▄▀▀█  █  █  █  █       █  █  █  █  █  █  █  █  █   ▀▄
    # ▀▄▄█  ▀▄▄█  ▀▄▄█       ▀▄▄█  █  ▀▄▄█  █▄▄▀  █  █  ▀▄▄▀
    #                         ▄▄▀      ▄▄▀  █

    def add_glyphs(self, directory, version_major, version_minor, version_patch):
        """Read and add SVG images as glyphs to the font.

        Walks through the provided directory and uses each ord(character).svg file
        as glyph for the character. Then using the provided config, set the font
        parameters and export TTF file to outdir.

        Parameters
        ----------
        directory : str
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
                # Get outlines
                src = "{}/{}.svg".format(name, name)
                src = directory + os.sep + src

                # importOutlines() will print FontForge errors for blank glyphs.
                # Prepend what glyph they refer to.
                print("", end=("\r" + name.ljust(9, " ") + " - "))
                g.importOutlines(src, ("removeoverlap", "correctdir"))
                g.removeOverlap()

                if version_major <3:
                    # SHEET VERSION 2 metrics, before scaling (BS) up so that the glyph is the full em height
                    bs_scan_hor_padding = 50
                    bs_glyph_wh = 700
                else:
                    # SHEET VERSION 3 metrics, before scaling (BS) up so that the glyph is the full em height
                    bs_scan_hor_padding = 125
                    bs_glyph_wh = 500

                # shift by the left margin. (i'm not actually sure why this is necessary, but it looks wrong without it)
                # (like, why don't i have to shift it vertically??)
                g.transform(psMat.translate(
                    -bs_scan_hor_padding, 
                    0
                ))

                pixel = self.metadata.get("pixel") or False
                
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
                        x = 1

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
                        x = 1

                # Scale everything up so that the glyphs are 1em tall, instead of the cartouches
                # The scaling center is the baseline, far left

                def debug_metrics(word_to_debug):
                    if name == word_to_debug:
                        print("\n", g.width, g.vwidth)
                        bottom = g.boundingBox()[1]
                        top    = g.boundingBox()[3]
                        print(
                            "top", int(top),
                            "bottom", int(bottom),
                            "sum", int(top-bottom),
                            "ratio", -top/bottom
                        )

                # debug_metrics("lupaTok")

                # move glyphs to where rescaling happens:
                # the left side of the glyph, at the height of the baseline
                g.transform(psMat.translate(
                    -bs_glyph_wh / 2,
                    # -375 # i'm not totally sure why this magic number works tbh
                    #      # it no longer seems to work?? weird
                    200-500 # works for sheet v2
                ))
                # debug_metrics("lupaTok")

                g.transform(psMat.scale(1 / bs_glyph_wh * 1000)) # divide by the SAFE area height; multiply by the SCAN area height
                # debug_metrics("lupaTok")

                g.transform(psMat.translate(
                    500, 
                    500-200
                ))
                # debug_metrics("lupaTok")

                g.width = 1000
                g.vwidth = 1000
                # debug_metrics("lupaTok")

        # get rid of stray metrics
        print("\r                                                ")

        # originally 800x1000, minus 50 margin on each side for scanning margin
        # ...though the vertical situation might be more complicated?
        for glyph in self.font:
            # self.font[glyph].width = 700
            # self.font[glyph].vwidth = 900  # used in vertical writing. might need to revise
            # self.font[glyph].width = 1000
            # self.font[glyph].vwidth = 1000  # used in vertical writing. might need to revise
            x = 1

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
        # spaces
        ideographic_space = self.font.createChar(ord("　"), "ideographicspace")
        ideographic_space.width = 1000
        space = self.font.createChar(ord(" "), "space")
        space.width = 0
        zero_width = self.font.createChar(0x200b, "zerowidth")
        zero_width.width = 0

        # other zero-width
        bang = self.font.createChar(ord("!"), "exclamation")
        bang.width = 0
        comma = self.font.createChar(ord(","), "comma")
        comma.width = 0
        question = self.font.createChar(ord("?"), "question")
        question.width = 0
        hyphen = self.font.createChar(ord("-"), "hyphen")
        hyphen.width = 0
        plus = self.font.createChar(ord("+"), "plus")
        plus.width = 0
        caret = self.font.createChar(ord("^"), "north")
        caret.width = 1000
        caret = self.font.createChar(ord("<"), "west")
        caret.width = 1000
        caret = self.font.createChar(ord(">"), "east")
        caret.width = 1000
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

        # todo: add "start of long pi" as an additional codepoint for the "pi" glyph
        # todo: then add "end of long pi" here
        sp_stacking_joiner = self.font.createChar(0xf1995, "stackJoinTok")
        sp_stacking_joiner.width = 0
        sp_scaling_joiner = self.font.createChar(0xf1996, "scaleJoinTok")
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

    def generate_font_file(self, filename, outdir, config_file, directory):
        """Output TTF file.

        Additionally checks for multiple outputs and duplicates.

        Parameters
        ----------
        filename : str
            Output filename.
        outdir : str
            Path to output directory.
        config_file : str
            Path to config file.
        """
        if filename is None:
            raise NameError("filename not found in config file.")

        outfile = str(
            directory
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
    def convert_main(self, config_file, directory, outdir, metadata, v_major, v_minor, v_patch):
        try:
            self.font = fontforge.font()
        except:
            import fontforge
            import psMat

        with open(config_file) as f:
            self.config = json.load(f)
        self.metadata = json.loads(metadata) or {}

        self.font = fontforge.font()
        self.set_properties()
        self.add_glyphs(directory, int(v_major), int(v_minor), int(v_patch))

        # Generate font and save as a .ttf file
        filename = self.metadata.get("filename", None) or self.config["props"].get(
            "filename", None
        )
        self.generate_font_file(str(filename), outdir, config_file, directory)


if __name__ == "__main__":
    if len(sys.argv) != 8:
        raise ValueError("Incorrect call to SVGtoTTF")
    SVGtoTTF().convert_main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
