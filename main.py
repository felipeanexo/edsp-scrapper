"""
Main entry point for the EDSP Web Scraper with clean architecture.
"""

import asyncio
import sys
import signal
from pathlib import Path

from src.application.scraper import EDSPScraper
from src.domain.entities import ScrapingConfig
from src.infrastructure.logger import structured_logger


async def run_sample_processing():
    """Run sample processing for testing."""
    global scraper_instance

    structured_logger.bind_context(action="main_sample_start").info(
        "🧪 Starting sample processing (page 1 only)"
    )

    config = ScrapingConfig(
        max_concurrent=12,
        retry_attempts=3,
        delay_between_requests=1.0,
        delay_between_pages=3.0,
        timeout=30000,
        headless=True,
    )

    scraper = EDSPScraper(config)
    scraper_instance = scraper

    try:
        stats = await scraper.process_sample(start_page=1, end_page=5)
        summary = scraper.get_summary()

        structured_logger.bind_context(
            action="sample_completed",
            total_schools=summary["total_schools"],
            success_rate=stats.success_rate,
        ).info(
            f"✅ Sample processing completed: {summary['total_schools']} schools, {stats.success_rate:.1f}% success rate"
        )

        # Print summary
        print("\n" + "=" * 50)
        print("📊 PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Total schools processed: {summary['total_schools']}")
        print(f"Success rate: {stats.success_rate:.1f}%")
        print(f"Successful: {stats.successful}")
        print(f"Errors: {stats.errors}")
        print(f"Skipped: {stats.skipped}")
        print(f"Pages processed: {stats.pages_processed}")
        print(
            f"Total institutions available: {stats.total_institutions if hasattr(stats, 'total_institutions') else 'N/A'}"
        )

        if summary["classifications"]:
            print("\nClassifications:")
            for classification, count in summary["classifications"].items():
                print(f"  {classification}: {count} schools")

        if summary["file_info"]["exists"]:
            print(f"\n📁 Results saved to: {summary['file_info']['filename']}")

        print("=" * 50)

    except Exception as e:
        structured_logger.log_error(e, "sample_processing_main")
        raise


async def run_full_processing():
    """Run full processing of all pages."""
    global scraper_instance

    structured_logger.bind_context(action="main_full_start").info(
        "🚀 Starting full-scale processing of all pages (with 100 results per page)"
    )

    config = ScrapingConfig(
        max_concurrent=12,
        retry_attempts=3,
        delay_between_requests=0.5,
        delay_between_pages=2.0,
        timeout=30000,
        headless=True,
    )

    scraper = EDSPScraper(config)
    scraper_instance = scraper

    try:
        stats = await scraper.process_all_pages()
        summary = scraper.get_summary()

        structured_logger.bind_context(
            action="full_completed",
            total_schools=summary["total_schools"],
            success_rate=stats.success_rate,
        ).info(
            f"🎉 Full processing completed: {summary['total_schools']} schools, {stats.success_rate:.1f}% success rate"
        )

        # Print summary
        print("\n" + "=" * 50)
        print("📊 FINAL PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Total schools: {summary['total_schools']}")
        print(f"Success rate: {stats.success_rate:.1f}%")
        print(f"Successful: {stats.successful}")
        print(f"Errors: {stats.errors}")
        print(f"Skipped: {stats.skipped}")
        print(f"Pages processed: {stats.pages_processed}")
        print(f"Total pages: {stats.total_pages}")

        if summary["classifications"]:
            print("\nClassifications:")
            for classification, count in summary["classifications"].items():
                print(f"  {classification}: {count} schools")

        if summary["file_info"]["exists"]:
            print(f"\n📁 Results saved to: {summary['file_info']['filename']}")
            print(f"File size: {summary['file_info']['size_bytes']} bytes")

        print("=" * 50)

    except Exception as e:
        structured_logger.log_error(e, "full_processing_main")
        raise


# Global variable to store the scraper instance
scraper_instance = None


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    global scraper_instance
    if scraper_instance:
        structured_logger.bind_context(action="graceful_shutdown").info(
            "🛑 Received interrupt signal, saving data and shutting down gracefully..."
        )
        try:
            # Force save any remaining data
            if hasattr(scraper_instance, "storage") and scraper_instance.storage:
                scraper_instance.storage.force_save()
                scraper_instance.storage.close()

            # Close browser contexts if available
            if hasattr(scraper_instance, "browser_manager"):
                structured_logger.bind_context(action="browser_cleanup").info(
                    "🧹 Cleaning up browser contexts..."
                )
        except Exception as e:
            structured_logger.bind_context(
                action="cleanup_error", error=str(e)
            ).warning(f"⚠️ Error during cleanup: {e}")
    sys.exit(0)


async def main():
    """Main entry point."""
    global scraper_instance

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("results").mkdir(exist_ok=True)

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "sample":
        await run_sample_processing()
    else:
        await run_full_processing()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        structured_logger.bind_context(action="user_interruption").warning(
            "⚠️ Processing interrupted by user"
        )
    except Exception as e:
        structured_logger.log_error(e, "main_execution")
        sys.exit(1)
