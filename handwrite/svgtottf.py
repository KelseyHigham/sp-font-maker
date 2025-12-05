#                           █                  █▀▀▀▄         ▄   █
#    █▄▀  ▄▀▀▄  ▄▀▀█  █  █  █   ▀▀▄  █▄▀       █   █  █  █  ▀█▀  █▀▀▄  ▄▀▀▄  █▀▀▄
#    █    █▄▄█  █  █  █  █  █  ▄▀▀█  █         █▀▀▀   █  █   █   █  █  █  █  █  █
#    █    ▀▄▄   ▀▄▄█  ▀▄▄█  █  ▀▄▄█  █         █      ▀▄▄█   ▀▄  █  █  ▀▄▄▀  █  █
#                ▄▄▀                                   ▄▄▀

import json
import os
import platform
import subprocess

from packaging.version import Version


def svg_to_ttf(
    debug_dir, out_dir, default_json, cli_args=None, other_words_string=None
):
    """Convert a directory with SVG images to TrueType Font.

    Calls a subprocess to the run this script with Fontforge Python
    environment, because the FontForge libraries don't work in regular Python.

    Then uses regular Python, and fontTools, to apply ligatures.

    Then outputs a web page with examples of the font.

    Parameters
    ----------
    debug_dir : str
        Path to directory with SVGs to be converted.
    out_dir : str
        Path to output directory.
    default_json : str
        Path to config file.
    cli_args : dict
        Dictionary containing the metadata (filename, family or style)
    """
    print("SVGtoTTF")
    sheet_version = cli_args.get("sheet_version") or "99999999.999999.999999"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    svgtottf_ffpython_path = os.path.join(current_dir, "svgtottf_ffpython.py")

    subprocess.run(
        (["ffpython"] if platform.system() == "Windows" else ["fontforge", "-script"])
        + [
            svgtottf_ffpython_path,
            default_json,
            debug_dir,
            out_dir,
            json.dumps(cli_args),
            str(Version(sheet_version).major),
            str(Version(sheet_version).minor),
            str(Version(sheet_version).micro),
        ]
    )
