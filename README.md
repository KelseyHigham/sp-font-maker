SP Font Maker, based on the English-language [Handwrite](https://github.com/builtree/handwrite).

[SP Font Maker homepage](https://wasokeli.github.io/sp-font-maker/), with tips and examples!

# Usage instructions

Fill out this image, and send it to someone who's managed to install the script. They'll give you your font file:
![template with an empty box for all the sitelen pona](https://wasokeli.github.io/sp-font-maker/template.png)

# Installation instructions

I don't really know how Python works. Someone please help me to make the [installation instructions](https://github.com/KelseyHigham/sp-font-maker/blob/dev/docs/contributing.md) easier!!!

---

# Info for developers

## Where glyphs are defined

Currently, the architecture looks like this:

- `default.json` (file inherited from Handwrite)
  - most default glyphs
  - `cli.py` writes custom words to specific indices in `glyphs-fancy`, in a font-specific copy of `default.json`
  - `sheettopng` uses the grid cell number as an index into `default.json`'s `glyphs-fancy`, to assign each grid cell a name, before saving each PNG
  - `svgtottf:add_ligatures` goes through `glyphs-fancy`, and creates a ligature for each entry with a `ligature` field
  - `svgtottf:add_glyphs` goes through `glyphs-fancy`, and adds each character to the font file, using the `codepoint` field if present
- `cli.py`
  - custom words
  - codepoints for UCSUR words not included on the template
  - mapping of ASCII special characters used in custom ligatures, to legal glyph names for those characters
  - open question: how should i associate the custom words string with the default page? is it just a first-page-only feature?
- `sheettopng.py`
  - omit certain glyphs (cartouche, ijklmpstuw vertically, te/to, pixel fonts) from being centered
  - shift cartouche scan area
  - generate the inner part of the cartouche
  - generate rotated ni, and rotated critters
  - copy existing glyphs to create ASCII codepoints
- `svgtottf.py`
  - add ligature for `space space`
  - add redundant ligatures for diagonal ni and critters (like `ni>v` and `niv>`)
  - print default glyphs on preview webpage
  - print custom glyphs on preview webpage, passed in directly from `cli.py`
  - add characters for zero-width space and ideographic space
  - add blank full- and zero-width glyphs for special characters

I think a better architecture would look like this:

- default-font-settings.yaml (.json is workable, but it would be nice if it supported comments)
- default-sheet.yaml
- optional further sheet .yaml files, specified on the command line alongside extra sheet images!