import sys
import os
import json
import uuid


class SVGtoTTF:
    def convert(self, directory, outdir, config, metadata=None):
        print("SVGtoTTF")
        """Convert a directory with SVG images to TrueType Font.

        Calls a subprocess to the run this script with Fontforge Python
        environment.

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
        bang = self.font.createMappedChar(ord("!"))
        bang.width = 0
        space = self.font.createMappedChar(ord(" "))
        space.width = 350
        comma = self.font.createMappedChar(ord(","))
        comma.width = 0
        question = self.font.createMappedChar(ord("?"))
        question.width = 0
        ideographic_space = self.font.createMappedChar(0x3000)
        ideographic_space.width = 700
        print(0x3000)

        print("Note: If you leave a glyph blank, you'll get a FontForge error like \"I'm")
        print("      sorry this file is too complex for me to understand (or is erroneous)\".")
        print("      It's fine, the font still works!")

        import psMat
        for k in self.config["glyphs"]:
            # Create character glyph
            g = self.font.createMappedChar(k)
            self.unicode_mapping.setdefault(k, g.glyphname)
            # Get outlines
            src = "{}/{}.svg".format(k, k)
            src = directory + os.sep + src
            print("\t", k, "         ", end=("\r"+chr(k)+" "+hex(k)+" "+str(k)+" - "))
            # print("importOutlines #", k)
            g.importOutlines(src, ("removeoverlap", "correctdir"))
            g.removeOverlap()

            # Vertically center sitelen pona
            if 0xf1900 <= k <= 0xf1988 or 0xf19a0 <= k <= 0xf19a3:
                top    = g.boundingBox()[-1]
                bottom = g.boundingBox()[1]
                g.transform(psMat.translate(0, 
                    self.font.ascent - (self.font.ascent + self.font.descent - (top - bottom)) / 2 - top
                ))
        print("                                                                                                         ")

    def set_bearings(self, bearings):
        """Add left and right bearing from config

        Parameters
        ----------
        bearings : dict
            Map from character: [left bearing, right bearing]
        """

        for glyph in self.font:
            print(glyph)
            self.font[glyph].left_side_bearing = 0  # generally a value between -100, 100.
            self.font[glyph].right_side_bearing = 0 # 0 makes the glyphs touch. maybe add like 50

        # The following code is useful if the bearing table is populated.
        # See the original ascii `handwrite` project.
        # default = bearings.get("Default", [60, 60])

        # for k, v in bearings.items():
        #     if v[0] is None:
        #         v[0] = default[0]
        #     if v[1] is None:
        #         v[1] = default[1]

        #     if k != "Default":
        #         if ord(str(k)) in self.unicode_mapping:
        #             glyph_name = self.unicode_mapping[ord(str(k))]
        #             self.font[glyph_name].left_side_bearing = v[0]
        #             self.font[glyph_name].right_side_bearing = v[1]

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

    def generate_font_file(self, filename, outdir, config_file):
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
            outdir
            + os.sep
            + (filename + ".ttf" if not filename.endswith(".ttf") else filename)
        )

        while os.path.exists(outfile):
            outfile = os.path.splitext(outfile)[0] + " (1).ttf"

        sys.stderr.write("\nGenerating %s...\n" % outfile)
        self.font.generate(outfile)

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
        self.unicode_mapping = {}
        self.set_properties()
        self.add_glyphs(directory)

        # bug: this is run after add_glyphs(), so it overrides any zero-width glyphs.
        # probably just put this snippet into that function
        for glyph in self.font:
            self.font[glyph].width = 700
            self.font[glyph].vwidth = 875

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
        self.generate_font_file(str(filename), outdir, config_file)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise ValueError("Incorrect call to SVGtoTTF")
    SVGtoTTF().convert_main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
