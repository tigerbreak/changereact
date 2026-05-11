#!/usr/bin/env python3
"""
design2code CLI - Pipeline orchestrator for converting design files to code.

This tool implements a reusable pipeline:
    Input (SVG/PDF) → Parser → IR (Intermediate Representation) → Generator → Code

Usage:
    python -m design2code.cli --svg Styles.svg --pdf Styles.pdf --output ./src
    python -m design2code.cli --svg design.svg --format react --output ./components
    python -m design2code.cli --ir design-ir.json --format react --output ./src
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add parent to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from design2code.ir.model import DesignIR
from design2code.parsers.svg_parser import SvgParser
from design2code.parsers.pdf_parser import PdfParser
from design2code.generators.react_gen import ReactGenerator


def parse_args():
    parser = argparse.ArgumentParser(
        prog="design2code",
        description="Convert Figma design exports (SVG/PDF) to React components",
    )
    
    # Input options
    input_group = parser.add_argument_group("Input")
    input_group.add_argument("--svg", type=str, help="Path to SVG design file")
    input_group.add_argument("--pdf", type=str, help="Path to PDF design file")
    input_group.add_argument("--ir", type=str, help="Path to existing IR JSON file (skip parsing)")
    
    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--output", "-o", type=str, default="./generated",
                              help="Output directory for generated code (default: ./generated)")
    output_group.add_argument("--format", "-f", type=str, default="react",
                              choices=["react"],
                              help="Output format (default: react)")
    
    # Pipeline options
    pipeline_group = parser.add_argument_group("Pipeline")
    pipeline_group.add_argument("--save-ir", type=str, help="Save IR to JSON file for debugging/reuse")
    pipeline_group.add_argument("--load-ir", type=str, help="Load IR from JSON file instead of parsing")
    pipeline_group.add_argument("--dry-run", action="store_true", help="Parse and show IR summary without generating code")
    
    return parser.parse_args()


def run_pipeline(
    svg_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
    ir_path: Optional[str] = None,
    output_dir: str = "./generated",
    save_ir: Optional[str] = None,
    dry_run: bool = False,
) -> DesignIR:
    """
    Run the full design-to-code pipeline.
    
    This is the main entry point for programmatic usage.
    
    Args:
        svg_path: Path to SVG file to parse
        pdf_path: Path to PDF file to parse
        ir_path: Path to existing IR JSON (skips parsing)
        output_dir: Directory for generated code
        save_ir: Path to save the IR JSON
        dry_run: If True, only parse and show summary
    
    Returns:
        The DesignIR object
    """
    print("=" * 60)
    print("  design2code - Figma Design → React Components")
    print("=" * 60)
    
    # --- Step 1: Parse input → IR ---
    print("\n📥 Step 1: Parsing design files...")
    
    if ir_path:
        print(f"   Loading existing IR from: {ir_path}")
        with open(ir_path, 'r') as f:
            ir = DesignIR.from_json(f.read())
    else:
        ir = None
        
        # Parse SVG (primary source)
        if svg_path:
            print(f"   Parsing SVG: {svg_path}")
            svg_parser = SvgParser(svg_path)
            ir = svg_parser.parse()
            print(f"   ✅ SVG parsed successfully")
        
        # Parse PDF (supplementary)
        if pdf_path:
            print(f"   Parsing PDF: {pdf_path}")
            pdf_parser = PdfParser(pdf_path)
            pdf_ir = pdf_parser.parse()
            
            # Merge PDF data into IR
            if ir:
                ir.root_elements.extend(pdf_ir.root_elements)
            else:
                ir = pdf_ir
            print(f"   ✅ PDF parsed successfully")
        
        if not ir:
            print("   ❌ Error: No input files provided (--svg or --pdf)")
            sys.exit(1)
    
    # --- Step 2: Save IR (optional) ---
    if save_ir:
        print(f"\n💾 Step 2: Saving IR to: {save_ir}")
        with open(save_ir, 'w', encoding='utf-8') as f:
            f.write(ir.to_json())
        print(f"   ✅ IR saved")
    
    # --- Step 3: Show IR summary ---
    print("\n📊 Step 3: IR Summary")
    print(f"   Source: {ir.source_file}")
    print(f"   Canvas: {ir.canvas_width} × {ir.canvas_height}")
    print(f"   Colors: {len(ir.colors)}")
    print(f"   Typography styles: {len(ir.typography)}")
    print(f"   Spacing tokens: {len(ir.spacing)}")
    print(f"   Components: {len(ir.components)}")
    print(f"   Elements: {len(ir.root_elements)}")
    
    if ir.colors:
        print("\n   🎨 Top Colors:")
        for c in ir.colors[:5]:
            print(f"      {c.name}: {c.value} (used {c.usage_count}×)")
    
    if ir.typography:
        print("\n   📝 Typography:")
        for t in ir.typography[:5]:
            weight = f" w={t.font_weight}" if t.font_weight else ""
            print(f"      {t.name}: {t.font_family} {t.font_size}px{weight}")
    
    # --- Step 4: Generate code ---
    if dry_run:
        print("\n🔍 Dry run - skipping code generation")
        return ir
    
    print(f"\n⚙️  Step 4: Generating React components...")
    generator = ReactGenerator(ir, output_dir=output_dir)
    generated = generator.generate()
    
    print(f"\n✅ Generated {len(generated)} files:")
    for name, path in generated.items():
        size = path.stat().st_size
        print(f"   📄 {name} ({size:,} bytes)")
    
    print(f"\n📂 Output directory: {Path(output_dir).absolute()}")
    print("\n" + "=" * 60)
    
    return ir


def main():
    args = parse_args()
    
    run_pipeline(
        svg_path=args.svg,
        pdf_path=args.pdf,
        ir_path=args.ir or args.load_ir,
        output_dir=args.output,
        save_ir=args.save_ir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
