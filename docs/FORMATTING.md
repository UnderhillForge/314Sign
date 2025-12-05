# 314Sign Formatting Guide

Quick reference for text formatting in your content. All formatting happens in the edit page — just type naturally and use these simple codes.

---

## Basic Text Formatting

### Headings
```
## Large Heading
### Medium Heading
```

Use headings to organize sections like "Today's Specials" or "Desserts"

**Example:**
```
## Dinner Menu
### Entrees
```

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

**Tip:** You don't need closing tags — color lasts until the end of the line!

---

## Separators

### Horizontal Line
```
---
```

Use three dashes to create a dividing line between sections.

---

## Font Size Override

Override the global font size for specific sections of text using size tags.

### Syntax
```
[sX]Your text here[/s]
```

Where X is the percentage of screen width (e.g., 10 for 10%, 15 for 15%)

### Examples
```
[s15]**SUPER SALE**[/s]
Normal sized text here

[s10]
**Today's Special**
Big text for the whole section
[/s]
```

**Note:** Size tags work across multiple lines until you close them with `[/s]`

---

## Text Alignment

Center or right-align text using alignment tags.

### Syntax
```
[center]Centered text[/center]
[right]Right-aligned text[/right]
```

### Examples
```
[center]
**Welcome to Our Restaurant**
Open Daily 11am - 9pm
[/center]

[right]Prices subject to change[/right]
```

**Note:** Text is left-aligned by default. Alignment tags work across multiple lines.

---

## Emoji Support

Add emoji directly in your menu text using the emoji toolbar buttons or copy-paste from your device:
- 🍔 Burgers
- 🍕 Pizza  
- 🍗 Chicken
- 🥗 Salads
- 🍰 Desserts
- ☕ Coffee
- 🍺 Beer
- 🍷 Wine

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
