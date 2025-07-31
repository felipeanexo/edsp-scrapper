"""
Domain entities for the EDSP scraper.
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class SchoolClassification:
    """School classification types with dynamic values."""

    PEI = "PEI"
    EE = "EE"
    UNKNOWN = "UNKNOWN"

    def __init__(self, value: str):
        self.value = value

    @classmethod
    def from_text(cls, text: str) -> "SchoolClassification":
        """Create classification from text, preserving original value if not PEI/EE."""
        if not text:
            return cls(cls.UNKNOWN)

        text = text.strip().upper()

        if text == "PEI":
            return cls(cls.PEI)
        elif text == "EE":
            return cls(cls.EE)
        else:
            # Preserve the original text value
            return cls(text)

    def __eq__(self, other):
        if isinstance(other, SchoolClassification):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"SchoolClassification('{self.value}')"


class ProcessingStatus(Enum):
    """Processing status for school data."""

    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass
class SchoolData:
    """School data entity."""

    name: str
    classification: SchoolClassification
    detail_url: str
    extraction_timestamp: datetime
    status: ProcessingStatus
    teaching_directorate: str = ""
    neighborhood: str = ""
    municipality: str = ""
    phone: str = ""
    email: str = ""
    ideb_score_final_years: str = ""
    idesp_score_final_years: str = ""
    ideb_score_high_school: str = ""
    idesp_score_high_school: str = ""
    total_students: str = ""
    age_06_10_final_years: str = ""
    age_11_14_final_years: str = ""
    age_15_17_final_years: str = ""
    age_18_plus_final_years: str = ""
    age_06_10_high_school: str = ""
    age_11_14_high_school: str = ""
    age_15_17_high_school: str = ""
    age_18_plus_high_school: str = ""
    total_classes: str = ""
    classes_final_years: str = ""
    classes_high_school: str = ""
    total_classrooms: str = ""
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV export."""
        return {
            "school_name": self.name,
            "classification": self.classification.value,
            "detail_url": self.detail_url,
            "extraction_timestamp": self.extraction_timestamp.isoformat(),
            "status": self.status.value,
            "teaching_directorate": self.teaching_directorate,
            "neighborhood": self.neighborhood,
            "municipality": self.municipality,
            "phone": self.phone,
            "email": self.email,
            "ideb_score_final_years": self.ideb_score_final_years,
            "idesp_score_final_years": self.idesp_score_final_years,
            "ideb_score_high_school": self.ideb_score_high_school,
            "idesp_score_high_school": self.idesp_score_high_school,
            "total_students": self.total_students,
            "age_06_10_final_years": self.age_06_10_final_years,
            "age_11_14_final_years": self.age_11_14_final_years,
            "age_15_17_final_years": self.age_15_17_final_years,
            "age_18_plus_final_years": self.age_18_plus_final_years,
            "age_06_10_high_school": self.age_06_10_high_school,
            "age_11_14_high_school": self.age_11_14_high_school,
            "age_15_17_high_school": self.age_15_17_high_school,
            "age_18_plus_high_school": self.age_18_plus_high_school,
            "total_classes": self.total_classes,
            "classes_final_years": self.classes_final_years,
            "classes_high_school": self.classes_high_school,
            "total_classrooms": self.total_classrooms,
            "error_message": self.error_message or "",
        }


@dataclass
class ProcessingStats:
    """Processing statistics entity."""

    total_processed: int = 0
    successful: int = 0
    errors: int = 0
    skipped: int = 0
    pages_processed: int = 0
    total_pages: int = 0
    total_institutions: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_processed == 0:
            return 0.0
        return (self.successful / self.total_processed) * 100

    def update_success(self):
        """Update stats for successful processing."""
        self.total_processed += 1
        self.successful += 1

    def update_error(self):
        """Update stats for error processing."""
        self.total_processed += 1
        self.errors += 1

    def update_skipped(self):
        """Update stats for skipped processing."""
        self.total_processed += 1
        self.skipped += 1


@dataclass
class BatchConfig:
    """Batch processing configuration."""

    start_page: int
    end_page: int
    batch_name: str
    max_concurrent: int = 2
    retry_attempts: int = 3
    delay_between_requests: float = 2.0
    delay_between_pages: float = 5.0


@dataclass
class ScrapingConfig:
    """Scraping configuration."""

    max_concurrent: int = 2
    retry_attempts: int = 3
    delay_between_requests: float = 2.0
    delay_between_pages: float = 5.0
    timeout: int = 60000
    headless: bool = True
    base_url: str = (
        "https://transparencia.educacao.sp.gov.br/Home/MapaDeEscolasPorDiretoria"
    )
