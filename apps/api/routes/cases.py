from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.orchestrator.engine import orchestrator
from core.registry.cases import case_registry
from core.state_machine.guards import InvalidTransitionError

router = APIRouter()


class CreateCaseRequest(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    priority: str = "normal"
    submitted_by: str = "imperial_user"


class RepairOrderRequest(BaseModel):
    strategy: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    scope: Optional[str] = None


class ReasonRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class SummaryRequest(BaseModel):
    summary: str = Field(..., min_length=1)


def _raise_case_error(exc: Exception) -> None:
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail="Case not found") from exc
    if isinstance(exc, InvalidTransitionError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise exc


def _get_case_or_404(case_id: str) -> dict:
    case = case_registry.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/cases")
def list_cases() -> dict:
    return {"items": case_registry.list_cases()}


@router.post("/cases")
def create_case(payload: CreateCaseRequest) -> dict:
    return case_registry.create_case(
        title=payload.title,
        content=payload.content,
        priority=payload.priority,
        submitted_by=payload.submitted_by,
    )


@router.post("/cases/{case_id}/accept")
def accept_case(case_id: str) -> dict:
    try:
        orchestrator.accept_case(case_id)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/submit-for-approval")
def submit_for_approval(case_id: str) -> dict:
    try:
        orchestrator.submit_for_approval(case_id)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/approve")
def approve_case(case_id: str) -> dict:
    try:
        orchestrator.approve_case(case_id)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/reject")
def reject_case(case_id: str, payload: ReasonRequest) -> dict:
    try:
        orchestrator.reject_case(case_id, reason=payload.reason)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/repair-pending")
def mark_repair_pending(case_id: str, payload: ReasonRequest) -> dict:
    try:
        orchestrator.mark_repair_pending(case_id, reason=payload.reason)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/rework")
def rework_case(case_id: str, payload: ReasonRequest) -> dict:
    try:
        orchestrator.request_rework(case_id, reason=payload.reason)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.get("/cases/{case_id}")
def get_case(case_id: str) -> dict:
    return _get_case_or_404(case_id)


@router.get("/cases/{case_id}/timeline")
def get_timeline(case_id: str) -> dict:
    _get_case_or_404(case_id)
    return {"case_id": case_id, "timeline": case_registry.get_timeline(case_id)}


@router.post("/cases/{case_id}/pause")
def pause_case(case_id: str) -> dict:
    try:
        orchestrator.pause_case(case_id)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/resume")
def resume_case(case_id: str) -> dict:
    try:
        orchestrator.resume_case(case_id)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/freeze")
def freeze_case(case_id: str) -> dict:
    try:
        orchestrator.freeze_case(case_id)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/cancel")
def cancel_case(case_id: str) -> dict:
    try:
        orchestrator.cancel_case(case_id)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/repair-order")
def repair_order(case_id: str, payload: RepairOrderRequest) -> dict:
    try:
        orchestrator.authorize_repair(
            case_id=case_id,
            strategy=payload.strategy,
            reason=payload.reason,
            scope=payload.scope,
        )
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/rerun")
def rerun_case(case_id: str, payload: ReasonRequest) -> dict:
    try:
        orchestrator.rerun_case(case_id, reason=payload.reason)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/report")
def report_case(case_id: str, payload: SummaryRequest) -> dict:
    try:
        orchestrator.mark_reporting(case_id, summary=payload.summary)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)


@router.post("/cases/{case_id}/archive")
def archive_case(case_id: str, payload: SummaryRequest) -> dict:
    try:
        orchestrator.archive_case(case_id, summary=payload.summary)
    except Exception as exc:
        _raise_case_error(exc)
    return _get_case_or_404(case_id)
