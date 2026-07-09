from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.password_policy import password_strength_errors


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserCreate(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    organization_name: str | None = Field(default=None, max_length=160)
    job_title: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    company: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    timezone: str | None = Field(default="America/Sao_Paulo", max_length=80)
    bio: str | None = Field(default=None, max_length=800)

    @model_validator(mode="after")
    def password_matches_policy(self) -> "UserCreate":
        errors = password_strength_errors(
            self.password,
            email=str(self.email),
            name=self.name,
            organization_name=self.organization_name,
        )
        if errors:
            raise ValueError(f"Password does not meet security policy: {', '.join(errors)}")
        return self


class LoginRequest(StrictModel):
    email: EmailStr
    password: str


class ProfileUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    job_title: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    company: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    timezone: str | None = Field(default=None, max_length=80)
    bio: str | None = Field(default=None, max_length=800)
    preferences: dict[str, Any] | None = None


class EmailTokenPayload(StrictModel):
    token: str = Field(min_length=20, max_length=240)


class PasswordResetRequest(StrictModel):
    email: EmailStr


class PasswordResetConfirm(StrictModel):
    token: str = Field(min_length=20, max_length=240)
    new_password: str = Field(min_length=12, max_length=128)


class AvatarUploadPayload(StrictModel):
    file_name: str = Field(min_length=1, max_length=180)
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    data_base64: str = Field(min_length=20)


class ProjectCreate(StrictModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    i18n: dict[str, Any] = Field(default_factory=dict)
    problem_type: str = "binary_classification"
    domain: str = "general"
    tags: list[str] = Field(default_factory=list)
    default_threshold: float = Field(default=0.70, ge=0, le=1)
    bias_sensitive_features: list[str] = Field(default_factory=list)


class ProjectUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = None
    i18n: dict[str, Any] | None = None
    status: Literal["active", "archived"] | None = None
    data_contract_mode: Literal["accept", "warn", "block"] | None = None


class MLModelCreate(StrictModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    i18n: dict[str, Any] = Field(default_factory=dict)
    problem_type: str = "binary_classification"
    target_name: str = "target"
    labels: dict[str, str] = Field(default_factory=lambda: {"positive": "positive", "negative": "negative"})
    default_threshold: float = Field(default=0.70, ge=0, le=1)
    primary_metric: str = "recall"
    expected_features: list[dict[str, Any]] = Field(default_factory=list)


class ModelVersionCreate(StrictModel):
    version: str = Field(min_length=1, max_length=40)
    algorithm: str = Field(default="Simulated Risk Formula", max_length=120)
    status: Literal["draft", "staging", "production", "deprecated"] = "draft"
    features: list[str] = Field(default_factory=list)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    training_metadata: dict[str, Any] = Field(default_factory=dict)
    offline_metrics: dict[str, float] = Field(default_factory=dict)
    changelog: str = ""
    notes: str = ""


class APIKeyCreate(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    scopes: list[
        Literal[
            "predictions:write",
            "predictions:batch",
            "feedback:write",
            "exports:read",
            "admin",
        ]
    ] = Field(default_factory=lambda: ["predictions:write"])
    expires_at: str | None = None


class PredictionPayload(StrictModel):
    project_id: str
    model_id: str
    model_version: str
    entity_id: str
    entity_type: str = "entity"
    entity_display_name: str | None = None
    features: dict[str, Any]
    prediction: dict[str, Any]
    explanations: list[dict[str, Any]] = Field(default_factory=list)
    decision: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("features")
    @classmethod
    def features_not_empty(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("features must not be empty")
        return value

    @field_validator("prediction")
    @classmethod
    def prediction_has_score_label(cls, value: dict[str, Any]) -> dict[str, Any]:
        if "score" not in value or "label" not in value:
            raise ValueError("prediction must include score and label")
        score = float(value["score"])
        if score < 0 or score > 1:
            raise ValueError("prediction.score must be between 0 and 1")
        threshold = float(value.get("threshold", 0.5))
        if threshold < 0 or threshold > 1:
            raise ValueError("prediction.threshold must be between 0 and 1")
        return value


class BatchPredictionPayload(StrictModel):
    items: list[PredictionPayload] = Field(min_length=1, max_length=500)


class FeedbackPayload(StrictModel):
    observed_label: str | None = None
    observed_value: int | float | bool | None = None
    feedback_date: str | None = None
    source: str = "manual"
    notes: str = ""


class AnnotationPayload(StrictModel):
    type: Literal["analyst_note", "false_positive_flag", "action_taken", "escalated"] = "analyst_note"
    content: str = Field(min_length=1, max_length=2000)
    tags: list[str] = Field(default_factory=list)


class AlertRulePayload(StrictModel):
    project_id: str
    model_id: str
    name: str
    i18n: dict[str, Any] = Field(default_factory=dict)
    type: Literal[
        "performance_threshold",
        "volume_drop",
        "data_drift",
        "prediction_drift",
        "missing_features",
        "deprecated_version_active",
        "feedback_rate_low",
    ]
    metric: str = "recall"
    operator: Literal["less_than", "greater_than"] = "less_than"
    threshold: float
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    min_feedback_count: int = 1
    enabled: bool = True


class AlertRuleUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    i18n: dict[str, Any] | None = None
    metric: str | None = None
    operator: Literal["less_than", "greater_than"] | None = None
    threshold: float | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    min_feedback_count: int | None = Field(default=None, ge=0)
    enabled: bool | None = None


class DataContractPayload(StrictModel):
    mode: Literal["accept", "warn", "block"] = "warn"
    expected_features: list[dict[str, Any]] | None = None


class SavedViewPayload(StrictModel):
    view: Literal["predictions", "operations", "lab", "governance", "entities"] = "predictions"
    name: str = Field(min_length=2, max_length=120)
    filters: dict[str, Any] = Field(default_factory=dict)
    columns: list[str] = Field(default_factory=list)
    sort: dict[str, Any] = Field(default_factory=dict)
    shared: bool = False


class EntityNotePayload(StrictModel):
    entity_id: str = Field(min_length=1, max_length=240)
    content: str = Field(min_length=1, max_length=2000)
    tags: list[str] = Field(default_factory=list)


class JobRunPayload(StrictModel):
    type: Literal["alerts", "drift", "metrics", "diagnostics", "dashboard"] = "alerts"
    project_id: str | None = None
    model_id: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class NotificationUpdate(StrictModel):
    read: bool = True


class WhatIfPayload(StrictModel):
    hypothetical_features: dict[str, Any]


class ReplayPayload(StrictModel):
    target_version: str
    replay_score: float | None = Field(default=None, ge=0, le=1)
    replay_label: str | None = None
    hypothetical_features: dict[str, Any] | None = None


class ExportPayload(StrictModel):
    type: Literal["predictions"] = "predictions"
    filters: dict[str, Any] = Field(default_factory=dict)
    format: Literal["csv", "json"] = "csv"
    include_features: bool = True
    include_explanations: bool = True
    redact_pii: bool = True
