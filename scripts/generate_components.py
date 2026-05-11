#!/usr/bin/env python3
"""Generate React components from parsed design tokens."""

import json
from pathlib import Path

INPUT_DIR = Path(__file__).parent.parent / "generated"
OUTPUT_DIR = Path(__file__).parent.parent / "generated" / "components"


def generate_theme_file(colors: list, text_styles: list) -> str:
    """Generate theme.ts with design tokens."""
    
    # Create color variables
    color_exports = []
    for color in colors:
        var_name = color['name'].replace('-', '_').upper()
        color_exports.append(f"export const {var_name} = '{color['value']}';")
    
    # Create typography styles
    typography_styles = {}
    for style in text_styles:
        style_key = style['full_name'].split()[0].lower() + '_' + str(style['fontSize']).replace('.', '_')
        typography_styles[style_key] = {
            'fontFamily': f"'{style['fontFamily'].replace('-', ' ').title()}', sans-serif",
            'fontSize': f"{style['fontSize']}px",
            'fontWeight': style['fontWeight'] if style['fontWeight'] else 'normal',
            'letterSpacing': style.get('letterSpacing', 'normal'),
            'color': f"colors.{style['color'].upper().replace('BLACK', 'COLOR_000000').replace('WHITE', 'COLOR_FFFFFF')}" if style['color'] not in ['black', 'white'] else style['color'],
        }
    
    theme_code = f"""// Auto-generated from Figma design tokens
// Do not edit manually

export const colors = {{
    {',\n    '.join([f"{color['name'].upper().replace('-', '_')}: '{color['value']}'" for color in colors])}
}} as const;

export type ColorKeys = keyof typeof colors;

export const typography = {{
    {',\n    '.join([f"{key}: {{\\n        fontFamily: '{val['fontFamily']}',\\n        fontSize: '{val['fontSize']}',\\n        fontWeight: '{val['fontWeight']}',\\n        letterSpacing: '{val['letterSpacing']}',\\n    }}" for key, val in list(typography_styles.items())[:10]])}
}} as const;

export const spacing = {{
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
}} as const;

export const breakpoints = {{
    mobile: '320px',
    tablet: '768px',
    desktop: '1533px',
}} as const;

export const theme = {{
    colors,
    typography,
    spacing,
    breakpoints,
}} as const;

export type Theme = typeof theme;
"""
    return theme_code


def generate_button_component(colors: list) -> str:
    """Generate Button component based on design tokens."""
    
    button_code = """import React from 'react';
import { colors, typography } from '../theme';

export interface ButtonProps {
    variant?: 'primary' | 'secondary' | 'dark' | 'light';
    size?: 'sm' | 'md' | 'lg';
    children: React.ReactNode;
    onClick?: () => void;
    className?: string;
    disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
    variant = 'primary',
    size = 'md',
    children,
    onClick,
    className = '',
    disabled = false,
}) => {
    const baseStyles: React.CSSProperties = {
        fontFamily: "'Encode Sans Expanded', sans-serif",
        fontSize: size === 'sm' ? '11px' : size === 'lg' ? '15px' : '13px',
        letterSpacing: '-0.06em',
        padding: size === 'sm' ? '8px 16px' : size === 'lg' ? '16px 32px' : '12px 24px',
        border: 'none',
        borderRadius: '4px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'all 0.2s ease-in-out',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
    };

    const variantStyles: Record<string, React.CSSProperties> = {
        primary: {
            backgroundColor: colors.COLOR_1F41FF,
            color: colors.COLOR_FFFFFF,
        },
        secondary: {
            backgroundColor: colors.COLOR_9747FF,
            color: colors.COLOR_FFFFFF,
        },
        dark: {
            backgroundColor: colors.COLOR_575757,
            color: colors.COLOR_FFFFFF,
        },
        light: {
            backgroundColor: colors.COLOR_FFFFFF,
            color: colors.COLOR_575757,
            border: `1px solid ${colors.COLOR_575757}`,
        },
    };

    const hoverStyles: Record<string, React.CSSProperties> = {
        primary: {
            backgroundColor: '#1a38e6',
        },
        secondary: {
            backgroundColor: '#8a3ee6',
        },
        dark: {
            backgroundColor: '#4a4a4a',
        },
        light: {
            backgroundColor: colors.COLOR_575757,
            color: colors.COLOR_FFFFFF,
        },
    };

    return (
        <button
            className={`button button-${variant} button-${size} ${className}`}
            style={{
                ...baseStyles,
                ...variantStyles[variant],
            }}
            onClick={onClick}
            disabled={disabled}
            onMouseEnter={(e) => {
                const target = e.currentTarget;
                const hover = hoverStyles[variant];
                Object.assign(target.style, hover);
            }}
            onMouseLeave={(e) => {
                const target = e.currentTarget;
                Object.assign(target.style, variantStyles[variant]);
            }}
        >
            {children}
        </button>
    );
};

export default Button;
"""
    return button_code


def generate_text_component(text_styles: list) -> str:
    """Generate Text component with typography styles."""
    
    # Extract unique style categories
    style_categories = {}
    for style in text_styles:
        if 'Header' in style['full_name']:
            category = 'header'
        elif 'Paragraph' in style['full_name']:
            category = 'paragraph'
        elif 'Link' in style['full_name']:
            category = 'link'
        elif 'Button' in style['full_name']:
            category = 'button_text'
        else:
            category = 'default'
        
        if category not in style_categories:
            style_categories[category] = style
    
    text_code = """import React from 'react';
import { colors, typography } from '../theme';

export type TextVariant = 
    | 'header1' 
    | 'header2' 
    | 'header3' 
    | 'header4' 
    | 'header5'
    | 'paragraph1'
    | 'paragraph2'
    | 'paragraph3'
    | 'link'
    | 'promotion'
    | 'body';

export interface TextProps {
    variant?: TextVariant;
    children: React.ReactNode;
    className?: string;
    color?: string;
    as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'p' | 'span' | 'a';
}

const variantMap: Record<TextVariant, React.CSSProperties> = {
    header1: {
        fontFamily: "'Encode Sans Condensed', sans-serif",
        fontSize: '126px',
        fontWeight: 600,
        letterSpacing: '-0.02em',
        lineHeight: 1.1,
        color: colors.COLOR_000000,
    },
    header2: {
        fontFamily: "'Encode Sans Expanded', sans-serif",
        fontSize: '40px',
        letterSpacing: '-0.06em',
        lineHeight: 1.2,
        color: colors.COLOR_000000,
    },
    header3: {
        fontFamily: "'Encode Sans Semi Condensed', sans-serif",
        fontSize: '37px',
        fontWeight: 600,
        letterSpacing: '-0.02em',
        lineHeight: 1.2,
        color: colors.COLOR_000000,
    },
    header4: {
        fontFamily: "'DM Sans', sans-serif",
        fontSize: '24px',
        fontWeight: 'bold',
        letterSpacing: '-0.02em',
        lineHeight: 1.3,
        color: colors.COLOR_000000,
    },
    header5: {
        fontFamily: "'Encode Sans Semi Condensed', sans-serif",
        fontSize: '20px',
        fontWeight: 600,
        letterSpacing: '-0.02em',
        lineHeight: 1.3,
        color: colors.COLOR_000000,
    },
    paragraph1: {
        fontFamily: "'Encode Sans Semi Condensed', sans-serif",
        fontSize: '32px',
        fontWeight: 600,
        letterSpacing: '-0.02em',
        lineHeight: 1.4,
        color: colors.COLOR_000000,
    },
    paragraph2: {
        fontFamily: "'Encode Sans Semi Condensed', sans-serif",
        fontSize: '30px',
        letterSpacing: '-0.02em',
        lineHeight: 1.4,
        color: colors.COLOR_000000,
    },
    paragraph3: {
        fontFamily: "'Encode Sans Semi Condensed', sans-serif",
        fontSize: '17px',
        letterSpacing: '-0.02em',
        lineHeight: 1.5,
        color: colors.COLOR_000000,
    },
    link: {
        fontFamily: "'Encode Sans Semi Condensed', sans-serif",
        fontSize: '18px',
        letterSpacing: '-0.02em',
        color: colors.COLOR_1F41FF,
        textDecoration: 'none',
        cursor: 'pointer',
    },
    promotion: {
        fontFamily: "'Encode Sans Semi Condensed', sans-serif",
        fontSize: '15px',
        fontWeight: 600,
        letterSpacing: '-0.02em',
        lineHeight: 1.4,
        color: colors.COLOR_000000,
    },
    body: {
        fontFamily: "'Encode Sans Expanded', sans-serif",
        fontSize: '16px',
        letterSpacing: '-0.02em',
        lineHeight: 1.5,
        color: colors.COLOR_575757,
    },
};

const defaultElements: Record<TextVariant, 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'p' | 'span' | 'a'> = {
    header1: 'h1',
    header2: 'h2',
    header3: 'h3',
    header4: 'h4',
    header5: 'h5',
    paragraph1: 'p',
    paragraph2: 'p',
    paragraph3: 'p',
    link: 'a',
    promotion: 'p',
    body: 'p',
};

export const Text: React.FC<TextProps> = ({
    variant = 'body',
    children,
    className = '',
    color,
    as,
}) => {
    const Component = as || defaultElements[variant];
    
    const style: React.CSSProperties = {
        ...variantMap[variant],
        margin: 0,
        ...(color && { color }),
    };

    return (
        <Component
            className={`text text-${variant} ${className}`}
            style={style}
        >
            {children}
        </Component>
    );
};

export default Text;
"""
    return text_code


def generate_navbar_component() -> str:
    """Generate Navbar component based on design tokens."""
    
    navbar_code = """import React, { useState } from 'react';
import { colors } from '../theme';

export interface NavItem {
    label: string;
    href: string;
    variant?: 'default' | 'active';
}

export interface NavbarProps {
    items?: NavItem[];
    logo?: React.ReactNode;
    className?: string;
    breakpoint?: 'desktop' | 'tablet' | 'mobile';
}

const defaultNavItems: NavItem[] = [
    { label: 'Classes', href: '#classes' },
    { label: 'About us', href: '#about' },
    { label: 'Book with us', href: '#book' },
];

export const Navbar: React.FC<NavbarProps> = ({
    items = defaultNavItems,
    logo,
    className = '',
    breakpoint = 'desktop',
}) => {
    const [isOpen, setIsOpen] = useState(false);

    const containerStyles: React.CSSProperties = {
        width: '100%',
        backgroundColor: colors.COLOR_FFFFFF,
        padding: breakpoint === 'mobile' ? '16px' : '24px 40px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: `1px solid ${colors.COLOR_E9E9E9}`,
        position: 'relative',
    };

    const linkStyles: React.CSSProperties = {
        fontFamily: "'Encode Sans Semi Condensed', sans-serif",
        fontSize: '18px',
        letterSpacing: '-0.02em',
        color: colors.COLOR_575757,
        textDecoration: 'none',
        padding: '8px 16px',
        transition: 'color 0.2s ease',
    };

    return (
        <nav className={`navbar navbar-${breakpoint} ${className}`} style={containerStyles}>
            <div className="navbar-logo">
                {logo || (
                    <span style={{
                        fontFamily: "'Encode Sans Semi Condensed', sans-serif",
                        fontSize: breakpoint === 'mobile' ? '24px' : '30px',
                        fontWeight: 600,
                        color: colors.COLOR_000000,
                    }}>
                        Movement Studios.
                    </span>
                )}
            </div>

            {breakpoint === 'mobile' ? (
                <>
                    <button
                        onClick={() => setIsOpen(!isOpen)}
                        style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '8px',
                        }}
                        aria-label="Toggle menu"
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M3 12h18M3 6h18M3 18h18" stroke={colors.COLOR_575757} strokeWidth="2" strokeLinecap="round"/>
                        </svg>
                    </button>
                    
                    {isOpen && (
                        <div className="mobile-menu" style={{
                            position: 'absolute',
                            top: '100%',
                            left: 0,
                            right: 0,
                            backgroundColor: colors.COLOR_FFFFFF,
                            padding: '16px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px',
                            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                        }}>
                            {items.map((item) => (
                                <a
                                    key={item.label}
                                    href={item.href}
                                    style={linkStyles}
                                    onMouseEnter={(e) => e.currentTarget.style.color = colors.COLOR_1F41FF}
                                    onMouseLeave={(e) => e.currentTarget.style.color = colors.COLOR_575757}
                                >
                                    {item.label}
                                </a>
                            ))}
                        </div>
                    )}
                </>
            ) : (
                <div className="nav-items" style={{
                    display: 'flex',
                    gap: breakpoint === 'tablet' ? '16px' : '24px',
                    alignItems: 'center',
                }}>
                    {items.map((item) => (
                        <a
                            key={item.label}
                            href={item.href}
                            style={{
                                ...linkStyles,
                                ...(item.variant === 'active' && { color: colors.COLOR_1F41FF }),
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.color = colors.COLOR_1F41FF}
                            onMouseLeave={(e) => e.currentTarget.style.color = item.variant === 'active' ? colors.COLOR_1F41FF : colors.COLOR_575757}
                        >
                            {item.label}
                        </a>
                    ))}
                </div>
            )}
        </nav>
    );
};

export default Navbar;
"""
    return navbar_code


def generate_color_palette_component(colors: list) -> str:
    """Generate ColorPalette component."""
    
    color_items = ",\n".join([
        f'        {{ name: "{c["name"]}", value: "{c["value"]}" }}'
        for c in colors
    ])
    
    palette_code = f"""import React from 'react';
import {{ colors }} from '../theme';

export interface ColorPaletteProps {{
    className?: string;
    showNames?: boolean;
}}

const colorList = [
{color_items}
];

export const ColorPalette: React.FC<ColorPaletteProps> = ({{
    className = '',
    showNames = true,
}}) => {{
    return (
        <div className={`color-palette ${{className}}`}} style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '16px',
            padding: '24px',
        }}>
            {{colorList.map((color) => (
                <div key={{color.name}} style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '8px',
                }}>
                    <div style={{
                        width: '64px',
                        height: '64px',
                        backgroundColor: color.value,
                        borderRadius: '8px',
                        border: '1px solid #E9E9E9',
                    }} />
                    {{showNames && (
                        <div style={{
                            fontFamily: "'Roboto Flex', sans-serif",
                            fontSize: '12px',
                            color: colors.COLOR_575757,
                            textAlign: 'center',
                        }}>
                            <div>{{color.name}}</div>
                            <div>{{color.value}}</div>
                        </div>
                    )}}
                </div>
            ))}}
        </div>
    );
}};

export default ColorPalette;
"""
    return palette_code


def generate_index_file(components: list) -> str:
    """Generate index.ts for component exports."""
    
    exports = "\n".join([
        f"export {{ {comp['name']} }} from './{comp['file']}';"
        for comp in components
    ])
    
    return f"""// Auto-generated component exports
// Do not edit manually

{exports}
"""


def main():
    """Main function to generate React components."""
    print("🎨 Generating React components from design tokens...")
    
    # Load design tokens
    tokens_path = INPUT_DIR / "design-tokens.json"
    with open(tokens_path, 'r') as f:
        tokens = json.load(f)
    
    colors = tokens['colors']
    text_styles = tokens['textStyles']
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Generate components
    generated_components = []
    
    # 1. Theme file
    print("\n📦 Generating theme.ts...")
    theme_code = generate_theme_file(colors, text_styles)
    theme_path = OUTPUT_DIR.parent / "theme.ts"
    with open(theme_path, 'w') as f:
        f.write(theme_code)
    print(f"   ✅ Saved to {theme_path}")
    
    # 2. Button component
    print("\n🔘 Generating Button.tsx...")
    button_code = generate_button_component(colors)
    button_path = OUTPUT_DIR / "Button.tsx"
    with open(button_path, 'w') as f:
        f.write(button_code)
    generated_components.append({'name': 'Button', 'file': 'Button'})
    print(f"   ✅ saved to {button_path}")
    
    # 3. Text component
    print("\n📝 Generating Text.tsx...")
    text_code = generate_text_component(text_styles)
    text_path = OUTPUT_DIR / "Text.tsx"
    with open(text_path, 'w') as f:
        f.write(text_code)
    generated_components.append({'name': 'Text', 'file': 'Text'})
    print(f"   ✅ saved to {text_path}")
    
    # 4. Navbar component
    print("\n🧭 Generating Navbar.tsx...")
    navbar_code = generate_navbar_component()
    navbar_path = OUTPUT_DIR / "Navbar.tsx"
    with open(navbar_path, 'w') as f:
        f.write(navbar_code)
    generated_components.append({'name': 'Navbar', 'file': 'Navbar'})
    print(f"   ✅ saved to {navbar_path}")
    
    # 5. Color Palette component
    print("\n🎨 Generating ColorPalette.tsx...")
    palette_code = generate_color_palette_component(colors)
    palette_path = OUTPUT_DIR / "ColorPalette.tsx"
    with open(palette_path, 'w') as f:
        f.write(palette_code)
    generated_components.append({'name': 'ColorPalette', 'file': 'ColorPalette'})
    print(f"   ✅ saved to {palette_path}")
    
    # 6. Index file
    print("\n📋 Generating index.ts...")
    index_code = generate_index_file(generated_components)
    index_path = OUTPUT_DIR / "index.ts"
    with open(index_path, 'w') as f:
        f.write(index_code)
    print(f"   ✅ saved to {index_path}")
    
    print("\n✅ All components generated successfully!")
    print(f"\n📁 Generated components:")
    for comp in generated_components:
        print(f"   - {comp['name']} ({comp['file']}.tsx)")
    
    print(f"\n📂 Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
