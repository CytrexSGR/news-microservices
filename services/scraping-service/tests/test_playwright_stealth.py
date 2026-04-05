"""Tests for Playwright Stealth Browser"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestStealthBrowser:
    def test_stealth_browser_import(self):
        from app.services.stealth.playwright_stealth import StealthBrowser
        assert StealthBrowser is not None

    def test_stealth_browser_init(self):
        from app.services.stealth.playwright_stealth import StealthBrowser

        stealth = StealthBrowser()
        assert stealth is not None
        # _stealth_available depends on whether playwright-stealth is installed
        assert isinstance(stealth._stealth_available, bool)

    @pytest.mark.asyncio
    async def test_create_stealth_context(self):
        from app.services.stealth.playwright_stealth import StealthBrowser

        stealth = StealthBrowser()

        # Mock browser
        mock_browser = MagicMock()
        mock_context = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        with patch.object(stealth, '_apply_stealth', new_callable=AsyncMock):
            context = await stealth.create_stealth_context(mock_browser)

            mock_browser.new_context.assert_called_once()

    def test_get_random_viewport(self):
        from app.services.stealth.playwright_stealth import StealthBrowser

        stealth = StealthBrowser()
        viewport = stealth._get_random_viewport()

        assert "width" in viewport
        assert "height" in viewport
        assert viewport["width"] >= 1024
        assert viewport["height"] >= 720

    def test_get_random_viewport_variety(self):
        """Test that viewports have variety"""
        from app.services.stealth.playwright_stealth import StealthBrowser

        stealth = StealthBrowser()
        viewports = [stealth._get_random_viewport() for _ in range(20)]

        # Check for some variety
        widths = {v["width"] for v in viewports}
        assert len(widths) >= 2, "Should have multiple viewport sizes"

    @pytest.mark.asyncio
    async def test_create_stealth_page(self):
        from app.services.stealth.playwright_stealth import StealthBrowser

        stealth = StealthBrowser()

        # Mock context and page
        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        with patch.object(stealth, '_stealth_page', new_callable=AsyncMock):
            page = await stealth.create_stealth_page(mock_context)

            mock_context.new_page.assert_called_once()
            # Human behavior scripts should be added
            assert mock_page.add_init_script.call_count >= 1

    @pytest.mark.asyncio
    async def test_add_human_behavior(self):
        from app.services.stealth.playwright_stealth import StealthBrowser

        stealth = StealthBrowser()

        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()

        await stealth._add_human_behavior(mock_page)

        # Should add multiple init scripts
        assert mock_page.add_init_script.call_count >= 3

    @pytest.mark.asyncio
    async def test_simulate_human_scroll(self):
        from app.services.stealth.playwright_stealth import StealthBrowser

        stealth = StealthBrowser()

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock()

        await stealth.simulate_human_scroll(mock_page, scroll_amount=200)

        # Should have scrolled multiple times
        assert mock_page.evaluate.call_count >= 1

    @pytest.mark.asyncio
    async def test_simulate_mouse_movement(self):
        from app.services.stealth.playwright_stealth import StealthBrowser

        stealth = StealthBrowser()

        mock_page = MagicMock()
        mock_page.viewport_size = {"width": 1920, "height": 1080}
        mock_page.mouse = MagicMock()
        mock_page.mouse.move = AsyncMock()

        await stealth.simulate_mouse_movement(mock_page)

        # Should have moved mouse
        assert mock_page.mouse.move.call_count >= 1

    @pytest.mark.asyncio
    async def test_simulate_mouse_movement_no_viewport(self):
        from app.services.stealth.playwright_stealth import StealthBrowser

        stealth = StealthBrowser()

        mock_page = MagicMock()
        mock_page.viewport_size = None

        # Should not fail when viewport is None
        await stealth.simulate_mouse_movement(mock_page)

    def test_singleton_instance(self):
        from app.services.stealth.playwright_stealth import get_stealth_browser

        sb1 = get_stealth_browser()
        sb2 = get_stealth_browser()
        assert sb1 is sb2
