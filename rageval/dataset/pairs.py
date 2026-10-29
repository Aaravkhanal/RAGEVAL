"""Paired control/conflict items: same question, added conflict document."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from rageval.core.schemas import BenchmarkItem


class PairedScenario(BaseModel):
    pair_id: str
    question: str
    control: Optional[BenchmarkItem] = None
    with_conflict: Optional[BenchmarkItem] = None
    items: List[BenchmarkItem] = Field(default_factory=list)

    def is_complete(self) -> bool:
        return self.control is not None and self.with_conflict is not None

    def same_question(self) -> bool:
        if self.control is None or self.with_conflict is None:
            return False
        return self.control.question.strip() == self.with_conflict.question.strip()


def _pair_id(item: BenchmarkItem) -> Optional[str]:
    return item.pair_id or item.metadata.get("pair_id")


def _pair_role(item: BenchmarkItem) -> Optional[str]:
    return item.pair_role or item.metadata.get("pair_role")


def group_paired_items(items: List[BenchmarkItem]) -> Dict[str, PairedScenario]:
    """Group items that share `pair_id` into control vs with_conflict roles."""
    grouped: Dict[str, PairedScenario] = {}
    for item in items:
        pid = _pair_id(item)
        if not pid:
            continue
        bundle = grouped.get(pid)
        if bundle is None:
            bundle = PairedScenario(pair_id=pid, question=item.question)
            grouped[pid] = bundle
        bundle.items.append(item)
        role = _pair_role(item)
        if role == "control":
            bundle.control = item
            bundle.question = item.question
        elif role in {"with_conflict", "conflict"}:
            bundle.with_conflict = item
    return grouped
