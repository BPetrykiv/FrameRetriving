import cv2
import numpy as np
import math

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

    vertical_lines = fix_vlines(rect, vertical_lines)

    if len(vertical_lines) > 0:
        columns = split_view_to_frames(rect, vertical_lines)
        return columns
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



def find_frames_v2(original_image, image, rect):
    frames = []

    rows = find_frames_per_row(original_image, image, rect)
    for row in rows:
        frames.append(find_vertical_frames(original_image, image, row))
    
    return frames


def group_by_width(rects, tolerance=0.05):
    groups = {}
    
    for rect in rects:
        (x1, y1, x2, y2) = rect
        width = x2 - x1
        
        found_group = False
        for key in groups.keys():
            if abs(key - width) / key <= tolerance:
                groups[key].append(rect)
                found_group = True
                break
        
        if not found_group:
            groups[width] = [rect]
    
    return groups

def find_largest_group(groups):
    max_group = max(groups.values(), key=lambda group: (len(group), sum(rect[2] - rect[0] for rect in group)))
    return max_group


def calculate_average_width(group):
    total_width = sum([rect[2] - rect[0] for rect in group])
    return total_width / len(group)

def detect_margins(groups, image_width):
    group_averages = {k: calculate_average_width(v) for k, v in groups.items()}
    sorted_groups = sorted(group_averages.items(), key=lambda item: item[1], reverse=True)
    
    frame_width = sorted_groups[0][1] if sorted_groups else 0
    side_margin = 0
    between_margin = 0
    
    if len(sorted_groups) > 1 and sorted_groups[1][1] > 100:
        side_margin = (image_width - sorted_groups[0][1] * 2) / 2

    count = math.floor(image_width / frame_width)
    between_margin = (image_width - count * frame_width - side_margin * 2) / (count - 1) if count > 1 else 0
    
    print(f'Large frame width detected: {frame_width}')
    
    if side_margin != 0:
        print(f'Medium side margin detected: {side_margin}')
    else:
        print(f'No significant medium side margin detected')
    
    if between_margin != 0:
        print(f'Margin between frames detected: {between_margin}')
    else:
        print(f'No significant Margin between frames detected')
    
    return frame_width, side_margin, between_margin


def find_views_v5(image_path):
    image = cv2.imread(image_path)
    image = cv2.resize(image, (1920, 1080), interpolation=cv2.INTER_LINEAR)

    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 250, 255)

    rows = find_frames_v2(image, edges, (0, 0, width, height))

    frames = []

    for row in rows:
        if len(row) == 0:
            continue
        
        groups = group_by_width(row)
        print(f'Groups: {groups}')
        
        frame_width, side_margin, between_frame_margin = detect_margins(groups, width)
        
        (x1, y1, _, y2) = row[0]
        x1 = side_margin if side_margin > 0 else between_frame_margin / 2

        count = math.floor(width / frame_width)
        
        for i in range(count):
            x2 = x1 + frame_width
            frames.append(image[y1:y2, int(x1):int(x2)])
            x1 = x2 + between_frame_margin
    
    for i, frame in enumerate(frames): 
        cv2.imshow(f'View {i}', frame)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()

find_views_v5('screencap4.png')