"""
Main scraper application with clean architecture.
"""

import asyncio
from typing import List, Optional

from src.domain.entities import (
    SchoolData,
    SchoolClassification,
    ProcessingStatus,
    ProcessingStats,
    BatchConfig,
    ScrapingConfig,
)
from src.application.services import SchoolDataProcessor, BatchProcessor
from src.infrastructure.browser import BrowserManager
from src.infrastructure.storage import CSVStorage
from src.infrastructure.logger import structured_logger


class EDSPScraper:
    """
    Main scraper application with clean architecture.

    Features:
    - Clean separation of concerns
    - Structured logging with context binding
    - Robust error handling
    - Single CSV output
    - Scalable batch processing
    """

    def __init__(self, config: ScrapingConfig = ScrapingConfig()):
        self.config = config
        self.browser_manager = BrowserManager(config)
        self.school_processor = SchoolDataProcessor()
        self.batch_processor = BatchProcessor(self.school_processor)
        self.storage = CSVStorage()
        self.all_schools: List[SchoolData] = []

    async def get_total_pages(self) -> int:
        """Get total number of pages from the website."""
        async for browser in self.browser_manager.get_browser_context():
            page = await browser.new_page()
            try:
                await page.goto(
                    self.config.base_url,
                    wait_until="domcontentloaded",
                    timeout=self.config.timeout,
                )
                await page.wait_for_timeout(5000)
                return await self.browser_manager.get_total_pages(page)
            finally:
                await page.close()

    async def get_total_institutions(self) -> int:
        """Get total number of institutions from the website."""
        async for browser in self.browser_manager.get_browser_context():
            page = await browser.new_page()
            try:
                await page.goto(
                    self.config.base_url,
                    wait_until="domcontentloaded",
                    timeout=self.config.timeout,
                )
                await page.wait_for_timeout(5000)
                return await self.browser_manager.get_total_institutions(page)
            finally:
                await page.close()

    async def process_school_data(self, raw_data: dict) -> Optional[SchoolData]:
        """Process raw school data into domain entity."""
        try:
            # Parse classification
            classification = self.school_processor.parse_school_classification(
                raw_data["classification"]
            )

            # Create school data
            school_data = self.school_processor.create_school_data(
                name=raw_data["name"],
                classification=classification,
                detail_url=raw_data["detail_url"],
                teaching_directorate=raw_data.get("teaching_directorate", ""),
                neighborhood=raw_data.get("neighborhood", ""),
                municipality=raw_data.get("municipality", ""),
                phone=raw_data.get("phone", ""),
                email=raw_data.get("email", ""),
                ideb_score_final_years=raw_data.get("ideb_score_final_years", ""),
                idesp_score_final_years=raw_data.get("idesp_score_final_years", ""),
                ideb_score_high_school=raw_data.get("ideb_score_high_school", ""),
                idesp_score_high_school=raw_data.get("idesp_score_high_school", ""),
                total_students=raw_data.get("total_students", ""),
                age_06_10_final_years=raw_data.get("age_06_10_final_years", ""),
                age_11_14_final_years=raw_data.get("age_11_14_final_years", ""),
                age_15_17_final_years=raw_data.get("age_15_17_final_years", ""),
                age_18_plus_final_years=raw_data.get("age_18_plus_final_years", ""),
                age_06_10_high_school=raw_data.get("age_06_10_high_school", ""),
                age_11_14_high_school=raw_data.get("age_11_14_high_school", ""),
                age_15_17_high_school=raw_data.get("age_15_17_high_school", ""),
                age_18_plus_high_school=raw_data.get("age_18_plus_high_school", ""),
                total_classes=raw_data.get("total_classes", ""),
                classes_final_years=raw_data.get("classes_final_years", ""),
                classes_high_school=raw_data.get("classes_high_school", ""),
                total_classrooms=raw_data.get("total_classrooms", ""),
            )

            # Update stats
            self.school_processor.update_stats_success()

            return school_data

        except Exception as e:
            structured_logger.log_error(e, "school_data_processing")
            self.school_processor.update_stats_error()

            # Create error school data
            return self.school_processor.create_school_data(
                name="",
                classification=SchoolClassification("UNKNOWN"),
                detail_url=raw_data.get("detail_url", ""),
                status=ProcessingStatus.ERROR,
                error_message=str(e),
            )

    async def process_batch(self, batch_config: BatchConfig) -> ProcessingStats:
        """Process a single batch of pages."""
        structured_logger.log_processing_start(
            batch_config.batch_name, batch_config.start_page, batch_config.end_page
        )

        batch_schools: List[SchoolData] = []

        async for browser, contexts in self.browser_manager.create_browser_contexts(4):
            # Calculate pages to process
            end_page = min(
                batch_config.end_page, self.school_processor.stats.total_pages
            )
            pages_to_process = list(range(batch_config.start_page, end_page + 1))

            structured_logger.bind_context(
                action="batch_processing",
                batch_name=batch_config.batch_name,
                pages=pages_to_process,
            ).info(f"🔄 Processing pages: {pages_to_process}")

            # Process pages in parallel using multiple contexts
            all_tasks = []
            for i, page_num in enumerate(pages_to_process):
                context = contexts[i % len(contexts)]
                task = self.browser_manager.process_page_parallel(page_num, context)
                all_tasks.append(task)

            if all_tasks:
                all_results = await asyncio.gather(*all_tasks, return_exceptions=True)

                # Process results
                for page_results in all_results:
                    if isinstance(page_results, list):
                        for raw_data in page_results:
                            school_data = await self.process_school_data(raw_data)
                            if school_data:
                                batch_schools.append(school_data)
                                self.all_schools.append(school_data)

                                # Save each school immediately for maximum safety
                                self.storage.write_single_school(school_data)

                # No need to save again - already saved individually
                if batch_schools:
                    structured_logger.bind_context(
                        action="immediate_save",
                        schools_saved=len(batch_schools),
                        total_saved=len(self.all_schools),
                    ).info(f"💾 Saved {len(batch_schools)} schools individually")

                # Update batch stats
                self.school_processor.stats.pages_processed += len(pages_to_process)

        # Log batch completion
        structured_logger.bind_context(
            action="batch_completed",
            batch_name=batch_config.batch_name,
            schools_processed=len(batch_schools),
            total_processed=self.school_processor.stats.total_processed,
            successful=self.school_processor.stats.successful,
            errors=self.school_processor.stats.errors,
        ).info(
            f"✅ Batch {batch_config.batch_name} completed: {len(batch_schools)} schools"
        )

        return self.school_processor.stats

    async def process_all_pages(self) -> ProcessingStats:
        """Process all pages with batch processing."""
        structured_logger.bind_context(action="full_processing_start").info(
            "🚀 Starting full-scale processing of all pages"
        )

        # Reset processing state
        self.school_processor.reset_processing_state()

        # Initialize CSV storage
        csv_filename = self.storage.initialize_csv()

        try:
            # Get total pages and institutions
            total_pages = await self.get_total_pages()
            total_institutions = await self.get_total_institutions()
            self.school_processor.stats.total_pages = total_pages
            self.school_processor.stats.total_institutions = total_institutions

            structured_logger.bind_context(
                action="total_institutions_info",
                total_institutions=total_institutions,
                total_pages=total_pages,
            ).info(
                f"📊 Total institutions to process: {total_institutions} across {total_pages} pages"
            )

            # Create batches
            batches = self.batch_processor.create_batches(total_pages, batch_size=12)

            # Process batches
            for i, batch_config in enumerate(batches, 1):
                batch_stats = await self.process_batch(batch_config)

                # Merge stats
                self.batch_processor.merge_stats(batch_stats)

                # Log progress
                self.batch_processor.log_progress(i, len(batches))

                # Pause between batches
                if i < len(batches):
                    structured_logger.bind_context(
                        action="batch_pause", next_batch=batch_config.batch_name
                    ).info("⏳ Pausing 5 seconds before next batch...")
                    await asyncio.sleep(5)

            # No need to write again - already saved individually in batches

            # Log final stats
            self.batch_processor.log_final_stats()

            structured_logger.log_completion(
                len(self.all_schools), self.batch_processor.stats.success_rate
            )

            return self.batch_processor.stats

        except Exception as e:
            structured_logger.log_error(e, "full_processing")
            # Force save any data before raising
            try:
                if hasattr(self, "storage") and self.storage:
                    self.storage.force_save()
            except Exception as save_error:
                structured_logger.bind_context(
                    action="emergency_save_error", error=str(save_error)
                ).error(f"❌ Failed to save data during error: {save_error}")
            raise
        finally:
            try:
                if hasattr(self, "storage") and self.storage:
                    self.storage.close()
            except Exception as close_error:
                structured_logger.bind_context(
                    action="storage_close_error", error=str(close_error)
                ).warning(f"⚠️ Error closing storage: {close_error}")

    async def process_sample(
        self, start_page: int = 1, end_page: int = 1
    ) -> ProcessingStats:
        """Process a sample of pages for testing."""
        structured_logger.bind_context(
            action="sample_processing", start_page=start_page, end_page=end_page
        ).info("🧪 Starting sample processing")

        # Reset processing state
        self.school_processor.reset_processing_state()

        # Initialize CSV storage
        csv_filename = self.storage.initialize_csv()

        try:
            # Get total pages and institutions
            total_pages = await self.get_total_pages()
            total_institutions = await self.get_total_institutions()
            self.school_processor.stats.total_pages = total_pages
            self.school_processor.stats.total_institutions = total_institutions

            # Sample processing configuration
            structured_logger.bind_context(
                action="sample_config",
                start_page=1,
                end_page=1,
                total_institutions=total_institutions,
            ).info(
                f"🧪 Sample configuration: pages 1-1 (Total institutions: {total_institutions})"
            )

            # Process sample pages directly (not using batch processing)
            structured_logger.log_processing_start("SAMPLE", 1, 1)

            batch_schools: List[SchoolData] = []

            async for browser, contexts in self.browser_manager.create_browser_contexts(
                2
            ):
                # Process only the sample page (always page 1)
                page_num = 1
                context = contexts[0]  # Use first context for sample

                structured_logger.bind_context(
                    action="sample_processing",
                    page_num=page_num,
                ).info(f"🧪 Processing sample page: {page_num}")

                # Process the single page
                page_results = await self.browser_manager.process_page_parallel(
                    page_num, context
                )

                if isinstance(page_results, list):
                    for raw_data in page_results:
                        school_data = await self.process_school_data(raw_data)
                        if school_data:
                            batch_schools.append(school_data)
                            self.all_schools.append(school_data)

                            # Save each school immediately
                            self.storage.write_single_school(school_data)

            # No need to write again - already saved individually

            # Create sample stats
            sample_stats = ProcessingStats()
            sample_stats.total_processed = len(batch_schools)
            sample_stats.successful = len(
                [s for s in batch_schools if s.status == ProcessingStatus.SUCCESS]
            )
            sample_stats.errors = len(
                [s for s in batch_schools if s.status == ProcessingStatus.ERROR]
            )
            sample_stats.pages_processed = 1
            sample_stats.total_institutions = total_institutions

            # Verify file integrity
            if hasattr(self, "storage") and self.storage:
                file_ok = self.storage.verify_file_integrity()
                if not file_ok:
                    structured_logger.bind_context(
                        action="file_integrity_warning"
                    ).warning("⚠️ File integrity check failed - data may be corrupted")

            # Log completion
            structured_logger.log_completion(
                len(self.all_schools), sample_stats.success_rate
            )

            return sample_stats

        except Exception as e:
            structured_logger.log_error(e, "sample_processing")
            # Force save any data before raising
            try:
                if hasattr(self, "storage") and self.storage:
                    self.storage.force_save()
            except Exception as save_error:
                structured_logger.bind_context(
                    action="emergency_save_error", error=str(save_error)
                ).error(f"❌ Failed to save data during error: {save_error}")
            raise
        finally:
            try:
                if hasattr(self, "storage") and self.storage:
                    self.storage.close()
            except Exception as close_error:
                structured_logger.bind_context(
                    action="storage_close_error", error=str(close_error)
                ).warning(f"⚠️ Error closing storage: {close_error}")

    def get_summary(self) -> dict:
        """Get processing summary."""
        classifications = {}
        for school in self.all_schools:
            if school.status == ProcessingStatus.SUCCESS:
                classification = school.classification.value
                classifications[classification] = (
                    classifications.get(classification, 0) + 1
                )

        return {
            "total_schools": len(self.all_schools),
            "classifications": classifications,
            "stats": self.batch_processor.stats,
            "file_info": self.storage.get_file_info(),
        }
