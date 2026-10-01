"""Pydantic models for SOP (Standard Operating Procedure) definitions."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Union, ForwardRef, List


class SOPCondition(BaseModel):
    """A single condition clause inside an SOP rule."""
    field: str
    operator: str  # eq, neq, gt, gte, lt, lte, in, not_in, contains, between
    value: Any


class SOPRule(BaseModel):
    """Top-level condition block — supports 'all' or 'any' combinators."""
    all: Optional[List[Any]] = None
    any: Optional[List[Any]] = None


class SOP(BaseModel):
    """A single Standard Operating Procedure."""
    id: str
    name: str
    category: str
    severity: str  # critical, high, moderate, low
    type: Optional[str] = "standard"  # standard | composite
    applies_when: SOPRule
    guidance: List[str]
    rationale: Optional[str] = ""
    priority: int = 50


class SOPMatch(BaseModel):
    """Result of matching a single SOP against facts."""
    sop: SOP
    matched: bool
    reason: str = ""
