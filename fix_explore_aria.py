import re

with open("frontend/src/pages/explore/ExplorePage.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Add aria-label to ChevronLeft buttons
content = re.sub(
    r'(<button\s+onClick=\{\(\) => scrollLeft\([^)]+\)\})',
    r'\1\n                            aria-label="Défiler à gauche"',
    content
)

# Add aria-label to ChevronRight buttons
content = re.sub(
    r'(<button\s+onClick=\{\(\) => scrollRight\([^)]+\)\})',
    r'\1\n                            aria-label="Défiler à droite"',
    content
)

# Clean up duplicates if any
content = re.sub(r'aria-label="[^"]+"\s+aria-label="[^"]+"', r'aria-label="Défiler"', content)

with open("frontend/src/pages/explore/ExplorePage.tsx", "w", encoding="utf-8") as f:
    f.write(content)

print("ExplorePage updated.")
