# Publishing Guide for Goutham Rajam

## Your Paper
**Title:** "S2S: An Autonomous Multi-Agent Framework for Specification-to-GDSII Chip Design with Deterministic Tool-Based Verification"  
**Author:** Goutham Rajam (solo)  
**File:** `docs/paper/s2s_paper.tex` (IEEE conference format)

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

| Venue | Type | Deadline (typical) | Prestige | Fit |
|-------|------|-------------------|----------|-----|
| **DAC** (Design Automation Conference) | Conference | Nov/Dec | Top-tier | Excellent |
| **ICCAD** (Int'l Conf. on CAD) | Conference | Apr/May | Top-tier | Excellent |
| **DATE** (Design, Automation & Test in Europe) | Conference | Sep | Top-tier | Good |
| **ASP-DAC** (Asia/South Pacific DAC) | Conference | Jul | Strong | Good |
| **MLCAD** (ML for CAD Workshop) | Workshop | ~Aug | Growing | Perfect fit |
| **IEEE TCAD** | Journal | Rolling | Top journal | Good (longer review) |
| **IEEE Design & Test** | Magazine | Rolling | Good | Good (shorter format) |

**Best first target for a new author:** MLCAD workshop (lower bar, perfect topic match) or DAC/ICCAD (higher prestige, competitive).

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
