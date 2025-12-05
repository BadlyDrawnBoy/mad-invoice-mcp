import argparse
import logging
import unittest

from bridge.cli import run
from bridge.utils.logging import configure_root


class ConfigureRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root_logger = logging.getLogger()
        self.original_handlers = list(self.root_logger.handlers)
        self.original_level = self.root_logger.level

    def tearDown(self) -> None:
        self.root_logger.handlers = self.original_handlers
        self.root_logger.setLevel(self.original_level)

    def test_configure_root_forces_reconfiguration(self) -> None:
        dummy_handler = logging.StreamHandler()
        dummy_handler.setFormatter(logging.Formatter("%(message)s"))

        self.root_logger.handlers = [dummy_handler]
        self.root_logger.setLevel(logging.WARNING)

        configure_root()

        self.assertNotIn(dummy_handler, self.root_logger.handlers)
        self.assertEqual(self.root_logger.level, logging.INFO)
        self.assertTrue(self.root_logger.handlers)
        formatter = self.root_logger.handlers[0].formatter
        self.assertIsNotNone(formatter)
        self.assertEqual(formatter._fmt, "%(levelname)s:%(name)s:%(message)s")

    def test_debug_flag_raises_logger_level(self) -> None:
        configure_root()
        cli_logger = logging.getLogger("bridge.cli")
        cli_logger_level = cli_logger.level

        args = argparse.Namespace(
            transport="stdio",
            mcp_host="127.0.0.1",
            mcp_port=8099,
            shim_host="127.0.0.1",
            shim_port=8081,
            debug=True,
        )

        try:
            run(
                args,
                logger=cli_logger,
                start_sse=lambda host, port: None,
                run_stdio=lambda: None,
                shim_factory=lambda upstream_base: None,
            )
            self.assertEqual(cli_logger.getEffectiveLevel(), logging.DEBUG)
        finally:
            cli_logger.setLevel(cli_logger_level)


__all__ = ["ConfigureRootTests"]
