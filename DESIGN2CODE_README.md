# design2code

A reusable pipeline for converting Figma design exports (SVG/PDF) into production-ready React components.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌────────────────┐     ┌──────────────┐     ┌──────────────┐
│   Input      │────▶│   Parser     │────▶│      IR        │────▶│  Generator    │────▶│   Output     │
│ SVG / PDF    │     │ Extract &    │     │  Intermediate  │     │  Code         │     │ React/TS     │
│              │     │ Normalize    │     │  Representation│     │               │     │              │
└──────────────┘     └──────────────┘     └────────────────┘     └──────────────┘     └──────────────┘
```

### Key Design Principle: IR (Intermediate Representation)

The **IR** is a framework-agnostic JSON structure that serves as the bridge between design files and code output. This makes the pipeline extensible:

- **Add new input formats** → write a parser that outputs IR (e.g., Figma API, Sketch)
- **Add new output formats** → write a generator that reads IR (e.g., Vue, Svelte, Swift)

```
  New Parser (Figma API) ──┐
  New Parser (Sketch)   ──┼──▶ IR ──┼──▶ React Generator
  New Parser (CSS)      ──┘         ├──▶ Vue Generator
                                    └──▶ Swift Generator
```

## Project Structure

```
design2code/
├── ir/
│   └── model.py          # IR data structures (ColorToken, TypographyToken, DesignElement, etc.)
├── parsers/
│   ├── svg_parser.py     # SVG → IR
│   └── pdf_parser.py     # PDF → IR
├── generators/
│   └── react_gen.py      # IR → React + TypeScript
├── cli.py                # Pipeline orchestrator
└── __init__.py
```

## IR Data Model

The IR captures all design information needed to generate UI code:

| Category | Description |
|----------|-------------|
| **Colors** | Extracted hex values with usage frequency and semantic naming |
| **Typography** | Font family, size, weight, letter-spacing per style |
| **Spacing** | Common spacing values derived from element positions |
| **Components** | Reusable component definitions (Button, Navbar, etc.) |
| **Elements** | Full element tree with position, style, and content |

## Installation

```bash
# Required for PDF parsing
pip install PyMuPDF

# The rest uses Python standard library only
```

## Usage

### CLI

```bash
# Full pipeline: SVG + PDF → React
python -m design2code.cli --svg Styles.svg --pdf Styles.pdf --output ./src

# SVG only → React
python -m design2code.cli --svg design.svg --output ./src

# Parse only, save IR for later use
python -m design2code.cli --svg design.svg --save-ir design-ir.json --dry-run

# Load existing IR → generate code (skip parsing)
python -m design2code.cli --ir design-ir.json --output ./src
```

### Programmatic

```python
from design2code.parsers.svg_parser import SvgParser
from design2code.generators.react_gen import ReactGenerator

# Step 1: Parse → IR
parser = SvgParser("Styles.svg")
ir = parser.parse()

# Step 2: IR → Code
generator = ReactGenerator(ir, output_dir="./src")
files = generator.generate()

for name, path in files.items():
    print(f"Generated: {path}")
```

### IR Reuse (Two-Stage Workflow)

```bash
# Stage 1: Parse once, save IR
python -m design2code.cli --svg design.svg --save-ir design-ir.json

# Stage 2: Use IR to generate (fast, no re-parsing)
python -m design2code.cli --ir design-ir.json --output ./project-a/src
python -m design2code.cli --ir design-ir.json --output ./project-b/src
```

## Generated Output

The React generator produces:

| File | Description |
|------|-------------|
| `theme.ts` | Design tokens (colors, typography, spacing, breakpoints) |
| `Button.tsx` | Button component with variants (primary/secondary/dark/light) |
| `Text.tsx` | Text component with all typography variants |
| `Navbar.tsx` | Responsive navbar with mobile/tablet/desktop breakpoints |
| `ColorPalette.tsx` | Color palette display component |
| `index.ts` | Barrel exports |

## Extending the Pipeline

### Adding a New Parser

```python
from design2code.ir.model import DesignIR, ColorToken, TypographyToken

class MyNewParser:
    def __init__(self, path: str):
        self.path = path
    
    def parse(self) -> DesignIR:
        ir = DesignIR(
            source_file=self.path,
            canvas_width=1440,
            canvas_height=900,
        )
        # Extract your data and populate IR
        ir.colors.append(ColorToken(name="primary", value="#1F41FF"))
        ir.typography.append(TypographyToken(name="h1", font_family="Arial", font_size=48))
        return ir
```

### Adding a New Generator

```python
from design2code.ir.model import DesignIR

class VueGenerator:
    def __init__(self, ir: DesignIR, output_dir: str = "./output"):
        self.ir = ir
        self.output_dir = Path(output_dir)
    
    def generate(self) -> dict:
        # Read self.ir.colors, self.ir.typography, etc.
        # Generate Vue SFC files
        return {"MyComponent.vue": path}
```

## Pipeline Stages Detail

### Stage 1: Parse
- **Input**: SVG file (from Figma export) and/or PDF file
- **Process**: Extract colors, typography, components, layout
- **Output**: `DesignIR` object

### Stage 2: Save IR (optional)
- **Input**: `DesignIR` object
- **Output**: JSON file for reuse/debugging

### Stage 3: Generate
- **Input**: `DesignIR` object
- **Process**: Apply templates and code generation logic
- **Output**: React + TypeScript component files

## Limitations

| Limitation | Workaround |
|-----------|-----------|
| Complex SVG masks/clips are skipped | Manual refinement of generated components |
| Auto-layout detection is basic | Define custom spacing in post-processing |
| Interactive states (hover/focus) are inferred | Add interaction logic manually |
| Image assets are not extracted | Reference images separately in your project |
