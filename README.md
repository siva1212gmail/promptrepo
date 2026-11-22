# ✦ PROMPT PETTI (ப்ராம்ப்ட் பெட்டி)

> **Trending AI image & video prompts for ChatGPT and Gemini — curated by [@aswinthefilmer](https://youtube.com/@aswinthefilmer) for Tamil, Malayalam, and Indian digital creators.**

---

## ⚡ Tech Stack & Architecture

- **Backend:** Django 5.2 (Python 3.11+), Django Templates, Django ORM.
- **Frontend:** Vanilla JavaScript (Fetch API, zero heavy frameworks, zero React), Mobile-First CSS with fluid typography (`clamp()`), CSS Grid, Flexbox.
- **Media & Images:** Pillow with automatic WebP conversion and optimization, touch-friendly interactive Before/After comparison slider (`touch-action: pan-y`).
- **Static Asset Serving:** WhiteNoise for production asset compression and cache headers.
- **Production Server:** Gunicorn WSGI.
- **Database:** SQLite3 by default; instant zero-code switch to PostgreSQL via `DATABASE_URL`.
- **Environment Configuration:** `python-decouple` with `.env` support.

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone <repo-url>
cd prompt

# Create virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment configuration:

```bash
cp .env.example .env
```

### 3. Apply Migrations & Seed Demo Data

Run the database migrations and the custom `seed_demo` management command:

```bash
python manage.py migrate
python manage.py seed_demo
```

The `seed_demo` command will automatically:
1. Initialize the singleton `SiteSettings` with social channel links (`@aswinthefilmer`) and daily drop time.
2. Create an administrative superuser account:
   - **Username:** `admin`
   - **Password:** `admin123`
3. Create all 8 prompt categories:
   - *Portrait*, *Couple Prompts*, *Festive*, *Birthday*, *Cinematic*, *General*, *Stories*, *Surreal*.
4. Seed 14 rich, realistic sample AI prompts for ChatGPT & Gemini (with generated WebP cards and before/after comparisons).
5. Seed realistic audience prompt requests.

### 4. Start the Development Server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## 🔒 Security Rule: YouTube Unlock Mechanism

Prompt Petti enforces a strict server-side security rule for protected prompt text:

1. **Zero Text Leakage:** The secret AI `prompt_text` is **NEVER** rendered in the public HTML, the list API (`/api/prompts/`), or any initial JSON response. CSS blur is only applied to dummy placeholder text.
2. **Unlock Flow:**
   - On the locked prompt card, the visitor taps **"1. Subscribe on YouTube"**, which opens Aswin's channel in a new tab.
   - The UI reveals **"2. I'm subscribed ✓"**.
   - Clicking this calls `POST /api/unlock/`, which sets a 1-year cookie (`unlocked=true`) and session flag.
   - Client JS then requests `GET /api/prompts/<id>/text/`.
   - The server verifies the cookie/session; if valid, it returns the real text with a smooth un-blur animation. If unverified, it returns `403 Forbidden`.
   - Once unlocked, all prompts across the site remain unlocked for that browser.

---

## ⏰ Daily 6:00 PM IST Auto-Publish Drop

### How It Works

1. **Timezone:** Configured to `Asia/Kolkata` (`USE_TZ = True`).
2. **Default Drop Schedule:** When creating a prompt in the dashboard without specifying a drop time, it automatically defaults to the **next 6:00 PM IST** (today if before 6 PM, or tomorrow if after 6 PM).
3. **Query-Level Auto-Publish:** The public site uses `Prompt.published.all()`, which filters on:
   ```python
   is_published=True, publish_at__lte=timezone.now()
   ```
   This guarantees that scheduled prompts go live the exact moment 6:00 PM IST passes — **no background workers or cron jobs required**.
4. **Live Countdown:** The hero bar computes the time remaining until the next 6:00 PM IST. When it reaches `00:00:00`, it celebrates with a toast notification and resets to tomorrow's 6 PM.
5. **Scheduler Management Command:**
   ```bash
   python manage.py publish_due
   ```
   Can be called by cron or background task runners if needed.

---

## 📱 Influencer Dashboard (`/dashboard/`)

A dedicated, mobile-friendly creator dashboard is accessible at `/dashboard/` (login protected):

- **Overview:** Live prompt stats, total likes counter, today's unlocks offset, pending requests, and the **Upcoming Drops Schedule Queue**.
- **Prompts Management:** Filter by live, scheduled, or draft status. Quick **"Publish Now ⚡"** button to drop queued items early.
- **Prompt Form:** Mobile-friendly stacked inputs, direct image uploads (cover, before, after) from phone camera or gallery, automatic Pillow WebP conversion.
- **Requests Box:** View suggestions sent by subscribers, review reference images/links, mark requests as done, and **Export all requests to CSV**.
- **Site Settings:** Edit YouTube link, Instagram URL, WhatsApp channel, drop time, and base unlock number.

---

## 🌐 Switching to PostgreSQL & Cloudinary

### Switching to PostgreSQL

Set the `DATABASE_URL` environment variable:

```env
DATABASE_URL=postgres://username:password@your-db-host:5432/promptpetti_db
```

`promptpetti/settings.py` automatically detects `DATABASE_URL` using `dj-database-url` and switches from SQLite to PostgreSQL without any code changes.

### Switching to Cloudinary (Media Storage)

1. Install Cloudinary packages:
   ```bash
   pip install cloudinary django-cloudinary-storage
   ```
2. In `.env`, add your credentials:
   ```env
   CLOUDINARY_STORAGE={'CLOUD_NAME':'your_cloud_name','API_KEY':'your_api_key','API_SECRET':'your_api_secret'}
   DEFAULT_FILE_STORAGE=cloudinary_storage.storage.MediaCloudinaryStorage
   ```
3. In `settings.py`, add `'cloudinary_storage'` and `'cloudinary'` to `INSTALLED_APPS` before `'django.contrib.staticfiles'`.

---

## 🚢 Production Deployment

### Procfile (Included)
```text
web: gunicorn promptpetti.wsgi --log-file -
```

### Render Deployment
1. Connect your GitHub repository to Render as a **Web Service**.
2. Environment: `Python 3`.
3. Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
4. Start Command: `gunicorn promptpetti.wsgi:application`
5. Add Environment Variables:
   - `SECRET_KEY`: A strong random string
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `your-app.onrender.com`
   - `DATABASE_URL`: Your Render PostgreSQL database URL

### Railway Deployment
1. Click **New Project** → **Deploy from GitHub repo**.
2. Add a PostgreSQL plugin to the project; Railway automatically provisions `DATABASE_URL`.
3. In service settings, add environment variables:
   - `SECRET_KEY`: A strong random string
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `*`
4. Railway detects `Procfile` and runs the application via Gunicorn with WhiteNoise automatically.

---

## 📱 Responsive Design Verification Report

The website was designed strictly **mobile-first** and tested across standard device screen sizes:

| Viewport Width | Device Category | Verified Behaviors |
| :--- | :--- | :--- |
| **320px** | Small phones (iPhone SE 1st gen, older Androids) | Single-column grid, compact navbar with logo & bookmark, full-width inputs, zero overflow, 44px tap targets. |
| **360px - 390px** | Standard modern phones (iPhone 12/13/14, Galaxy S21) | Modal opens as a smooth full-screen bottom sheet with sticky close button, before/after slider pan-y drag, stacked hero. |
| **412px - 430px** | Large phones (iPhone Pro Max, Pixel 7 Pro) | 2-column card grid, horizontal scrolling categories with snap, touch swipe on Most Liked row. |
| **600px** | Foldables / Phablets | Fluid headline scaling (`clamp()`), countdown bar layout adjusts from stacked to inline. |
| **768px** | Tablets portrait (iPad Mini, iPad 10th Gen) | 3-column card grid, hamburger menu transitions to full desktop links, request form inline attachment toggles. |
| **820px - 1024px** | Tablets landscape / iPad Air / Small Laptops | Modal converts to centered two-column view (media left, details right), 3-column grid. |
| **1280px** | Standard Laptops / MacBooks | Hero displays side-by-side with interactive mock terminal typing card, vertical "VOL.01" label visible. |
| **1440px - 1920px+** | Desktops & Ultra-Wide Displays | Centered container (1280px max-width) prevents stretching, 4-column card grid, smooth hover lifts. |

### Responsive & Accessibility Highlights:
- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">` ensures safe-area handling for iPhone notches.
- Inputs have `font-size: 1rem` (16px) to completely eliminate unwanted iOS auto-zoom on focus.
- Touch drag before/after slider uses `touch-action: pan-y` so vertical page gestures are never hijacked.
- Keyboard navigation: modal closes with `Escape`, focus trapped, slider controllable via `Left/Right` arrow keys.
- Respects `prefers-reduced-motion` by disabling marquee ticker and transitions for sensitive users.
