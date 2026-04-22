"""
World_Structural_Engine1.0.py

World-level fortune layer built on top of the S-World dynamics pattern
from WGL 3.32, fully decoupled from personal astro/bazi data, with an
optional structural interpretation channel (0–27 WLM layers).

Architecture
------------
    WorldState          : world-level state container (inputs + outputs)
    WorldStructuralState: WLM layer + tension annotation (optional)
    WGL_WorldEngine     : synthesises world_* fields from S/D/E fields
    WorldFortuneEngine  : world fortune indices (no structural channel)
    WorldFortuneEngineV2: world fortune indices + structural + astro/bazi hints

Quick start
-----------
    # Minimal (no structural channel):
    state = WorldState(s_density=1.2, d_stability=0.5, e_offset=0.1, ...)
    result = demo_world_tick(state)

    # With structural channel:
    w_struct = WorldStructuralState(layer=12, tension=0.4)
    result = demo_world_tick_v2(state, w_struct, astro_hint="Saturn rx")
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


# ============================================================
# WorldState — world-level state container
# ============================================================

@dataclass
class WorldState:
    """
    World-level state used by WGL_WorldEngine and both fortune engines.

    Inputs
    ------
    s_texture   : {coherence, turbulence, granularity, smoothness}
    s_density   : scalar in [0, +∞) — appearance density
    s_spectrum  : {R, G, B, Y, C, M, K} channel intensities in [0, 1]
    s_occlusion : scalar in [0, 1]
    d_stability : scalar — tension-dominant (+) vs compression-dominant (−)
    e_offset    : scalar — structural offset from baseline
    exposure    : {"score": float} — external pressure
    protection  : {"severity": float} — protection pressure

    Outputs  (populated by WGL_WorldEngine.tick)
    -------
    world_texture
    world_density
    world_event_matrix
    world_offset_field
    world_dynamics
    """

    # Inputs
    s_texture:   Optional[Dict[str, float]]       = field(default=None)
    s_density:   float                            = 0.0
    s_spectrum:  Optional[Dict[str, float]]       = field(default=None)
    s_occlusion: float                            = 0.0
    d_stability: float                            = 0.0
    e_offset:    float                            = 0.0
    exposure:    Optional[Dict[str, float]]       = field(default=None)
    protection:  Optional[Dict[str, float]]       = field(default=None)

    # Outputs
    world_texture:      Optional[Dict[str, float]]              = field(default=None)
    world_density:      float                                   = 0.0
    world_event_matrix: Optional[Dict[Tuple[str, str], float]]  = field(default=None)
    world_offset_field: float                                   = 0.0
    world_dynamics:     float                                   = 0.0


# ============================================================
# WorldStructuralState — WLM layer annotation (optional)
# ============================================================

@dataclass
class WorldStructuralState:
    """
    WLM structural classification layer.

    layer      : 0–27 structural layer (WLM ontology)
    tension    : normalised structural tension [0.0–1.0]
    confidence : optional confidence score for the classification
    """
    layer:      int
    tension:    float
    confidence: float = 1.0


# ============================================================
# WGL_WorldEngine — S-World synthesis
# ============================================================

class WGL_WorldEngine:
    """
    S-World Engine: synthesises world_* outputs from S/D/E/exposure/protection.

    S_KEYS = (R, G, B, Y, C, M, K)
    """

    S_KEYS: Tuple[str, ...] = ("R", "G", "B", "Y", "C", "M", "K")

    # ── World texture ─────────────────────────────────────────────────

    def compute_world_texture(self, state: WorldState) -> Dict[str, float]:
        """
        Fuse s_texture with protection severity and exposure score.

        turbulence_W = turbulence_S + 0.5 × severity + 0.3 × exposure_score
        All channels clamped to [0, 1].
        """
        tex  = state.s_texture  or {}
        prot = state.protection or {}
        expo = state.exposure   or {}

        turb_add = (
            prot.get("severity", 0.0) * 0.5 +
            expo.get("score",    0.0) * 0.3
        )

        return {
            "coherence":   min(1.0, tex.get("coherence",   0.0)),
            "turbulence":  min(1.0, tex.get("turbulence",  0.0) + turb_add),
            "granularity": min(1.0, tex.get("granularity", 0.0)),
            "smoothness":  min(1.0, tex.get("smoothness",  0.0)),
        }

    # ── World density ─────────────────────────────────────────────────

    def compute_world_density(self, state: WorldState) -> float:
        """
        ρ_W = s_density × (1 + S_D_clamped)

        High D-stability amplifies appearance density.
        """
        s_d = min(10.0, max(-10.0, state.d_stability))
        return max(0.0, state.s_density * (1.0 + max(0.0, s_d)))

    # ── World event matrix ────────────────────────────────────────────

    def compute_world_event_matrix(
        self, state: WorldState
    ) -> Dict[Tuple[str, str], float]:
        """
        7 × 7 interaction matrix: (ch_i, ch_j) → v_i × v_j

        Diagonal  : self-interaction (pure channel intensity)
        Off-diagonal: cross-channel coupling (structural interference)
        """
        spec = state.s_spectrum or {ch: 0.0 for ch in self.S_KEYS}
        return {
            (i, j): spec.get(i, 0.0) * spec.get(j, 0.0)
            for i in self.S_KEYS
            for j in self.S_KEYS
        }

    # ── World offset field ────────────────────────────────────────────

    def compute_world_offset_field(self, state: WorldState) -> float:
        """
        World offset = e_offset + exposure drift

        Exposure score contributes a positive drift: external structural
        pressure increases the world's offset from its 0-state baseline.
        """
        expo_drift = state.exposure.get("score", 0.0) * 0.3 if state.exposure else 0.0
        return state.e_offset + expo_drift

    # ── World dynamics ────────────────────────────────────────────────

    def compute_world_dynamics(
        self,
        texture:      Dict[str, float],
        density:      float,
        event_matrix: Dict[Tuple[str, str], float],
        offset_field: float,
    ) -> float:
        """
        dW/dt = γ·coherence + δ·density + η·ev_mean − λ·|offset_field|

          coherence    : structural order drives positive world dynamics
          density      : thick appearance sustains the world
          ev_mean      : mean event intensity (cross-channel activity)
          offset_field : large offsets drain world stability (−λ term)
        """
        coherence = texture.get("coherence", 0.0)
        ev_vals   = list(event_matrix.values())
        ev_mean   = (sum(ev_vals) / len(ev_vals)) if ev_vals else 0.0

        gamma, delta, eta, lam = 1.0, 0.5, 0.3, 0.8
        return (
            gamma * coherence +
            delta * density  +
            eta   * ev_mean  -
            lam   * abs(offset_field)
        )

    # ── Full world synthesis ──────────────────────────────────────────

    def tick(self, state: WorldState) -> WorldState:
        """Compute all world_* fields on the given WorldState and return it."""
        wt   = self.compute_world_texture(state)
        wd   = self.compute_world_density(state)
        wem  = self.compute_world_event_matrix(state)
        wof  = self.compute_world_offset_field(state)
        wdyn = self.compute_world_dynamics(wt, wd, wem, wof)

        state.world_texture      = wt
        state.world_density      = wd
        state.world_event_matrix = wem
        state.world_offset_field = wof
        state.world_dynamics     = wdyn
        return state


# ============================================================
# _FortuneBase — shared index computation logic
# ============================================================

class _FortuneBase:
    """
    Internal mixin that provides raw index computations.
    Both fortune engines call these, each optionally adding a
    structural-tension term on top.
    """

    @staticmethod
    def _ev_mean(state: WorldState) -> float:
        evm = state.world_event_matrix or {}
        vals = list(evm.values())
        return (sum(vals) / len(vals)) if vals else 0.0

    @staticmethod
    def _fortune_base(state: WorldState) -> float:
        dyn  = state.world_dynamics
        dens = state.world_density
        offs = state.world_offset_field
        return (
            dyn
            + 0.5 * math.tanh(dens / 3.0)
            - 0.7 * math.tanh(abs(offs))
        )

    @staticmethod
    def _risk_base(state: WorldState) -> float:
        dens = state.world_density
        offs = abs(state.world_offset_field)
        occ  = state.s_occlusion
        return max(0.0,
            0.4 * math.tanh(dens / 3.0) +
            0.4 * math.tanh(offs)       +
            0.4 * occ
        )

    @classmethod
    def _opportunity_base(cls, state: WorldState) -> float:
        dyn    = max(0.0, state.world_dynamics)
        ev_term = math.tanh(cls._ev_mean(state) * 5.0)
        return dyn + 0.5 * ev_term

    @classmethod
    def _liquidity_base(cls, state: WorldState) -> float:
        dens    = state.world_density
        occ     = state.s_occlusion
        ev_term = math.tanh(cls._ev_mean(state) * 5.0)
        return max(0.0,
            0.5 * math.exp(-dens) +
            0.3 * (1.0 - occ)    +
            0.4 * ev_term
        )

    @staticmethod
    def _trend_base(state: WorldState) -> float:
        return math.tanh(state.world_dynamics) - 0.3 * math.tanh(abs(state.world_offset_field))


# ============================================================
# WorldFortuneEngine — no structural channel (V1 API)
# ============================================================

class WorldFortuneEngine(_FortuneBase):
    """
    World fortune indices derived purely from world_* fields.

    Does not know about personal charts, bazi, or WLM layers.

    Indices (rough scale)
    ---------------------
    world_fortune_index     : overall favorable/unfavorable  (~−1 … +2)
    world_risk_index        : structural risk / instability  (0 … ~1.2)
    world_opportunity_index : positive dynamism              (0 … ~2)
    world_liquidity_index   : flow / openness                (0 … ~1.2)
    world_trend             : signed trend indicator         (−1.3 … +1)
    """

    def compute_fortune_index(self, state: WorldState) -> float:
        return self._fortune_base(state)

    def compute_risk_index(self, state: WorldState) -> float:
        return self._risk_base(state)

    def compute_opportunity_index(self, state: WorldState) -> float:
        return self._opportunity_base(state)

    def compute_liquidity_index(self, state: WorldState) -> float:
        return self._liquidity_base(state)

    def compute_trend(self, state: WorldState) -> float:
        return self._trend_base(state)

    def compute_all(self, state: WorldState) -> Dict[str, float]:
        return {
            "world_fortune_index":     self.compute_fortune_index(state),
            "world_risk_index":        self.compute_risk_index(state),
            "world_opportunity_index": self.compute_opportunity_index(state),
            "world_liquidity_index":   self.compute_liquidity_index(state),
            "world_trend":             self.compute_trend(state),
        }


# ============================================================
# WorldFortuneEngineV2 — structural + astro/bazi channels
# ============================================================

class WorldFortuneEngineV2(_FortuneBase):
    """
    Extended fortune engine with WLM structural interpretation and
    optional astro/bazi hint pass-through.

    Structural tension modulates every index:
      - fortune   : +0.3 × tension  (higher tension → more structural activation)
      - risk      : +0.4 × tension  (higher tension → more risk)
      - opportunity: −0.2 × tension (higher tension → less free opportunity)
      - liquidity : −0.2 × tension  (higher tension → less flow)
      - trend     : −0.2 × tension  (higher tension → dampened trend)

    Astro/bazi hints are passed through as metadata only — no numeric
    computation is performed here; that belongs to dedicated sub-engines.
    """

    def compute_fortune_index(self, state: WorldState, w_struct: WorldStructuralState) -> float:
        return self._fortune_base(state) + 0.3 * w_struct.tension

    def compute_risk_index(self, state: WorldState, w_struct: WorldStructuralState) -> float:
        base = max(0.0,
            0.3 * math.tanh(state.world_density / 3.0) +
            0.3 * math.tanh(abs(state.world_offset_field)) +
            0.3 * state.s_occlusion
        )
        return max(0.0, base + 0.4 * w_struct.tension)

    def compute_opportunity_index(self, state: WorldState, w_struct: WorldStructuralState) -> float:
        return self._opportunity_base(state) + 0.2 * (1.0 - w_struct.tension)

    def compute_liquidity_index(self, state: WorldState, w_struct: WorldStructuralState) -> float:
        return max(0.0, self._liquidity_base(state) - 0.2 * w_struct.tension)

    def compute_trend(self, state: WorldState, w_struct: WorldStructuralState) -> float:
        return self._trend_base(state) - 0.2 * w_struct.tension

    def compute_all(
        self,
        state: WorldState,
        w_struct: WorldStructuralState,
        astro_hint: Optional[str] = None,
        bazi_hint:  Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "fortune_index":      self.compute_fortune_index(state, w_struct),
            "risk_index":         self.compute_risk_index(state, w_struct),
            "opportunity_index":  self.compute_opportunity_index(state, w_struct),
            "liquidity_index":    self.compute_liquidity_index(state, w_struct),
            "trend":              self.compute_trend(state, w_struct),
            "structural_layer":   w_struct.layer,
            "structural_tension": w_struct.tension,
            "astro_hint":         astro_hint,
            "bazi_hint":          bazi_hint,
        }


# ============================================================
# Convenience builders and demo entries
# ============================================================

def build_world_engine() -> WGL_WorldEngine:
    """One-call builder for a standalone world engine."""
    return WGL_WorldEngine()


def demo_world_tick(initial_state: WorldState) -> Dict[str, Any]:
    """
    Run WGL_WorldEngine + WorldFortuneEngine (V1) on a given WorldState.
    Returns the updated state and fortune indices.
    """
    state   = build_world_engine().tick(initial_state)
    indices = WorldFortuneEngine().compute_all(state)
    return {"state": state, "indices": indices}


def demo_world_tick_v2(
    initial_state: WorldState,
    w_struct:      WorldStructuralState,
    astro_hint:    Optional[str] = None,
    bazi_hint:     Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run WGL_WorldEngine + WorldFortuneEngineV2 on a given WorldState.
    Returns the updated state and extended fortune indices.
    """
    state   = build_world_engine().tick(initial_state)
    indices = WorldFortuneEngineV2().compute_all(state, w_struct, astro_hint, bazi_hint)
    return {"state": state, "indices": indices}
