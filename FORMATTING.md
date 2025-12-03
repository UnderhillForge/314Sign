# 314Sign Formatting Guide

Quick reference for formatting your menu specials with Markdown and color tags.

---

## Basic Text Formatting

### Headings
```
## Large Heading
### Medium Heading
```

Use headings to organize sections like "Today's Specials" or "Appetizers"

---

### Bold & Italic
```
**Bold text** - Great for item names
*Italic text* - Perfect for descriptions
```

**Example:**
```
**Burger** - Classic beef with all the fixings
*Served with fries and coleslaw*
```

---

## Lists

### Bullet Lists
```
- French Fries
- Onion Rings
- Side Salad
```

Automatically adds bullet points (•) in front of each item.

---

## Color Tags

Add color to prices, specials, or any text. Color applies until the end of the line or the next color tag.

### Available Colors
```
{r}  Red text
{y}  Yellow text (perfect for prices!)
{g}  Green text
{b}  Blue text
{o}  Orange text (great for callouts)
{p}  Pink text
{w}  White text
```

### Examples
```
**Burger** - {y}$8.95
**Steak** - {y}$16.95

{o}Ask about our daily dessert special!
```

**Tip:** You don't need closing tags - the color lasts until the end of the line!

---

## Separators

### Horizontal Line
```
---
```

Use three dashes to create a dividing line between sections.

---

## Complete Menu Example

```markdown
## Tonight's Dinner Specials

**Burger** - {y}$8.95  
Classic beef burger with lettuce, tomato, onion

**Stromboli** - {y}$10.95  
Rolled with pepperoni, sausage, and mozzarella

**Wings** - {y}12 for $11.50 | 6 for $7.95  
*Choice of Buffalo, BBQ, or Garlic Parmesan*

---

### Sides
- French Fries - {y}$3.50
- Onion Rings - {y}$4.25
- Side Salad - {y}$3.95

{o}**Ask about our daily dessert special!**
```

---

## Quick Tips

✅ **DO:**
- Leave blank lines between sections for better spacing
- Use `**bold**` for item names
- Use `{y}` for prices (yellow stands out great)
- Use `*italic*` for descriptions
- Preview before saving

❌ **DON'T:**
- Forget the space after `##` in headings
- Forget the space after `-` in lists
- Use too many colors (keep it simple!)

---

## Need Help?

The editor has a built-in **Help** tab with live examples. Just tap the Help button (?) to see all formatting options with real-time previews!
