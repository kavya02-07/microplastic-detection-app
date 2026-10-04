"""
Scientific reference information for the four microplastic morphology classes.

This module holds literature-derived CONTEXT only. It is used by the PDF report
(backend/api/reports.py) to explain what each morphological class means. None of
the statements here are inferred from, or validated by, an individual analysis:
the YOLO model classifies particles by learned visual features only.

Citation handling:
    * REFERENCES is an ordered list; a reference's citation number is its
      1-based position in that list.
    * Every statement below carries a list of reference keys. Use
      `format_citations(keys)` to render them as "[1, 4]" so that numbers in
      the report body always match the References section.

Every reference was checked against its publisher / DOI registry record
(Crossref, Europe PMC, WHO IRIS, GESAMP). No numerical morphology cutoff
(e.g. an aspect-ratio threshold for fibres) is given because the cited
harmonisation guidance (GESAMP 2019, Table 2.3) defines shapes qualitatively.
"""

# ─── References (order defines citation numbers) ─────────────────────────────

REFERENCES: list[dict] = [
    {
        "key": "gesamp2019",
        "text": (
            "GESAMP (2019). Guidelines for the monitoring and assessment of plastic "
            "litter in the ocean (Kershaw, P.J., Turra, A. and Galgani, F., eds.). "
            "IMO/FAO/UNESCO-IOC/UNIDO/WMO/IAEA/UN/UNEP/UNDP/ISA Joint Group of Experts "
            "on the Scientific Aspects of Marine Environmental Protection. "
            "Rep. Stud. GESAMP No. 99, 130 p."
        ),
        "url": "https://www.gesamp.org/publications/guidelines-for-the-monitoring-and-assessment-of-plastic-litter-in-the-ocean",
    },
    {
        "key": "hartmann2019",
        "text": (
            "Hartmann, N.B., Hüffer, T., Thompson, R.C., Hassellöv, M., et al. (2019). "
            "Are We Speaking the Same Language? Recommendations for a Definition and "
            "Categorization Framework for Plastic Debris. Environmental Science & "
            "Technology, 53(3), 1039-1047."
        ),
        "doi": "10.1021/acs.est.8b05297",
    },
    {
        "key": "hidalgoruz2012",
        "text": (
            "Hidalgo-Ruz, V., Gutow, L., Thompson, R.C., Thiel, M. (2012). Microplastics "
            "in the Marine Environment: A Review of the Methods Used for Identification "
            "and Quantification. Environmental Science & Technology, 46(6), 3060-3075."
        ),
        "doi": "10.1021/es2031505",
    },
    {
        "key": "cole2011",
        "text": (
            "Cole, M., Lindeque, P., Halsband, C., Galloway, T.S. (2011). Microplastics "
            "as contaminants in the marine environment: A review. Marine Pollution "
            "Bulletin, 62(12), 2588-2597."
        ),
        "doi": "10.1016/j.marpolbul.2011.09.025",
    },
    {
        "key": "browne2011",
        # Title reproduced exactly as published (including the original spelling "Woldwide").
        "text": (
            "Browne, M.A., Crump, P., Niven, S.J., Teuten, E., et al. (2011). "
            "Accumulation of Microplastic on Shorelines Woldwide: Sources and Sinks. "
            "Environmental Science & Technology, 45(21), 9175-9179."
        ),
        "doi": "10.1021/es201811s",
    },
    {
        "key": "defalco2019",
        "text": (
            "De Falco, F., Di Pace, E., Cocca, M., Avella, M. (2019). The contribution "
            "of washing processes of synthetic clothes to microplastic pollution. "
            "Scientific Reports, 9, 6633."
        ),
        "doi": "10.1038/s41598-019-43023-x",
    },
    {
        "key": "mato2001",
        "text": (
            "Mato, Y., Isobe, T., Takada, H., Kanehiro, H., et al. (2001). Plastic Resin "
            "Pellets as a Transport Medium for Toxic Chemicals in the Marine Environment. "
            "Environmental Science & Technology, 35(2), 318-324."
        ),
        "doi": "10.1021/es0010498",
    },
    {
        "key": "khatmullina2017",
        "text": (
            "Khatmullina, L., Isachenko, I. (2017). Settling velocity of microplastic "
            "particles of regular shapes. Marine Pollution Bulletin, 114(2), 871-880."
        ),
        "doi": "10.1016/j.marpolbul.2016.11.024",
    },
    {
        "key": "wright2013",
        "text": (
            "Wright, S.L., Thompson, R.C., Galloway, T.S. (2013). The physical impacts "
            "of microplastics on marine organisms: A review. Environmental Pollution, "
            "178, 483-492."
        ),
        "doi": "10.1016/j.envpol.2013.02.031",
    },
    {
        "key": "rochman2019",
        "text": (
            "Rochman, C.M., Brookson, C., Bikker, J., Djuric, N., et al. (2019). "
            "Rethinking microplastics as a diverse contaminant suite. Environmental "
            "Toxicology and Chemistry, 38(4), 703-711."
        ),
        "doi": "10.1002/etc.4371",
    },
    {
        "key": "kappler2016",
        "text": (
            "Käppler, A., Fischer, D., Oberbeckmann, S., Schernewski, G., et al. (2016). "
            "Analysis of environmental microplastics by vibrational microspectroscopy: "
            "FTIR, Raman or both? Analytical and Bioanalytical Chemistry, 408(29), "
            "8377-8391."
        ),
        "doi": "10.1007/s00216-016-9956-3",
    },
    {
        "key": "who2019",
        "text": (
            "World Health Organization (2019). Microplastics in drinking-water. "
            "Geneva: WHO. ISBN 978-92-4-151619-8."
        ),
        "url": "https://www.who.int/publications/i/item/9789241516198",
    },
    {
        "key": "who2022",
        "text": (
            "World Health Organization (2022). Dietary and inhalation exposure to nano- "
            "and microplastic particles and potential implications for human health. "
            "Geneva: WHO. ISBN 978-92-4-005460-8."
        ),
        "url": "https://www.who.int/publications/i/item/9789240054608",
    },
    {
        "key": "vethaak2021",
        "text": (
            "Vethaak, A.D., Legler, J. (2021). Microplastics and human health. "
            "Science, 371(6530), 672-674."
        ),
        "doi": "10.1126/science.abe5041",
    },
    {
        "key": "marfella2024",
        "text": (
            "Marfella, R., Prattichizzo, F., Sardu, C., Fulgenzi, G., et al. (2024). "
            "Microplastics and Nanoplastics in Atheromas and Cardiovascular Events. "
            "New England Journal of Medicine, 390(10), 900-910."
        ),
        "doi": "10.1056/NEJMoa2309822",
    },
]

CITATION_NUMBERS: dict[str, int] = {
    ref["key"]: idx for idx, ref in enumerate(REFERENCES, start=1)
}

# Short "Author (Year)" form for a compact, non-numbered source line — used by
# the condensed report so full formatted references don't need a standalone
# References section.
SHORT_CITE: dict[str, str] = {
    "gesamp2019": "GESAMP (2019)",
    "hartmann2019": "Hartmann et al. (2019)",
    "frias2019": "Frias & Nash (2019)",
    "hidalgoruz2012": "Hidalgo-Ruz et al. (2012)",
    "cole2011": "Cole et al. (2011)",
    "browne2011": "Browne et al. (2011)",
    "defalco2019": "De Falco et al. (2019)",
    "mato2001": "Mato et al. (2001)",
    "khatmullina2017": "Khatmullina & Isachenko (2017)",
    "wright2013": "Wright et al. (2013)",
    "rochman2019": "Rochman et al. (2019)",
    "kappler2016": "Käppler et al. (2016)",
    "who2019": "WHO (2019)",
    "who2022": "WHO (2022)",
    "vethaak2021": "Vethaak & Legler (2021)",
    "marfella2024": "Marfella et al. (2024)",
}


def short_sources(keys: list[str]) -> str:
    """Render reference keys as a compact, deduplicated 'Author (Year)' list."""
    seen = []
    for k in keys:
        label = SHORT_CITE.get(k, k)
        if label not in seen:
            seen.append(label)
    return "; ".join(seen)


def format_citations(keys: list[str]) -> str:
    """Render reference keys as a sorted bracketed citation, e.g. '[1, 4]'."""
    if not keys:
        return ""
    nums = sorted({CITATION_NUMBERS[k] for k in keys})
    return "[" + ", ".join(str(n) for n in nums) + "]"


def format_reference(ref: dict) -> str:
    """Full reference string including DOI or URL."""
    text = ref["text"]
    if ref.get("doi"):
        return f"{text} https://doi.org/{ref['doi']}"
    if ref.get("url"):
        return f"{text} {ref['url']}"
    return text


# ─── Key scientific distinctions (shown before the class profiles) ───────────
# Each entry: (heading, text, [reference keys])

KEY_DISTINCTIONS: list[tuple[str, str, list[str]]] = [
    (
        "Morphology, not chemistry",
        "Fibers, Films, Fragments and Pellets are morphological (shape) categories. "
        "Shape is one of several descriptors used to categorise plastic debris, "
        "alongside size, colour and origin; polymer composition is a separate, "
        "defining property that shape does not reveal.",
        ["hartmann2019", "gesamp2019"],
    ),
    (
        "Shape is not proof of source",
        "Morphology can give some indication of potential sources and environmental "
        "behaviour, but morphological descriptions can be subjective, and a shape "
        "class assigned by this model does not establish the actual source or "
        "pathway of any particle.",
        ["gesamp2019"],
    ),
    (
        "No polymer identification",
        "The YOLO model does not identify polymer composition (e.g. PE, PP, PET, PS, "
        "PVC or nylon). Visual or image-based methods also cannot confirm that a "
        "particle is plastic rather than a natural material of similar appearance.",
        ["gesamp2019", "hidalgoruz2012"],
    ),
    (
        "Polymer identification requires spectroscopy",
        "Confirming that particles are plastic and determining their polymer type "
        "requires complementary analytical techniques, most commonly FTIR or Raman "
        "spectroscopy; the two methods can be complementary.",
        ["gesamp2019", "hidalgoruz2012", "kappler2016"],
    ),
    (
        "Detection is not a risk assessment",
        "Detecting and classifying particles in an image does not establish toxicity, "
        "exposure dose, contamination severity, disease risk or human-health risk.",
        ["who2022", "vethaak2021"],
    ),
    (
        "Human-health evidence is limited",
        "Humans can be exposed to micro- and nanoplastics via food, water and air. "
        "WHO reviews concluded that the available data were of very limited use for "
        "assessing human-health risk and identified major knowledge gaps. Effects "
        "reported in preclinical (in vitro and animal) studies do not by themselves "
        "demonstrate effects in humans. One observational human study associated "
        "chemically identified micro- and nanoplastics in carotid artery plaque with "
        "a higher rate of subsequent cardiovascular events; an observational "
        "association does not establish causation, and that study did not assess "
        "particle morphology.",
        ["who2019", "who2022", "vethaak2021", "marfella2024"],
    ),
]


# ─── Per-class profiles ──────────────────────────────────────────────────────
# Attribute order and display labels for the per-class profile tables.

PROFILE_ATTRIBUTES: list[tuple[str, str]] = [
    ("characteristics", "Morphological characteristics"),
    ("sources", "Commonly reported sources"),
    ("pathways", "Pathways into aquatic environments"),
    ("behaviour", "Environmental behaviour / relevance"),
    ("ecological", "Potential ecological relevance"),
    ("human_health", "Potential human-health relevance"),
    ("uncertainty", "Uncertainty / limitations"),
]

# Short GESAMP field descriptor for each display class (GESAMP 2019, Table 2.3).
GESAMP_DESCRIPTOR: dict[str, str] = {
    "Fibers": "Line (fibre, filament, strand)",
    "Films": "Film (sheet)",
    "Fragments": "Fragment (granule, flake)",
    "Pellets": "Pellet (resin bead)",
}

# Each attribute value: (text, [reference keys])
MORPHOLOGY_PROFILES: dict[str, dict[str, tuple[str, list[str]]]] = {
    "Fibers": {
        "characteristics": (
            "Long fibrous material with a length substantially longer than its width "
            "(GESAMP 'line' category, which includes fibres, filaments and strands).",
            ["gesamp2019"],
        ),
        "sources": (
            "Commonly attributed to textiles and to ropes or fishing lines. Washing of "
            "synthetic clothing releases large numbers of microfibres.",
            ["gesamp2019", "browne2011", "defalco2019"],
        ),
        "pathways": (
            "Laundry wastewater and sewage effluent have been identified as a pathway "
            "for textile fibres; fishing activity is a source of filaments.",
            ["browne2011", "defalco2019", "gesamp2019"],
        ),
        "behaviour": (
            "Shape affects settling: laboratory experiments found that long "
            "cylindrical particles cut from fishing line settled differently from "
            "spheres, and were poorly described by predictions developed for "
            "natural sediments.",
            ["khatmullina2017"],
        ),
        "ecological": (
            "Ingestion of microplastics has been demonstrated in a range of marine "
            "organisms, with uncertain consequences for organism health; evidence "
            "comes mainly from field observations and laboratory studies rather than "
            "fibre-specific population-level outcomes.",
            ["cole2011", "wright2013"],
        ),
        "human_health": (
            "No fibre-specific human-health effect has been established. Human "
            "exposure to microplastics via ingestion and inhalation is recognised, "
            "but available data are insufficient for risk assessment.",
            ["who2022", "vethaak2021"],
        ),
        "uncertainty": (
            "Very thin or colourless fibres are difficult to confirm as plastic by "
            "visual methods alone; natural (e.g. cellulosic) fibres can look similar. "
            "Source attribution (textile vs. fishing gear) cannot be made from shape "
            "alone.",
            ["gesamp2019", "defalco2019"],
        ),
    },
    "Films": {
        "characteristics": (
            "Flat, flexible particles with smooth or angular edges (GESAMP 'film' / "
            "sheet category).",
            ["gesamp2019"],
        ),
        "sources": (
            "Generally secondary microplastics formed by wear, tear and fragmentation "
            "of larger thin, flexible plastic items. Packaging is the largest "
            "plastics market sector, and polyethylene is widely used in plastic bags, "
            "but the parent item of an individual film cannot be determined from "
            "shape.",
            ["gesamp2019", "cole2011"],
        ),
        "pathways": (
            "Mismanaged land-based waste and litter, followed by weathering and "
            "fragmentation in the environment. Most plastic litter entering the ocean "
            "is estimated to originate from inadequate waste management on land.",
            ["gesamp2019"],
        ),
        "behaviour": (
            "Size and shape both influence transport, degradation and impacts; "
            "buoyancy additionally depends on polymer density, which the image-based "
            "model cannot determine.",
            ["gesamp2019", "khatmullina2017"],
        ),
        "ecological": (
            "Ingestion of microplastics has been demonstrated in a range of marine "
            "organisms and may facilitate transfer of additives or hydrophobic "
            "pollutants to biota.",
            ["cole2011", "wright2013"],
        ),
        "human_health": (
            "No film-specific human-health effect has been established; human risk "
            "from microplastic exposure cannot currently be characterised with the "
            "available data.",
            ["who2022", "vethaak2021"],
        ),
        "uncertainty": (
            "Thin transparent films may have low optical contrast in microscopic "
            "images. Polymer type and parent product require chemical analysis "
            "(e.g. FTIR/Raman).",
            ["gesamp2019", "kappler2016"],
        ),
    },
    "Fragments": {
        "characteristics": (
            "Irregularly shaped, hard particles with the appearance of having been "
            "broken down from a larger piece of litter (GESAMP 'fragment' category; "
            "also described as granules or flakes).",
            ["gesamp2019"],
        ),
        "sources": (
            "Secondary microplastics resulting from weathering and fragmentation of "
            "larger plastic items, both during use and after loss to the "
            "environment.",
            ["gesamp2019", "cole2011"],
        ),
        "pathways": (
            "Fragmentation of plastic litter already in the environment, driven by "
            "UV radiation and mechanical abrasion (e.g. on exposed shorelines or at "
            "the sea surface), together with land-based and maritime inputs.",
            ["gesamp2019"],
        ),
        "behaviour": (
            "Fragmentation tends to increase the proportion of smaller particles over "
            "time; fragments retain the structural properties of the parent polymer. "
            "Reviewed field studies most often reported fragments as polyethylene and "
            "polypropylene, which is a literature observation, not a property of "
            "these detections.",
            ["gesamp2019", "hidalgoruz2012"],
        ),
        "ecological": (
            "Small particles may be ingested by low-trophic organisms; the "
            "bioavailability and physical impacts of microplastics depend on "
            "properties such as size and density.",
            ["wright2013", "cole2011"],
        ),
        "human_health": (
            "No fragment-specific human-health effect has been established. "
            "Microplastics differ in size, shape and chemistry and are best treated "
            "as a diverse contaminant suite rather than a single hazard.",
            ["rochman2019", "who2022"],
        ),
        "uncertainty": (
            "Irregular fragments can resemble mineral or biogenic particles; plastic "
            "identity and polymer type require spectroscopic confirmation.",
            ["gesamp2019", "hidalgoruz2012"],
        ),
    },
    "Pellets": {
        "characteristics": (
            "Hard particles with a spherical, smooth or granular shape (GESAMP "
            "'pellet' category; also called resin beads).",
            ["gesamp2019"],
        ),
        "sources": (
            "Plastic resin pellets are an important type of primary microplastic: an "
            "industrial raw material, typically in the 1-5 mm size range, used to "
            "transport polymer between manufacturing sites.",
            ["gesamp2019", "mato2001", "cole2011"],
        ),
        "pathways": (
            "Unintentional release to the environment during plastic manufacturing "
            "and transport.",
            ["mato2001"],
        ),
        "behaviour": (
            "Field and adsorption experiments showed that polypropylene resin pellets "
            "accumulate hydrophobic contaminants (PCBs, DDE) from ambient seawater; "
            "shape also affects settling behaviour.",
            ["mato2001", "khatmullina2017"],
        ),
        "ecological": (
            "Resin pellets are sometimes ingested by seabirds and other marine "
            "organisms, and their potential role as a transport medium for "
            "contaminants is an ecological concern.",
            ["mato2001", "cole2011"],
        ),
        "human_health": (
            "Contaminant sorption to pellets was measured in environmental samples; "
            "it does not demonstrate human exposure or harm. No pellet-specific "
            "human-health effect has been established.",
            ["mato2001", "who2022"],
        ),
        "uncertainty": (
            "The model's 'Pellets' class is assigned from image shape. Near-spherical "
            "particles (e.g. foams or natural grains) may appear similar, and "
            "industrial origin cannot be confirmed from an image. Pixel measurements "
            "in this report are not calibrated to physical size.",
            ["gesamp2019"],
        ),
    },
}


def get_profile(class_name: str) -> dict[str, tuple[str, list[str]]] | None:
    """Return the literature profile for a display class name, or None."""
    return MORPHOLOGY_PROFILES.get(class_name)


def _validate() -> None:
    """Fail fast at import if any statement cites an unknown reference key."""
    known = set(CITATION_NUMBERS)
    for _, _, keys in KEY_DISTINCTIONS:
        assert set(keys) <= known, keys
    for cls, profile in MORPHOLOGY_PROFILES.items():
        assert set(profile) == {k for k, _ in PROFILE_ATTRIBUTES}, cls
        for text, keys in profile.values():
            assert keys and set(keys) <= known, (cls, keys)


_validate()
