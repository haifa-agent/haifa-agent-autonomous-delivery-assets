import unittest

from depot.adapter.registry import HandlerRegistry
from depot.core.errors import NotFoundError


class RegistryTest(unittest.TestCase):
    def test_register_and_dispatch(self):
        registry = HandlerRegistry()
        registry.register("Ping", lambda *, value=0: value + 1)
        self.assertIn("ping", registry)
        self.assertEqual(2, registry.dispatch("ping", value=1))

    def test_lookup_is_case_insensitive(self):
        registry = HandlerRegistry()
        registry.register("list", lambda **_: "ok")
        self.assertEqual("ok", registry.get("LIST")())

    def test_unknown_operation(self):
        with self.assertRaises(NotFoundError):
            HandlerRegistry().get("missing")

    def test_names_are_sorted(self):
        registry = HandlerRegistry()
        for name in ("b", "a", "c"):
            registry.register(name, lambda **_: None)
        self.assertEqual(["a", "b", "c"], registry.names())


if __name__ == "__main__":
    unittest.main()
