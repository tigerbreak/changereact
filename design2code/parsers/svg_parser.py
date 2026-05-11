"""
SVG Parser module.

Parses SVG files exported from Figma and converts them into the 
framework-agnostic Intermediate Representation (IR).

Usage:
    from design2code.parsers.svg_parser import SvgParser
    
    parser = SvgParser("path/to/design.svg")
    ir = parser.parse()
"""

import re
from pathlib import Path
from typing import Optional
from ..ir.model import (
    DesignIR,
    DesignElement,
    ElementType,
    BoxStyle,
    TextStyle,
    ColorToken,
    TypographyToken,
    ComponentDefinition,
    SpacingToken,
)


class SvgParser:
    """Parses SVG design files and converts them to DesignIR."""

    def __init__(self, svg_path: str):
        self.svg_path = Path(svg_path)
        self.svg_content = ""
        self._color_usage: dict[str, int] = {}
        self._extracted_texts: list[dict] = []
        self._extracted_groups: list[dict] = []
        self._viewbox = {"width": 0, "height": 0}

    def parse(self) -> DesignIR:
        """Main entry point: parse SVG and return DesignIR."""
        self._load_svg()
        self._parse_viewbox()
        self._extract_colors()
        self._extract_text_styles()
        self._extract_components()
        self._build_element_tree()

        return self._build_ir()

    def _load_svg(self):
        """Load SVG file content."""
        with open(self.svg_path, "r", encoding="utf-8") as f:
            self.svg_content = f.read()

    def _parse_viewbox(self):
        """Extract viewBox dimensions."""
        match = re.search(r'viewBox="[^"]*"', self.svg_content)
        if match:
            parts = match.group().split('"')[1].split()
            if len(parts) >= 4:
                self._viewbox = {
                    "width": float(parts[2]),
                    "height": float(parts[3]),
                }
        
        # Fallback to width/height attributes
        if self._viewbox["width"] == 0:
            w_match = re.search(r'width="(\d+(?:\.\d+)?)"', self.svg_content)
            h_match = re.search(r'height="(\d+(?:\.\d+)?)"', self.svg_content)
            if w_match:
                self._viewbox["width"] = float(w_match.group(1))
            if h_match:
                self._viewbox["height"] = float(h_match.group(1))

    def _extract_colors(self):
        """Extract all colors from SVG fill/stroke attributes."""
        color_pattern = re.compile(r'(?:fill|stroke)="(#?[A-Fa-f0-9]{3,8})"')
        self._color_usage = {}

        for match in color_pattern.finditer(self.svg_content):
            hex_color = match.group(1)
            # Normalize short hex
            if len(hex_color) == 4 and hex_color.startswith("#"):
                hex_color = "#" + "".join([c * 2 for c in hex_color[1:]])
            hex_color = hex_color.upper()

            if hex_color not in ("NONE",):
                self._color_usage[hex_color] = self._color_usage.get(hex_color, 0) + 1

    def _extract_text_styles(self):
        """Extract all text elements and their typography information."""
        self._extracted_texts = []
        
        text_pattern = re.compile(
            r'<text\s([^>]*?)>([\s\S]*?)</text>',
            re.MULTILINE,
        )

        for match in text_pattern.finditer(self.svg_content):
            attrs_str = match.group(1)
            content = match.group(2)

            element_id = self._extract_attr(attrs_str, 'id')
            if not element_id:
                continue

            font_family = self._extract_attr(attrs_str, 'font-family')
            font_size = self._extract_attr(attrs_str, 'font-size')
            font_weight = self._extract_attr(attrs_str, 'font-weight')
            letter_spacing = self._extract_attr(attrs_str, 'letter-spacing')
            fill = self._extract_attr(attrs_str, 'fill')

            # Extract text content and position from tspan
            tspan_pattern = re.compile(
                r'<tspan[^>]*?x="([^"]+)"[^>]*?y="([^"]+)"[^>]*?>([^<]+)</tspan>'
            )
            text_lines = []
            first_x, first_y = 0.0, 0.0

            for i, tspan_match in enumerate(tspan_pattern.finditer(content)):
                x = float(tspan_match.group(1))
                y = float(tspan_match.group(2))
                text = tspan_match.group(3)
                text_lines.append(text)
                if i == 0:
                    first_x, first_y = x, y

            self._extracted_texts.append({
                "id": element_id,
                "font_family": font_family,
                "font_size": float(font_size) if font_size else 16.0,
                "font_weight": font_weight,
                "letter_spacing": letter_spacing,
                "color": fill or "black",
                "x": first_x,
                "y": first_y,
                "content": " ".join(text_lines),
            })

    def _extract_components(self):
        """Extract component groups from SVG."""
        self._extracted_groups = []
        
        # Find all <g> elements with id
        group_pattern = re.compile(
            r'<g\s([^>]*?)id="([^"]+)"',
            re.MULTILINE,
        )

        for match in group_pattern.finditer(self.svg_content):
            group_id = match.group(2)
            attrs_str = match.group(1)

            # Skip mask/clip paths and patterns
            if any(skip in group_id.lower() for skip in [
                'mask', 'clip', 'pattern', 'path-', 'image'
            ]):
                continue

            # Classify component type
            comp_type = self._classify_component(group_id)

            self._extracted_groups.append({
                "id": group_id,
                "type": comp_type,
                "attrs": attrs_str,
            })

    def _classify_component(self, group_id: str) -> ElementType:
        """Classify a group element into a component type."""
        gid_lower = group_id.lower()
        
        if any(k in gid_lower for k in ['button', 'btn']):
            return ElementType.BUTTON
        elif any(k in gid_lower for k in ['nav', 'header', 'menu', 'toolbar']):
            return ElementType.NAV
        elif any(k in gid_lower for k in ['card', 'frame', 'container', 'box']):
            return ElementType.CONTAINER
        elif any(k in gid_lower for k in ['label', 'tag']):
            return ElementType.TEXT
        elif any(k in gid_lower for k in ['input', 'field', 'form']):
            return ElementType.INPUT
        elif any(k in gid_lower for k in ['icon', 'logo']):
            return ElementType.ICON
        elif any(k in gid_lower for k in ['image', 'photo', 'picture']):
            return ElementType.IMAGE
        
        return ElementType.UNKNOWN

    def _build_element_tree(self):
        """Build the element tree structure from extracted data."""
        # This is a simplified version - in production, you'd parse the
        # full SVG DOM to build the actual tree
        pass

    def _build_ir(self) -> DesignIR:
        """Construct the final DesignIR from all extracted data."""
        ir = DesignIR(
            source_file=str(self.svg_path),
            canvas_width=self._viewbox["width"],
            canvas_height=self._viewbox["height"],
        )

        # Build color tokens
        ir.colors = self._build_color_tokens()

        # Build typography tokens
        ir.typography = self._build_typography_tokens()

        # Build spacing tokens
        ir.spacing = self._build_spacing_tokens()

        # Build component definitions
        ir.components = self._build_component_definitions()

        # Build root elements
        ir.root_elements = self._build_root_elements()

        return ir

    def _build_color_tokens(self) -> list[ColorToken]:
        """Build ColorToken list from extracted colors."""
        tokens = []
        for color_hex, count in sorted(
            self._color_usage.items(), key=lambda x: x[1], reverse=True
        ):
            name = self._semantic_color_name(color_hex)
            tokens.append(ColorToken(
                name=name,
                value=color_hex,
                usage_count=count,
            ))
        return tokens

    def _build_typography_tokens(self) -> list[TypographyToken]:
        """Build TypographyToken list from extracted text styles."""
        seen = set()
        tokens = []

        for text in self._extracted_texts:
            # Create a unique key for this style
            style_key = (
                text["font_family"],
                text["font_size"],
                text["font_weight"],
                text["letter_spacing"],
            )

            if style_key in seen:
                continue
            seen.add(style_key)

            # Generate a meaningful name
            name = self._generate_typography_name(text)

            tokens.append(TypographyToken(
                name=name,
                font_family=text["font_family"] or "inherit",
                font_size=text["font_size"],
                font_weight=text["font_weight"],
                letter_spacing=text["letter_spacing"],
            ))

        return tokens

    def _build_spacing_tokens(self) -> list[SpacingToken]:
        """Extract common spacing values from element positions."""
        # Collect y-coordinates and compute gaps
        y_values = sorted([t["y"] for t in self._extracted_texts])
        gaps = []
        for i in range(1, len(y_values)):
            gap = y_values[i] - y_values[i - 1]
            if gap > 0:
                gaps.append(round(gap))

        # Find common spacing values
        from collections import Counter
        spacing_counts = Counter(gaps)
        
        tokens = []
        for i, (value, _count) in enumerate(
            spacing_counts.most_common(8)
        ):
            size_name = ["xs", "sm", "md", "lg", "xl", "xxl", "xxxl", "huge"][i]
            tokens.append(SpacingToken(name=size_name, value=value))

        return tokens

    def _build_component_definitions(self) -> list[ComponentDefinition]:
        """Build component definitions from extracted groups."""
        components = []
        seen_names = set()

        for group in self._extracted_groups:
            name = group["id"].replace(" ", "_").replace("=", "_")
            if name in seen_names:
                continue
            seen_names.add(name)

            comp = ComponentDefinition(
                name=name,
                element_type=group["type"],
                description=f"Component extracted from SVG group '{group['id']}'",
            )
            components.append(comp)

        return components

    def _build_root_elements(self) -> list[DesignElement]:
        """Build root-level design elements."""
        elements = []
        
        # Create text elements
        for text in self._extracted_texts:
            element = DesignElement(
                id=text["id"],
                name=text["id"].split()[0] if text["id"] else "text",
                element_type=ElementType.TEXT,
                box=BoxStyle(
                    position="absolute",
                    top=f"{text['y']}px",
                    left=f"{text['x']}px",
                ),
                text_style=TextStyle(
                    font_family=text["font_family"],
                    font_size=f"{text['font_size']}px",
                    font_weight=text["font_weight"],
                    letter_spacing=text["letter_spacing"],
                    color=text["color"],
                ),
                text_content=text["content"],
            )
            elements.append(element)

        return elements

    # --- Helper methods ---

    @staticmethod
    def _extract_attr(attrs_str: str, attr_name: str) -> Optional[str]:
        """Extract an attribute value from an SVG attribute string."""
        pattern = rf'{attr_name}="([^"]+)"'
        match = re.search(pattern, attrs_str)
        return match.group(1) if match else None

    @staticmethod
    def _semantic_color_name(hex_color: str) -> str:
        """Generate a semantic name for a color."""
        color_map = {
            "#000000": "black",
            "#FFFFFF": "white",
            "#F5F5F5": "background-gray",
            "#E9E9E9": "light-gray",
            "#C5C5C5": "border-gray",
            "#575757": "text-secondary",
            "#1F41FF": "primary-blue",
            "#9747FF": "accent-purple",
            "#D0FBF9": "bg-cyan",
            "#D900FF": "accent-magenta",
            "#2200FF": "primary-deep-blue",
        }
        return color_map.get(hex_color, f"color-{hex_color[1:].lower()}")

    @staticmethod
    def _generate_typography_name(text: dict) -> str:
        """Generate a unique name for a typography style."""
        import re as _re
        font_id = text["id"]
        size_str = str(text["font_size"]).replace(".", "_")

        # Try to extract style from the element id
        if "Header" in font_id:
            num_match = _re.search(r'Header\s*(\d+)', font_id)
            num = num_match.group(1) if num_match else "x"
            # Check for Mono/Expanded/etc variants after the number
            after_header = font_id[font_id.index("Header") + 6:]  # everything after "Header"
            after_header = after_header.replace(num, "").strip()
            variant = _re.sub(r'[^a-zA-Z]', '', after_header.split()[0]).lower() if after_header.split() else ""
            if variant:
                return f"h{num}-{variant}"
            return f"h{num}"
        elif "Paragraph" in font_id:
            num_match = _re.search(r'Paragraph\s*(\d+)', font_id)
            num = num_match.group(1) if num_match else size_str
            return f"body-{num}"
        elif "Button" in font_id:
            return "button-text"
        elif "Link" in font_id:
            return "link"
        elif "Label" in font_id:
            return "label"
        elif "Color" in font_id or "Component" in font_id or "Photo" in font_id:
            return f"label-{size_str}"
        else:
            return f"text-{size_str}"
