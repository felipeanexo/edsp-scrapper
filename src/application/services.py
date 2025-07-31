"""
Application services with business logic for school data processing.
"""

from typing import List, Optional, Set
from datetime import datetime

from src.domain.entities import (
    SchoolData,
    SchoolClassification,
    ProcessingStatus,
    ProcessingStats,
    BatchConfig,
)
from src.infrastructure.logger import structured_logger


class SchoolDataProcessor:
    """Service for processing school data with business logic."""

    def __init__(self):
        self.processed_urls: Set[str] = set()
        self.stats = ProcessingStats()

    def reset_processing_state(self):
        """Reset processing state for new execution."""
        self.processed_urls.clear()
        self.stats = ProcessingStats()

    def parse_school_classification(
        self, classification_text: str
    ) -> SchoolClassification:
        """Parse school classification from text, preserving original value if not PEI/EE."""
        return SchoolClassification.from_text(classification_text)

    def create_school_data(
        self,
        name: str,
        classification: SchoolClassification,
        detail_url: str,
        teaching_directorate: str = "",
        neighborhood: str = "",
        municipality: str = "",
        phone: str = "",
        email: str = "",
        ideb_score_final_years: str = "",
        idesp_score_final_years: str = "",
        ideb_score_high_school: str = "",
        idesp_score_high_school: str = "",
        total_students: str = "",
        age_06_10_final_years: str = "",
        age_11_14_final_years: str = "",
        age_15_17_final_years: str = "",
        age_18_plus_final_years: str = "",
        age_06_10_high_school: str = "",
        age_11_14_high_school: str = "",
        age_15_17_high_school: str = "",
        age_18_plus_high_school: str = "",
        total_classes: str = "",
        classes_final_years: str = "",
        classes_high_school: str = "",
        total_classrooms: str = "",
        status: ProcessingStatus = ProcessingStatus.SUCCESS,
        error_message: Optional[str] = None,
    ) -> SchoolData:
        """Create school data entity."""
        return SchoolData(
            name=name,
            classification=classification,
            detail_url=detail_url,
            extraction_timestamp=datetime.now(),
            status=status,
            teaching_directorate=teaching_directorate,
            neighborhood=neighborhood,
            municipality=municipality,
            phone=phone,
            email=email,
            ideb_score_final_years=ideb_score_final_years,
            idesp_score_final_years=idesp_score_final_years,
            ideb_score_high_school=ideb_score_high_school,
            idesp_score_high_school=idesp_score_high_school,
            total_students=total_students,
            age_06_10_final_years=age_06_10_final_years,
            age_11_14_final_years=age_11_14_final_years,
            age_15_17_final_years=age_15_17_final_years,
            age_18_plus_final_years=age_18_plus_final_years,
            age_06_10_high_school=age_06_10_high_school,
            age_11_14_high_school=age_11_14_high_school,
            age_15_17_high_school=age_15_17_high_school,
            age_18_plus_high_school=age_18_plus_high_school,
            total_classes=total_classes,
            classes_final_years=classes_final_years,
            classes_high_school=classes_high_school,
            total_classrooms=total_classrooms,
            error_message=error_message,
        )

    def is_url_processed(self, url: str) -> bool:
        """Check if URL has been processed."""
        # Normalize URL to avoid duplicates with different formats
        normalized_url = url.strip()
        if normalized_url.startswith("/"):
            normalized_url = f"https://transparencia.educacao.sp.gov.br{normalized_url}"
        return normalized_url in self.processed_urls

    def mark_url_processed(self, url: str):
        """Mark URL as processed."""
        # Normalize URL before adding
        normalized_url = url.strip()
        if normalized_url.startswith("/"):
            normalized_url = f"https://transparencia.educacao.sp.gov.br{normalized_url}"
        self.processed_urls.add(normalized_url)

    def update_stats_success(self):
        """Update statistics for successful processing."""
        self.stats.update_success()

    def update_stats_error(self):
        """Update statistics for error processing."""
        self.stats.update_error()

    def update_stats_skipped(self):
        """Update statistics for skipped processing."""
        self.stats.update_skipped()


class BatchProcessor:
    """Service for batch processing coordination."""

    def __init__(self, school_processor: SchoolDataProcessor):
        self.school_processor = school_processor
        self.stats = ProcessingStats()

    def create_batches(
        self, total_pages: int, batch_size: int = 5
    ) -> List[BatchConfig]:
        """Create batch configurations for processing."""
        batches = []
        batch_number = 1

        for start_page in range(1, total_pages + 1, batch_size):
            end_page = min(start_page + batch_size - 1, total_pages)
            batch_name = f"BATCH_{batch_number:03d}"

            batch_config = BatchConfig(
                start_page=start_page,
                end_page=end_page,
                batch_name=batch_name,
                max_concurrent=12,
                retry_attempts=3,
                delay_between_requests=0.4,
                delay_between_pages=1.5,
            )

            batches.append(batch_config)
            batch_number += 1

        structured_logger.bind_context(
            action="batches_created",
            total_pages=total_pages,
            batch_size=batch_size,
            batch_count=len(batches),
        ).info(f"📋 Created {len(batches)} batches for processing")

        return batches

    def merge_stats(self, batch_stats: ProcessingStats):
        """Merge batch statistics into total stats."""
        self.stats.total_processed += batch_stats.total_processed
        self.stats.successful += batch_stats.successful
        self.stats.errors += batch_stats.errors
        self.stats.skipped += batch_stats.skipped
        self.stats.pages_processed += batch_stats.pages_processed

    def get_progress_percentage(self, current_batch: int, total_batches: int) -> float:
        """Calculate progress percentage."""
        return (current_batch / total_batches) * 100

    def log_progress(self, current_batch: int, total_batches: int):
        """Log progress information."""
        progress = self.get_progress_percentage(current_batch, total_batches)

        structured_logger.bind_context(
            action="progress_update",
            current_batch=current_batch,
            total_batches=total_batches,
            progress_percentage=progress,
            total_processed=self.stats.total_processed,
            successful=self.stats.successful,
            errors=self.stats.errors,
        ).info(
            f"📊 Progress: {progress:.1f}% ({current_batch}/{total_batches} batches)"
        )

    def log_final_stats(self):
        """Log final processing statistics."""
        structured_logger.bind_context(
            action="final_stats",
            total_processed=self.stats.total_processed,
            successful=self.stats.successful,
            errors=self.stats.errors,
            skipped=self.stats.skipped,
            success_rate=self.stats.success_rate,
        ).info(
            f"🎉 Final Statistics: {self.stats.total_processed} total, {self.stats.success_rate:.1f}% success rate"
        )
