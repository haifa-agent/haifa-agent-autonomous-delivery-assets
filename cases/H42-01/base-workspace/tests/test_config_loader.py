import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from depot.adapter.config_loader import DepotConfig, load_config
from depot.core.errors import ConfigError


class ConfigLoaderTest(unittest.TestCase):
    def _file(self, directory, payload):
        path = Path(directory) / "config.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_defaults_only(self):
        config = load_config()
        self.assertEqual("WH-CEN", config.warehouse)
        self.assertEqual("CN", config.region)

    def test_file_overrides_defaults(self):
        with TemporaryDirectory() as directory:
            path = self._file(directory, {"warehouse": "WH-EAS"})
            config = load_config(file_path=path)
        self.assertEqual("WH-EAS", config.warehouse)
        self.assertEqual("CN", config.region)

    def test_override_wins_over_file(self):
        with TemporaryDirectory() as directory:
            path = self._file(directory, {"warehouse": "WH-EAS", "region": "SG"})
            config = load_config(file_path=path, overrides={"warehouse": "WH-CEN", "region": None})
        self.assertEqual("WH-CEN", config.warehouse)
        self.assertEqual("SG", config.region)

    def test_feature_flags_merge(self):
        config = DepotConfig.defaults().merged({"feature_flags": {"a": True}})
        config = config.merged({"feature_flags": {"b": True}})
        self.assertEqual({"a": True, "b": True}, config.feature_flags)

    def test_unknown_key_is_refused(self):
        with self.assertRaises(ConfigError):
            DepotConfig.defaults().merged({"nope": 1})


if __name__ == "__main__":
    unittest.main()
