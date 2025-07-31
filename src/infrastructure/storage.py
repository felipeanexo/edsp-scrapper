"""
Storage infrastructure for CSV file management.
"""

import csv
import threading
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from src.domain.entities import SchoolData
from src.infrastructure.logger import structured_logger


class CSVStorage:
    """CSV storage manager for school data."""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.filename: Optional[str] = None
        self._csv_writer: Optional[csv.DictWriter] = None
        self._csv_file = None
        self._write_lock = threading.Lock()

    def initialize_csv(self, filename: Optional[str] = None) -> str:
        """Initialize CSV file for writing."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"edsp_schools_{timestamp}.csv"

        self.filename = self.output_dir / filename

        # Create CSV file with headers
        self._csv_file = open(self.filename, "w", newline="", encoding="utf-8")
        fieldnames = [
            "school_name",
            "classification",
            "detail_url",
            "extraction_timestamp",
            "status",
            "teaching_directorate",
            "neighborhood",
            "municipality",
            "phone",
            "email",
            "ideb_score_final_years",
            "idesp_score_final_years",
            "ideb_score_high_school",
            "idesp_score_high_school",
            "total_students",
            "age_06_10_final_years",
            "age_11_14_final_years",
            "age_15_17_final_years",
            "age_18_plus_final_years",
            "age_06_10_high_school",
            "age_11_14_high_school",
            "age_15_17_high_school",
            "age_18_plus_high_school",
            "total_classes",
            "classes_final_years",
            "classes_high_school",
            "total_classrooms",
            "error_message",
        ]

        self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=fieldnames)
        self._csv_writer.writeheader()

        structured_logger.bind_context(
            action="csv_initialized", filename=str(self.filename)
        ).info(f"📁 Initialized CSV file: {self.filename}")

        return str(self.filename)

    def write_school_data(self, school_data: SchoolData):
        """Write school data to CSV with thread safety."""
        if not self._csv_writer:
            raise RuntimeError("CSV file not initialized. Call initialize_csv() first.")

        with self._write_lock:
            row_data = school_data.to_dict()
            self._csv_writer.writerow(row_data)

            structured_logger.bind_context(
                action="school_written",
                school_name=school_data.name,
                status=school_data.status.value,
            ).debug(f"📝 Written school data: {school_data.name}")

    def write_single_school(self, school: SchoolData):
        """Write a single school data entry to CSV immediately."""
        self.write_school_data(school)
        # Force flush to ensure data is written to disk
        if self._csv_file:
            self._csv_file.flush()

    def write_multiple_schools(self, schools: List[SchoolData]):
        """Write multiple school data entries to CSV."""
        for school in schools:
            self.write_school_data(school)

        structured_logger.bind_context(action="batch_written", count=len(schools)).info(
            f"📝 Written {len(schools)} schools to CSV"
        )

    def close(self):
        """Close CSV file with forced flush."""
        if self._csv_file:
            # Force flush any pending data
            self._csv_file.flush()
            # Ensure data is written to disk
            import os

            os.fsync(self._csv_file.fileno())
            self._csv_file.close()
            structured_logger.bind_context(
                action="csv_closed", filename=str(self.filename)
            ).info(f"📁 Closed CSV file: {self.filename}")

    def force_save(self):
        """Force save all pending data to disk."""
        if self._csv_file:
            self._csv_file.flush()
            import os

            os.fsync(self._csv_file.fileno())
            structured_logger.bind_context(
                action="force_save", filename=str(self.filename)
            ).info(f"💾 Force saved data to: {self.filename}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_file_info(self) -> dict:
        """Get information about the CSV file."""
        if not self.filename or not self.filename.exists():
            return {"exists": False}

        stat = self.filename.stat()
        return {
            "exists": True,
            "filename": str(self.filename),
            "size_bytes": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    def verify_file_integrity(self) -> bool:
        """Verify that the CSV file is valid and not corrupted."""
        if not self.filename or not self.filename.exists():
            return False

        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                # Check if file has content
                content = f.read()
                if not content.strip():
                    return False

                # Check if it's valid CSV
                f.seek(0)
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    return False

                # Count rows
                row_count = sum(1 for row in reader)
                structured_logger.bind_context(
                    action="file_integrity_check",
                    filename=str(self.filename),
                    row_count=row_count,
                ).info(f"✅ File integrity verified: {row_count} rows")

                return True
        except Exception as e:
            structured_logger.bind_context(
                action="file_integrity_error", filename=str(self.filename), error=str(e)
            ).error(f"❌ File integrity check failed: {e}")
            return False

    def get_partial_data_count(self) -> int:
        """Get count of successfully saved records."""
        if not self.filename or not self.filename.exists():
            return 0

        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                # Skip header
                next(reader, None)
                # Count data rows
                return sum(1 for row in reader)
        except Exception as e:
            structured_logger.bind_context(
                action="partial_data_count_error", error=str(e)
            ).error(f"❌ Failed to count partial data: {e}")
            return 0
