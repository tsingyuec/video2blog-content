# PyMOL demo script (.pml)
# Usage: uv run pymol demo.pml

fetch 1ao7
hide everything
show cartoon
color cyan
bg_color white
orient

# Uncomment the next two lines to export a picture (ray is slower):
# ray 1200, 900
# png pymol_demo.png
