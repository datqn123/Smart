```markdown
# Design System Document: The Guided Sanctuary

## 1. Overview & Creative North Star
**Creative North Star: "The Editorial Archive"**

This design system rejects the frantic, high-density clutter of traditional ERPs. Instead, it treats enterprise data as a curated collection of knowledge. By merging the precision of a Swiss grid with the breathing room of a high-end lifestyle journal, we transform "management" into "stewardship."

The system breaks the "software template" look through **Intentional Asymmetry** and **Tonal Depth**. We prioritize cognitive ease over information density. Key data points are treated like editorial pull-quotes—large, authoritative, and surrounded by whitespace—ensuring that the user never feels overwhelmed, only guided.

---

## 2. Colors & Surface Architecture
The palette is a sophisticated range of muted slates and atmospheric greys designed to recede, allowing the user's work to take center stage.

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1px solid borders to section off content. Traditional "boxes" create visual noise. Boundaries must be defined solely through:
1. **Background Color Shifts:** Use `surface-container-low` for secondary sidebars against a `surface` background.
2. **Nesting Depth:** Stack `surface-container-lowest` cards on top of `surface-container` sections to create a natural, "physical" lift.

### Surface Hierarchy & Layering
Treat the UI as a series of stacked, premium paper stocks.
- **Base Layer (`surface` / `#f8f9fa`):** The canvas.
- **The Content Well (`surface-container-low`):** Used for large grouped areas.
- **The Focused Card (`surface-container-lowest`):** For active work items.
- **The Glass Effect:** For floating navigation or modals, use `surface` at 80% opacity with a `24px` backdrop-blur. This creates a "frosted glass" look that keeps the user grounded in their previous context.

### Signature Textures
Avoid flat, dead fills on Primary CTAs. Use a subtle linear gradient (Top-Left to Bottom-Right) transitioning from `primary` (#4b6076) to `primary_dim` (#3f546a). This adds a "weighted" feel to buttons, making them feel like physical objects rather than digital pixels.

---

## 3. Typography: The Voice of Authority
We use a dual-sans-serif approach to balance character with utility.

- **The Display Voice (`Public Sans`):** Used for `display` and `headline` scales. This is our "Editorial" voice. It is bold, steady, and trustworthy. Use generous letter-spacing (-0.02em) for headlines to maintain a premium feel.
- **The Utility Voice (`Inter`):** Used for `title`, `body`, and `label` scales. Inter provides exceptional legibility at small sizes within complex ERP tables and forms.

**Hierarchy Strategy:** 
Large `display-md` headers should be used to announce page sections, creating a sense of "place." Body text must always utilize a line height of at least `1.6` to ensure the eye can glide across long-form data without fatigue.

---

## 4. Elevation & Depth
In this system, elevation is a feeling, not a drop-shadow.

- **Tonal Layering:** 90% of hierarchy is achieved by placing a "lighter" color on a "darker" background. Place `surface-container-lowest` (#ffffff) cards on `surface-container-low` (#f1f4f6) backgrounds.
- **Ambient Shadows:** Shadows are reserved only for elements that truly "float" (Modals, Dropdowns). Use a multi-layered shadow:
  - *Shadow:* `0px 10px 30px rgba(43, 52, 55, 0.06)` (A tinted shadow using `on_surface`).
- **The Ghost Border:** If a form field requires a border for clarity, use `outline_variant` at **20% opacity**. It should be felt, not seen.

---

## 5. Components

### Buttons (The Anchor)
- **Primary:** Gradient fill (`primary` to `primary_dim`), `on_primary` text, `0.75rem` (md) corner radius.
- **Secondary:** `secondary_container` fill with `on_secondary_container` text. No border.
- **Tertiary:** No fill. `primary` text weight set to 600.

### Input Fields
- **Style:** Use `surface_container_lowest` for the fill. 
- **States:** On focus, do not change the border color to a harsh blue. Instead, shift the background to `surface_bright` and apply a subtle `2px` outer glow of `primary_fixed_dim`.
- **Forbid:** Do not use "Floating Labels" that move on click. Use static `label-md` text above the field for permanent legibility.

### Cards & Lists
- **The Divider Rule:** Forbid 1px horizontal lines between list items. Use `24px` of vertical whitespace (from our spacing scale) to separate rows. 
- **Interaction:** On hover, a card should not "lift" with a shadow. It should subtly shift its background color to `surface_container_high`.

### Guided Navigation (Mini-ERP Specific)
- **The Breadcrumb Trail:** Use `label-md` in `on_surface_variant`. Replace the standard "/" separator with a subtle `outline_variant` dot.
- **The "Notify Owner" Action:** Instead of a vibrating orange or red, use a `tertiary_container` pill with `on_tertiary_container` text. It is a "calm alert"—noticeable but not alarming.

---

## 6. Do’s and Don’ts

### Do
- **Do** use asymmetrical layouts. A wide left column for content and a narrow right column for metadata creates an editorial feel.
- **Do** use "Optical Centering." Sometimes, perfectly mathematical centering looks wrong in a "soft" system; trust your eye.
- **Do** maximize whitespace. If you think there is enough room, add 8px more.

### Don't
- **Don't** use pure black (#000000) for text. Use `on_surface` (#2b3437) to keep the contrast accessible but soft.
- **Don't** use standard Material Design "Ripple" effects. Use soft "Fade-In/Fade-Out" transitions (200ms Ease-In-Out).
- **Don't** use icons as the sole communicator. Always pair icons with `label-sm` text to ensure the "Guided" promise of the system.

---

## 7. Roundedness Scale
To maintain the "Sanctuary" feel, we avoid sharp edges which trigger "fight or flight" responses in the brain.
- **sm (0.25rem):** Internal elements (Checkboxes).
- **DEFAULT (0.5rem):** Standard Buttons and Inputs.
- **lg (1rem):** Cards and main Content Containers.
- **xl (1.5rem):** Hero sections and large Modals.
- **full (9999px):** Chips and Tags.```