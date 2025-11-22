#!/bin/bash
# Demo script showing interactive mode usage

echo "=========================================="
echo "Interactive Mode Demo"
echo "=========================================="
echo ""
echo "Running: python intro_renderer.py"
echo ""
echo "This will launch interactive mode where you'll be prompted for:"
echo "  1. Style file path"
echo "  2. Section name (Intro A, Intro B, etc.)"
echo "  3. Chord root (C, D, E, F, G, A, B, with sharps/flats)"
echo "  4. Major or minor quality"
echo "  5. Output file name"
echo ""
echo "All prompts are in both Korean (한글) and English."
echo ""
echo "=========================================="
echo "Command-line Mode Demo"
echo "=========================================="
echo ""
echo "Running: python intro_renderer.py --style demo_style.mid --section 'Intro A' --chord G --quality major --out demo_output.mid"
echo ""

# Ensure demo file exists
if [ ! -f "demo_style.mid" ]; then
    echo "Creating demo style file..."
    python3 create_demo.py
    echo ""
fi

# Run command-line mode demo
python3 intro_renderer.py --style demo_style.mid --section "Intro A" --chord G --quality major --out demo_output.mid

echo ""
echo "=========================================="
echo "Demo complete!"
echo "=========================================="
