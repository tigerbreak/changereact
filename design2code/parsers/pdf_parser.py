"""
PDF Parser module.

Parses PDF files exported from Figma and extracts layout, text, and 
design information to contribute to the Intermediate Representation (IR).

Usage:
    from design2code.parsers.pdf_parser import PdfParser
    
    parser = PdfParser("path/to/design.pdf")
    ir = parser.parse()
"""

import json
from pathlib import Path
from ..ir.model import (
    DesignIR,
    DesignElement,
    ElementType,
    BoxStyle,
    TextStyle,
)


class PdfParser:
    """Parses PDF design files and extracts layout information."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)

    def parse(self) -> DesignIR:
        """Main entry point: parse PDF and return DesignIR."""
        import fitz  # PyMuPDF

        doc = fitz.open(self.pdf_path)

        ir = DesignIR(
            source_file=str(self.pdf_path),
            canvas_width=0,
            canvas_height=0,
        )

        for page in doc:
            if ir.canvas_width == 0:
                ir.canvas_width = page.rect.width
                ir.canvas_height = page.rect.height

            # Extract text blocks
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

            for block in blocks:
                if block.get("type") != 0:  # Skip non-text blocks
                    continue

                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue

                        element = DesignElement(
                            id=f"pdf-{span.get('font', 'unknown')}-{span.get('size', 0)}",
                            name=f"text-{text[:20].replace(' ', '-').lower()}",
                            element_type=ElementType.TEXT,
                            box=BoxStyle(
                                position="absolute",
                                top=f"{span['origin'][1]}px",
                                left=f"{span['origin'][0]}px",
                            ),
                            text_style=TextStyle(
                                font_family=span.get("font", "unknown"),
                                font_size=f"{span.get('size', 16)}px",
                                color=f"#{span.get('color', 0):06x}",
                            ),
                            text_content=text,
                        )
                        ir.root_elements.append(element)

        doc.close()
        return ir
