"""
Intermediate Representation (IR) for design-to-code pipeline.

This module defines the data structures that serve as the bridge between
design file parsers (SVG, PDF, Figma API) and code generators (React, Vue, etc.).

The IR is framework-agnostic and captures all design information needed
to generate production-ready UI components.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ElementType(str, Enum):
    """Types of UI elements in the design."""
    CONTAINER = "container"
    TEXT = "text"
    BUTTON = "button"
    IMAGE = "image"
    ICON = "icon"
    INPUT = "input"
    LINK = "link"
    NAV = "nav"
    CARD = "card"
    DIVIDER = "divider"
    UNKNOWN = "unknown"


class ComponentVariant(str, Enum):
    """Variants for components like buttons."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    OUTLINE = "outline"
    GHOST = "ghost"
    DANGER = "danger"
    SUCCESS = "success"


@dataclass
class ColorToken:
    """Represents a color in the design system."""
    name: str
    value: str  # hex value like "#1F41FF"
    usage_count: int = 0
    semantic_name: Optional[str] = None  # e.g., "primary", "background", "text"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "usage_count": self.usage_count,
            "semantic_name": self.semantic_name,
        }


@dataclass
class TypographyToken:
    """Represents a typography style in the design system."""
    name: str
    font_family: str
    font_size: float  # in pixels
    font_weight: Optional[str] = None
    line_height: Optional[float] = None
    letter_spacing: Optional[str] = None
    text_transform: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "line_height": self.line_height,
            "letter_spacing": self.letter_spacing,
            "text_transform": self.text_transform,
        }


@dataclass
class SpacingToken:
    """Represents a spacing value in the design system."""
    name: str
    value: float  # in pixels


@dataclass
class BoxStyle:
    """CSS box model properties."""
    width: Optional[str] = None
    height: Optional[str] = None
    padding: Optional[str] = None
    margin: Optional[str] = None
    border_radius: Optional[str] = None
    border: Optional[str] = None
    background_color: Optional[str] = None
    box_shadow: Optional[str] = None
    display: Optional[str] = None
    flex_direction: Optional[str] = None
    justify_content: Optional[str] = None
    align_items: Optional[str] = None
    gap: Optional[str] = None
    position: Optional[str] = None
    top: Optional[str] = None
    left: Optional[str] = None
    overflow: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items() if v is not None
        }


@dataclass
class TextStyle:
    """Text-specific styling."""
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_weight: Optional[str] = None
    line_height: Optional[str] = None
    letter_spacing: Optional[str] = None
    color: Optional[str] = None
    text_align: Optional[str] = None
    text_decoration: Optional[str] = None
    text_transform: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items() if v is not None
        }


@dataclass
class DesignElement:
    """
    A single element in the design.
    This is the core building block of the IR.
    """
    id: str
    name: str
    element_type: ElementType
    box: BoxStyle = field(default_factory=BoxStyle)
    text_style: Optional[TextStyle] = None
    text_content: Optional[str] = None
    children: list["DesignElement"] = field(default_factory=list)
    props: dict = field(default_factory=dict)
    variants: list[str] = field(default_factory=list)
    source_line: Optional[int] = None  # For debugging/tracing back to source

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "name": self.name,
            "element_type": self.element_type.value,
            "box": self.box.to_dict(),
        }
        if self.text_style:
            result["text_style"] = self.text_style.to_dict()
        if self.text_content:
            result["text_content"] = self.text_content
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        if self.props:
            result["props"] = self.props
        if self.variants:
            result["variants"] = self.variants
        if self.source_line:
            result["source_line"] = self.source_line
        return result


@dataclass
class ComponentDefinition:
    """
    A reusable component definition extracted from the design.
    Examples: Button, Navbar, Card, etc.
    """
    name: str
    element_type: ElementType
    props_schema: dict = field(default_factory=dict)  # {prop_name: prop_type}
    variants: list[dict] = field(default_factory=list)
    base_element: Optional[DesignElement] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "name": self.name,
            "element_type": self.element_type.value,
            "props_schema": self.props_schema,
            "variants": self.variants,
        }
        if self.base_element:
            result["base_element"] = self.base_element.to_dict()
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class DesignIR:
    """
    The complete Intermediate Representation.
    
    This is the output of parsers and input of generators.
    It contains everything needed to generate UI code.
    """
    # Metadata
    source_file: str
    canvas_width: float
    canvas_height: float
    
    # Design tokens
    colors: list[ColorToken] = field(default_factory=list)
    typography: list[TypographyToken] = field(default_factory=list)
    spacing: list[SpacingToken] = field(default_factory=list)
    
    # Structure
    components: list[ComponentDefinition] = field(default_factory=list)
    root_elements: list[DesignElement] = field(default_factory=list)
    
    # Responsive breakpoints (if detected)
    breakpoints: dict = field(default_factory=lambda: {
        "mobile": 320,
        "tablet": 768,
        "desktop": 1024,
    })

    def to_dict(self) -> dict:
        return {
            "metadata": {
                "source_file": self.source_file,
                "canvas_width": self.canvas_width,
                "canvas_height": self.canvas_height,
                "breakpoints": self.breakpoints,
            },
            "tokens": {
                "colors": [c.to_dict() for c in self.colors],
                "typography": [t.to_dict() for t in self.typography],
                "spacing": [{"name": s.name, "value": s.value} for s in self.spacing],
            },
            "components": [c.to_dict() for c in self.components],
            "root_elements": [e.to_dict() for e in self.root_elements],
        }

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "DesignIR":
        """Reconstruct DesignIR from a dictionary."""
        ir = cls(
            source_file=data["metadata"]["source_file"],
            canvas_width=data["metadata"]["canvas_width"],
            canvas_height=data["metadata"]["canvas_height"],
            breakpoints=data["metadata"].get("breakpoints", {}),
        )
        
        # Reconstruct colors
        for c in data.get("tokens", {}).get("colors", []):
            ir.colors.append(ColorToken(
                name=c["name"],
                value=c["value"],
                usage_count=c.get("usage_count", 0),
                semantic_name=c.get("semantic_name"),
            ))
        
        # Reconstruct typography
        for t in data.get("tokens", {}).get("typography", []):
            ir.typography.append(TypographyToken(
                name=t["name"],
                font_family=t["font_family"],
                font_size=t["font_size"],
                font_weight=t.get("font_weight"),
                line_height=t.get("line_height"),
                letter_spacing=t.get("letter_spacing"),
                text_transform=t.get("text_transform"),
            ))
        
        # Reconstruct spacing
        for s in data.get("tokens", {}).get("spacing", []):
            ir.spacing.append(SpacingToken(
                name=s["name"],
                value=s["value"],
            ))
        
        # Reconstruct components
        for c in data.get("components", []):
            ir.components.append(ComponentDefinition(
                name=c["name"],
                element_type=ElementType(c["element_type"]),
                props_schema=c.get("props_schema", {}),
                variants=c.get("variants", []),
                description=c.get("description"),
            ))
        
        # Reconstruct root elements
        for e_data in data.get("root_elements", []):
            box_data = e_data.get("box", {})
            box = BoxStyle(**{k: v for k, v in box_data.items() if v is not None})
            
            text_style_data = e_data.get("text_style")
            text_style = TextStyle(**{k: v for k, v in text_style_data.items() if v is not None}) if text_style_data else None
            
            element = DesignElement(
                id=e_data["id"],
                name=e_data["name"],
                element_type=ElementType(e_data["element_type"]),
                box=box,
                text_style=text_style,
                text_content=e_data.get("text_content"),
                props=e_data.get("props", {}),
                variants=e_data.get("variants", []),
            )
            ir.root_elements.append(element)
        
        return ir

    @classmethod
    def from_json(cls, json_str: str) -> "DesignIR":
        """Load DesignIR from JSON string."""
        import json
        return cls.from_dict(json.loads(json_str))
