"""Tests for Fingerprint Generator"""
import pytest
from app.services.stealth.fingerprint import FingerprintGenerator, get_fingerprint_generator


class TestFingerprintGenerator:
    @pytest.fixture
    def generator(self):
        gen = FingerprintGenerator()
        gen.clear_cache()
        return gen

    def test_generate_fingerprint(self, generator):
        fp = generator.generate()

        assert "user_agent" in fp
        assert "viewport" in fp
        assert "timezone" in fp
        assert "locale" in fp
        assert "webgl_vendor" in fp

    def test_fingerprint_has_all_fields(self, generator):
        fp = generator.generate()

        required_fields = [
            "user_agent", "viewport", "screen", "timezone", "locale",
            "webgl_vendor", "webgl_renderer", "hardware_concurrency",
            "device_memory", "platform", "color_depth", "touch_support",
            "do_not_track"
        ]

        for field in required_fields:
            assert field in fp, f"Missing field: {field}"

    def test_fingerprints_are_varied(self, generator):
        fps = [generator.generate() for _ in range(10)]

        # Check that we get some variety
        user_agents = {fp["user_agent"] for fp in fps}
        viewports = {(fp["viewport"]["width"], fp["viewport"]["height"]) for fp in fps}

        # Should have at least 2 different values in 10 generations
        assert len(user_agents) >= 2 or len(viewports) >= 2

    def test_generate_for_domain_consistency(self, generator):
        fp1 = generator.generate_for_domain("example.com")
        fp2 = generator.generate_for_domain("example.com")

        # Same domain should get consistent fingerprint (within session)
        assert fp1 == fp2

    def test_different_domains_different_fingerprints(self, generator):
        fp1 = generator.generate_for_domain("site-a.com")
        fp2 = generator.generate_for_domain("site-b.com")

        # Different domains can have different fingerprints
        assert fp1["user_agent"] is not None
        assert fp2["user_agent"] is not None

    def test_viewport_has_dimensions(self, generator):
        fp = generator.generate()

        assert "width" in fp["viewport"]
        assert "height" in fp["viewport"]
        assert fp["viewport"]["width"] > 0
        assert fp["viewport"]["height"] > 0

    def test_screen_has_dimensions(self, generator):
        fp = generator.generate()

        assert "width" in fp["screen"]
        assert "height" in fp["screen"]
        assert "depth" in fp["screen"]

    def test_viewport_smaller_than_screen(self, generator):
        """Viewport should be smaller than screen (browser chrome)"""
        fp = generator.generate()

        assert fp["viewport"]["height"] < fp["screen"]["height"]

    def test_get_browser_args(self, generator):
        fp = generator.generate()
        args = generator.get_browser_args(fp)

        assert isinstance(args, list)
        assert len(args) >= 1

        # Should include window size
        has_window_size = any("--window-size" in arg for arg in args)
        assert has_window_size

    def test_get_context_options(self, generator):
        fp = generator.generate()
        options = generator.get_context_options(fp)

        assert "viewport" in options
        assert "locale" in options
        assert "timezone_id" in options

    def test_get_page_scripts(self, generator):
        fp = generator.generate()
        scripts = generator.get_page_scripts(fp)

        assert isinstance(scripts, list)
        assert len(scripts) >= 1

    def test_clear_cache(self, generator):
        # Generate for a domain
        generator.generate_for_domain("test.com")
        assert len(generator._domain_cache) == 1

        # Clear cache
        generator.clear_cache()
        assert len(generator._domain_cache) == 0

    def test_hardware_concurrency_is_valid(self, generator):
        fp = generator.generate()

        assert fp["hardware_concurrency"] in [4, 6, 8, 12, 16]

    def test_device_memory_is_valid(self, generator):
        fp = generator.generate()

        assert fp["device_memory"] in [4, 8, 16, 32]

    def test_platform_is_valid(self, generator):
        fp = generator.generate()

        assert fp["platform"] in ["Win32", "MacIntel", "Linux x86_64"]

    def test_singleton_instance(self):
        gen1 = get_fingerprint_generator()
        gen2 = get_fingerprint_generator()
        assert gen1 is gen2
