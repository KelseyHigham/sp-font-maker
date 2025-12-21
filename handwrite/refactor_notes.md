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
