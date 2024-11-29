import os
import itertools
import json
import cv2
from packaging.version import Version

class SHEETtoPNG:
    """Converter class to convert input sample sheet to character PNGs."""

    def convert(self, sheet, characters_dir, config, metadata, cols=20, rows=9):
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
            characters_dir, sheet, threshold_value, metadata, cols=cols, rows=rows
        )
        self.save_images(
            characters, # more like cells
            characters_dir,
            config,
            metadata
        )

    def detect_characters(self, characters_dir, sheet_image, threshold_value, metadata, cols=20, rows=9):
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
        cv2.imwrite(os.path.join(characters_dir, "analysis step 1 - image" + ".png"), image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(os.path.join(characters_dir, "analysis step 2 - grayscale" + ".png"), gray)

        # Threshold and filter the image for better contour detection
        _, thresh = cv2.threshold(gray, threshold_value, 255, 1)
        cv2.imwrite(os.path.join(characters_dir, "analysis step 3 - threshold" + ".png"), thresh)
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel, iterations=2)
        cv2.imwrite(os.path.join(characters_dir, "analysis step 4 - close" + ".png"), close)

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

        # for row in range(rows):
        #     print(contours[row])

# START OF KELLY ZONE
        import math
        def small_rect(contour):
            # find a smaller rect,
            # with the aspect ratio of boundingRect,
            # but the area of contourArea
            # (doesn't help)
            left, top, width, height = cv2.boundingRect(contour)
            area         = cv2.contourArea(contour)
            aspect_ratio = width/height
            center_x = left + width/2
            center_y = top + height/2
            width_s  = math.sqrt(area*aspect_ratio)
            height_s = math.sqrt(area/aspect_ratio)
            left_s = center_x - width_s/2
            top_s  = center_y - height_s/2
            return left_s, top_s, width_s, height_s

        # for debug imaging
        from PIL import Image, ImageDraw
        debug_image = Image.open(sheet_image)
        debug_draw = ImageDraw.Draw(debug_image)

        # Draw each contour on the image
        for contour in contours:
            # Convert the contour to a list of tuples for PIL
            contour_pil = [tuple(point[0]) for point in contour]
            # Draw the contour
            debug_draw.polygon(contour_pil, outline=(0x00, 0xff, 0x00), width=2)

        # output the initial 9 rows as images, for debug purposes

        row_images = []
        for row in range(rows):
            left, top, width, height = cv2.boundingRect(contours[row])
            # left_s, top_s, width_s, height_s = small_rect(contours[row])

            roi = image[
                top : top  + height,
                left: left + width
            ]
            row_images.append([roi, left, top])

            # # doesn't help
            # roi = image[
            #     int(top_s) : int(top_s  + height_s),
            #     int(left_s): int(left_s + width_s)
            # ]
            # row_images.append([roi, left_s, top_s])

            debug_draw.rectangle([left, top, left+width, top+height], outline=(0xff, 0x00, 0x00))
            # debug_draw.rectangle([left_s, top_s, left_s+width_s, top_s+height_s], outline=(0x00, 0x00, 0xff))

        row_images.sort(key=lambda x: x[2])

        # row_dir = os.path.join(characters_dir, "9 rows")
        row_dir = os.path.join(characters_dir)
        if not os.path.exists(row_dir):
            os.mkdir(row_dir)
        for row in range(rows):
            cv2.imwrite(os.path.join(row_dir, "analysis step 5 - row" + str(row+1) + ".png"), row_images[row][0])


        # Since amongst all the contours, the expected case is that the 4 sided contours
        # containing the characters should have the maximum area, so we loop through the first
        # rows*colums contours and add them to final list after cropping.
        characters = []
        for row in range(rows):
            # Calculate the bounding of the contour and approximate the height
            # and width for final cropping.
            row_x, row_y, row_w, row_h = cv2.boundingRect(contours[row])
            # row_x, row_y, row_w, row_h = small_rect(contours[row]) # doesn't help

            sheet_version = metadata.get("sheetversion") or "99999999.999999.999999"
            if Version(sheet_version) < Version("3"):
                # SHEET VERSION 2:
                # The grid unit here is roughly 0.125cm on the printed page, or 0.25cm in the original huge file.
                # Each row bounding box (black line) is 164*12, 
                grid_row_w = 164
                grid_row_h = 12
                # with 2 hor padding and 1 ver padding on each side.
                grid_hor_padding = 2
                grid_ver_padding = 1
                # There are 20 glyphs per row. Each glyph scan area is 8x10.
                grid_scan_w = 8
                grid_scan_h = 10
                # The visible gray squares are 7x7, to help with human and scanning errors.
                grid_glyph_w = 7
                grid_scan_hor_padding = 0.5
            else:
                # SHEET VERSION 3:
                # The grid unit here is roughly 1/6cm on the printed page, or 1/3cm in the original huge file.
                # Each row bounding box (black line) is 126x12,
                grid_row_w = 126
                grid_row_h = 12
                # with 3 hor padding and 2 ver padding on each side.
                grid_hor_padding = 3
                grid_ver_padding = 2
                # There are 20 glyphs per row. Each glyph scan area is 6x8.
                grid_scan_w = 6
                grid_scan_h = 8
                # The visible gray squares are 4x4, to help with human and scanning errors.
                grid_glyph_w = 4
                grid_scan_hor_padding = 1

            # Convert glyph and padding from grid cells into pixels,
            # using the measured size of each row
            glyph_w      = grid_scan_w      * row_w/grid_row_w
            glyph_h      = grid_scan_h      * row_h/grid_row_h
            left_padding = grid_hor_padding * row_w/grid_row_w
            top_padding  = grid_ver_padding * row_h/grid_row_h

            for col in range(cols):
                glyph_top  = row_y + top_padding
                glyph_left = row_x + left_padding + col*glyph_w
                roi = image[
                    int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + glyph_w)
                ]
                characters.append([roi, glyph_left, glyph_top, glyph_w, glyph_h])
        debug_image.save(os.path.join(characters_dir, "analysis PREVIEW" + ".png"))

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
        glyph_left, glyph_top, glyph_w, glyph_h = right_cartouche[1], right_cartouche[2], right_cartouche[3], right_cartouche[4]
        roi = image[int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + 1)]
        sorted_characters.append([roi, glyph_left, glyph_top, glyph_w, glyph_h])

        # shift the left and right cartouche scan area inward, to match how the gray boxes are shifted
        # glyph_left = left_cartouche[1] + glyph_w/16
        glyph_left = left_cartouche[1] + grid_scan_hor_padding * glyph_w/grid_scan_w
        roi = image[int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + glyph_w)]
        sorted_characters[120][0] = roi
        sorted_characters[120][1] = glyph_left

        glyph_left = right_cartouche[1] - grid_scan_hor_padding * glyph_w/grid_scan_w
        roi = image[int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + glyph_w)]
        sorted_characters[121][0] = roi
        sorted_characters[121][1] = glyph_left

        # add ali
        ali = sorted_characters[4]
        sorted_characters.append(ali)

        # add Latin [ _ ] . :, necessary for ligatures
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

        # add Latin a e n o, necessary for ligatures
        a = sorted_characters[0]
        sorted_characters.append(a)
        e = sorted_characters[9]
        sorted_characters.append(e)
        n = sorted_characters[148]
        sorted_characters.append(n)
        o = sorted_characters[68]
        sorted_characters.append(o)

        # add uppercase IJKLMPSTUW, for Pingo and name glyphs
        for i,c in enumerate("ijklmpstuw"):
            sorted_characters.append(sorted_characters[124+i])

        # add uppercase AENO
        uppercase_a = sorted_characters[0]
        sorted_characters.append(uppercase_a)
        uppercase_e = sorted_characters[9]
        sorted_characters.append(uppercase_e)
        uppercase_n = sorted_characters[148]
        sorted_characters.append(uppercase_n)
        uppercase_o = sorted_characters[68]
        sorted_characters.append(uppercase_o)

        # g for Pingo, shown as k
        g = sorted_characters[126]
        sorted_characters.append(g)
        # y for yupekosi, shown as j
        y = sorted_characters[125]
        sorted_characters.append(y)
        # v for Vivi, shown as w
        v = sorted_characters[133]
        sorted_characters.append(v)
        # V for Vivi, shown as w
        uppercase_v = sorted_characters[133]
        sorted_characters.append(uppercase_v)

        # for adding future unofficial letters:
        # letter, glyph index, codepoint
        # b 129 62
        # c 130 63
        # d 131 64
        # f 129 66
        # h 126 68
        # q 126 71
        # r 133 72
        # x 130 78
        # z 130 7a


# END OF KELLY ZONE

        return sorted_characters

    def save_images(self, characters, characters_dir, config, metadata):
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
            # Kelly note: the script does not support multiple sheets, actually

        # Kelly note: `characters` is more like `cells`, since not every cell contains a glyph
        for cellNum, images in enumerate(characters):

            with open(config) as f:
                glyphList = json.load(f).get("glyphs-fancy", {})
                curMetadatum = glyphList[cellNum]
                if len(glyphList) > cellNum:
                    if 'name' in curMetadatum:
                        character = os.path.join(characters_dir, curMetadatum['name'])
                        if not os.path.exists(character):
                            os.mkdir(character)
                        # print(character, curMetadatum['name'] + ".png")
                        cv2.imwrite(
                            os.path.join(character, curMetadatum['name'] + ".png"),
                            images[0],
                        )

        # Trim cartouche characters
            # We'll have to do the same thing for long pi
            # and any other character that spans two cells
        self.pad("right", characters_dir, metadata, "cartoucheStartTok")
        self.pad("right", characters_dir, metadata, "bracketleft")
        
        self.pad("left",  characters_dir, metadata, "cartoucheEndTok")
        self.pad("left",  characters_dir, metadata, "bracketright")

        self.pad("right", characters_dir, metadata, "cartoucheMiddleTok", True)
        self.pad("left",  characters_dir, metadata, "cartoucheMiddleTok", True)
        self.pad("right", characters_dir, metadata, "underscore", True)
        self.pad("left",  characters_dir, metadata, "underscore", True)

    def pad(self, side, characters_dir, metadata, char_name, resize=False):
        from PIL import Image, ImageDraw
        char_img = Image.open(characters_dir + "/" + char_name + "/" + char_name + ".png")

        # resize the cartouche middle from 1px wide to the standard width (for a given sheet version)
        sheet_version = metadata.get("sheetversion") or "99999999.999999.999999"
        if Version(sheet_version) < Version("3"):
            # SHEET VERSION 2: Each glyph scan area is 8x10.
            grid_scan_w = 8
            grid_scan_h = 10
            # The visible gray squares are 7x7, to help with human and scanning errors.
            grid_glyph_w = 7
            grid_scan_hor_padding = 0.5
        else:
            # SHEET VERSION 3: Each glyph scan area is 6x18.
            grid_scan_w = 6
            grid_scan_h = 8
            # The visible gray squares are 4x4, to help with human and scanning errors.
            grid_glyph_w = 4
            grid_scan_hor_padding = 1
        if resize:
            char_img = char_img.resize((int(char_img.height * grid_scan_w/grid_scan_h), char_img.height))

        draw = ImageDraw.Draw(char_img)
        left, top, right, bottom = 0, 0, char_img.width, char_img.height
        in_pixels = char_img.width/grid_scan_w
        if side == "left":
            draw.rectangle(
                (
                    (     left,                                                                    top        ), 
                    #             scan padding                      cartouche overlap
                    (     left  + grid_scan_hor_padding*in_pixels - grid_glyph_w*in_pixels/42,     bottom     )
                ),
                fill="white"
            )
        if side == "right":
            draw.rectangle(
                (
                    #             scan padding                      cartouche overlap
                    (     right - grid_scan_hor_padding*in_pixels + grid_glyph_w*in_pixels/42,     top        ), 
                    (     right,                                                                   bottom     )
                ),
                fill="white"
            )
        char_img.save(characters_dir + "/" + char_name + "/" + char_name + ".png")