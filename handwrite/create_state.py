# def create_state(sheet, debug_dir, out_dir, default_json, cli_args, other_words_string):
#     state = {
#         sheet: 
#     }
#     return state

# what does everyone need from default_json and cli_args?
# - can we just pass everyone the CONTENTS of cli_args instead of a bundle???
# - `default.toml` has glyphs in separate sections, but `serialized_glyphs.json` has them in the pile that svgtottf_ffpython needs
# sheettopng.py:
# - dj: glyphs-fancy
# - ca: version
# - ca: pixelated
# pngtosvg.py:
# - dj: [nothing]
# - ca: pixelated
# - ca: version
# svgtottf.py:
# add_ligatures:
# - dj: glyphs-fancy
# - ca: family
# - ca: filename
# create_toml_html:
# - dj: [nothing]
# - ca: family
# - ca: filename
# - ca: designer
# - ca: license
# - ca: license url
# svgtottf_ffpython.py:
# - dj (as config): glyphs-fancy
# - dj (as config): pixel_size
# - ca: filename