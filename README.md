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

- `default.toml` (file inherited from Handwrite)
  - most default glyphs
  - `cli.py` writes custom words to specific indices in `glyphs-fancy`, in a font-specific JSON copy of `default.toml`
  - `sheettopng` uses the grid cell number as an index into `default.toml`'s `glyphs-fancy`, to assign each grid cell a name, before saving each PNG
  - `svgtottf:add_ligatures` goes through `glyphs-fancy`, and creates a ligature for each entry with a `ligature` field
    - also adds them to `glyphs_with_ligatures`, for cartouching
    - also hard-codes the list `cartoucheable_non_words`
  - `svgtottf:add_glyphs` goes through `glyphs-fancy`, and adds each character to the font file, using the `codepoint` field if present
  - codepoints for UCSUR words not included on the template
  - mapping of ASCII special characters used in custom ligatures, to legal glyph names for those characters
  - copy existing glyphs to create ASCII codepoints
  - add ligature for `space space`
  - omit certain glyphs (cartouche, ijklmpstuw vertically, te/to, pixel fonts) from having their *scan areas* centered
    - note that the *vector glyphs themselves* are actually centered later
  - add characters for zero-width space and ideographic space
  - add blank full- and zero-width glyphs for special characters
- `cli.py`
  - positions of custom word slots
  - open question: how should i associate the custom words string with the default page? is it just a first-page-only feature?
- `sheettopng.py`
  - positions of custom word slots
  - shift cartouche scan area
  - generate PNG for the inner part of the cartouche
- `add_ligatures.py`
- `create_toml_html.py`
  - print default glyphs on preview webpage
  - print custom glyphs on preview webpage, passed in directly from `cli.py`
- `svgtottf.py` (including `_ffpython`)

This complexity prevents us from adding [these features](https://github.com/KelseyHigham/sp-font-maker/issues/1).

I think a better architecture would look like this:

- `default-sheet.toml`:
  - the physical position and behaviors of the 180 glyphs on the 1st sheet
  - the generated cartouche middle
- `default-font-settings.toml`:
  - glyph names necessary for custom ligatures (letters and numbers)
  - fallback glyphs for punctuation used in sitelen Lasina prose, such as `,;!?`
  - fallback glyphs for ligatures used in unsupported SP features, such as `(){}*",+&`
- optional further sheet .toml files, specified on the command line alongside extra sheet images!
