#!/usr/bin/env python3
"""Build the PULL THE SOURCE dataset (synthetic, fictional products).

Writes public scenario files (shown to the model) and SEPARATE answer keys.
Source roles (never shown to the model):
  E   sole support for requirement a   (withdrawing it -> Insufficient evidence)
  D1,D2 independent supports for requirement b (withdrawing one -> still Supported)
  K   sole support for requirement c   (never withdrawn in evaluation)
  I   irrelevant to every requirement  (withdrawing it -> still Supported)
  N   near-miss: on the topic of requirement a but does not establish it
      (other model, or vague claim) -- a lure, supports nothing
  X   (practice only) explicitly contradicts requirement a
Requirement order and source order are shuffled with a fixed seed so that
position / ID carries no information about role.
"""
import json, random, hashlib, os

SEED = 20261115
HERE = os.path.dirname(os.path.abspath(__file__))

def S(id, buyer, product, a, b, c, E, D1, D2, K, I, N, **extra):
    d = dict(id=id, buyer=buyer, product=product, reqs=dict(a=a, b=b, c=c),
             src=dict(E=E, D1=D1, D2=D2, K=K, I=I, N=N))
    d.update(extra)
    return d

EVAL = [
 S("E01", "Mira", "Brevo K2 kettle",
   "It must be no taller than 22 cm.", "It must boil 1 litre of water in under 4 minutes.", "It must switch off automatically when the water boils.",
   "Manufacturer specification sheet: the Brevo K2 is 19 cm tall including the lid.",
   "Lab test report: the Brevo K2 boiled 1 litre of water in 3 minutes 10 seconds.",
   "Magazine review: we timed the Brevo K2 at 3 minutes 25 seconds to boil 1 litre.",
   "User manual: the Brevo K2 switches off automatically once the water reaches a boil.",
   "Retailer listing: the Brevo K2 is sold in sage green and charcoal.",
   "Manufacturer specification sheet: the larger Brevo K3 is 21 cm tall including the lid."),
 S("E02", "Jonah", "Tarn 28 backpack",
   "It must fit a 16-inch laptop.", "It must weigh under 1.2 kg.", "It must include a rain cover.",
   "Retailer measurement: the Tarn 28 laptop sleeve accepts laptops up to 16.2 inches.",
   "Retailer listing: the Tarn 28 weighed 1.05 kg on the shop scale.",
   "Independent review: our Tarn 28 sample weighed 1.08 kg.",
   "Packing list: every Tarn 28 ships with a detachable rain cover.",
   "Product page: the Tarn 28 sternum strap has a built-in whistle.",
   "Brand advertisement: the Tarn 28 is described as 'laptop-friendly'."),
 S("E03", "Priya", "Lumet Arc desk lamp",
   "It must have a USB-C charging port.", "Its colour temperature must be adjustable down to 2700 K.", "Its arm must reach at least 40 cm.",
   "Product page: the base of the Lumet Arc has one USB-C charging port (15 W).",
   "Specification sheet: the Lumet Arc colour temperature adjusts from 2700 K to 6000 K.",
   "Independent review: we measured the Lumet Arc at 2700 K on its warmest setting.",
   "Specification sheet: the Lumet Arc arm extends to 46 cm.",
   "Warranty card: the Lumet Arc carries a two-year warranty.",
   "Product page: the Lumet Arc Pro has two USB-C charging ports."),
 S("E04", "Sam", "Corvin U9 bike lock",
   "It must weigh under 1.5 kg.", "Its shackle must fit around a frame tube 5 cm wide.", "It must include a frame mount.",
   "Specification sheet: the Corvin U9 weighs 1.3 kg.",
   "Specification sheet: the Corvin U9 shackle has an internal width of 9 cm.",
   "Independent review: the Corvin U9 closed around a 6 cm frame tube with room to spare.",
   "Box contents list: the Corvin U9 comes with a frame mount.",
   "Product page: the Corvin U9 is supplied with three keys.",
   "Forum post: one rider calls the Corvin U9 'not too heavy'."),
 S("E05", "Aiko", "Halden 2 tent",
   "Its floor must be at least 128 cm wide.", "Its packed weight must be under 2.5 kg.", "It must have two doors.",
   "Specification sheet: the Halden 2 floor is 132 cm wide.",
   "Specification sheet: the Halden 2 has a packed weight of 2.2 kg.",
   "Independent review: our packed Halden 2 weighed 2.3 kg.",
   "Product page: the Halden 2 has two doors, one on each side.",
   "Retailer listing: the Halden 2 stuff sack is orange.",
   "Specification sheet: the Halden 3 floor is 180 cm wide."),
 S("E06", "Leo", "Sonvia H40 headphones",
   "They must work with a wired 3.5 mm connection.", "Battery life must be at least 30 hours.", "They must fold for travel.",
   "Box contents list: the Sonvia H40 includes a 3.5 mm audio cable and has a 3.5 mm jack on the left ear cup.",
   "Lab test report: the Sonvia H40 played for 38 hours on one charge.",
   "Independent review: the Sonvia H40 lasted 35 hours in our battery test.",
   "Product page: the Sonvia H40 ear cups fold flat into the headband.",
   "App store listing: the Sonvia companion app has an equaliser.",
   "Archived product page: the earlier Sonvia H30 had a 3.5 mm jack."),
 S("E07", "Dana", "Pulso 600 blender",
   "Its jar must be dishwasher-safe.", "Its jar must hold at least 1.5 litres.", "It must be quieter than 90 dB at top speed.",
   "User manual: the Pulso 600 jar and lid are dishwasher-safe on the top rack.",
   "Specification sheet: the Pulso 600 jar capacity is 1.75 litres.",
   "Independent review: we filled the Pulso 600 jar with 1.7 litres up to the maximum line.",
   "Lab test report: the Pulso 600 measured 86 dB at top speed.",
   "Product page: the Pulso 600 power cord is 1 metre long.",
   "Brand advertisement: the Pulso 600 is described as 'easy to clean'."),
 S("E08", "Felix", "Marlo Cabin 55 suitcase",
   "Its external size must be within 55 x 40 x 20 cm including wheels.", "It must weigh under 3 kg.", "It must have a built-in combination lock.",
   "Retailer measurement: the Marlo Cabin 55 measures 54 x 38 x 20 cm including wheels and handles.",
   "Specification sheet: the Marlo Cabin 55 weighs 2.6 kg.",
   "Independent review: our Marlo Cabin 55 weighed 2.7 kg empty.",
   "Product page: the Marlo Cabin 55 has a built-in three-digit combination lock.",
   "Retailer listing: the Marlo Cabin 55 lining has a striped pattern.",
   "Retailer measurement: the Marlo Cabin 50 measures 50 x 35 x 20 cm including wheels."),
 S("E09", "Ines", "Mola G1 coffee grinder",
   "It must grind fine enough for espresso.", "Its hopper must hold at least 200 g of beans.", "It must have a grind timer.",
   "Lab test report: at setting 3 the Mola G1 produced an espresso-fine grind that pulled a standard espresso shot.",
   "Specification sheet: the Mola G1 hopper holds 250 g of beans.",
   "Independent review: we loaded 240 g of beans into the Mola G1 hopper.",
   "User manual: the Mola G1 has a grind timer adjustable from 5 to 60 seconds.",
   "Retailer listing: the Mola G1 is available in matte white.",
   "Packaging text: the Mola G1 box says 'for every brew style'."),
 S("E10", "Omar", "Pacer V3 running watch",
   "It must be water resistant to at least 50 m.", "Its battery must last at least 20 hours in GPS mode.", "It must have built-in GPS.",
   "Specification sheet: the Pacer V3 is rated water resistant to 50 m (5 ATM).",
   "Lab test report: the Pacer V3 ran for 26 hours in GPS mode.",
   "Independent review: the Pacer V3 lasted 24 hours with GPS on.",
   "Product page: the Pacer V3 has a built-in GPS receiver and does not need a phone.",
   "Retailer listing: the Pacer V3 strap comes in three colours.",
   "Product page: the separate Pacer V3 Dive model is rated water resistant to 100 m."),
 S("E11", "Ruth", "Sedda Flex office chair",
   "It must be rated for a user weight of at least 120 kg.", "Its seat must adjust down to 42 cm or lower.", "It must have adjustable armrests.",
   "Certification document: the Sedda Flex is certified for a user weight of 136 kg.",
   "Specification sheet: the Sedda Flex seat height range is 40 to 52 cm.",
   "Independent review: we measured the lowest Sedda Flex seat height at 41 cm.",
   "Product page: the Sedda Flex armrests adjust in height and width.",
   "Retailer listing: the Sedda Flex ships in a single box.",
   "Customer comment: 'the Sedda Flex feels sturdy'."),
 S("E12", "Tomas", "Calda Mini space heater",
   "It must switch off automatically if tipped over.", "It must draw no more than 1500 W.", "It must have an adjustable thermostat.",
   "User manual: the Calda Mini switches off automatically if it is tipped over.",
   "Specification sheet: the Calda Mini is rated at 1200 W on its highest setting.",
   "Independent review: our power meter read 1180 W with the Calda Mini on high.",
   "Product page: the Calda Mini has an adjustable thermostat dial.",
   "Retailer listing: the Calda Mini has a carry handle on the back.",
   "Product page: the Calda Tower has tip-over protection."),
]

PRACTICE = [
 S("P01", "Nell", "Riva 750 water bottle",
   "It must be leak-proof.", "It must hold at least 700 ml.", "It must fit a standard 7.5 cm cup holder.",
   "Lab test report: the Riva 750 did not leak when shaken upside down for ten minutes.",
   "Specification sheet: the Riva 750 holds 750 ml.",
   "Independent review: we poured 740 ml into the Riva 750.",
   "Retailer test: the Riva 750 fits a standard 7.5 cm cup holder.",
   "Retailer listing: the Riva 750 comes in four colours.",
   "Brand advertisement: the Riva 750 is 'made for life on the go'."),
 # initially Insufficient evidence: no source establishes requirement a
 S("P02", "Kofi", "Estra 10 tablet stand",
   "It must hold a tablet in portrait orientation.", "It must weigh under 400 g.", "It must fold flat.",
   None,
   "Specification sheet: the Estra 10 weighs 310 g.",
   "Independent review: our Estra 10 weighed 320 g.",
   "Product page: the Estra 10 folds flat to 1 cm thick.",
   "Retailer listing: the Estra 10 is sold in silver.",
   "Product page: the Estra 12 holds tablets in portrait and landscape.",
   kind="insufficient"),
 # initially Contradicted: source X explicitly shows requirement a is not met
 S("P03", "Lena", "Vento S desk fan",
   "It must be quieter than 40 dB on its lowest setting.", "It must oscillate.", "It must have a timer.",
   None,
   "Product page: the Vento S oscillates through 90 degrees.",
   "Independent review: the Vento S swept side to side in our test.",
   "User manual: the Vento S has a timer of up to 8 hours.",
   "Retailer listing: the Vento S cable is 1.5 metres long.",
   "Brand advertisement: the Vento S is 'whisper quiet'.",
   kind="contradicted",
   X="Lab test report: the Vento S measured 47 dB on its lowest setting."),
]

def build(sc, idx):
    rng = random.Random(SEED + idx * 101 + (0 if sc["id"].startswith("E") else 5000))
    rkeys = ["a", "b", "c"]; rng.shuffle(rkeys)
    rid = {k: f"R{i+1}" for i, k in enumerate(rkeys)}
    roles = [r for r in ["E", "D1", "D2", "K", "I", "N", "X"] if sc["src"].get(r) or (r == "X" and sc.get("X"))]
    texts = dict(sc["src"]);
    if sc.get("X"): texts["X"] = sc["X"]
    rng.shuffle(roles)
    sid = {r: f"S{i+1}" for i, r in enumerate(roles)}
    supports = {"E": "a", "D1": "b", "D2": "b", "K": "c"}
    public = dict(
        id=sc["id"], buyer=sc["buyer"], product=sc["product"],
        recommendation=f"{sc['buyer']} should buy the {sc['product']}.",
        requirements=[dict(id=rid[k], text=sc["reqs"][k]) for k in rkeys],
        sources=[dict(id=sid[r], text=texts[r]) for r in roles],
    )
    key_sources = {sid[r]: dict(role=r,
                                supports=rid[supports[r]] if r in supports else None,
                                contradicts=rid["a"] if r == "X" else None) for r in roles}
    kind = sc.get("kind", "standard")
    if kind == "standard":
        br = [("essential", "E"), ("irrelevant", "I"), ("redundant", rng.choice(["D1", "D2"]))]
    elif kind == "insufficient":
        br = [("irrelevant", "I")]
    else:
        br = [("irrelevant", "I"), ("contradiction_withdrawn", "X")]
    rng.shuffle(br)
    letters = "XYZ"
    branches_pub, branches_key = [], {}
    all_ids = [s["id"] for s in public["sources"]]
    for i, (btype, role) in enumerate(br):
        b = letters[i]
        branches_pub.append(dict(branch=b, withdraw=sid[role]))
        valid = [s for s in all_ids if s != sid[role]]
        branches_key[b] = dict(type=btype, withdraw=sid[role], gold=gold_label(public, key_sources, valid))
    public["branches"] = branches_pub
    key = dict(id=sc["id"], kind=kind, sources=key_sources,
               initial_gold=gold_label(public, key_sources, all_ids), branches=branches_key)
    return public, key

def gold_label(public, key_sources, valid):
    """The single frozen decision rule (mirrors task rule 3)."""
    if any(key_sources[s]["contradicts"] for s in valid):
        return "Contradicted"
    for r in public["requirements"]:
        if not any(key_sources[s]["supports"] == r["id"] for s in valid):
            return "Insufficient evidence"
    return "Supported"

def main():
    os.makedirs(f"{HERE}/data", exist_ok=True); os.makedirs(f"{HERE}/keys", exist_ok=True)
    for name, scs in [("eval", EVAL), ("practice", PRACTICE)]:
        pubs, keys = [], []
        for i, sc in enumerate(scs):
            p, k = build(sc, i); pubs.append(p); keys.append(k)
        json.dump(pubs, open(f"{HERE}/data/{name}_scenarios.json", "w"), indent=1)
        json.dump(keys, open(f"{HERE}/keys/{name}_keys.json", "w"), indent=1)
        print(name, len(pubs), "scenarios")
        for k in keys:
            print(" ", k["id"], k["initial_gold"], {b: (v["type"][:5], v["withdraw"], v["gold"][:4]) for b, v in k["branches"].items()})

if __name__ == "__main__":
    main()
