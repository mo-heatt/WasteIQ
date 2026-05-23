# WasteIQ Control Center

WasteIQ converts one open waste bunker into a software-defined 9-layer energy map, then recommends the safest balanced region-based furnace funnel feed for the next 2 hours.

> This is not autonomous crane control. It is human-in-the-loop decision support. Deterministic simulation calculates the mix, and AI explains the recommendation.

## Problem

Waste-to-energy plants receive trucks with different waste codes, weights and timestamps. Each waste code has a different calorific value, but the furnace needs a stable feed near **10 MJ/kg** and inside the **8-12 MJ/kg** safe operating band.

The bunker is one open pit. Rebuilding it into separate storage chambers would be expensive and unrealistic, so WasteIQ creates a virtual software map instead.

## What Changed: 3 Regions + 9 Layers

The earlier demo grouped material into LOW / MEDIUM / HIGH CV zones. The final version keeps the operator action simple but makes the data model smarter:

- **9 virtual waste-code layers**: internal energy intelligence for each known waste code.
- **LEFT / CENTER / RIGHT operational regions**: the crane operator's practical action surface.
- **Final funnel recipe is region-based**: the operator receives tonnes and percentages from LEFT, CENTER and RIGHT, not abstract waste-code quantities.

## How It Works

```text
Truck Intake -> Receiving Area -> Recommended unloading region
-> Virtual 9-layer bunker map -> Region composition update
-> Funnel optimizer -> 2-hour feed plan
-> Fuel Area -> AI explanation -> Operator approval
```

WasteIQ uses:

1. shipment waste code,
2. shipment weight,
3. timestamp,
4. recommended unloading region,
5. Challenge 1 bunker availability.

The virtual map estimates where each waste-code layer is expected inside the open bunker. It does not claim perfect physical sorting.

## Operational Flow

### Receiving Area

Incoming trucks are classified by waste code and calorific value. WasteIQ recommends an unloading region using Challenge 1 capacity data:

- CV < 10: prefer LEFT.
- 10 <= CV <= 13: prefer CENTER.
- CV > 13: prefer RIGHT.
- If the preferred region is above 85% fill or short on available mass, WasteIQ chooses the region with the highest available capacity and marks the assignment as a fallback.

The truck still unloads into one open bunker. LEFT, CENTER and RIGHT are guided operational regions, not walls or reconstructed storage chambers.

### Before / After Next Shipment

The app shows how the next truck changes the live operating plan:

1. current bunker state before the next shipment,
2. latest truck and recommended unloading region,
3. updated virtual 9-layer map after unloading,
4. old funnel recipe vs new funnel recipe,
5. how the 2-hour feed plan changed.

This proves WasteIQ updates dynamically as trucks keep arriving.

### Fuel Area

The Fuel Area turns the optimized region recipe into a furnace-ready blend:

- tonnes pulled from LEFT, CENTER and RIGHT,
- full waste-code composition inside the fuel mix,
- average CV,
- total mass,
- safe/unsafe status,
- 5 operator steps before release to furnace.

The final operator answer is region-based: for example, pull 13.0t from LEFT, 7.0t from CENTER and 0.0t from RIGHT over the next 2 hours.

## Challenge 1 Integration

Challenge 1 should write:

```text
data/challenge1_bunker_state.json
```

Expected shape:

```json
{
  "timestamp": "2025-09-04T10:00:00",
  "source": "challenge_1_bunker_image_model",
  "total_fill_percent": 64,
  "regions": [
    { "region_id": "LEFT", "fill_percent": 72, "available_mass_tonnes": 45 },
    { "region_id": "CENTER", "fill_percent": 58, "available_mass_tonnes": 60 },
    { "region_id": "RIGHT", "fill_percent": 40, "available_mass_tonnes": 32 }
  ]
}
```

If missing, WasteIQ uses clearly labeled **Demo Challenge 1 data**.

## Deterministic Engine vs AI

The LLM does not calculate the recipe.

Python code deterministically handles:

- shipment cleaning,
- waste-code-to-CV mapping,
- 9-layer map construction,
- LEFT/CENTER/RIGHT region average CV calculation,
- 2-hour funnel simulation,
- optimizer scoring,
- forecast and operator tonnes.

The optional AI layer only explains the deterministic result. If `OPENROUTER_API_KEY` is missing, fallback explanation text is used.

Agent Mode presents the explanation as an operator-facing sequence:

1. Reading latest truck data...
2. Updating virtual 9-layer bunker map...
3. Checking Challenge 1 capacity...
4. Calculating region average CV...
5. Testing 2-hour funnel recipes...
6. Comparing naive and optimized mix...
7. Preparing operator recommendation...

## Backend Endpoints

```text
GET  /api/health
GET  /api/dataset/summary
GET  /api/challenge1/state
GET  /api/layers
GET  /api/regions
GET  /api/truck-assignment/latest
POST /api/truck-assignment/simulate
GET  /api/dashboard
GET  /api/simulation/default
POST /api/simulate
GET  /api/optimizer/comparison
GET  /api/recommendation
GET  /api/operations/before-after
GET  /api/operations/fuel-area
GET  /api/demo/steps
GET  /api/impact
```

Manual region simulation:

```json
{
  "left_pct": 65,
  "center_pct": 25,
  "right_pct": 10,
  "feed_rate_tonnes_per_hour": 10,
  "duration_hours": 2
}
```

## Frontend Pages

- **Control Room**: current CV, Challenge 1 badge, latest truck assignment, region cards, recommended funnel feed, forecast and AI explanation.
- **Dataset**: shipments, tonnes, waste-code distribution and latest records.
- **Receiving Area**: latest and recent trucks, assigned unloading regions and movement status.
- **Challenge 1 Input**: real/demo badge and LEFT/CENTER/RIGHT fill and mass.
- **9-Layer Bunker Map**: waste-code layer cards with CV, estimated mass and preferred region.
- **Region Composition**: LEFT/CENTER/RIGHT average CV and layer composition.
- **Before / After Shipment**: current state, next truck, updated state and old vs new feed recipe.
- **Funnel Optimizer**: manual LEFT/CENTER/RIGHT 2-hour recipe testing plus naive equal region mix vs optimized region mix.
- **Fuel Area**: final fuel blend, full waste-code composition and furnace readiness.
- **Agent Mode**: deterministic recommendation explained in operator language.
- **Demo Mode**: guided judge story.
- **Impact**: target, safe band, optimized error and operator decision value.

## Judge Demo Flow

1. Open **Control Room**: “WasteIQ turns one open bunker into a 9-layer energy map and gives the next furnace recipe.”
2. Open **Receiving Area**: “The latest truck is classified and assigned to a guided unloading region.”
3. Open **Dataset**: “Shipment records provide weight, time and waste code.”
4. Open **Challenge 1 Input**: “Challenge 1 provides current LEFT/CENTER/RIGHT capacity.”
5. Open **9-Layer Bunker Map**: “We track each waste code as a virtual energy layer.”
6. Open **Region Composition**: “Each region gets an average CV from its layer composition.”
7. Open **Before / After Shipment**: “The plan updates when the next truck is unloaded.”
8. Open **Funnel Optimizer**: “Any region recipe can be tested, then compared against the optimized 2-hour plan.”
9. Open **Fuel Area**: “The recipe becomes a furnace-ready blend with full composition.”
10. Open **Agent Mode**: “AI explains the deterministic recommendation; it does not calculate it.”
11. Open **Demo Mode**: “Here is the complete story step by step.”
12. Open **Impact**: “This gives the operator a safe decision in under 10 seconds.”

## Run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Docker

```bash
docker compose up --build
```

## Data Files

Shipment data is read from:

1. `data/shipments.json`
2. fallback `public-files/shipments.json`
3. fallback generated demo shipments

Challenge 1 state is read from:

```text
data/challenge1_bunker_state.json
```

## Assumptions

- Target CV is 10 MJ/kg.
- Safe operating band is 8-12 MJ/kg.
- CV < 10 prefers LEFT.
- 10 <= CV <= 13 prefers CENTER.
- CV > 13 prefers RIGHT.
- Candidate region mixes are generated in 5% increments.
- Default horizon is 2 hours at 10 tonnes/hour.
- The 9-layer map is an estimated software model, not a claim of exact visual identification.

## Limitations

- No actual image processing is implemented here.
- No LiDAR processing, moisture, density, emissions, autonomous crane control, complex furnace physics or multi-agent orchestration.
- Region mapping should be refined when Challenge 1 provides richer spatial classification.
- The operator reviews and approves every action.
