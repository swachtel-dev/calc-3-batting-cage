# Calc III Batting Cage

Practice problem tool for Rize Calculus III. Mirrors the Calc II cage at
[swachtel-dev/calc-batting-cage](https://github.com/swachtel-dev/calc-batting-cage).

**Live:** https://swachtel-dev.github.io/calc-3-batting-cage/

## Files

- `index.html` — single-page UI (KaTeX, dark/light theme, no build step)
- `problems.json` — 494 problems across 44 Paul's-section topic groups
- `build_problems.py` — generator: rebuilds `problems.json` from the upstream
  `question_bank.csv` (lives in the Mucking/coursedev repo)

## Coverage

- Vectors and 3D space (Ch 11–12)
- Partial derivatives (Ch 13)
- Applications of partial derivatives (Ch 14)
- Multiple integrals (Ch 15)
- Line integrals (Ch 16)
- Surface integrals (Ch 17)

493 of 494 problems ship with full worked solutions. The single held-back
item shows a "coming soon" placeholder (the source problem text is likely
mistyped; flagged for review).
