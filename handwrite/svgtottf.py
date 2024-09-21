import sys
import os
import json
import uuid


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

        # fontTools: input font file
        infile = str(directory + os.sep + (filename + "_without-ligatures.ttf"))
        # sys.stderr.write("\nAdding ligatures to %s\n" % infile)

        # fontTools: output font file
        filename = filename + ".ttf" if not filename.endswith(".ttf") else filename
        outfile = str(outdir + os.sep + filename)
        while os.path.exists(outfile):
            filename = os.path.splitext(filename)[0] + " (1).ttf"
            outfile = outdir + os.sep + filename

        ligatures_string = "feature liga {\n"
        list_of_ligs = []

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
                    list_of_ligs.append((
                        "  sub " + k['ligature'] + " space by " + k['name'] + ";", 
                        len(k['ligature'].split(' ')) + 1
                    ))

        list_of_ligs.append(("  sub comma space by zerowidth;", 2))

        # sort them by number of tokens
        list_of_ligs.sort(reverse=True, key=lambda x: x[1])

        # add to our cool string
        for line in list_of_ligs:
            ligatures_string += line[0] + "\n"

        ligatures_string += "} liga;"
        # print(ligatures_string)

        from fontTools import ttLib  # camelCase!
        tt = ttLib.TTFont(infile)
        from fontTools.feaLib import builder  # camelCase!
        builder.addOpenTypeFeaturesFromString(tt, ligatures_string)
        sys.stderr.write("\nGenerating %s...\n" % outfile)
        tt.save(outfile)

        self.generate_web_page(outdir, filename, family)

    def generate_web_page(self, outdir, filename, family):
        example_web_page = open(outdir + os.sep + family + ".html", "w", encoding="utf-8")
        example_web_page.write(
"""
<style type=\"text/css\">
    @font-face {
        font-family: '""" + family + """';
        src: url('""" + filename + """')
    }
    * {
        font-family: '""" + family + """', 'Chalkboard SE', 'Comic Sans MS', sans-serif;
        font-size: 48px;
        line-height: 1em;
    }
    h1, p {
        font-family: "Chalkboard SE", "Comic Sans MS", sans-serif;
    }
</style>
<h1>""" + family + ", tan " + "mama ona" + """</h1>
nasin sitelen sin a!<br><br>

a akesi ala alasa ale anpa ante anu awen e en esun ijo ike ilo insa jaki jan jelo jo<br>
kala kalama kama kasi ken kepeken kili kiwen ko kon kule kulupu kute la lape laso lawa len lete li<br>
lili linja lipu loje lon luka lukin lupa ma mama mani meli mi mije moku moli monsi mu mun musi<br>
mute nanpa nasa nasin nena ni nimi noka o olin ona open pakala pali palisa pan pana pi pilin pimeja<br>
pini pipi poka poki pona pu sama seli selo seme sewi sijelo sike sin sina sinpin sitelen sona soweli suli<br>
suno supa suwi tan taso tawa telo tenpo toki tomo tu unpa uta utala walo wan waso wawa weka wile<br>
[].:ijklmpst,uw<br>
kijetesantakalu kin kipisi ku lanpan leko misikeke monsuta n namako soko tonsi<br>
epiku jasima linluwi majuna meso oko su<br><br>

ilo li pali e sitelen ni:<br>
　jan [sama olin namako jaki ala] li sitelen e pu kepeken wawa mute.<br>
　󱤑󱦐󱥖󱥅󱥸󱤐󱤂󱦑󱤧󱥠󱤉󱥕󱤙󱥵󱤼󱦜<br><br>

mi pona e pali kepeken sitelen _, kepeken sitelen 󱦒:<br>
　jan [sama_olin_namako_jaki_ala_] li sitelen e pu kepeken wawa mute.<br>
　󱤑󱦐󱥖󱦒󱥅󱦒󱥸󱦒󱤐󱦒󱤂󱦒󱦑󱤧󱥠󱤉󱥕󱤙󱥵󱤼󱦜<br><br>
[<span style="color: red; opacity: .5;">]</span>[.]<br>
[<span style="color: red; opacity: .5;">._</span>][.._.]<br>
[<span style="color: red; opacity: .5;">._</span><span style="color: yellow; opacity: .5;">._</span><span style="color: blue; opacity: .5;">._</span>]<br>

sina pona tan lukin
<p>License: ???</p>

<span style="white-space: break-spaces">
telo oko li ken ante e pilin
tan jan [kiwen en][tomo awen mi insa]:

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
</span>
"""
        )
        example_web_page.close()

    def set_properties(self):
        """Set metadata of the font from config."""
        props = self.config["props"]
        lang = props.get("lang", "English (US)")
        fontname = self.metadata.get("filename", None) or props.get(
            "filename", "Example"
        )
        family = self.metadata.get("family", None) or fontname
        style = self.metadata.get("style", None) or props.get("style", "Regular")

        self.font.familyname = fontname
        self.font.fontname = fontname + "-" + style
        self.font.fullname = fontname + " " + style
        self.font.encoding = props.get("encoding", "UnicodeFull")

        for k, v in props.items():
            if hasattr(self.font, k):
                if isinstance(v, list):
                    v = tuple(v)
                setattr(self.font, k, v)

        if self.config.get("sfnt_names", None):
            self.config["sfnt_names"]["Family"] = family
            self.config["sfnt_names"]["Fullname"] = family + " " + style
            self.config["sfnt_names"]["PostScriptName"] = family + "-" + style
            self.config["sfnt_names"]["SubFamily"] = style

        self.config["sfnt_names"]["UniqueID"] = family + " " + str(uuid.uuid4())

        for k, v in self.config.get("sfnt_names", {}).items():
            self.font.appendSFNTName(str(lang), str(k), str(v))

    def add_glyphs(self, directory):
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

                # Vertically center sitelen pona, middot, colon
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

                # Horizontally center sitelen pona, middot, colon, letters
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
                        700 - right - (700 - width) / 2, 
                        0
                    ))

        # get rid of stray metrics
        print("\r                                                ")

        # originally 800x1000, minus 50 margin on each side for scanning margin
        # ...though the vertical situation might be more complicated?
        for glyph in self.font:
            self.font[glyph].width = 700
            self.font[glyph].vwidth = 900  # What does this actually do? Does ascent/descent control everything?

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

        # combining cartouche extension
        self.font[0xf1992].width = 0
        self.font[0xf1992].transform(psMat.translate(-700, 0))
        self.font[0x5f].width = 0
        self.font[0x5f].transform(psMat.translate(-700, 0))

        # later i should move these into default.json
        # spaces
        space = self.font.createChar(ord(" "), "space")
        space.width = 700
        ideographic_space = self.font.createChar(ord("　"))
        ideographic_space.width = 700
        # zero-width
        bang = self.font.createChar(ord("!"), "exclamation")
        bang.width = 0
        comma = self.font.createChar(ord(","), "comma")
        comma.width = 0
        question = self.font.createChar(ord("?"), "question")
        question.width = 0
        zero_width = self.font.createChar(-1, "zerowidth")
        zero_width.width = 0
        # todo: add "start of long pi" as an additional codepoint for the "pi" glyph
        # todo: then add "end of long pi" here
        sp_stacking_joiner = self.font.createChar(0xf1995)
        sp_stacking_joiner.width = 0
        sp_scaling_joiner = self.font.createChar(0xf1996)
        sp_scaling_joiner.width = 0
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

    def set_bearings(self):
        """Add left and right bearing
        """

        for glyph in self.font:
            print(glyph)
            self.font[glyph].left_side_bearing = 0  # Generally a value between -100, 100.
            self.font[glyph].right_side_bearing = 0 # 0 makes the glyphs touch. Maybe add like 50

    def set_kerning(self, table):
        """Set kerning values in the font.

        Parameters
        ----------
        table : dict
            Config dictionary with kerning values/autokern bool.
        """
        rows = table["rows"]
        rows = [list(i) if i != None else None for i in rows]
        cols = table["cols"]
        cols = [list(i) if i != None else None for i in cols]

        self.font.addLookup("kern", "gpos_pair", 0, [["kern", [["latn", ["dflt"]]]]])

        if table.get("autokern", True):
            self.font.addKerningClass(
                "kern", "kern-1", table.get("seperation", 0), rows, cols, True
            )
        else:
            kerning_table = table.get("table", False)
            if not kerning_table:
                raise ValueError("Kerning offsets not found in the config file.")
            flatten_list = (
                lambda y: [x for a in y for x in flatten_list(a)]
                if type(y) is list
                else [y]
            )
            offsets = [0 if x is None else x for x in flatten_list(kerning_table)]
            self.font.addKerningClass("kern", "kern-1", rows, cols, offsets)

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
            + (filename + "_without-ligatures.ttf")
        )

        # while os.path.exists(outfile):
        #     outfile = os.path.splitext(outfile)[0] + " (1).ttf"

        # Generate font, but without ligatures yet, to temporary directory
        # sys.stderr.write("\nCreating %s\n" % outfile)
        self.font.generate(outfile)
        self.font.save(outfile + ".sfd")

    def convert_main(self, config_file, directory, outdir, metadata):
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
        self.add_glyphs(directory)

        # bearing table
        # Bearings position the glyph relative to the edges of the glyph's drawing.
        # This is useful for variable-width fonts, but not for monospaced fonts.
        # self.set_bearings(self.config["typography_parameters"].get("bearing_table", {}))

        # kerning table
        # self.set_kerning(self.config["typography_parameters"].get("kerning_table", {}))

        # Generate font and save as a .ttf file
        filename = self.metadata.get("filename", None) or self.config["props"].get(
            "filename", None
        )
        self.generate_font_file(str(filename), outdir, config_file, directory)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise ValueError("Incorrect call to SVGtoTTF")
    SVGtoTTF().convert_main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
