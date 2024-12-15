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

        # for debug imaging
        from PIL import Image, ImageDraw
        debug_image = Image.open(sheet_image).convert("RGB")
        debug_draw = ImageDraw.Draw(debug_image)
        pixel = metadata.get("pixel") or False
        if pixel:
            debug_width = 1
        else:
            debug_width = 2 

        # # Draw each *non-rectangular* contour on the image
        # for i, contour in enumerate(contours):
        #     # Convert the contour to a list of tuples for PIL
        #     contour_pil = [tuple(point[0]) for point in contour]
        #     # Draw the contour
        #     if len(contour_pil) > 1:
        #         # print(i)
        #         debug_draw.polygon(contour_pil, outline="blue", width=debug_width) # slow
        #         # debug_image.save(os.path.join(characters_dir, "analysis PREVIEW" + ".png")) # slower
        #         x = 1

        # Just reverse sort by area, for debug drawing.
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        for maybe_row in range(rows*2):
            if len(contours) > maybe_row:
                contour_pil = [tuple(point[0]) for point in contours[maybe_row]]
                if len(contour_pil) > 1:
                    # print(maybe_row)
                    debug_draw.polygon(contour_pil, outline="blue", width=debug_width)
                    x = 1
        # debug_image.save(os.path.join(characters_dir, "analysis PREVIEW" + ".png"))

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

        # Draw each row contour on the image
        for i, contour in enumerate(contours):
            # print(i)
            # Convert the contour to a list of tuples for PIL
            contour_pil = [tuple(point[0]) for point in contour]
            # print(contour) # this is fine. actually it looks wrong but the resulting bbox is right
            # Draw the contour
            debug_draw.polygon(contour_pil, outline="red", width=debug_width)
        # debug_image.save(os.path.join(characters_dir, "analysis PREVIEW" + ".png"))

        # output the biggest 9 rows as images, for debug purposes
        row_images = []
        for row in range(rows):
            # print(row)
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

            debug_draw.rectangle([left, top, left+width, top+height], outline="lime")
            # debug_draw.rectangle([left_s, top_s, left_s+width_s, top_s+height_s], outline="blue")
            # debug_image.save(os.path.join(characters_dir, "analysis PREVIEW" + ".png"))

        row_images.sort(key=lambda x: x[2])

        # row_dir = os.path.join(characters_dir, "9 rows")
        row_dir = os.path.join(characters_dir)
        if not os.path.exists(row_dir):
            os.mkdir(row_dir)
        for row in range(rows):
            cv2.imwrite(os.path.join(row_dir, "analysis step 5 - row" + str(row+1) + ".png"), row_images[row][0])

        # sort the biggest 9 rows, top-to-bottom
        contours[0:9] = sorted(contours[0:9], key=lambda cnt: cv2.boundingRect(cnt)[1])

        # Since amongst all the contours, the expected case is that the 4 sided contours
        # containing the characters should have the maximum area, so we loop through the first
        # rows*colums contours and add them to final list after cropping.
        characters = []
        for row in range(rows):
            # Calculate the bounding of the contour and approximate the height
            # and width for final cropping.
            row_x, row_y, row_w, row_h = cv2.boundingRect(contours[row])
            # print(row_x, row_y, row_w, row_h)
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
            #                    █                       ▀               █                   ▄        █
            # █▀▄▀▄   ▀▀▄  █  █  █▀▀▄  ▄▀▀▄       █▀▀▄  ▀█  ▀▄ ▄▀  ▄▀▀▄  █        ▀▀▄  █▄▀  ▀█▀       █▀▀▄  █  █  ▄▀▀█
            # █ █ █  ▄▀▀█  █  █  █  █  █▄▄█       █  █   █    █    █▄▄█  █       ▄▀▀█  █     █        █  █  █  █  █  █
            # █ █ █  ▀▄▄█  ▀▄▄█  █▄▄▀  ▀▄▄        █▄▄▀   █  ▄▀ ▀▄  ▀▄▄   █       ▀▄▄█  █     ▀▄       █▄▄▀  ▀▄▄█  ▀▄▄█
            #               ▄▄▀                   █                                                                ▄▄▀
            # import math
            glyph_w      =     grid_scan_w      * row_w/grid_row_w
            glyph_h      =     grid_scan_h      * row_h/grid_row_h
            left_padding = int(grid_hor_padding * row_w/grid_row_w)
            top_padding  =     grid_ver_padding * row_h/grid_row_h
            # print(glyph_w, glyph_h, left_padding, top_padding)

            prev_x_shift = 0
            for col in range(cols):
                glyph_top  = row_y + top_padding
                glyph_left = row_x + left_padding + col*glyph_w
                # print("row" + str(row) + ", col" + str(col) + ": " + str(glyph_left))
                roi = image[
                    int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + glyph_w)
                ]

                # funny algorithm to center glyph scan areas while scanning.
                # this helps if groups of glyphs are uniformly shifted left or right,
                # which can happen when physical paper is bent.
                # normally bent paper will result in glyphs bleeding into each other's scan areas.
                # this mostly mitigates that.

                #        ▀               █                   ▄        █                      █
                # █▀▀▄  ▀█  ▀▄ ▄▀  ▄▀▀▄  █        ▀▀▄  █▄▀  ▀█▀       █▀▀▄  █  █  ▄▀▀█       █▀▀▄  ▄▀▀▄  █▄▀  ▄▀▀▄
                # █  █   █    █    █▄▄█  █       ▄▀▀█  █     █        █  █  █  █  █  █       █  █  █▄▄█  █    █▄▄█
                # █▄▄▀   █  ▄▀ ▀▄  ▀▄▄   █       ▀▄▄█  █     ▀▄       █▄▄▀  ▀▄▄█  ▀▄▄█       █  █  ▀▄▄   █    ▀▄▄
                # █                                                                ▄▄▀
                # we wanna find the center of gravity of the cell
                # and we'll use that to move the cell
                # to avoid like, scanning one pixel of a neighboring glyph
                old_glyph_left = glyph_left
                new_glyph_left = glyph_left
                old_glyph_top = glyph_top
                new_glyph_top = glyph_top
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, threshold_value, 255, 1)
                # this is where the magic happens
                # i call it magic because i don't understand it
                moments = cv2.moments(thresh)
                if moments['m00'] != 0:
                    centroid_x = moments['m10']/moments['m00']
                    centroid_y = moments['m01']/moments['m00']
                    x_shift = (centroid_x - glyph_w/2)
                    y_shift = (centroid_y - glyph_h/2)
                    if col != 0:
                        # avoid large deviations glyph-to-glyph, 
                        # by nudging halfway towards the previous glyph's shift
                        x_shift = (x_shift + prev_x_shift)/2
                        # TODO: am i actually *resetting* x_shift for new rows??
                        #       if not, extreme x_shift on the right side could affect glyphs on the left side
                    prev_x_shift = x_shift
                    # print("shift:", int(centroid_x - glyph_w/2), int(centroid_y - glyph_h/2))
                    new_glyph_left = glyph_left + x_shift
                    new_glyph_top  = glyph_top  + y_shift

                    # don't apply this algorithm to the cartouche and te/to, which it breaks
                    # don't apply this algorithm to ijklmpstuw, where it's mostly useless
                    # don't apply this algorithm to pixel art, where it's useless at best
                    centered = True
                    if row == 6:
                        if (col == 0  or # cartouche open
                            col == 1  or # cartouche close
                            col == 14 or # te
                            col == 15):  # to
                            centered = False
                            # print("not centered:", row, col)
                            # TODO: reset x_shift after cartouches and te/to
                            #       so that it doesn't affect the letters and custom nimi
                            # ALTERNATELY, keep it in place, to help with paper scanned sheets...?
                            # maybe just... don't *affect* x_shift during cartouches and te/to...
                    if centered and not pixel:
                        # toggle this line to toggle the algorithm, 
                        # while still previewing the algorithm on "analysis PREVIEW.png".
                        # (note that i'm only implementing horizontal shift, 
                        # not the vertical shift that that sheet implies.)
                        # (also note that cartouche and te/to are shown as shifted,
                        # even though they're not.)
                        #    (actually this might not be the case anymore.)
                        glyph_left = glyph_left + x_shift
                        x = 1

                    roi = image[
                        int(glyph_top ) : int(glyph_top  + glyph_h),
                        int(glyph_left) : int(glyph_left + glyph_w)
                    ]

                characters.append([roi, glyph_left, glyph_top, glyph_w, glyph_h])
                debug_draw.rectangle([old_glyph_left, old_glyph_top, old_glyph_left+glyph_w, old_glyph_top+glyph_h], 
                    outline="lime", width=debug_width)
                if not pixel:
                    debug_draw.rectangle([glyph_left, new_glyph_top, glyph_left+glyph_w, new_glyph_top+glyph_h], 
                        outline="red", width=debug_width)
                # # i don't understand the following result, but it scares me...
                # # why are the first 3 custom boxes treated as not centered?
                # if centered: 
                #     debug_draw.rectangle([glyph_left, new_glyph_top, glyph_left+glyph_w, new_glyph_top+glyph_h], 
                #         outline="red", fill="red", width=debug_width)
                # debug_image.save(os.path.join(characters_dir, "analysis PREVIEW" + ".png")) # every glyph
            # debug_image.save(os.path.join(characters_dir, "analysis PREVIEW" + ".png")) # every row

        debug_image.save(os.path.join(characters_dir, "analysis PREVIEW" + ".png")) # after processing

        # Now we have the characters but since they are all mixed up we need to position them.
        # Sort characters based on 'y' coordinate and group them by number of rows at a time. Then
        # sort each group based on the 'x' coordinate.
        # (Kelly note: this might be redundant?)
        # sort all glyphs by y
        characters.sort(key=lambda x: x[2])
        sorted_characters = []
        for row_id in range(rows):
            sorted_characters.extend(
                # sort groups of 20 glyphs by x
                sorted(characters[cols * row_id : cols * (row_id + 1)], key=lambda x: x[1])
            )



        # █▀▀▀  █   █  ▀▀█▀▀  █▀▀▀▄    █
        # █▄▄    ▀▄▀     █    █   █   █ █
        # █      ▄▀▄     █    █▀█▀   █▄▄▄█
        # █▄▄▄  █   █    █    █  ▀▄  █   █

        # ▄▀▀▀▄  █    █   █  █▀▀▀▄  █   █  ▄▀▀▀▄
        # █      █     █ █   █   █  █▄▄▄█  ▀▄▄▄
        # █  ▀█  █      █    █▀▀▀   █   █      █
        # ▀▄▄▄▀  █▄▄▄   █    █      █   █  ▀▄▄▄▀
        # These are appended to the glyph list, and they need to be kept
        # in sync with default.json, starting from line 216: "cartoucheMiddleTok"
        


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
        sorted_characters.append(sorted_characters[4]) # ali

        # directional glyphs
        for i in range(7): # 8 directions; diagonal alts are in svgtottf.py
            sorted_characters.append(sorted_characters[65])  # ni
        for i in range(7):
            sorted_characters.append(sorted_characters[1])   # akesi
        for i in range(7):
            sorted_characters.append(sorted_characters[81])  # pipi
        for i in range(7):
            sorted_characters.append(sorted_characters[20])  # kala
        for i in range(7):
            sorted_characters.append(sorted_characters[140]) # kijetesantakalu
        for i in range(7):
            sorted_characters.append(sorted_characters[98])  # soweli
        for i in range(7):
            sorted_characters.append(sorted_characters[116]) # waso

        # Latin characters

        # add Latin [ _ ] . :, necessary for ligatures
        sorted_characters.append(sorted_characters[120]) # bracketleft 
        sorted_characters.append(sorted_characters[180]) # underscore  
        sorted_characters.append(sorted_characters[121]) # bracketright
        sorted_characters.append(sorted_characters[122]) # period
        sorted_characters.append(sorted_characters[123]) # colon 

        # add Latin a e n o, necessary for ligatures
        sorted_characters.append(sorted_characters[0]) # a
        sorted_characters.append(sorted_characters[9]) # e
        sorted_characters.append(sorted_characters[148]) # n
        sorted_characters.append(sorted_characters[68]) # o

        # add uppercase IJKLMPSTUW, for Pingo and name glyphs
        for i,c in enumerate("ijklmpstuw"):
            sorted_characters.append(sorted_characters[124+i])

        # add uppercase AENO
        sorted_characters.append(sorted_characters[0]) # A
        sorted_characters.append(sorted_characters[9]) # E
        sorted_characters.append(sorted_characters[148]) # N
        sorted_characters.append(sorted_characters[68]) # O

        # g for Pingo, shown as k
        sorted_characters.append(sorted_characters[126]) # g, shown as k
        # y for yupekosi, shown as j
        sorted_characters.append(sorted_characters[125]) # y, shown as j
        # v for Vivi, shown as w
        sorted_characters.append(sorted_characters[133]) # v, shown as w
        # V for Vivi, shown as w
        sorted_characters.append(sorted_characters[133]) # V, shown as w
        # G
        sorted_characters.append(sorted_characters[126]) # G, shown as k
        # Y
        sorted_characters.append(sorted_characters[125]) # Y, shown as j

        sorted_characters.append(sorted_characters[129]) # b, shown as p
        sorted_characters.append(sorted_characters[129]) # B, shown as p
        sorted_characters.append(sorted_characters[130]) # c, shown as s
        sorted_characters.append(sorted_characters[130]) # C, shown as s
        sorted_characters.append(sorted_characters[131]) # d, shown as t
        sorted_characters.append(sorted_characters[131]) # D, shown as t
        sorted_characters.append(sorted_characters[129]) # f, shown as p
        sorted_characters.append(sorted_characters[129]) # F, shown as p
        sorted_characters.append(sorted_characters[126]) # h, shown as k
        sorted_characters.append(sorted_characters[126]) # H, shown as k
        sorted_characters.append(sorted_characters[126]) # q, shown as k
        sorted_characters.append(sorted_characters[126]) # Q, shown as k
        sorted_characters.append(sorted_characters[133]) # r, shown as w
        sorted_characters.append(sorted_characters[133]) # R, shown as w
        sorted_characters.append(sorted_characters[130]) # x, shown as s
        sorted_characters.append(sorted_characters[130]) # X, shown as s
        sorted_characters.append(sorted_characters[130]) # z, shown as s
        sorted_characters.append(sorted_characters[130]) # Z, shown as s
        


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

        self.rotate(characters_dir, metadata, False,  45, "niTok.SE")
        self.rotate(characters_dir, metadata, False,  90, "niTok.E")
        self.rotate(characters_dir, metadata, False, 135, "niTok.NE")
        self.rotate(characters_dir, metadata, False, 180, "niTok.N")
        self.rotate(characters_dir, metadata, False, 225, "niTok.NW")
        self.rotate(characters_dir, metadata, False, 270, "niTok.W")
        self.rotate(characters_dir, metadata, False, 315, "niTok.SW")

        self.rotate(characters_dir, metadata, False,  45, "akesiTok.NW")
        self.rotate(characters_dir, metadata, False,  90, "akesiTok.W")
        self.rotate(characters_dir, metadata, False, 135, "akesiTok.SW")
        self.rotate(characters_dir, metadata, False, 180, "akesiTok.S")
        self.rotate(characters_dir, metadata, False, 225, "akesiTok.SE")
        self.rotate(characters_dir, metadata, False, 270, "akesiTok.E")
        self.rotate(characters_dir, metadata, False, 315, "akesiTok.NE")

        self.rotate(characters_dir, metadata, False,  45, "pipiTok.NW")
        self.rotate(characters_dir, metadata, False,  90, "pipiTok.W")
        self.rotate(characters_dir, metadata, False, 135, "pipiTok.SW")
        self.rotate(characters_dir, metadata, False, 180, "pipiTok.S")
        self.rotate(characters_dir, metadata, False, 225, "pipiTok.SE")
        self.rotate(characters_dir, metadata, False, 270, "pipiTok.E")
        self.rotate(characters_dir, metadata, False, 315, "pipiTok.NE")

        self.rotate(characters_dir, metadata, False,  45, "kalaTok.NE")
        self.rotate(characters_dir, metadata, False,  90, "kalaTok.N")
        self.rotate(characters_dir, metadata, True,  315, "kalaTok.NW")
        self.rotate(characters_dir, metadata, True,    0, "kalaTok.W")
        self.rotate(characters_dir, metadata, True,   45, "kalaTok.SW")
        self.rotate(characters_dir, metadata, False, 270, "kalaTok.S")
        self.rotate(characters_dir, metadata, False, 315, "kalaTok.SE")

        self.rotate(characters_dir, metadata, False,  45, "kijetesantakaluTok.NE")
        self.rotate(characters_dir, metadata, False,  90, "kijetesantakaluTok.N")
        self.rotate(characters_dir, metadata, True,  315, "kijetesantakaluTok.NW")
        self.rotate(characters_dir, metadata, True,    0, "kijetesantakaluTok.W")
        self.rotate(characters_dir, metadata, True,   45, "kijetesantakaluTok.SW")
        self.rotate(characters_dir, metadata, False, 270, "kijetesantakaluTok.S")
        self.rotate(characters_dir, metadata, False, 315, "kijetesantakaluTok.SE")

        self.rotate(characters_dir, metadata, False,  45, "soweliTok.NE")
        self.rotate(characters_dir, metadata, False,  90, "soweliTok.N")
        self.rotate(characters_dir, metadata, True,  315, "soweliTok.NW")
        self.rotate(characters_dir, metadata, True,    0, "soweliTok.W")
        self.rotate(characters_dir, metadata, True,   45, "soweliTok.SW")
        self.rotate(characters_dir, metadata, False, 270, "soweliTok.S")
        self.rotate(characters_dir, metadata, False, 315, "soweliTok.SE")

        self.rotate(characters_dir, metadata, False,  45, "wasoTok.NE")
        self.rotate(characters_dir, metadata, False,  90, "wasoTok.N")
        self.rotate(characters_dir, metadata, True,  315, "wasoTok.NW")
        self.rotate(characters_dir, metadata, True,    0, "wasoTok.W")
        self.rotate(characters_dir, metadata, True,   45, "wasoTok.SW")
        self.rotate(characters_dir, metadata, False, 270, "wasoTok.S")
        self.rotate(characters_dir, metadata, False, 315, "wasoTok.SE")

    def rotate(self, characters_dir, metadata, flip, degrees_ccw, char_name):
        from PIL import Image, ImageDraw
        char_img = Image.open(characters_dir + "/" + char_name + "/" + char_name + ".png")
        if flip:
            char_img = char_img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        # bilinear might not be the strat; test with different fonts
        char_img = char_img.rotate(angle=degrees_ccw, fillcolor=(0xF0, 0xF0, 0xF0, 0xFF), resample=Image.Resampling.BILINEAR)
        char_img.save(characters_dir + "/" + char_name + "/" + char_name + ".png")

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
            # SHEET VERSION 3: Each glyph scan area is 6x8.
            grid_scan_w = 6
            grid_scan_h = 8
            # The visible gray squares are 4x4, to help with human and scanning errors.
            grid_glyph_w = 4
            grid_scan_hor_padding = 1
        if resize:
            # default bicubic resampling gives us round caps on the cartouche extension
            # which lowers the chance of overlap artifacts, from stacked antialiasing on one pixel
            # like in Arabic or Latin cursive font design
            char_img = char_img.resize((int(char_img.height * grid_scan_w/grid_scan_h), char_img.height))

        draw = ImageDraw.Draw(char_img)
        left, top, right, bottom = 0, 0, char_img.width, char_img.height
        in_pixels = char_img.width/grid_scan_w
        #        ▀               █                   ▄        █
        # █▀▀▄  ▀█  ▀▄ ▄▀  ▄▀▀▄  █        ▀▀▄  █▄▀  ▀█▀       █▀▀▄  █  █  ▄▀▀█
        # █  █   █    █    █▄▄█  █       ▄▀▀█  █     █        █  █  █  █  █  █
        # █▄▄▀   █  ▄▀ ▀▄  ▀▄▄   █       ▀▄▄█  █     ▀▄       █▄▄▀  ▀▄▄█  ▀▄▄█
        # █                                                                ▄▄▀
            # we need to still draw padding
            # but for font sizes that aren't divisible by 4, like 6px and 10px,
            # we'll have uneven padding on the left and right
            # (because the left padding is 1.5 for 6px, and 2.5 for 10px)
            # so we need to calculate it in a way that's consistent with the padding on each scanned glyph
        pixel = metadata.get("pixel") or False
        if not pixel:
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