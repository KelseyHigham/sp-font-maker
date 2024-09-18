import os
import itertools
import json

import cv2

# Seq: A-Z, a-z, 0-9, SPECIAL_CHARS
ALL_CHARS = list(
    itertools.chain(
        # rows 1-6
        range(0xf1900, 0xf1978), # 120 nimi pu; first 6 rows
        [
            # row 7
            0xf1990, # cartouche open
            0xf1991, # cartouche close
            0xf199c, # middot
            0xf199d, # colon
            105,     # i
            106,     # j
            107,     # k
            108,     # l
            109,     # m
            112,     # p
            115,     # s
            116,     # t
            117,     # u
            119,     # w
            0,0,0,0, 0,0, # (poki jaki)

            # row 8
            0xf1980, # kijetesantakalu
            0xf1979, # kin
            0xf197b, # kipisi
            0xf1988, # ku
            0xf1985, # lanpan
            0xf197c, # leko
            0xf1987, # misikeke
            0xf197d, # monsuta
            0xf1986, # n
            0xf1978, # namako
            0xf1981, # soko
            0xf197e, # tonsi
            0,0,0,0, 0,0,0,0, # (poki jaki)

            # row 9
            0xf1983, # epiku
            0xf197f, # jasima
            0,       # linluwi
            0xf19a2, # majuna
            0xf1982, # meso
            0xf197a, # oko
            0,       # su
            0,0,0,0, 0,0,0,0, 0,0,0,0, 0, # (poki jaki)

            # added after rows are processed
            0xf1992, # combining cartouche extension, UCSUR
            97,     # a
            101,    # e
            110,    # n
            111,    # o
        ],

    )
)


class SHEETtoPNG:
    """Converter class to convert input sample sheet to character PNGs."""

    def convert(self, sheet, characters_dir, config, cols=20, rows=9):
        print("SHEETtoPNG")
        """Convert a sheet of sample writing input to a custom directory structure of PNGs.

        Detect all characters in the sheet as a separate contours and convert each to
        a PNG image in a temp/user provided directory.

        Parameters
        ----------
        sheet : str
            Path to the sheet file to be converted.
        characters_dir : str
            Path to directory to save characters in.
        config: str
            Path to config file.
        cols : int, default=8
            Number of columns of expected contours. Defaults to 8 based on the default sample.
        rows : int, default=10
            Number of rows of expected contours. Defaults to 10 based on the default sample.
        """
        with open(config) as f:
            threshold_value = json.load(f).get("threshold_value", 200)
        if os.path.isdir(sheet):
            raise IsADirectoryError("Sheet parameter should not be a directory.")
        characters = self.detect_characters(
            sheet, threshold_value, cols=cols, rows=rows
        )
        self.save_images(
            characters, # more like cells
            characters_dir,
            config
        )

    def detect_characters(self, sheet_image, threshold_value, cols=20, rows=9):
        """Detect contours on the input image and filter them to get only characters.

        Uses opencv to threshold the image for better contour detection. After finding all
        contours, they are filtered based on area, cropped and then sorted sequentially based
        on coordinates. Finally returs the cols*rows top candidates for being the character
        containing contours.

        Parameters
        ----------
        sheet_image : str
            Path to the sheet file to be converted.
        threshold_value : int
            Value to adjust thresholding of the image for better contour detection.
        cols : int, default=8
            Number of columns of expected contours. Defaults to 8 based on the default sample.
        rows : int, default=10
            Number of rows of expected contours. Defaults to 10 based on the default sample.

        Returns
        -------
        sorted_characters : list of list
            Final rows*cols contours in form of list of list arranged as:
            sorted_characters[x][y] denotes contour at x, y position in the input grid.
        """
        # TODO Raise errors and suggest where the problem might be

        # Read the image and convert to grayscale
        image = cv2.imread(sheet_image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold and filter the image for better contour detection
        _, thresh = cv2.threshold(gray, threshold_value, 255, 1)
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel, iterations=2)

        # Search for contours.
        contours, h = cv2.findContours(
            close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter contours based on number of sides and then reverse sort by area.
        contours = sorted(
            filter(
                lambda cnt: len(
                    cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
                )
                == 4,
                contours,
            ),
            key=cv2.contourArea,
            reverse=True,
        )

# START OF KELLY ZONE

        # Calculate the bounding of the first contour and approximate the height
        # and width for final cropping.
        _, _, bw, bh = cv2.boundingRect(contours[0])

        # Each row bounding box (black line) is 164*12, 
        # with 2 hor padding and 1 ver padding on each side.
        # There are 20 glyphs per row. Each glyph scan area is 8x10.
        # The visible gray squares are 7x7, to help with human and scanning errors.
        # (The unit here is 0.125cm on the printed page, or 0.25cm in the original huge file.)
        glyph_w, glyph_h = bw*8/164, bh*10/12
        left_padding, top_padding = bw*2/164, bh*1/12

        # Since amongst all the contours, the expected case is that the 4 sided contours
        # containing the characters should have the maximum area, so we loop through the first
        # rows*colums contours and add them to final list after cropping.
        characters = []
        for row in range(rows):
            bx, by, bw, bh = cv2.boundingRect(contours[row])
            for col in range(cols):
                glyph_top  = by + top_padding
                glyph_left = bx + left_padding + col*glyph_w
                roi = image[int(glyph_top ) : int(glyph_top  + glyph_h),
                            int(glyph_left) : int(glyph_left + glyph_w)]
                characters.append([roi, glyph_left, glyph_top])

        # Now we have the characters but since they are all mixed up we need to position them.
        # Sort characters based on 'y' coordinate and group them by number of rows at a time. Then
        # sort each group based on the 'x' coordinate.
        characters.sort(key=lambda x: x[2])
        sorted_characters = []
        for k in range(rows):
            sorted_characters.extend(
                sorted(characters[cols * k : cols * (k + 1)], key=lambda x: x[1])
            )

        # for the middle portion of the cartouche, grab the leftmost 1px column
        # of the right cartouche. it'll be automatically stretched to the width
        # of a glyph when it's converted to BMP, then SVG.
        left_cartouche  = sorted_characters[120]
        right_cartouche = sorted_characters[121]
        glyph_left, glyph_top = right_cartouche[1], right_cartouche[2]
        roi = image[int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + 1)]
        sorted_characters.append([roi, glyph_left, glyph_top])

        # shift the left and right cartouche scan area inward, to match how the gray boxes are shifted        
        glyph_left = left_cartouche[1] + glyph_w/16
        roi = image[int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + glyph_w)]
        sorted_characters[120][0] = roi
        sorted_characters[120][1] = glyph_left

        glyph_left = right_cartouche[1] - glyph_w/16
        roi = image[int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + glyph_w)]
        sorted_characters[121][0] = roi
        sorted_characters[121][1] = glyph_left

        # add Latin a e n o
        a = sorted_characters[0]
        sorted_characters.append(a)
        e = sorted_characters[9]
        sorted_characters.append(e)
        n = sorted_characters[148]
        sorted_characters.append(n)
        o = sorted_characters[68]
        sorted_characters.append(o)

        # add Latin [ _ ] . :
        bracketleft  = sorted_characters[120]
        sorted_characters.append(bracketleft)
        underscore   = sorted_characters[180]
        sorted_characters.append(underscore)
        bracketright = sorted_characters[121]
        sorted_characters.append(bracketright)
        period = sorted_characters[122]
        sorted_characters.append(period)
        colon  = sorted_characters[123]
        sorted_characters.append(colon)


# END OF KELLY ZONE

        return sorted_characters

    def save_images(self, characters, characters_dir, config):
        """Create directory for each character and save as PNG.

        Creates directory and PNG file for each image as following:

            characters_dir/ord(character)/ord(character).png  (SINGLE SHEET INPUT)
            characters_dir/sheet_filename/ord(character)/ord(character).png  (MULTIPLE SHEETS INPUT)

        Parameters
        ----------
        characters : list of list
            Sorted list of character images each inner list representing a row of images.
        characters_dir : str
            Path to directory to save characters in.
        """
        os.makedirs(characters_dir, exist_ok=True)

        # Create directory for each character and save the png for the characters
        # Structure (single sheet): UserProvidedDir/ord(character)/ord(character).png
        # Structure (multiple sheets): UserProvidedDir/sheet_filename/ord(character)/ord(character).png
        # Kelly note: `characters` is more like `cells`, since not every cell contains a glyph
        for k, images in enumerate(characters):

            with open(config) as f:
                glyphs = json.load(f).get("glyphs-fancy", {})
                if len(glyphs) > k:
                    if 'name' in glyphs[k]:
                        character = os.path.join(characters_dir, glyphs[k]['name'])
                        if not os.path.exists(character):
                            os.mkdir(character)
                        cv2.imwrite(
                            os.path.join(character, glyphs[k]['name'] + ".png"),
                            images[0],
                        )