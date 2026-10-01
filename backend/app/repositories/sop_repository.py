"""SOP repository — loads policies from YAML at startup."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import yaml

from app.models.sop import SOP, SOPRule, SOPCondition

logger = logging.getLogger(__name__)

# Default path to the policy file
_DEFAULT_POLICY_PATH = Path(__file__).resolve().parent.parent / "policies" / "sops.yaml"


def _parse_rule(raw: dict) -> SOPRule:
    """Recursively parse an applies_when block into SOPRule / SOPCondition."""
    all_items = raw.get("all")
    any_items = raw.get("any")

    def _parse_item(item: dict):
        # If item has 'all' or 'any', it is a nested SOPRule
        if "all" in item or "any" in item:
            return _parse_rule(item)
        # Otherwise it is a leaf SOPCondition
        return SOPCondition(**item)

    return SOPRule(
        all=[_parse_item(i) for i in all_items] if all_items else None,
        any=[_parse_item(i) for i in any_items] if any_items else None,
    )


class SOPRepository:
    """Loads and exposes SOPs from the YAML policy file.

    Policies are reloaded on every call to ``load()`` so that new SOPs
    can be added without modifying code — just restart the app.
    """

    def __init__(self, policy_path: Optional[str | Path] = None):
        self.policy_path = Path(policy_path) if policy_path else _DEFAULT_POLICY_PATH
        self._sops: list[SOP] = []

    def load(self) -> list[SOP]:
        """Parse the YAML file and return a list of SOP models."""
        if not self.policy_path.exists():
            logger.error("Policy file not found: %s", self.policy_path)
            return []

        with open(self.policy_path, "r", encoding="utf-8") as f:
            raw_list = yaml.safe_load(f)

        sops: list[SOP] = []
        for entry in raw_list:
            rule = _parse_rule(entry.get("applies_when", {}))
            sop = SOP(
                id=entry["id"],
                name=entry["name"],
                category=entry["category"],
                severity=entry["severity"],
                type=entry.get("type", "standard"),
                applies_when=rule,
                guidance=entry.get("guidance", []),
                rationale=entry.get("rationale", ""),
                priority=entry.get("priority", 50),
            )
            sops.append(sop)

        self._sops = sops
        logger.info("Loaded %d SOPs from %s", len(sops), self.policy_path)
        return sops

    def get_all(self) -> list[SOP]:
        """Return all loaded SOPs (call load() first)."""
        if not self._sops:
            self.load()
        return self._sops

    def get_by_id(self, sop_id: str) -> Optional[SOP]:
        """Look up a single SOP by its ID."""
        for sop in self.get_all():
            if sop.id == sop_id:
                return sop
        return None
