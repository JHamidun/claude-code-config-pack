---
name: theme-factory
description: "Стилизация артефакта темой: 10 пресетов цвета/шрифтов или новая тема на лету, дек в том числе. Триггеры: «смени тему», «стилизация». НЕ CSS для deck-stage → deck-themes."
license: Complete terms in LICENSE.txt
---


# Theme Factory Skill

This skill provides a curated collection of professional font and color themes themes, each with carefully selected color palettes and font pairings. Once a theme is chosen, it can be applied to any artifact.

## Purpose

To apply consistent, professional styling to presentation slide decks, use this skill. Each theme includes:
- A cohesive color palette with hex codes
- Complementary font pairings for headers and body text
- A distinct visual identity suitable for different contexts and audiences

## Usage Instructions

To apply styling to a slide deck or other artifact:

1. **Show the theme showcase**: Display the `theme-showcase.pdf` file to allow users to see all available themes visually. Do not make any modifications to it; simply show the file for viewing.
2. **Ask for their choice**: Ask which theme to apply to the deck
3. **Wait for selection**: Get explicit confirmation about the chosen theme
4. **Apply the theme**: Once a theme has been chosen, apply the selected theme's colors and fonts to the deck/artifact

## Themes Available

The following 10 themes are available, each showcased in `theme-showcase.pdf`:

1. **Ocean Depths** - Professional and calming maritime theme
2. **Sunset Boulevard** - Warm and vibrant sunset colors
3. **Forest Canopy** - Natural and grounded earth tones
4. **Modern Minimalist** - Clean and contemporary grayscale
5. **Golden Hour** - Rich and warm autumnal palette
6. **Arctic Frost** - Cool and crisp winter-inspired theme
7. **Desert Rose** - Soft and sophisticated dusty tones
8. **Tech Innovation** - Bold and modern tech aesthetic
9. **Botanical Garden** - Fresh and organic garden colors
10. **Midnight Galaxy** - Dramatic and cosmic deep tones

## Theme Details

Each theme is defined in the `themes/` directory with complete specifications including:
- Cohesive color palette with hex codes
- Complementary font pairings for headers and body text
- Distinct visual identity suitable for different contexts and audiences

## Application Process

After a preferred theme is selected:
1. Read the corresponding theme file from the `themes/` directory
2. Apply the specified colors and fonts consistently throughout the deck
3. Ensure proper contrast and readability
4. Maintain the theme's visual identity across all slides

## Fonts: the presets name Linux families — substitute before applying (local note, not upstream)

All 10 themes in `themes/` name only **DejaVu Sans / DejaVu Serif / FreeSans / FreeSerif**.
These are GNU/Linux system families: they are **not installed on this machine** (checked against
`C:/Windows/Fonts`), and in a claude.ai artifact the CSP admits web fonts only from Google Fonts.
Applied literally, a theme therefore delivers its palette and silently loses its typography —
everything falls back to the default sans, which looks like "the theme did not apply".

So when applying a theme:

1. Take the **palette** from the theme file as written — it is the part that works everywhere.
2. Replace the **font pair** with something that will actually load in the target medium
   (Google Fonts for artifacts and web pages; installed Windows families for local HTML/PDF).
   Keep the character of the original: DejaVu Sans / FreeSans → a neutral grotesque,
   DejaVu Serif / FreeSerif → a book serif.
3. Russian text: verify the substitute carries Cyrillic before shipping — see `fonts-bundle`.
4. Note that in 7 of 10 presets both roles name one family in two weights, so there is no real
   pairing to preserve — pick a header/body pair yourself.

## Create your Own Theme
To handle cases where none of the existing themes work for an artifact, create a custom theme. Based on provided inputs, generate a new theme similar to the ones above. Give the theme a similar name describing what the font/color combinations represent. Use any basic description provided to choose appropriate colors/fonts. After generating the theme, show it for review and verification. Following that, apply the theme as described above.
