"""Concrete Corporate History contract validator."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from validator_common import BaseValidator

from .content import ContentIntegrationMixin
from .lifecycle import LifecycleMixin
from .model import TITLE, IndependentSubsystemConfig, ModeGraphResult
from .parsing import ParsingMixin
from .scheduler import SchedulerMixin


class Validator(
    ParsingMixin,
    SchedulerMixin,
    LifecycleMixin,
    ContentIntegrationMixin,
    BaseValidator,
):
    TITLE = TITLE
    STAGED_EXTENSIONS = [".txt", ".json", ".yml"]

    def __init__(self, mod_path: str, **kwargs):
        super().__init__(mod_path, **kwargs)
        self._root = Path(self.mod_path)
        self._manifest_path = self._root / "tools" / "corporate_history_contract.json"
        self._manifest_payload: Dict[str, object] = {}
        self._independent_subsystems: Tuple[IndependentSubsystemConfig, ...] = ()
        self._effect_call_parents_cache: Optional[Dict[str, Set[str]]] = None
        self._effect_call_children_cache: Optional[Dict[str, List[str]]] = None
        self._on_action_effect_calls_cache: Optional[
            Dict[str, List[Tuple[str, int, int]]]
        ] = None
        self._independent_mode_graph_cache: Dict[
            Tuple[int, FrozenSet[str], bool], ModeGraphResult
        ] = {}

    def run_validations(self):
        self._log_section("loading manifest")
        chains = self._load_manifest()
        if not chains:
            return
        chain_by_namespace = {chain.namespace: chain for chain in chains}
        chain_by_root = {chain.root: chain for chain in chains}

        self._log_section("indexing corporate history")
        effect_defs = self._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
        self._effect_call_parents_cache = self._effect_call_parents(effect_defs)
        self._effect_call_children_cache = self._effect_call_children(effect_defs)
        event_defs = self._load_events()
        idea_defs = self._load_idea_definitions(chains, event_defs)
        core_namespaces = self._discover_core_namespaces(
            effect_defs.get("corporate_history_on_startup", []),
            effect_defs,
        )
        independent_namespaces = {
            namespace
            for subsystem in self._independent_subsystems
            for namespace in subsystem.namespaces
        }
        core_namespaces.difference_update(independent_namespaces)
        call_sites = self._load_event_call_sites(
            event_defs, effect_defs, core_namespaces
        )
        mode_defs = self._load_top_level_blocks(
            [
                "common/game_rules/00_game_rules.txt",
                "common/scripted_triggers/MD_corporate_history_triggers.txt",
            ]
        )

        self._log_section("mode contract")
        self._report(
            self._validate_mode_contract(mode_defs),
            "Corporate-history game-rule modes are exact",
            "Corporate-history game-rule mode issues:",
            category="Corporate-history mode contract",
        )

        self._log_section("independent subsystems")
        self._report(
            self._validate_independent_subsystems(
                self._independent_subsystems, chains, effect_defs, event_defs
            ),
            "Independent subsystem ownership and mode paths are coherent",
            "Independent subsystem contract issues:",
            category="Corporate-history independent subsystems",
        )

        self._log_section("manifest coverage")
        self._report(
            self._validate_manifest_coverage(
                chains, core_namespaces, chain_by_namespace
            ),
            "Corporate-history manifest covers current namespaces",
            "Corporate-history manifest coverage issues:",
            category="Corporate-history manifest",
        )
        self._report(
            self._validate_lifecycle_metadata(
                chains, effect_defs, event_defs, call_sites
            ),
            "Corporate-history lifecycle metadata matches scripted behavior",
            "Corporate-history lifecycle metadata issues:",
            category="Corporate-history manifest",
        )

        self._log_section("reusable decision lifecycles")
        self._report(
            self._validate_reusable_decision_lifecycles(effect_defs),
            "Reusable corporate and computing decision lifecycles are coherent",
            "Reusable corporate and computing decision lifecycle issues:",
            category="Corporate-history reusable decision lifecycles",
        )

        self._log_section("event reachability")
        self._report(
            self._validate_event_reachability(
                chains, event_defs, call_sites, effect_defs
            ),
            "Corporate-history event reachability is intact",
            "Corporate-history event reachability issues:",
            category="Corporate-history event reachability",
        )

        self._log_section("core-chain mode paths")
        self._report(
            self._validate_core_chain_mode_paths(
                chains, effect_defs, event_defs, call_sites
            ),
            "Core-chain events and reconstruction obey the mode contract",
            "Corporate-history core-chain mode issues:",
            category="Corporate-history core-chain modes",
        )

        self._log_section("corporate-history host architecture")
        self._report(
            self._validate_oem_startup_architecture(
                effect_defs, event_defs, call_sites
            ),
            "Corporate-history host architecture is intact",
            "Corporate-history host architecture issues:",
            category="OEM startup architecture",
        )

        self._log_section("dispatcher integrity")
        self._report(
            self._validate_dispatchers(chains, effect_defs, event_defs, call_sites),
            "Corporate-history dispatchers are intact",
            "Corporate-history dispatcher issues:",
            category="Corporate-history dispatcher integrity",
        )

        self._log_section("tier-1 contract")
        self._report(
            self._validate_tier_one_contract(
                chains, effect_defs, event_defs, idea_defs
            ),
            "Tier-1 chains satisfy the framework contract",
            "Tier-1 corporate-history contract issues:",
            category="Corporate-history Tier-1 contract",
        )

        self._log_section("clamp coverage")
        self._report(
            self._validate_clamp_coverage(chains, event_defs, effect_defs),
            "Bounded variables clamp correctly",
            "Corporate-history clamp coverage issues:",
            category="Corporate-history clamp coverage",
        )

        self._log_section("reconstruction safety")
        self._report(
            self._validate_reconstruction_safety(chains, effect_defs, event_defs),
            "Reconstruction effects are safe",
            "Corporate-history reconstruction issues:",
            category="Corporate-history reconstruction safety",
        )

        self._log_section("completion markers")
        self._report(
            self._validate_completion_markers(chains, effect_defs),
            "Reconstruction-complete markers have valid ownership",
            "Corporate-history completion-marker issues:",
            category="Corporate-history completion markers",
        )

        self._log_section("cross-chain ownership")
        self._report(
            self._validate_cross_chain_ownership(
                chains, chain_by_root, event_defs, effect_defs
            ),
            "Cross-chain ownership stays within the declared contract",
            "Corporate-history cross-chain ownership issues:",
            category="Corporate-history cross-chain ownership",
        )

        self._log_section("localisation contract")
        self._report(
            self._validate_localisation_contract(chains, event_defs),
            "Corporate-history English localisation is complete",
            "Corporate-history English localisation issues:",
            category="Corporate-history localisation contract",
        )

        self._log_section("economic bridge")
        self._report(
            self._validate_economic_bridge(chains, event_defs, effect_defs),
            "Corporate-history economic bridge is coherent",
            "Corporate-history economic bridge issues:",
            category="Corporate-history economic bridge",
        )

        self._log_section("real-options economic layer")
        self._report(
            self._validate_economic_layers(effect_defs, chains),
            "Corporate-history real-options economic layers are coherent",
            "Corporate-history real-options economic-layer issues:",
            category="Corporate-history real-options economic layer",
        )

        self._log_section("shared systems")
        self._report(
            self._validate_shared_systems(effect_defs, event_defs),
            "Shared-system contracts are coherent",
            "Shared-system contract issues:",
            category="Shared-system contract",
        )
