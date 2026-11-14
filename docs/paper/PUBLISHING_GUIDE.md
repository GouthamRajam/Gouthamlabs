# Publishing Guide for Goutham Rajam

## Your Paper
**Title:** "S2S: Autonomous Multi-Agent Specification-to-GDSII Chip Design with Deterministic Verification"  
**Author:** Goutham Rajam (solo)  
**File:** `docs/paper/s2s_paper.tex` (IEEE conference format)  
**Page count:** ~6 content pages + ~1 reference page (fits all major venues)

---

## Step-by-Step: How to Publish

### Step 1: Create an arXiv Account (Free, ~5 minutes)
1. Go to https://arxiv.org/user/register
2. Sign up with your email
3. You'll need an **endorsement** for your first submission in the `cs.AR` (Computer Architecture) or `cs.AI` category. arXiv may auto-endorse you, or you can ask an endorsed author to endorse you.
4. No cost. arXiv is free and open-access.

### Step 2: Compile the Paper to PDF
You need a LaTeX installation. Options:
- **Overleaf** (easiest, free): Go to https://overleaf.com, create account, upload `s2s_paper.tex`, click "Recompile"
- **Local**: Install TexLive, then run `pdflatex s2s_paper.tex && bibtex s2s_paper && pdflatex s2s_paper.tex && pdflatex s2s_paper.tex`

### Step 3: Submit to arXiv (Free Preprint)
1. Log in to arXiv
2. Click "Submit" → choose category `cs.AR` (Hardware Architecture) with cross-list to `cs.AI`
3. Upload your `.tex` file (arXiv compiles it server-side)
4. Fill in metadata (title, abstract, author)
5. Submit → you get a permanent arXiv ID (e.g., `arXiv:2611.XXXXX`)
6. Paper is publicly available within 1-2 business days

**Why arXiv first:** It timestamps your work, gives you a citable reference, and is free. Many researchers read arXiv daily.

### Step 4 (Optional): Submit to a Peer-Reviewed Venue
After arXiv, consider submitting to a conference or journal:

| Venue | Type | Page Limit | Cost | Deadline (typical) | Fit |
|-------|------|-----------|------|-------------------|-----|
| **arXiv** | Preprint | No limit | **FREE** | Anytime | Excellent |
| **DAC** | Conference | 6 + 1 ref | ~$800 reg | Nov/Dec | Excellent |
| **ICCAD** | Conference | 6 + 1 ref | ~$700 reg | Apr/May | Excellent |
| **DATE** | Conference | 6 + 1 ref | ~$600 reg | Sep | Good |
| **MLCAD** | Workshop | 6 (refs excl.) | ~$400 reg | ~Aug | Perfect fit |
| **ASP-DAC** | Conference | 6 + 1 ref | ~$500 reg | Jul | Good |
| **IEEE TCAD** | Journal | ~15 | $0 (OA extra) | Rolling | Good |

**Page format notes:**
- The paper is formatted to **6+1 pages** in IEEE two-column (IEEEtran conference class)
- This fits all conference venues above without modification
- For arXiv, the paper can be submitted as-is (no page limit)
- For MLCAD, references are excluded from the 6-page count, so this fits

**Best first target for a new author:** arXiv first (free, instant), then MLCAD workshop (lower bar, perfect topic match) or DAC/ICCAD (higher prestige, competitive). Conference submission requires registration fees ($400-800).

### Step 5: Put Supplementary Materials on GitHub
Your GitHub repo (https://github.com/GouthamRajam/Gouthamlabs) already has:
- Complete codebase
- Agent definitions
- Trajectory logs
- Signoff evidence

Add a note in the repo README linking to the arXiv paper once published.

---

## Tips for First-Time Authors

1. **Solo authorship is fine.** Many important papers have single authors. Your work stands on its own merits.

2. **The honest limitations section is a strength.** Reviewers respect papers that clearly state what doesn't work. The provenance audit section will likely be praised.

3. **Before submitting to a conference**, read 2-3 recent accepted papers from that venue to match the style and depth expectations.

4. **Responding to reviews:** If you submit to a conference and get reviews, respond point-by-point. Be factual and gracious. Reviewers are volunteers.

5. **Affiliation:** As an independent researcher, list "Independent Researcher" as your affiliation. This is perfectly acceptable.

6. **ORCID:** Consider creating a free ORCID ID (https://orcid.org) — it's a unique researcher identifier that follows you across publications.

---

## What to Do Right Now

1. Upload `s2s_paper.tex` to Overleaf to compile to PDF
2. Create an arXiv account
3. Submit to arXiv under `cs.AR` + `cs.AI`
4. Share the arXiv link on your GitHub README
5. Consider submitting to MLCAD or DAC

Good luck with your first publication!
