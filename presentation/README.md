# Squeezed Signals Presentation

A 45-minute presentation covering the evolution of observability data compression across metrics, logs, and traces.

## 🎯 Presentation Overview

**Duration:** 45 minutes  
**Target Audience:** Computer science students and engineers interested in data compression  
**Format:** Progressive teaching from basic concepts to advanced techniques

### Structure

1. **Introduction (5 min)** - The observability data explosion and project goals
2. **Metrics (12 min)** - Time-series compression journey (1x → 79.7x)
3. **Logs (12 min)** - Structured text compression with CLP algorithm (1x → 50.8x)
4. **Traces (10 min)** - Distributed execution compression (1x → 25x)
5. **Reality Check (6 min)** - Trade-offs, production considerations, and lessons learned

## 🚀 Running the Presentation

### Option 1: Open Locally

Simply open the HTML file in your browser:

```bash
# From the project root
cd presentation
open index.html  # macOS
# OR
xdg-open index.html  # Linux
# OR
start index.html  # Windows
```

### Option 2: Run with a Local Server

For the best experience (especially if you make modifications):

```bash
# Using Python's built-in server
cd presentation
python -m http.server 8000

# Then open in your browser:
# http://localhost:8000
```

### Option 3: Use VS Code Live Server

1. Install the "Live Server" extension in VS Code
2. Right-click on `index.html`
3. Select "Open with Live Server"

## ⌨️ Navigation

- **Next slide:** Space, →, ↓, or Page Down
- **Previous slide:** ←, ↑, or Page Up
- **Slide overview:** Press `Esc` or `O`
- **Help:** Press `?`
- **Fullscreen:** Press `F`
- **Speaker notes:** Press `S` (opens in new window)

## 📊 Presentation Highlights

### Key Achievements Shown

- **Metrics:** 84 MB → 1 MB (79.7x compression)
  - Demonstrates XOR compression, delta encoding, pattern detection
  
- **Logs:** 5 MB → 99 KB (50.8x compression)
  - Deep dive into CLP (Compressed Log Processor) algorithm
  
- **Traces:** 134 KB → 5.4 KB (25x compression)
  - Service topology and span relationship exploitation

### Technical Concepts Covered

1. **Binary Encoding** - CBOR vs JSON
2. **Generic Compression** - zstd algorithm
3. **Domain-Specific Techniques:**
   - Metrics: XOR compression (Gorilla), delta encoding, pattern detection
   - Logs: Template extraction, variable classification
   - Traces: Service topology, parent-child relationships
4. **Columnar Storage** - Why it matters for compression
5. **Production Trade-offs** - Storage vs CPU vs Query Speed

## 🎨 Customization

The presentation uses Reveal.js with a dark theme. To customize:

1. **Change theme:** Edit the CSS link in `index.html`:
   ```html
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/theme/black.css">
   ```
   Available themes: black, white, league, beige, sky, night, serif, simple, solarized

2. **Adjust timing:** Modify the section content in `index.html`

3. **Add speaker notes:** Add notes within slides:
   ```html
   <section>
       <h2>Slide Title</h2>
       <p>Slide content</p>
       <aside class="notes">
           These notes appear in speaker view only
       </aside>
   </section>
   ```

## 📝 Presentation Tips

### For Presenters

1. **Start with motivation:** Emphasize the scale of observability data (petabytes!)
2. **Use the live demos:** Show the actual compression ratios from running the code
3. **Emphasize patterns:** Each signal type has unique characteristics to exploit
4. **Highlight the CLP algorithm:** It's the star of the logs section
5. **Reality check is crucial:** Don't oversell compression - discuss trade-offs
6. **Interactive elements:** Ask audience about their experience with these systems

### Time Management

- Introduction: 5 minutes (slides 1-5)
- Metrics: 12 minutes (slides 6-14)
- Logs: 12 minutes (slides 15-23)
- Traces: 10 minutes (slides 24-31)
- Reality Check: 6 minutes (slides 32-36)

### Key Messages

1. **Domain knowledge is powerful:** Understanding data structure beats generic algorithms
2. **Progressive optimization:** Each technique builds on the previous
3. **No free lunch:** Better compression = higher CPU cost
4. **Production reality:** Use tiered storage with different compression levels

## 🔗 Related Resources

- **Project Repository:** https://github.com/flash1293/squeezed-signals
- **YScope CLP:** https://github.com/y-scope/clp (production log compression)
- **Facebook Gorilla Paper:** Time-series compression algorithm used in production
- **Zstandard:** https://facebook.github.io/zstd/ (compression algorithm)
- **Reveal.js Documentation:** https://revealjs.com/ (presentation framework)

## 📄 Exporting to PDF

To create a PDF version:

1. Open the presentation in Chrome/Chromium
2. Add `?print-pdf` to the URL: `file:///path/to/index.html?print-pdf`
3. Open Print dialog (Ctrl/Cmd + P)
4. Set destination to "Save as PDF"
5. Adjust settings:
   - Layout: Portrait
   - Margins: None
   - Background graphics: Enabled
6. Save

## 🛠️ Technical Details

**Framework:** Reveal.js 4.5.0  
**Hosting:** No server required (can run from file://)  
**Dependencies:** All loaded via CDN (no npm install needed)  
**Browser Support:** Modern browsers (Chrome, Firefox, Safari, Edge)

## 💡 Making It Interactive

Consider enhancing the presentation with:

1. **Live demos:** Run the compression scripts during the presentation
2. **Q&A slides:** Add blank slides for questions between sections
3. **Code walkthroughs:** Show key algorithms from the actual code
4. **Comparative visualizations:** Display compression ratios as bar charts

## 📧 Questions?

For questions about the presentation or the compression techniques, refer to the main project README or the detailed documentation in each signal directory:
- `metrics/docs/README.md`
- `logs/docs/README.md`
- `traces/docs/README.md`
