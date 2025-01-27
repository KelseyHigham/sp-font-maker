# Development

## Linux

1. Install Potrace using apt

    ```console
    sudo apt-get install potrace
    ```

2. Install fontforge

    ```console
    sudo apt-get install fontforge
    ```

    ???+ warning
        Since the PPA for fontforge is no longer maintained, apt might not work for some users.
        The preferred way to install is using the AppImage from: https://fontforge.org/en-US/downloads/

3. Clone the repository or your fork

    ```console
    git clone https://github.com/KelseyHigham/sp-font-maker
    ```

4. (Optional) Make a virtual environment and activate it

    ```console
    python -m venv .venv
    source .venv/bin/activate
    ```

5. In the project directory run:

    ```console
    pip install -e .[dev]
    ```

6. Use `handwrite -h` to see instructions on using the command-line tool.
   - Put the font name in `--filename`, and the author in `--designer`.
   - A friendly license like OFL or CC0 is necessary for putting your font on ilo Linku.

You are ready to go!

## Windows

1. Install [Potrace](http://potrace.sourceforge.net/#downloading) and make sure it's in your PATH.

2. Install [fontforge](https://fontforge.org/en-US/downloads/) and make sure scripting is enabled. Add it to your PATH:
   - press Start
   - type "env"
   - click "Edit the system environment variables"
   - add `C:\Program Files (x86)\FontForgeBuilds\bin` to your PATH

3. Clone the repository or your fork

    ```console
    git clone https://github.com/KelseyHigham/sp-font-maker
    ```

4. (Optional) Make a virtual environment and activate it

    ```console
    python -m venv .venv
    .venv\Scripts\activate
    ```

5. In the project directory run:

    ```console
    pip install -e .[dev]
    ```

    If you don't have `pip` installed, install [Python](https://www.python.org/downloads/) from the website, or type `python` to install Python and PIP from the Microsoft Store.

6. Use `handwrite -h` to see instructions on using the command-line tool.
   - Put the font name in `--filename`, and the author in `--designer`.
   - A friendly license like OFL or CC0 is necessary for putting your font on ilo Linku.

You are ready to go!