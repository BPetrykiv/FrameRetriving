import cv2
import numpy as np

def draw_lines(image, lines, color=(0, 255, 0), thickness=2):
    if lines is not None:
        for line in lines:
            if (isinstance(line, np.ndarray)):
                line = line[0]

            x1, y1, x2, y2 = line
            cv2.line(image, (x1, y1), (x2, y2), color, thickness)
    return image

def is_proportional(rect, min_ratio=0.5, max_ratio=2.0):
    (x1, y1, x2, y2) = rect
    width = abs(x2 - x1)
    height = abs(y2 - y1)

    if height == 0 or width == 0:
        return False

    ratio = width / height

    return min_ratio <= ratio <= max_ratio

def filter_proportional_frames(frames, min_ratio=0.5, max_ratio=2.0):
    return [frame for frame in frames if is_proportional(frame, min_ratio, max_ratio)]

def fix_hlines(view_rect, lines):

    if lines is None or len(lines) == 0:
        return []

    (x1, y1, x2, y2) = view_rect

    normalized_lines = []
    for line in lines:
        _, line_y1, _, _ = line[0]
        line_y1 = line_y1 + y1
        if line_y1 != y1 and line_y1 != y2:
            normalized_lines.append((x1, line_y1, x2, line_y1))

    normalized_lines.sort(key=lambda line: line[1])  # Sort by y1

    unique_lines = []
    for line in normalized_lines:
        if len(unique_lines) == 0 or line[1] - unique_lines[-1][1] > 2:
            unique_lines.append(line)

    return normalized_lines

def split_view_to_rows(view_rect, horizontal_lines):

    (x1, y1, x2, y2) = view_rect

    start_line = (x1, y1, x2, y1)  # Start at the top of the view_rect
    end_line = (x1, y2, x2, y2)    # End at the bottom of the view_rect

    extended_lines = [start_line] + horizontal_lines + [end_line]
    
    rows = []

    for i in range(len(extended_lines) - 1):
        _, y, _, _ = extended_lines[i]
        _, y_next, _, _ = extended_lines[i + 1]

        # rect_height = y_next - y

        # if rect_height < 10:  # Skip rects with small height
        #     continue

        rect = (x1, y, x2, y_next)  # Define the rectangle
        rows.append(rect)

    return rows

def fix_vlines(view_rect, lines):
    if lines is None or len(lines) == 0:
        return []

    (x1, y1, x2, y2) = view_rect

    normalized_lines = []
    for line in lines:
        line_x1, line_y1, line_x2, line_y2 = line[0]
        line_x1 = line_x1 + x1
        if line_x1 != x1 and line_x1 != x2:
            normalized_lines.append((line_x1, y1, line_x1, y2))

    normalized_lines.sort(key=lambda line: line[0])

    unique_lines = []
    for line in normalized_lines:
        if len(unique_lines) == 0 or line[0] - unique_lines[-1][0] > 2:
            unique_lines.append(line)

    return normalized_lines

def split_view_to_frames(view_rect, vertical_lines):
    (x1, y1, x2, y2) = view_rect

    start_line = (x1, y1, x1, y2)  # Start at the left of the view_rect
    end_line = (x2, y1, x2, y2)    # End at the right of the view_rect

    extended_lines = [start_line] + vertical_lines + [end_line]
    
    frames = []

    for i in range(len(extended_lines) - 1):
        x, _, _, _ = extended_lines[i]
        x_next, _, _, _ = extended_lines[i + 1]

        # rect_width = x_next - x

        # if rect_width < 10:  # Skip rects with small width
        #     continue

        rect = (x, y1, x_next, y2)  # Define the rectangle
        frames.append(rect)

    return frames

def find_vertical_frames(original_image, image, rect):
    (x1, y1, x2, y2) = rect
    sub_image = image[y1:y2, x1:x2]

    lines = cv2.HoughLinesP(sub_image, 1, np.pi / 180, 100, minLineLength=(y2 - y1)/2, maxLineGap=(y2 - y1)/10)
    vertical_lines = [line for line in lines if line[0][0] == line[0][2]] if lines is not None else []

    # copy = original_image[y1:y2, x1:x2].copy()
    # draw_lines(copy, vertical_lines)

    vertical_lines = fix_vlines(rect, vertical_lines)

    if len(vertical_lines) > 0:

        # copy = original_image[y1:y2, x1:x2].copy()
        # draw_lines(copy, vertical_lines)
        # cv2.imshow(f'Current View {x1 + x2}', copy)
        # cv2.imshow(f'Canny View {x1 + x2}', sub_image)

        # while True:
        #     key = cv2.waitKey(0)
        #     if key == ord('n') or key == ord('N'):
        #         cv2.destroyWindow(f'Current View {x1 + x2}')
        #         cv2.destroyWindow(f'Canny View {x1 + x2}')
        #         break

        columns = split_view_to_frames(rect, vertical_lines)
        frames = []
        for column in columns:
            frames.extend(find_horizontal_frames(original_image, image, column))
        return frames
    else:
        return [rect]




def find_horizontal_frames(original_image, image, rect):
    (x1, y1, x2, y2) = rect
    sub_image = image[y1:y2, x1:x2]

    lines = cv2.HoughLinesP(sub_image, 1, np.pi / 180, 100, minLineLength=(x2 - x1)/2, maxLineGap=(x2 - x1)/10)
    horizontal_lines = [line for line in lines if line[0][1] == line[0][3]] if lines is not None else []

    # copy = original_image[y1:y2, x1:x2].copy()
    # draw_lines(copy, horizontal_lines)
    horizontal_lines = fix_hlines(rect, horizontal_lines)

    if len(horizontal_lines) > 0:
        
        # # copy = original_image[y1:y2, x1:x2].copy()
        # # draw_lines(copy, horizontal_lines)
        # cv2.imshow(f'Current View {x1 + x2}', copy)
        # cv2.imshow(f'Canny View {x1 + x2}', sub_image)

        # while True:
        #     key = cv2.waitKey(0)
        #     if key == ord('n') or key == ord('N'):
        #         cv2.destroyWindow(f'Current View {x1 + x2}')
        #         cv2.destroyWindow(f'Canny View {x1 + x2}')
        #         break

        rows = split_view_to_rows(rect, horizontal_lines)
        frames = []
        for row in rows:
            frames.extend(find_vertical_frames(original_image, image, row))
        return frames
    else:
        return [rect]
    
def find_frames_per_row(original_image, image, rect):
    (x1, y1, x2, y2) = rect

    lines = cv2.HoughLinesP(image, 1, np.pi / 180, 100, minLineLength=(x2 - x1)/2, maxLineGap=(x2 - x1)/10)
    horizontal_lines = [line for line in lines if line[0][1] == line[0][3]] if lines is not None else []

    horizontal_lines = fix_hlines(rect, horizontal_lines)

    if len(horizontal_lines) > 0:
        rows = split_view_to_rows(rect, horizontal_lines)
        return rows
    else:
        return [rect]


def find_frames(original_image, image, rect):
    frames = find_horizontal_frames(original_image, image, rect)
    
    if len(frames) == 1:
        frames = find_vertical_frames(original_image, image, rect)
        
    
    return filter_proportional_frames(frames, 0.56, 1.5)


def find_frames_v2(original_image, image, rect):
    frames = []

    rows = find_frames_per_row(original_image, image, rect)
    for row in rows:
        frames.append(filter_proportional_frames(find_vertical_frames(original_image, image, row)))
    
    return frames


def find_views_v4(image_path):
    image = cv2.imread(image_path)
    image = cv2.resize(image, (1920, 1080), interpolation=cv2.INTER_LINEAR)

    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 250, 255)

    frame_rects = find_frames_v2(image, edges, (0, 0, width, height))

    print(f'rects {frame_rects}')

    frames = []

    FRAME_MARGIN = 10
    SIDE_MARGIN = 250 

    count = len([rect for rect in frame_rects if rect])
    frame_height = (height - FRAME_MARGIN * (count - 1)) // count

    y1 = 0

    for row in frame_rects:
        count = len(row)
        if count == 0:
            continue

        side_margin_exist = count == 2 and len(frame_rects) > 1
        
        if side_margin_exist:
            frame_width = (width - SIDE_MARGIN * 2 - FRAME_MARGIN * (count - 1)) // count
        else:
            frame_width = (width - FRAME_MARGIN * (count - 1)) // count

        print(f'frame_width {frame_width}')

        if side_margin_exist:
            x1 = SIDE_MARGIN
        else:
            x1 = 0
        
        for i in range(count):
            x2 = x1 + frame_width
            y2 = y1 + frame_height
            frames.append(image[y1:y2, int(x1):int(x2)])
            x1 = x2 + FRAME_MARGIN
        
        y1 = y1 + frame_height

    for i, frame in enumerate(frames): 
        cv2.imshow(f'View {i}', frame)

    # for i, (x1, y1, x2, y2) in enumerate(frame_rects):
    #     view = image[y1:y2, x1:x2]
    #     # height, width = view.shape[:2]
    #     # view = cv2.resize(view, (int(width / 2), int(height / 2)), interpolation=cv2.INTER_LINEAR)

    #     cv2.imshow(f'View {i}', view)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()

find_views_v4('screencap5.png')