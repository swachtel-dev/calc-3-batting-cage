#!/usr/bin/env python3
"""
Build problems.json for the Calc III Batting Cage from question_bank.csv.

Reads:
    ../question_bank.csv (rows with location='Batting-Cage')
    /tmp/calc3_notes.json or sitemap.json (for section titles + Paul URL)

Writes:
    ./problems.json
    JSON object keyed by Paul's section id (e.g. "13.6"); each entry:
    { id, title, chapter, chapterNum, unit, unitTitle, notesUrl, problems: [...] }
    Each problem: { prompt, problem, answer, solution }

The HTML loads problems.json at runtime; updating problems does NOT require
editing index.html.

Solutions: when bank rows have empty `answer`/`solution`, those fields ship
empty in problems.json. The `index.html` UI degrades gracefully: it shows the
problem and a "Solution coming soon" placeholder instead of a full solution.
A separate agent populates answer/solution back into the bank, then this
script re-runs.

Usage:
    python3 build_problems.py
    python3 build_problems.py --verify    # also print per-section counts
"""
import csv
import json
import sys
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).parent
BANK = HERE.parent / "question_bank.csv"
NOTES_MAP = HERE.parent / "reference-docs" / "sitemap.json"  # has CalcIII section titles + URLs
OUT = HERE / "problems.json"

# Paul's Calc II sections used in our Calc III (vectors / 3D / vector functions chapters)
CALCII_NOTES = {
    "11.1": ("Vectors - The Basics",                  "https://tutorial.math.lamar.edu/Classes/CalcII/Vectors_Basics.aspx"),
    "11.2": ("Vector Arithmetic",                     "https://tutorial.math.lamar.edu/Classes/CalcII/VectorArithmetic.aspx"),
    "11.3": ("Dot Product",                           "https://tutorial.math.lamar.edu/Classes/CalcII/DotProduct.aspx"),
    "11.4": ("Cross Product",                         "https://tutorial.math.lamar.edu/Classes/CalcII/CrossProduct.aspx"),
    "12.1": ("The 3-D Coordinate System",             "https://tutorial.math.lamar.edu/Classes/CalcII/3DCoords.aspx"),
    "12.2": ("Equations of Lines",                    "https://tutorial.math.lamar.edu/Classes/CalcII/EqnsOfLines.aspx"),
    "12.3": ("Equations of Planes",                   "https://tutorial.math.lamar.edu/Classes/CalcII/EqnsOfPlanes.aspx"),
    "12.6": ("Vector Functions",                      "https://tutorial.math.lamar.edu/Classes/CalcII/VectorFunctions.aspx"),
    "12.7": ("Calculus with Vector Functions",        "https://tutorial.math.lamar.edu/Classes/CalcII/VectorFcnsCalculus.aspx"),
    "12.8": ("Tangent, Normal and Binormal Vectors",  "https://tutorial.math.lamar.edu/Classes/CalcII/TangentNormalVectors.aspx"),
    "12.9": ("Arc Length with Vector Functions",      "https://tutorial.math.lamar.edu/Classes/CalcII/VectorArcLength.aspx"),
    "12.10":("Curvature",                             "https://tutorial.math.lamar.edu/Classes/CalcII/Curvature.aspx"),
    "12.11":("Velocity and Acceleration",             "https://tutorial.math.lamar.edu/Classes/CalcII/Velocity_Acceleration.aspx"),
    "12.12":("Cylindrical Coordinates",               "https://tutorial.math.lamar.edu/Classes/CalcII/CylindricalCoords.aspx"),
    "12.13":("Spherical Coordinates",                 "https://tutorial.math.lamar.edu/Classes/CalcII/SphericalCoords.aspx"),
}

CHAPTERS = {
    11: "Vectors (from Paul's Calc II)",
    12: "3-Dimensional Space (from Paul's Calc II)",
    13: "Partial Derivatives",
    14: "Applications of Partial Derivatives",
    15: "Multiple Integrals",
    16: "Line Integrals",
    17: "Surface Integrals",
}

# Section -> (unit, unit_title). Mirrors course_plan_draft.md.
SECTION_UNIT = {
    "11.1": (1,  "Onboarding + Calc I/II Review + Intro to Vectors"),
    "11.2": (2,  "Vector Operations"),
    "11.3": (2,  "Vector Operations"),
    "11.4": (2,  "Vector Operations"),
    "12.1": (3,  "3D Space, Lines, Planes & Vector Functions"),
    "12.2": (3,  "3D Space, Lines, Planes & Vector Functions"),
    "12.3": (3,  "3D Space, Lines, Planes & Vector Functions"),
    "12.6": (3,  "3D Space, Lines, Planes & Vector Functions"),
    "12.7": (3,  "3D Space, Lines, Planes & Vector Functions"),
    "12.8": (4,  "Tangent, Normal, Arc Length, Curvature & Motion"),
    "12.9": (4,  "Tangent, Normal, Arc Length, Curvature & Motion"),
    "12.10":(4,  "Tangent, Normal, Arc Length, Curvature & Motion"),
    "12.11":(4,  "Tangent, Normal, Arc Length, Curvature & Motion"),
    "12.12":(10, "Triple Integrals: Cartesian, Cylindrical & Spherical"),
    "12.13":(10, "Triple Integrals: Cartesian, Cylindrical & Spherical"),
    "13.1": (5,  "Limits, Partial Derivatives & the Chain Rule"),
    "13.2": (5,  "Limits, Partial Derivatives & the Chain Rule"),
    "13.3": (5,  "Limits, Partial Derivatives & the Chain Rule"),
    "13.4": (5,  "Limits, Partial Derivatives & the Chain Rule"),
    "13.6": (5,  "Limits, Partial Derivatives & the Chain Rule"),
    "13.7": (6,  "Directional Derivatives, Gradient & Tangent Planes"),
    "14.1": (6,  "Directional Derivatives, Gradient & Tangent Planes"),
    "14.2": (6,  "Directional Derivatives, Gradient & Tangent Planes"),
    "14.3": (8,  "Optimization of Multivariable Functions"),
    "14.4": (8,  "Optimization of Multivariable Functions"),
    "14.5": (8,  "Optimization of Multivariable Functions"),
    "15.1": (9,  "Double Integrals & Polar Coordinates"),
    "15.2": (9,  "Double Integrals & Polar Coordinates"),
    "15.3": (9,  "Double Integrals & Polar Coordinates"),
    "15.4": (9,  "Double Integrals & Polar Coordinates"),
    "15.5": (10, "Triple Integrals: Cartesian, Cylindrical & Spherical"),
    "15.6": (10, "Triple Integrals: Cartesian, Cylindrical & Spherical"),
    "15.7": (10, "Triple Integrals: Cartesian, Cylindrical & Spherical"),
    "16.1": (11, "Vector Fields & Line Integrals"),
    "16.2": (11, "Vector Fields & Line Integrals"),
    "16.3": (11, "Vector Fields & Line Integrals"),
    "16.4": (11, "Vector Fields & Line Integrals"),
    "16.5": (11, "Vector Fields & Line Integrals"),
    "16.6": (12, "Conservative Fields, Green's, Stokes' & Divergence Theorems"),
    "16.7": (12, "Conservative Fields, Green's, Stokes' & Divergence Theorems"),
    "17.1": (12, "Conservative Fields, Green's, Stokes' & Divergence Theorems"),
    "17.2": (12, "Conservative Fields, Green's, Stokes' & Divergence Theorems"),
    "17.3": (12, "Conservative Fields, Green's, Stokes' & Divergence Theorems"),
    "17.4": (12, "Conservative Fields, Green's, Stokes' & Divergence Theorems"),
    "17.5": (12, "Conservative Fields, Green's, Stokes' & Divergence Theorems"),
    "17.6": (12, "Conservative Fields, Green's, Stokes' & Divergence Theorems"),
}


def load_section_meta():
    """Return {section_id: (title, notesUrl)} for all in-scope sections."""
    meta = dict(CALCII_NOTES)  # 11.x and 12.x
    sm = json.load(open(NOTES_MAP))
    for ch in sm["chapters"]:
        for s in ch["sections"]:
            sec_id = s["title"].split()[0]
            title = " ".join(s["title"].split()[1:])
            meta[sec_id] = (title, s["notes_url"])
    return meta


def main():
    verify = "--verify" in sys.argv
    rows = list(csv.DictReader(open(BANK)))
    cage = [r for r in rows if r["location"] == "Batting-Cage"]
    meta = load_section_meta()

    by_section = defaultdict(list)
    for r in cage:
        sec = r["pauls_section"]
        by_section[sec].append(r)

    out = {}
    for sec in sorted(by_section.keys(), key=lambda s: tuple(int(x) for x in s.split("."))):
        if sec not in SECTION_UNIT:
            print(f"WARN: section {sec} not in SECTION_UNIT map; skipping {len(by_section[sec])} problems")
            continue
        unit, unit_title = SECTION_UNIT[sec]
        title, notes_url = meta.get(sec, (f"Section {sec}", "#"))
        ch_num = int(sec.split(".")[0])
        problems = []
        for r in by_section[sec]:
            problems.append({
                "id": r["question_id"],
                "klo": r["klo_id"],
                "tier": r["tier"],
                "prompt": "",
                "problem": r["question_text"],
                "answer": r.get("answer", "").strip(),
                "solution": r.get("solution", "").strip(),
            })
        out[sec] = {
            "id": sec,
            "title": title,
            "chapter": CHAPTERS.get(ch_num, ""),
            "chapterNum": ch_num,
            "unit": unit,
            "unitTitle": unit_title,
            "notesUrl": notes_url,
            "problems": problems,
        }

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    total = sum(len(v["problems"]) for v in out.values())
    print(f"Wrote {OUT} ({len(out)} sections, {total} problems)")

    if verify:
        print("\nPer-section counts:")
        for sec, data in out.items():
            n = len(data["problems"])
            n_with_sol = sum(1 for p in data["problems"] if p["solution"])
            print(f"  {sec:<6} ({data['title'][:32]:<32})  total={n:>3}  solutions={n_with_sol:>3}")


if __name__ == "__main__":
    main()
