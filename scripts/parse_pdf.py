#!/usr/bin/env python3
"""Parse PDF design file and extract layout, text, and design information."""

import json
from pathlib import Path
import fitz  # PyMuPDF

PDF_PATH = Path(__file__).parent.parent / "Styles.pdf"
OUTPUT_DIR = Path(__file__).parent.parent / "generated"


def parse_pdf(pdf_path: Path) -> dict:
    """Parse PDF and extract design information."""
    print(f"📖 Reading PDF from: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    
    pdf_data = {
        "metadata": {
            "page_count": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
        },
        "pages": [],
    }
    
    for page_num, page in enumerate(doc):
        page_data = {
            "page_number": page_num + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "text_blocks": [],
            "images": [],
            "colors": [],
        }
        
        # Extract text blocks
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        
        for block in blocks:
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            page_data["text_blocks"].append({
                                "text": text,
                                "x": span["origin"][0],
                                "y": span["origin"][1],
                                "font": span.get("font", ""),
                                "size": span.get("size", 0),
                                "color": span.get("color", "#000000"),
                            })
            
            elif block.get("type") == 1:  # Image block
                page_data["images"].append({
                    "x": block["bbox"][0],
                    "y": block["bbox"][1],
                    "width": block["bbox"][2] - block["bbox"][0],
                    "height": block["bbox"][3] - block["bbox"][1],
                })
        
        pdf_data["pages"].append(page_data)
        print(f"   Page {page_num + 1}: {len(page_data['text_blocks'])} text blocks, "
              f"{len(page_data['images'])} images")
    
    doc.close()
    return pdf_data


def main():
    """Main function to parse PDF."""
    pdf_data = parse_pdf(PDF_PATH)
    
    # Save to JSON
    output_path = OUTPUT_DIR / "pdf-data.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pdf_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ PDF data saved to: {output_path}")
    
    # Print summary
    print("\n📋 PDF Summary:")
    print(f"   Pages: {pdf_data['metadata']['page_count']}")
    
    total_text = sum(len(page['text_blocks']) for page in pdf_data['pages'])
    total_images = sum(len(page['images']) for page in pdf_data['pages'])
    print(f"   Total text blocks: {total_text}")
    print(f"   Total images: {total_images}")


if __name__ == "__main__":
    main()
