# World Structural Fortune Engine (WSFE) — Version 1.1

A modular, world‑scale structural interpretation engine built on top of:

- **S‑World Dynamics** (from WGL 3.x)
- **0–27 WLM Structural Layer Mapping** (classification only)
- **Astro/Bazi Time Hints** (LLM‑supplied, not computed in code)
- **World Fortune Indices** (fortune, risk, opportunity, liquidity, trend)

This engine provides a unified framework for interpreting world‑level states through structural, dynamical, and contextual lenses without exposing any generative or higher‑order layers.

---

## 1. Overview

The World Structural Fortune Engine (WSFE) transforms a world snapshot into:

- **World dynamics** (S‑World)
- **Structural layer (0–27)** (WLM classification)
- **Structural tension**
- **Astro/Bazi contextual hints**
- **Fortune indices** (fortune, risk, opportunity, liquidity, trend)

This system is **interpretive**, not predictive.  
It does **not** generate events or simulate worldlines.  
It provides a structured, multi‑layered view of world conditions.

---

## 2. Architecture

WSFE consists of four layers:

### **Layer 1 — S‑World Engine (WGL_WorldEngine)**
Computes world‑level appearance fields:

- `world_texture`
- `world_density`
- `world_event_matrix`
- `world_offset_field`
- `world_dynamics`

### **Layer 2 — WLM Structural Mapper (0–27)**
Maps world_* fields into:

- `structural_layer` (0–27)
- `structural_tension` (0.0–1.0)
- `confidence` (optional)

This is a **classification layer**, not a generative layer.

### **Layer 3 — Time Context Layer (Astro/Bazi Hints)**
Optional LLM‑supplied hints:

- `astro_hint`
- `bazi_hint`

These are **not computed in code**.  
They act as contextual metadata.

### **Layer 4 — WorldFortuneEngineV2**
Produces world‑level indices:

- `fortune_index`
- `risk_index`
- `opportunity_index`
- `liquidity_index`
- `trend`

Plus structural metadata:

- `structural_layer`
- `structural_tension`
- `astro_hint`
- `bazi_hint`

---

## 3. Data Structures

### **WorldState**
Holds S‑World inputs and outputs.

### **WorldStructuralState**
```python
@dataclass
class WorldStructuralState:
    layer: int                 # 0–27 structural layer
    tension: float             # normalized tension [0.0–1.0]
    confidence: float = 1.0
```

---

## 4. WorldFortuneEngineV2 API

### **Function Signature**
```python
def compute_all(
    self,
    state: WorldState,
    w_struct: WorldStructuralState,
    astro_hint: Optional[str] = None,
    bazi_hint: Optional[str] = None,
) -> Dict[str, Any]:
```

### **Outputs**
```json
{
  "fortune_index": float,
  "risk_index": float,
  "opportunity_index": float,
  "liquidity_index": float,
  "trend": float,
  "structural_layer": int,
  "structural_tension": float,
  "astro_hint": "optional string",
  "bazi_hint": "optional string"
}
```

---

## 5. Example Pipeline

```python
world_engine   = WGL_WorldEngine()
fortune_engine = WorldFortuneEngineV2()
layer_mapper   = WLM_LayerMapper()

state = world_engine.tick(initial_state)
w_struct = layer_mapper.map(state)

indices = fortune_engine.compute_all(
    state,
    w_struct,
    astro_hint="compression window",
    bazi_hint="metal-over-wood"
)
```

---

## 6. What This Engine Is *Not*

- Not a divination system  
- Not a worldline generator  
- Not a predictive oracle  
- Not a simulation of future events  


WSFE is a **structural interpreter**, not a generative model.

---

## 7. Versioning

- **1.0** — Base S‑World + fortune indices  
- **1.1** — Added 0–27 WLM structural layer + tension + astro/bazi hints  

---

## 8. License

MIT License (or your preferred license)

---

## 9. Notes

This engine is designed for:

- structural analysis  
- world‑state interpretation  
- research  
- modeling  
- narrative systems  
- AI‑assisted reasoning  

It is intentionally modular and safe, exposing no generative or higher‑order structural layers.

