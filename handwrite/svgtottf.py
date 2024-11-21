import sys
import os
import json
import uuid
import datetime


class SVGtoTTF:
    def convert(self, directory, outdir, config, metadata=None):
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

        self.add_ligatures(directory, outdir, config, metadata)


    def add_ligatures(self, directory, outdir, config, metadata=None):
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

        license = self.metadata.get("license", None) or self.config["sfnt_names"].get("License", "All rights reserved")
        licenseurl = self.metadata.get("licenseurl", None) or self.config["sfnt_names"].get("License URL", "")
        if license == "ofl":
            license = "SIL Open Font License, Version 1.1"
            licenseurl = "https://openfontlicense.org"
        if license == "cc0":
            license = "CC0 1.0 Universal"
            licenseurl = "https://creativecommons.org/publicdomain/zero/1.0/"

        # fontTools: input font file
        infile = str(directory + os.sep + (filename + " without ligatures.ttf"))
        # sys.stderr.write("\nAdding ligatures to %s\n" % infile)

        # fontTools: output font file
        filename = filename + ".ttf" if not filename.endswith(".ttf") else filename
        outfile = str(outdir + os.sep + filename)
        while os.path.exists(outfile):
            filename = os.path.splitext(filename)[0] + " (1).ttf"
            outfile = outdir + os.sep + filename

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
        sys.stderr.write("\nGenerating %s...\n" % outfile)
        tt.save(outfile)



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

  # Not implemented in SP Font Maker:
  # "all ku suli",                   # kokosila
  # "all ku suli and UCSUR words",   # apeja, pake, powe
  # "community requested nimisin",
  # "name glyphs",
  # "long pi",
  # "character variants",
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
# Autofilled for Kelly. If you're not Kelly, these URLs are inaccurate. But you can make them accurate, with a GitHub pull request!
# fontfile = "https://github.com/wasokeli/wasokeli.github.io/raw/main/sp-font-maker/''' + filename.replace(" ", "%20") + '''"
# repo     = "https://github.com/wasokeli/wasokeli.github.io/tree/main/sp-font-maker"
# webpage  = "https://wasokeli.github.io/sp-font-maker/''' + family.replace(" ", "-") + '''.html"
''')
        feature_file.close()



        self.generate_web_page(outdir, filename, family, designer, license, licenseurl)

    def generate_web_page(self, outdir, filename, family, designer, license, licenseurl):
        example_web_page = open(outdir + os.sep + family.replace(" ", "-") + ".html", "w", encoding="utf-8")
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
        line-height: 1.5em;
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
<!--a　akesi　ala　alasa　ale　anpa　ante　anu　awen　e　en　esun　ijo　ike　ilo　insa　jaki　jan　jelo　jo<br>
kala　kalama　kama　kasi　ken　kepeken　kili　kiwen　ko　kon　kule　kulupu　kute　la　lape　laso　lawa　len　lete　li<br>
lili　linja　lipu　loje　lon　luka　lukin　lupa　ma　mama　mani　meli　mi　mije　moku　moli　monsi　mu　mun　musi<br>
mute　nanpa　nasa　nasin　nena　ni　nimi　noka　o　olin　ona　open　pakala　pali　palisa　pan　pana　pi　pilin　pimeja<br>
pini　pipi　poka　poki　pona　pu　sama　seli　selo　seme　sewi　sijelo　sike　sin　sina　sinpin　sitelen　sona　soweli　suli<br>
suno　supa　suwi　tan　taso　tawa　telo　tenpo　toki　tomo　tu　unpa　uta　utala　walo　wan　waso　wawa　weka　wile<br>
[　]　.　:　i　j　k　l　m　p　s　t　u　w　te　to<br>
kijetesantakalu　kin　kipisi　ku　lanpan　leko　misikeke　monsuta　n　namako　soko　tonsi<br>
epiku　jasima　linluwi　majuna　meso　oko　su<br><br>-->

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
[].:ijklmpst,uw,te to<br>
kijetesantakalu kin kipisi ku lanpan leko misikeke monsuta n namako soko tonsi<br>
epiku jasima linluwi majuna meso oko su<br><br>
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


<textarea class="tp">sina ken sitelen wile lon ni</textarea>
</span></span>

<script>
/*  workaround for Chromium

    Chrome has a bug where ligatures aren't properly applied at typing-time. for example, if you type "pona", it erroneously shows a p followed by a sideways 6, rather than one smile.
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
                self.config["sfnt_names"]["License"] = "OFL-1.1"
                self.config["sfnt_names"]["License URL"] = "https://openfontlicense.org"
            if license == "cc0":
                self.config["sfnt_names"]["License"] = "CC0-1.0"
                self.config["sfnt_names"]["License URL"] = "https://creativecommons.org/publicdomain/zero/1.0/"


        self.config["sfnt_names"]["UniqueID"] = family + " " + str(uuid.uuid4())

        for k, v in self.config.get("sfnt_names", {}).items():
            self.font.appendSFNTName(str(lang), k, v)

    def add_glyphs(self, directory, metadata, version_major, version_minor, version_patch):
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

                # Vertically center sitelen pona, middot, colon
                # Todo: just center everything *except* certain glyphs
                    # do NOT center a-z, cartouches, long pi, te/to
                if (    
                    0xf1900 <= cp <= 0xf1988 or      # pu & ku suli
                    0xf19a0 <= cp <= 0xf19a3 or      # historical
                    cp == 0xf199c or cp == 0x2e or   # period
                    cp == 0xf199d or cp == 0x3a or   # colon
                    cp == 0x61 or                    # a
                    cp == 0x65 or                    # e
                    cp == 0x6e or                    # n
                    cp == 0x6f                       # o
                ):
                    bottom = g.boundingBox()[1]
                    top    = g.boundingBox()[3]
                    g.transform(psMat.translate(
                        0, 
                        self.font.ascent - top - (self.font.ascent + self.font.descent - (top - bottom)) / 2
                    ))
                    x = 1

                # Horizontally center sitelen pona, middot, colon, letters
                # Todo: just center everything *except* certain glyphs
                    # do NOT center cartouches, long pi, te/to
                if (
                    0xf1900 <= cp <= 0xf1988 or      # pu & ku suli
                    0xf19a0 <= cp <= 0xf19a3 or      # historical
                    cp == 0xf199c or cp == 0x2e or   # period
                    cp == 0xf199d or cp == 0x3a or   # colon
                    0x61 <= cp <= 0x7a               # aeijklmnopstuw
                ):
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
                g.transform(psMat.translate(
                    -bs_glyph_wh / 2,
                    -375 # i'm not totally sure why this magic number works tbh
                ))
                g.transform(psMat.scale(1 / bs_glyph_wh * 1000)) # divide by the SAFE area height; multiply by the SCAN area height
                g.transform(psMat.translate(
                    500, 
                    500
                ))



                # print(g.width, g.vwidth)
                g.width = 1000
                g.vwidth = 1000

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
        caret = self.font.createChar(ord("^"), "caret")
        caret.width = 0
        ampersand = self.font.createChar(ord("&"), "ampersand")
        ampersand.width = 0
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
        self.add_glyphs(directory, metadata, int(v_major), int(v_minor), int(v_patch))

        # Generate font and save as a .ttf file
        filename = self.metadata.get("filename", None) or self.config["props"].get(
            "filename", None
        )
        self.generate_font_file(str(filename), outdir, config_file, directory)


if __name__ == "__main__":
    if len(sys.argv) != 8:
        raise ValueError("Incorrect call to SVGtoTTF")
    SVGtoTTF().convert_main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
