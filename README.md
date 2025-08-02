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

- default.json (file inherited from Handwrite)
  - most default glyphs
- cli.py
  - support for special characters in ligatures
  - codepoints for UCSUR words not included on the template
- sheettopng.py
  - omit certain glyphs (cartouche, ijklmpstuw vertically, te/to, pixel fonts) from being centered
  - shift cartouche scan area
  - generate the inner part of the cartouche
  - generate rotated ni, and rotated critters
  - copy existing glyphs to create ASCII codepoints
- svgtottf.py
  - add ligature for `space space`
  - add redundant ligatures for diagonal ni and critters (like `ni>v` and `niv>`)
  - print default glyphs on preview webpage
  - add characters for zero-width space and ideographic space
  - add blank full- and zero-width glyphs for special characters

I think a better architecture would look like this:

- default-font-settings.toml (.json is workable, but it would be nice if it supported comments, and shared .toml with Linku)
- default-first-sheet.toml
- optional further sheet .toml files, specified on the command line alongside extra sheet images!