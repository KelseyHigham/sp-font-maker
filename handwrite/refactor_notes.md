Where are cartouches still hard-coded? Where would we require special attention for long pi?
- add_ligatures.py, inevitably
- more places, probably

---

What does everyone need from default_json and cli_args?
- Can we just pass everyone the CONTENTS of cli_args instead of a bundle?
sheettopng.py:
- dj: glyphs.sheet
- dj: glyphs.derived
- dj: glyphs.copied
- dj: *writes* pixel_size
- ca: version
- ca: pixelated
pngtosvg.py:
- dj: glyphs.sheet
- dj: glyphs.derived
- dj: glyphs.copied
- ca: pixelated
- ca: version
svgtottf.py: & svgtottf_ffpython.py:
- dj (as config): glyphs-fancy
- dj (as config): pixel_size
- ca: filename
add_ligatures:
- dj: glyphs-fancy
- ca: family
- ca: filename
create_toml_html:
- dj: [nothing]
- ca: family
- ca: filename
- ca: designer
- ca: license
- ca: license url

--------


what do we need to include in the TOML to make cartouche middles *entirely*
data-driven?
such that you can implement long pi and long awen in here?
in long pi, Start is 1000 wide and End is 0 wide.

out of scope for now:
in long ala, you can parse *backwards*, so there's technically *three* glyphs.
is that just for ala?

long la requires reverse chaining. when going left-to-right, you can't tell
the difference between la's { and ala's {.


-----


things to test for, when i eventually add regression testing
this will probably need to be evaluated by eye

- ascii and ucsur
- cartouches
- stacking
- kulupu&word
- redraws
- rotated critters

do writeins work?
- stacked not overridden
- kulupu&word not overridden
- ni-numbers not overridden
- kepen not overridden
- multiple ligatures with `/` not overridden
- rotate writein critters

-----

PLANNED BREAKING CHANGES, PROBABLY BATCH THEM:
- Make output directory optional. Default to working directory
- Change cli tool name to `sp-font-maker`
- Change word placeholder to `-`, probably? Because `_` interferes with
  writein hacky long pi

-----

What should we call it when default_json is stored as a dict in memory?
- font_data
- config

What about when it's just the URI of a JSON or TOML file?
- font_data_json, font_data_toml
- config_json, config_toml

-----

feature suggestion: automatically generate a cartouche for words which aren't included in the template by default
- (stretch goal: words that people don't fill out)

implementation:
- in the .fea file, within `# WORDS`, create glyphs based on ligatures in the first step, like usual.
  - like this: `sub o k e by okeTok`
  - this avoids the case of "k o k o s i l a" turning into "koTok koTok s i laTok"
  - we'll also need to actually create those glyphs, i think, as ideographic spaces.
- before any `# COMBOS` (so that replacements can include combos), create replacements like this:
  - `sub okeTok by cartoucheStart oTok kenTok eTok cartoucheEnd`

-----

probably reformat default.toml so that it reflects what's technically going on, rather than what's going on at a human level.
that way it's easier to add new features:
- cyrillic ligatures
- fallback cartouches
- sitelen sitelen pokis
- nested/scaled combos

what would a really literal format look like?
- array of cells/source-drawings
  - (is this devoid of content, just numbers 0–179?)
- array of named glyphs, which point to source-drawings, sometimes with modifications
  - (is this glyphs.sheet? except we can't add items that aren't on the sheet, because it breaks the array... aaaa)
    - (maybe each entry in glyphs.sheet should be an array of tables)
    - (and we can have an array of ligatures)
  - separate(?) array of *optional* logical glyphs, for writeins, e.g. silapa
- array of ligatures, which point to logical glyphs
  - separate(?) array of *optional* ligatures, for writeins, e.g. la2
  - as such, a source-drawing can be tied to multiple logical glyphs

possible architecture:
- glyphs.sheet is *only* an array of source-drawings
- UNLESS you add `type="word"`, in which case it adds the glyph name and ligatures?
- with the most common case handled, the entire rest of the file can be literal