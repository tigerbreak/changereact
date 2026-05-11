#!/usr/bin/env python3
"""Parse SVG design file and extract design tokens, text styles, and components."""

import re
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

SVG_PATH = Path(__file__).parent.parent / "Styles.svg"
OUTPUT_DIR = Path(__file__).parent.parent / "generated"


def extract_text_styles(svg_content: str) -> list[dict]:
    """Extract all text styles from SVG."""
    text_styles = []
    
    # Pattern to match text elements - attributes can be in any order
    # First, find all text element blocks
    text_pattern = re.compile(
        r'<text\s([^>]*?)>([\s\S]*?)</text>',
        re.MULTILINE
    )
    
    for match in text_pattern.finditer(svg_content):
        attrs_str = match.group(1)
        content = match.group(2)
        
        # Extract individual attributes
        id_match = re.search(r'id="([^"]+)"', attrs_str)
        fill_match = re.search(r'fill="([^"]+)"', attrs_str)
        font_family_match = re.search(r'font-family="([^"]+)"', attrs_str)
        font_size_match = re.search(r'font-size="([^"]+)"', attrs_str)
        font_weight_match = re.search(r'font-weight="([^"]+)"', attrs_str)
        letter_spacing_match = re.search(r'letter-spacing="([^"]+)"', attrs_str)
        
        if not id_match:
            continue
        
        element_id = id_match.group(1)
        fill = fill_match.group(1) if fill_match else "black"
        font_family = font_family_match.group(1) if font_family_match else "inherit"
        font_size = float(font_size_match.group(1)) if font_size_match else 16
        font_weight = font_weight_match.group(1) if font_weight_match else None
        letter_spacing = letter_spacing_match.group(1) if letter_spacing_match else None
        
        # Extract text content from tspan
        tspan_pattern = re.compile(r'<tspan[^>]*?x="([^"]+)"[^>]*?y="([^"]+)"[^>]*?>([^<]+)</tspan>')
        text_content = []
        first_x, first_y = 0, 0
        
        for i, tspan_match in enumerate(tspan_pattern.finditer(content)):
            x = float(tspan_match.group(1))
            y = float(tspan_match.group(2))
            text = tspan_match.group(3)
            text_content.append(text)
            if i == 0:
                first_x, first_y = x, y
        
        # Create style name
        style_name = element_id.split()[0] if len(element_id.split()) > 1 else element_id
        
        text_styles.append({
            "name": style_name,
            "full_name": element_id,
            "fontFamily": font_family.replace(" ", "-").lower(),
            "fontSize": font_size,
            "fontWeight": font_weight,
            "letterSpacing": letter_spacing,
            "color": fill,
            "x": first_x,
            "y": first_y,
            "content": " ".join(text_content)[:50],  # Truncate for display
        })
    
    return text_styles


def extract_colors(svg_content: str) -> list[dict]:
    """Extract all unique colors from SVG."""
    color_pattern = re.compile(r'(?:fill|stroke)="(#?[A-Fa-f0-9]{3,8})"')
    colors = defaultdict(int)
    
    for match in color_pattern.finditer(svg_content):
        hex_color = match.group(1)
        if len(hex_color) == 4 and hex_color.startswith('#'):  # Short hex
            hex_color = '#' + ''.join([c*2 for c in hex_color[1:]])
        if hex_color not in ['none', 'None']:
            colors[hex_color.upper()] += 1
    
    # Sort by frequency and return top colors
    sorted_colors = sorted(colors.items(), key=lambda x: x[1], reverse=True)
    
    result = []
    for color, count in sorted_colors:
        # Generate meaningful name
        if color == '#000000' or color == '#000':
            name = "black"
        elif color == '#FFFFFF' or color == '#FFF':
            name = "white"
        elif color == '#F5F5F5':
            name = "background-gray"
        elif color == '#E9E9E9':
            name = "light-gray"
        else:
            name = f"color-{color.replace('#', '').lower()}"
        
        result.append({
            "name": name,
            "value": color,
            "count": count,
        })
    
    return result


def extract_components(svg_content: str) -> list[dict]:
    """Extract component definitions from SVG groups."""
    components = []
    
    # Find all group elements with IDs
    group_pattern = re.compile(r'<g[^>]*?id="([^"]+)"', re.MULTILINE)
    
    for match in group_pattern.finditer(svg_content):
        group_id = match.group(1)
        
        # Categorize components
        if 'Button' in group_id:
            comp_type = "button"
        elif 'Nav' in group_id:
            comp_type = "nav"
        elif 'Label' in group_id:
            comp_type = "label"
        elif 'Frame' in group_id:
            comp_type = "container"
        else:
            comp_type = "group"
        
        components.append({
            "id": group_id,
            "type": comp_type,
            "name": group_id.replace(" ", "_").replace("=", "_"),
        })
    
    return components


def main():
    """Main function to parse SVG and generate design tokens."""
    print(f"📖 Reading SVG from: {SVG_PATH}")
    
    with open(SVG_PATH, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    print(f"📊 SVG file size: {len(svg_content):,} characters")
    
    # Extract design tokens
    print("\n🔍 Extracting text styles...")
    text_styles = extract_text_styles(svg_content)
    print(f"   Found {len(text_styles)} text styles")
    
    print("\n🎨 Extracting colors...")
    colors = extract_colors(svg_content)
    print(f"   Found {len(colors)} unique colors")
    
    print("\n🧩 Extracting components...")
    components = extract_components(svg_content)
    print(f"   Found {len(components)} component groups")
    
    # Generate design tokens JSON
    design_tokens = {
        "metadata": {
            "source": "Styles.svg",
            "viewBox": "0 0 1533 5813",
            "canvasWidth": 1533,
            "canvasHeight": 5813,
        },
        "colors": colors[:20],  # Top 20 colors
        "textStyles": text_styles,
        "components": components,
    }
    
    # Save extracted data
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "design-tokens.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(design_tokens, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Design tokens saved to: {output_path}")
    
    # Print summary
    print("\n📋 Summary:")
    print(f"   Colors: {len(colors)} unique")
    print(f"   Text Styles: {len(text_styles)}")
    print(f"   Components: {len(components)}")
    
    # Show top colors
    print("\n🎨 Top Colors:")
    for color in colors[:5]:
        print(f"   {color['name']}: {color['value']} (used {color['count']} times)")
    
    # Show text styles
    print("\n📝 Text Styles:")
    for style in text_styles[:10]:
        print(f"   {style['name']}: {style['fontFamily']} {style['fontSize']}px "
              f"{'weight=' + str(style['fontWeight']) if style['fontWeight'] else ''}")


if __name__ == "__main__":
    main()
