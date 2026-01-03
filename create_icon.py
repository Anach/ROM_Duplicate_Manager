#!/usr/bin/env python3
"""
Helper script to create a classic Pacman icon and convert it to base64
This will generate both an ICO file and the base64 string
"""

from PIL import Image, ImageDraw
import base64
import io
import math

def create_classic_pacman_icon():
    # Create a 64x64 icon with classic Pacman colors
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))  # Transparent background
    draw = ImageDraw.Draw(img)

    # Classic Pacman colors
    pacman_yellow = (255, 215, 0)  # Classic golden yellow
    eye_black = (0, 0, 0)  # Black for eye
    eye_white = (255, 255, 255)  # White highlight
    pellet_white = (255, 255, 255)  # White power pellets

    # Center and radius for main body
    center_x, center_y = size // 2, size // 2
    radius = 26  # Larger radius for better visibility

    # Draw main Pacman body as a complete circle first
    draw.ellipse([center_x - radius, center_y - radius,
                  center_x + radius, center_y + radius],
                 fill=pacman_yellow)

    # Create the mouth by drawing a triangular "bite"
    # Calculate mouth points for a 45-degree opening
    mouth_angle = 45  # degrees for mouth opening
    angle_top = math.radians(-mouth_angle / 2)
    angle_bottom = math.radians(mouth_angle / 2)

    # Mouth tip extends to the edge
    mouth_tip_x = center_x + radius
    mouth_tip_y = center_y

    # Mouth edges
    mouth_top_x = center_x + radius * math.cos(angle_top)
    mouth_top_y = center_y + radius * math.sin(angle_top)
    mouth_bottom_x = center_x + radius * math.cos(angle_bottom)
    mouth_bottom_y = center_y + radius * math.sin(angle_bottom)

    # Draw the mouth cutout as a triangle
    mouth_points = [
        (center_x, center_y),
        (mouth_tip_x, mouth_tip_y),
        (mouth_top_x, mouth_top_y),
        (center_x, center_y),
        (mouth_bottom_x, mouth_bottom_y),
        (mouth_tip_x, mouth_tip_y)
    ]

    # Create a polygon to cut out the mouth area
    draw.polygon([(center_x, center_y), (mouth_top_x, mouth_top_y), (mouth_tip_x, mouth_tip_y)],
                fill=(0, 0, 0, 0))
    draw.polygon([(center_x, center_y), (mouth_tip_x, mouth_tip_y), (mouth_bottom_x, mouth_bottom_y)],
                fill=(0, 0, 0, 0))

    # Draw the eye
    eye_x = center_x - 8
    eye_y = center_y - 10
    eye_radius = 6

    # Black eye
    draw.ellipse([eye_x - eye_radius, eye_y - eye_radius,
                  eye_x + eye_radius, eye_y + eye_radius],
                 fill=eye_black)

    # White highlight in eye
    highlight_x = eye_x - 2
    highlight_y = eye_y - 2
    highlight_radius = 2
    draw.ellipse([highlight_x - highlight_radius, highlight_y - highlight_radius,
                  highlight_x + highlight_radius, highlight_y + highlight_radius],
                 fill=eye_white)

    # Add power pellets in front of Pacman
    pellet_radius = 3
    pellet_positions = [
        (center_x + radius + 10, center_y - 5),
        (center_x + radius + 10, center_y + 8)
    ]

    for pellet_x, pellet_y in pellet_positions:
        if pellet_x < size - pellet_radius:
            draw.ellipse([pellet_x - pellet_radius, pellet_y - pellet_radius,
                          pellet_x + pellet_radius, pellet_y + pellet_radius],
                         fill=pellet_white)

    return img
    mouth_angle = 35  # degrees
    start_angle = -mouth_angle // 2
    end_angle = 360 - mouth_angle // 2

    # Draw Pacman body (circle with mouth cut out)
    # First draw full circle
    draw.ellipse([center_x - radius, center_y - radius,
                  center_x + radius, center_y + radius],
                 fill=pacman_yellow, outline=pacman_outline, width=2)

    # Create mouth by drawing a triangle to "cut out" the mouth area
    mouth_tip_x = center_x + radius - 2
    mouth_tip_y = center_y

    # Calculate mouth edges
    angle_rad_top = math.radians(start_angle)
    angle_rad_bottom = math.radians(-start_angle)

    mouth_top_x = center_x + (radius - 2) * math.cos(angle_rad_top)
    mouth_top_y = center_y + (radius - 2) * math.sin(angle_rad_top)
    mouth_bottom_x = center_x + (radius - 2) * math.cos(angle_rad_bottom)
    mouth_bottom_y = center_y + (radius - 2) * math.sin(angle_rad_bottom)

    # Draw triangular mouth cutout
    mouth_points = [
        (center_x, center_y),
        (mouth_top_x, mouth_top_y),
        (mouth_tip_x, mouth_tip_y),
        (mouth_bottom_x, mouth_bottom_y)
    ]
    draw.polygon(mouth_points, fill=(0, 0, 0, 0))  # Transparent to cut out

    # Redraw the outline for the mouth
    draw.line([(center_x, center_y), (mouth_top_x, mouth_top_y)],
              fill=pacman_outline, width=2)
    draw.line([(center_x, center_y), (mouth_bottom_x, mouth_bottom_y)],
              fill=pacman_outline, width=2)

    # Draw eye
    eye_x = center_x - radius // 3
    eye_y = center_y - radius // 3
    eye_size = 4
    draw.ellipse([eye_x - eye_size//2, eye_y - eye_size//2,
                  eye_x + eye_size//2, eye_y + eye_size//2],
                 fill=eye_color)

    # Add some 16-bit style "pixels" for extra retro feel
    # Add highlight on Pacman
    highlight_x = center_x - radius // 4
    highlight_y = center_y - radius // 2
    draw.ellipse([highlight_x - 3, highlight_y - 2, highlight_x + 3, highlight_y + 2],
                 fill=(255, 255, 200))

    # Add a few small "power pellet" dots around Pacman for context
    dot_color = (255, 255, 255)
    dot_positions = [
        (center_x + radius + 8, center_y - 8),
        (center_x + radius + 8, center_y + 8),
        (center_x + radius + 16, center_y)
    ]

    for dot_x, dot_y in dot_positions:
        if dot_x < size - 2 and dot_y < size - 2:
            draw.ellipse([dot_x - 2, dot_y - 2, dot_x + 2, dot_y + 2], fill=dot_color)

    return img

def save_icon_and_get_base64():
    icon = create_classic_pacman_icon()

    # Save as ICO file
    icon.save('pacman_icon.ico', format='ICO', sizes=[(64, 64)])
    print("Classic Pacman icon saved as 'pacman_icon.ico'")
    # Convert to base64
    buffer = io.BytesIO()
    icon.save(buffer, format='PNG')
    icon_data = buffer.getvalue()
    base64_string = base64.b64encode(icon_data).decode('utf-8')

    print("\nBase64 string for embedding in your Python app:")
    print("="*60)
    print(f'PACMAN_ICON_BASE64 = "{base64_string}"')
    print("="*60)

    # Also save the base64 to a file for easy copying
    with open('pacman_icon_base64.txt', 'w') as f:
        f.write(f'PACMAN_ICON_BASE64 = "{base64_string}"\n')

    print("\nBase64 string also saved to 'pacman_icon_base64.txt'")

    return base64_string

if __name__ == "__main__":
    try:
        base64_icon = save_icon_and_get_base64()
        print(f"\nClassic Pacman icon created successfully!")
        print("You can now use the base64 string in your ROM Duplicate Manager application.")
        print("\nTo use this icon in your app, add the base64 string to your Python file")
        print("and use it to set the window icon using tkinter's iconphoto method.")
    except ImportError:
        print("PIL (Pillow) is required to run this script.")
        print("Install it with: pip install Pillow")
    except Exception as e:
        print(f"Error creating classic Pacman icon: {e}")