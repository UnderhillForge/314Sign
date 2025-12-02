# 314Sign — The Dead-Simple Digital Menu Board

> **No apps. No logins. No tech skills.**  
> Just point a mobile browser at edit.html, make changes, and **watch it update instantly** on screen.

314Sign turns any **Raspberry Pi 5 + fullpageOS** into a **beautiful, live-updating digital sign** — perfect for **restaurants, private clubs, cafés, or kitchens**.

---

## Features

| Feature | Why It Matters |
|-------|----------------|
| **Edit from any phone** | Staff use their own device — no training needed |
| **Live preview & instant update** | Changes appear in **< 3 seconds** |
| **Custom backgrounds & fonts** | Match your brand with Comic Sans, handwriting, or elegance |
| **Upload photos from phone** | Snap a special → upload → done |
| **Zero apps or accounts** | Works on **Wi-Fi only**, no internet required |
| **Auto-reload kiosk** | No manual refresh — just works |

---

## Quick Start (5 Minutes)

```bash
# 1. Flash fullpageOS on your Pi 5
# 2. Boot, enable SSH, connect to Wi-Fi
# 3. Run the one-click setup:
curl -sSL https://raw.githubusercontent.com/UnderhillForge/314Sign/main/setup-kiosk.sh | sudo bash

# 4. Open in browser:
http://raspberrypi.local
