import os
import itertools
import json
import cv2
from packaging.version import Version
from PIL import Image, ImageDraw

def sheet_to_png(sheet, debug_dir, default_json, cli_args, other_words_string, cols=20, rows=9):
    """Convert a sheet of sample writing input to a custom directory structure of PNGs.

    Detect all characters in the sheet as a separate contours and convert each to
    a PNG image in a temp/user provided directory.

    Parameters
    ----------
    sheet : str
        Path to the sheet file to be converted.
    debug_dir : str
        Path to directory to save characters in.
    default_json: str
        Path to config file.
    cols : int, default=8
        Number of columns of expected contours. Defaults to 8 based on the default sample.
    rows : int, default=10
        Number of rows of expected contours. Defaults to 10 based on the default sample.
    """
    print("SHEETtoPNG")
    if os.path.isdir(sheet):
        raise IsADirectoryError("Sheet parameter should not be a directory.")
    characters = detect_characters(
        debug_dir, default_json, sheet, cli_args, other_words_string, cols=cols, rows=rows
    )
    save_images(
        characters, # more like cells
        debug_dir,
        default_json,
        cli_args
    )









def detect_characters(debug_dir, default_json, sheet_image, cli_args, other_words_string, cols=20, rows=9):
        """Detect contours on the input image and filter them to get only characters.

        Uses opencv to threshold the image for better contour detection. After finding all
        contours, they are filtered based on area, cropped and then sorted sequentially based
        on coordinates. Finally returs the cols*rows top candidates for being the character
        containing contours.

        Parameters
        ----------
        sheet_image : str
            Path to the sheet file to be converted.
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
        cv2.imwrite(os.path.join(debug_dir, "analysis step 1 - image" + ".png"), image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(os.path.join(debug_dir, "analysis step 2 - grayscale" + ".png"), gray)

        # Threshold and filter the image for better contour detection
        threshold_value = 127 # formerly 200. change back if black rectangles aren't being detected as dark enough.
        _, thresh = cv2.threshold(gray, threshold_value, 255, 1)
        cv2.imwrite(os.path.join(debug_dir, "analysis step 3 - threshold" + ".png"), thresh)
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

        pixel = cli_args.get("pixel") or False
        if pixel:
            iterations = 0
        else:
            iterations = 2
        close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel, iterations=iterations)

        cv2.imwrite(os.path.join(debug_dir, "analysis step 4 - close" + ".png"), close)

        # Search for contours.
        contours, h = cv2.findContours(
            close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # for debug imaging
        debug_image = Image.open(sheet_image).convert("RGB")
        debug_draw = ImageDraw.Draw(debug_image)
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
        #         # debug_image.save(os.path.join(debug_dir, "analysis PREVIEW" + ".png")) # slower
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
        # debug_image.save(os.path.join(debug_dir, "analysis PREVIEW" + ".png"))

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
        # debug_image.save(os.path.join(debug_dir, "analysis PREVIEW" + ".png"))

        # output the biggest 9 rows as images, for debug purposes
        row_images = []
        row_areas = []
        for row in range(rows):
            # print(row)
            left, top, width, height = cv2.boundingRect(contours[row])
            # left_s, top_s, width_s, height_s = small_rect(contours[row])
            row_areas.append(width*height)

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
            # debug_image.save(os.path.join(debug_dir, "analysis PREVIEW" + ".png"))

        average_row_area = 0
        for row in range(rows): average_row_area += row_areas[row]
        average_row_area /= rows

        too_small_row = average_row_area * 0.75
        too_big_row   = average_row_area * 1.125
        for row in range(rows):
            if not (too_small_row < row_areas[row] < too_big_row):
                print(f"⚠️ Row[{row}] is {row_areas[row]/average_row_area:.2g}x the average row area! "
                    + "Check the analysis PNGs.\n" + "   This usually happens if someone's custom nimi label gets too close to a big black rectangle, preventing it from being recognized as a rectangle.")

        # sort top to bottom
        row_images.sort(key=lambda x: x[2])

        # row_dir = os.path.join(debug_dir, "9 rows")
        row_dir = os.path.join(debug_dir)
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

            sheet_version = cli_args.get("sheetversion") or "99999999.999999.999999"
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
            import math
            glyph_w      =            grid_scan_w      * row_w/grid_row_w
            glyph_h      =            grid_scan_h      * row_h/grid_row_h
            # math.floor ensures that for odd scan widths, a left-aligned pixel font glyph is
            # horizontally centered on the scan area, which is cute
            left_padding = math.floor(grid_hor_padding * row_w/grid_row_w)
            top_padding  =            grid_ver_padding * row_h/grid_row_h
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

                # we wanna find the center of gravity of the cell
                # and we'll use that to move the cell
                # to avoid like, scanning one pixel of a neighboring glyph
                old_glyph_left = glyph_left
                new_glyph_left = glyph_left
                old_glyph_top = glyph_top
                new_glyph_top = glyph_top
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 127, 255, 1)
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
                            # don't affect x_shift during cartouches and te/to, because they're likely to be off to the side
                            x_shift = prev_x_shift

                    prev_x_shift = x_shift
                    # print("shift:", int(centroid_x - glyph_w/2), int(centroid_y - glyph_h/2))
                    new_glyph_left = glyph_left + x_shift
                    new_glyph_top  = glyph_top  + y_shift

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
                # debug_image.save(os.path.join(debug_dir, "analysis PREVIEW" + ".png")) # every glyph
            # debug_image.save(os.path.join(debug_dir, "analysis PREVIEW" + ".png")) # every row

        debug_image.save(os.path.join(debug_dir, "analysis PREVIEW" + ".png")) # after processing

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





        # redraws

        if other_words_string:
            other_words = other_words_string.split()
            blank_cells = [ # default.toml indices of the blank cells on the page
                                                             136, 137, 138, 139, # 4 cells
                                         152, 153, 154, 155, 156, 157, 158, 159, # 8 cells
                167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179  # 13 cells
            ]

            for position, word in enumerate(other_words):
                with open(default_json) as f:
                    glyph_json = json.load(f).get("glyphs-fancy", {})
                for default_glyph_index, default_glyph in enumerate(glyph_json):
                    if 'name' in default_glyph:
                        if default_glyph['name'] == word + "Tok":
                            sorted_characters[default_glyph_index] = sorted_characters[blank_cells[position]]
                            # todo: remove redundant glyphs from the preview web page






        # here we start messing with glyphs based on their hardcoded indices.
        # this logic should be reworked to read from default_json instead.
        # for glyph in default_json:
            # if glyph["scan-shift"]:
                # do the things


        # cartouches
        open_cartouche  = sorted_characters[120]
        close_cartouche = sorted_characters[121]
        glyph_left, glyph_top, glyph_w, glyph_h = open_cartouche[1], open_cartouche[2], open_cartouche[3], open_cartouche[4]
        cartouche_middle_glyph_left = glyph_left + glyph_w - 1

        # shift the open and close cartouche scan area inward, to match how the gray boxes are shifted
        # glyph_left = open_cartouche[1] + glyph_w/16
        # print("horizontal padding", grid_scan_hor_padding * glyph_w/grid_scan_w)
        if pixel:
            right_scan_padding = math.floor(grid_scan_hor_padding * glyph_w/grid_scan_w)
            left_scan_padding  = math.ceil( grid_scan_hor_padding * glyph_w/grid_scan_w)
        else:
            right_scan_padding = grid_scan_hor_padding * glyph_w/grid_scan_w
            left_scan_padding  = grid_scan_hor_padding * glyph_w/grid_scan_w

        glyph_left = open_cartouche[1] + grid_scan_hor_padding * glyph_w/grid_scan_w
        roi = image[int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + glyph_w)]
        sorted_characters[120][0] = roi
        sorted_characters[120][1] = glyph_left

        glyph_left = close_cartouche[1] - grid_scan_hor_padding * glyph_w/grid_scan_w
        roi = image[int(glyph_top ) : int(glyph_top  + glyph_h),
                    int(glyph_left) : int(glyph_left + glyph_w)]
        sorted_characters[121][0] = roi
        sorted_characters[121][1] = glyph_left



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
        


        # for the middle portion of the cartouche, grab the rightmost 1px column
        # of the open cartouche. it'll be automatically stretched to the width
        # of a glyph when it's converted to BMP, then SVG.
        roi = image[int(glyph_top                  ) : int(glyph_top                   + glyph_h),
                    int(cartouche_middle_glyph_left) : int(cartouche_middle_glyph_left + 1)]
        #                                                                    # bug? vv
        sorted_characters.append([roi, cartouche_middle_glyph_left, glyph_top, glyph_w, glyph_h])



        # Latin characters

        # add Latin [ _ ] . :, necessary for ligatures
        sorted_characters.append(sorted_characters[120]) # bracketleft 
        sorted_characters.append(sorted_characters[180]) # underscore  
        sorted_characters.append(sorted_characters[121]) # bracketright
        sorted_characters.append(sorted_characters[122]) # period
        sorted_characters.append(sorted_characters[123]) # colon 

        # add Latin a e n o, necessary for ligatures
        sorted_characters.append(sorted_characters[0])   # a
        sorted_characters.append(sorted_characters[9])   # e
        sorted_characters.append(sorted_characters[148]) # n
        sorted_characters.append(sorted_characters[68])  # o



        # add every other Latin letter, for Pingo and name glyphs

        sorted_characters.append(sorted_characters[0])   # A, shown as a
        sorted_characters.append(sorted_characters[9])   # E, shown as e
        sorted_characters.append(sorted_characters[148]) # N, shown as n
        sorted_characters.append(sorted_characters[68])  # O, shown as o

        for i,c in enumerate("ijklmpstuw"):
            sorted_characters.append(sorted_characters[124+i]) # uppercase IJKLMPSTUW, shown as lowercase

        sorted_characters.append(sorted_characters[129]) # b, shown as p
        sorted_characters.append(sorted_characters[129]) # B, shown as p
        sorted_characters.append(sorted_characters[130]) # c, shown as s
        sorted_characters.append(sorted_characters[130]) # C, shown as s
        sorted_characters.append(sorted_characters[131]) # d, shown as t
        sorted_characters.append(sorted_characters[131]) # D, shown as t
        sorted_characters.append(sorted_characters[129]) # f, shown as p
        sorted_characters.append(sorted_characters[129]) # F, shown as p
        sorted_characters.append(sorted_characters[126]) # g, shown as k
        sorted_characters.append(sorted_characters[126]) # G, shown as k
        sorted_characters.append(sorted_characters[126]) # h, shown as k
        sorted_characters.append(sorted_characters[126]) # H, shown as k
        sorted_characters.append(sorted_characters[126]) # q, shown as k
        sorted_characters.append(sorted_characters[126]) # Q, shown as k
        sorted_characters.append(sorted_characters[133]) # r, shown as w
        sorted_characters.append(sorted_characters[133]) # R, shown as w
        sorted_characters.append(sorted_characters[133]) # v, shown as w
        sorted_characters.append(sorted_characters[133]) # V, shown as w
        sorted_characters.append(sorted_characters[130]) # x, shown as s
        sorted_characters.append(sorted_characters[130]) # X, shown as s
        sorted_characters.append(sorted_characters[125]) # y, shown as j
        sorted_characters.append(sorted_characters[125]) # Y, shown as j
        sorted_characters.append(sorted_characters[130]) # z, shown as s
        sorted_characters.append(sorted_characters[130]) # Z, shown as s
        



        return sorted_characters









def save_images(characters, debug_dir, default_json, cli_args):
        """Create directory for each character and save as PNG.

        Creates directory and PNG file for each image as following:

            debug_dir/ord(character)/ord(character).png  (SINGLE SHEET INPUT)
            debug_dir/sheet_filename/ord(character)/ord(character).png  (MULTIPLE SHEETS INPUT)

        Parameters
        ----------
        characters : list of list
            Sorted list of character images each inner list representing a row of images.
        debug_dir : str
            Path to directory to save characters in.
        """
        os.makedirs(debug_dir, exist_ok=True)

        # Create directory for each character and save the png for the characters
        # Structure (single sheet): UserProvidedDir/ord(character)/ord(character).png
        # Structure (multiple sheets): UserProvidedDir/sheet_filename/ord(character)/ord(character).png
            # Kelly note: the script does not support multiple sheets, actually

        # Kelly note: `characters` is more like `cells`, since not every cell contains a glyph
        for cellNum, images in enumerate(characters):

            with open(default_json) as f:
                glyphList = json.load(f).get("glyphs-fancy", {})
                curMetadatum = glyphList[cellNum]
                if len(glyphList) > cellNum: # should this be `>=`?
                    if 'name' in curMetadatum:
                        character = os.path.join(debug_dir, curMetadatum['name'])
                        if not os.path.exists(character):
                            os.mkdir(character)
                        # print(character, curMetadatum['name'] + ".png")
                        cv2.imwrite(
                            os.path.join(character, curMetadatum['name'] + ".png"),
                            images[0],
                        )

        # Read pixel size and write it to default.json, so svgtottf_ffpython can use it.
        # If this brittle codeblock breaks, just comment it out, and svgtottf_ffpython will assume an 8px font.
        with open(default_json) as f:
            json_data = json.load(f)
        first_char_name = json_data.get("glyphs-fancy", {})[0].get('name', 'aTok')
        first_char_img  = Image.open(debug_dir + "/" + first_char_name + "/" + first_char_name + ".png")
        json_data["pixel-size"] = first_char_img.size[0]*2/3
        with open(default_json, "w") as file:
            json.dump(json_data, file, indent=4)

        # Trim cartouche characters
            # We'll have to do the same thing for long pi
            # and any other character that spans two cells
        pad("right", debug_dir, cli_args, "cartoucheStartTok")
        pad("right", debug_dir, cli_args, "bracketleft")
        
        pad("left",  debug_dir, cli_args, "cartoucheEndTok")
        pad("left",  debug_dir, cli_args, "bracketright")

        pad("right", debug_dir, cli_args, "cartoucheMiddleTok", True)
        pad("left",  debug_dir, cli_args, "cartoucheMiddleTok", True)
        pad("right", debug_dir, cli_args, "underscore", True)
        pad("left",  debug_dir, cli_args, "underscore", True)










def pad(side, debug_dir, cli_args, char_name, resize=False):
        char_img = Image.open(debug_dir + "/" + char_name + "/" + char_name + ".png")

        # resize the cartouche middle from 1px wide to the standard width (for a given sheet version)
        sheet_version = cli_args.get("sheetversion") or "99999999.999999.999999"
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
        left, top, right, bottom = 0, 0, char_img.width-1, char_img.height-1
        in_pixels = char_img.width/grid_scan_w

        pixel = cli_args.get("pixel") or False
        import math

        # the middle of the cartouche is made from the rightmost 1px column of the open cartouche.
        # in pixel fonts, we include that 1px column in the close cartouche.
        if pixel:
            #                              `ceil` and `floor` are for 6px and 10px fonts,
            #                              which have 1px more padding on the left side
            left_scan_padding       = math.ceil (grid_scan_hor_padding*in_pixels)
            right_scan_padding      = math.floor(grid_scan_hor_padding*in_pixels)
            cartouche_overlap_pixel = 1
            cartouche_overlap  = 0
        else:
            left_scan_padding  = grid_scan_hor_padding*in_pixels
            right_scan_padding = grid_scan_hor_padding*in_pixels
            cartouche_overlap  = grid_glyph_w*in_pixels/42
            cartouche_overlap_pixel = 0
        if side == "left":
            draw.rectangle(
                ((left,                                                                       top   ),     
                 (left + left_scan_padding - cartouche_overlap - cartouche_overlap_pixel - 1, bottom)),
                fill="white"
            )
        if side == "right":
            draw.rectangle(
                ((right - right_scan_padding + cartouche_overlap + 1, top   ), 
                 (right,                                              bottom)),
                fill="white"
            )
        char_img.save(debug_dir + "/" + char_name + "/" + char_name + ".png")