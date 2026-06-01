from pathlib import Path
import yaml

def load_bundle_config():
    bundle_file = Path("databricks.yml")

    assert bundle_file.exists(), f"Bundle configuration file not found: {bundle_file}"

    with open(bundle_file, "r") as f:
        return yaml.safe_load(f)

def test_bundle_file_exists():
    assert Path("databricks.yml").exists()


def test_resources_section_exists():
    config = load_bundle_config()

    assert "resources" in config

def test_jobs_section_exists():
    config = load_bundle_config()

    assert "jobs" in config["resources"]

def test_pipelines_section_exists():
    config = load_bundle_config()

    assert "pipelines" in config["resources"]