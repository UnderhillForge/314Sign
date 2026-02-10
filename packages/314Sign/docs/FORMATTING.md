# Text Formatting Guide

314Sign supports rich text formatting through simple color tags and text styling.

## Color Tags

Add colors to your menu text using these tags:

- `{r}` **red** text `{/r}`
- `{y}` **yellow** text `{/y}`
- `{g}` **green** text `{/g}`
- `{b}` **blue** text `{/b}`
- `{o}` **orange** text `{/o}`
- `{p}` **pink** text `{/p}`
- `{w}` **white** text `{/w}`
- `{lg}` **light grey** text `{/lg}`

### Examples

```
{y}$8.95{/y} - Yellow price
{r}SOLD OUT{/r} - Red alert text
{g}Vegetarian{/g} - Green dietary indicator
```

## Text Alignment

Control text positioning:

- `[center]...[/center]` - Center align text
- `[right]...[/right]` - Right align text

### Examples

```
[center]Welcome to Our Restaurant![/center]
[right]$12.95[/right]
```

## Size Overrides

Change text size with size tags:

- `[s15]...[/s]` - Custom size (15pt in this example)
- `[s20]Large Heading[/s]` - 20pt text
- `[s10]Small Note[/s]` - 10pt text

### Examples

```
[s18]Special of the Day[/s]
[s12]All prices include tax[/s]
```

## Combining Tags

You can combine color and size tags:

```
[y][s16]$9.99[/s][/y] - Yellow 16pt price
[r][center]CLOSED[/center][/r] - Red centered closed sign
```

## Best Practices

1. **Use colors sparingly** - Too many colors can be distracting
2. **Consistent sizing** - Use similar sizes for similar content types
3. **Contrast** - Ensure colored text is readable on your background
4. **Preview changes** - Always preview before saving to kiosk

## Quick Reference

| Tag | Description | Example |
|-----|-------------|---------|
| `{r}...{/r}` | Red text | `{r}Error{/r}` |
| `{y}...{/y}` | Yellow text | `{y}$5.99{/y}` |
| `{g}...{/g}` | Green text | `{g}Vegan{/g}` |
| `{b}...{/b}` | Blue text | `{b}Info{/b}` |
| `[center]...[/center]` | Center align | `[center]Title[/center]` |
| `[right]...[/right]` | Right align | `[right]$10.00[/right]` |
| `[s15]...[/s]` | Size override | `[s15]Big Text[/s]` |

---

*Formatting is applied when you save your menu. Use the live preview to see changes before committing.*
