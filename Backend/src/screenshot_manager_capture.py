"""
screenshot_manager/capture.py - Screenshot capture and management
Handles taking screenshots, comparing with baseline, and generating diffs
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image
from loguru import logger

try:
    from selenium.webdriver.remote.webdriver import WebDriver as SeleniumWebDriver
except ImportError:
    SeleniumWebDriver = None

try:
    from playwright.sync_api import Page as PlaywrightPage
except ImportError:
    PlaywrightPage = None


@dataclass
class ScreenshotMetadata:
    """Metadata for a screenshot"""
    filename: str
    timestamp: str
    test_name: str
    test_id: str
    file_path: Path
    file_size: int
    image_hash: str
    width: int
    height: int
    format: str = "png"
    quality: int = 95


class ScreenshotCapture:
    """Handle screenshot capture and management"""
    
    def __init__(
        self,
        base_path: Path = Path("test_data/screenshots"),
        format: str = "png",
        quality: int = 95
    ):
        """
        Initialize screenshot capture
        
        Args:
            base_path: Base path for storing screenshots
            format: Image format (png, jpg)
            quality: Image quality (1-100)
        """
        self.base_path = Path(base_path)
        self.baseline_path = self.base_path / "baseline"
        self.current_path = self.base_path / "current"
        self.diffs_path = self.base_path / "diffs"
        self.format = format
        self.quality = quality
        
        # Create directories
        self.baseline_path.mkdir(parents=True, exist_ok=True)
        self.current_path.mkdir(parents=True, exist_ok=True)
        self.diffs_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized ScreenshotCapture at {base_path}")
    
    def capture_selenium(
        self,
        driver: SeleniumWebDriver,
        test_name: str,
        test_id: str = "",
        full_page: bool = False
    ) -> Optional[ScreenshotMetadata]:
        """
        Capture screenshot from Selenium WebDriver
        
        Args:
            driver: Selenium WebDriver instance
            test_name: Name of the test
            test_id: Test ID
            full_page: Capture full page (scrolling) or just viewport
            
        Returns:
            ScreenshotMetadata object
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_{timestamp}.{self.format}"
            file_path = self.current_path / filename
            
            # Take screenshot
            if full_page:
                # Full page screenshot using JavaScript
                screenshot_data = self._capture_full_page_selenium(driver)
            else:
                screenshot_data = driver.get_screenshot_as_png()
            
            # Save screenshot
            with open(file_path, 'wb') as f:
                f.write(screenshot_data)
            
            # Get image metadata
            image = Image.open(file_path)
            metadata = ScreenshotMetadata(
                filename=filename,
                timestamp=timestamp,
                test_name=test_name,
                test_id=test_id,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                image_hash=self._calculate_hash(file_path),
                width=image.width,
                height=image.height,
                format=self.format,
                quality=self.quality
            )
            
            logger.info(f"Captured screenshot: {filename}")
            return metadata
        
        except Exception as e:
            logger.error(f"Failed to capture Selenium screenshot: {str(e)}")
            return None
    
    def capture_playwright(
        self,
        page: PlaywrightPage,
        test_name: str,
        test_id: str = "",
        full_page: bool = False
    ) -> Optional[ScreenshotMetadata]:
        """
        Capture screenshot from Playwright Page
        
        Args:
            page: Playwright Page instance
            test_name: Name of the test
            test_id: Test ID
            full_page: Capture full page or just viewport
            
        Returns:
            ScreenshotMetadata object
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_{timestamp}.{self.format}"
            file_path = self.current_path / filename
            
            # Take screenshot ปรับให้นานขึ้นเพราะรอAnimetionของเว็บ มีบางเว็บใช้
            page.screenshot(
                path=str(file_path),
                full_page=full_page,
                type=self.format,
                animations="disabled",
                timeout=60000
            )
            
            # Get image metadata
            image = Image.open(file_path)
            metadata = ScreenshotMetadata(
                filename=filename,
                timestamp=timestamp,
                test_name=test_name,
                test_id=test_id,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                image_hash=self._calculate_hash(file_path),
                width=image.width,
                height=image.height,
                format=self.format,
                quality=self.quality
            )
            
            logger.info(f"Captured screenshot: {filename}")
            return metadata
        
        except Exception as e:
            logger.error(f"Failed to capture Playwright screenshot: {str(e)}")
            return None
    
    def compare_with_baseline(
        self,
        current_screenshot: Path,
        test_name: str,
        threshold: float = 0.95
    ) -> Tuple[bool, float, Optional[Path]]:
        """
        Compare current screenshot with baseline
        
        Args:
            current_screenshot: Path to current screenshot
            test_name: Test name (to find baseline)
            threshold: Similarity threshold (0-1)
            
        Returns:
            Tuple of (is_match, similarity_score, diff_image_path)
        """
        try:
            # Find baseline
            baseline_files = list(self.baseline_path.glob(f"{test_name}*"))
            if not baseline_files:
                logger.warning(f"No baseline found for {test_name}")
                # Create baseline from current
                self._create_baseline(current_screenshot, test_name)
                return True, 1.0, None
            
            baseline_path = baseline_files[0]
            
            # Compare images
            similarity, diff_image = self._compare_images(
                baseline_path,
                current_screenshot
            )
            
            # Save diff if not matching
            diff_path = None
            if similarity < threshold:
                diff_path = self.diffs_path / f"{test_name}_diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                cv2.imwrite(str(diff_path), diff_image)
                logger.warning(f"Visual regression detected: {test_name} ({similarity:.2%})")
            
            is_match = similarity >= threshold
            logger.info(f"Comparison for {test_name}: {similarity:.2%} (match: {is_match})")
            
            return is_match, similarity, diff_path
        
        except Exception as e:
            logger.error(f"Failed to compare screenshots: {str(e)}")
            return False, 0.0, None
    
    def create_baseline_from_current(self, test_name: str) -> bool:
        """
        Create baseline from current screenshot
        
        Args:
            test_name: Test name
            
        Returns:
            Success status
        """
        try:
            current_files = sorted(
                self.current_path.glob(f"{test_name}*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if not current_files:
                logger.warning(f"No current screenshot found for {test_name}")
                return False
            
            current_path = current_files[0]
            self._create_baseline(current_path, test_name)
            logger.info(f"Created baseline for {test_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create baseline: {str(e)}")
            return False
    
    def update_all_baselines(self) -> int:
        """
        Update all baselines from current screenshots
        
        Returns:
            Number of baselines updated
        """
        updated = 0
        current_screenshots = list(self.current_path.glob("*"))
        
        for screenshot in current_screenshots:
            try:
                # Extract test name (remove timestamp)
                parts = screenshot.stem.split("_")
                test_name = "_".join(parts[:-2])  # Remove timestamp parts
                
                self._create_baseline(screenshot, test_name)
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update baseline for {screenshot}: {str(e)}")
        
        logger.info(f"Updated {updated} baselines")
        return updated
    
    # Private methods
    
    def _capture_full_page_selenium(self, driver: SeleniumWebDriver) -> bytes:
        """Capture full page screenshot using Selenium"""
        
        # Get original dimensions
        original_size = driver.get_window_size()
        required_width = driver.execute_script("return document.body.scrollWidth")
        required_height = driver.execute_script("return document.body.scrollHeight")
        
        # Set window size
        driver.set_window_size(required_width, required_height)
        
        # Take screenshot
        screenshot = driver.get_screenshot_as_png()
        
        # Restore original size
        driver.set_window_size(original_size['width'], original_size['height'])
        
        return screenshot
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _create_baseline(self, source_path: Path, test_name: str) -> None:
        """Create baseline from source screenshot"""
        
        # Remove old baselines for this test
        old_baselines = list(self.baseline_path.glob(f"{test_name}*"))
        for old_baseline in old_baselines:
            old_baseline.unlink()
        
        # Copy new baseline
        baseline_filename = f"{test_name}_baseline.{self.format}"
        baseline_path = self.baseline_path / baseline_filename
        
        image = Image.open(source_path)
        if self.format == "png":
            image.save(baseline_path)
        elif self.format == "jpg":
            image = image.convert("RGB")
            image.save(baseline_path, quality=self.quality)
    
    def _compare_images(
        self,
        baseline_path: Path,
        current_path: Path
    ) -> Tuple[float, np.ndarray]:
        """
        Compare two images and return similarity score
        
        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            
        Returns:
            Tuple of (similarity_score, diff_image)
        """
        
        # Read images
        baseline_img = cv2.imread(str(baseline_path), cv2.IMREAD_COLOR)
        current_img = cv2.imread(str(current_path), cv2.IMREAD_COLOR)
        
        # Resize current to match baseline if needed
        if baseline_img.shape != current_img.shape:
            current_img = cv2.resize(
                current_img,
                (baseline_img.shape[1], baseline_img.shape[0])
            )
        
        # Calculate difference
        diff = cv2.absdiff(baseline_img, current_img)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Calculate similarity
        non_zero_count = cv2.countNonZero(gray_diff)
        total_pixels = gray_diff.shape[0] * gray_diff.shape[1]
        similarity = 1.0 - (non_zero_count / total_pixels)
        
        # Create diff visualization
        _, diff_mask = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
        diff_image = baseline_img.copy()
        diff_image[diff_mask == 255] = [0, 0, 255]  # Red for differences
        
        return similarity, diff_image
    
    def cleanup_old_screenshots(self, days: int = 7) -> int:
        """
        Clean up old screenshots
        
        Args:
            days: Keep screenshots newer than this many days
            
        Returns:
            Number of files deleted
        """
        import time
        
        deleted = 0
        cutoff_time = time.time() - (days * 86400)
        
        for screenshot_path in self.current_path.glob("*"):
            if screenshot_path.stat().st_mtime < cutoff_time:
                screenshot_path.unlink()
                deleted += 1
        
        logger.info(f"Cleaned up {deleted} old screenshots")
        return deleted
