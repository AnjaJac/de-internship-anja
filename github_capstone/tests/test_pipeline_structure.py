from pathlib import Path
import yaml


def load_bundle_config():
    bundle_file = Path("databricks.yml")

    with open(bundle_file, "r") as f:
        return yaml.safe_load(f)


def test_resources_exist():
    config = load_bundle_config()

    assert "resources" in config


def test_job_exists():
    config = load_bundle_config()

    jobs = config["resources"].get("jobs", {})

    assert len(jobs) > 0, "No jobs defined in bundle"


def test_pipeline_exists():
    config = load_bundle_config()

    pipelines = config["resources"].get("pipelines", {})

    assert len(pipelines) > 0, "No pipelines defined in bundle"


def test_expected_job_present():
    config = load_bundle_config()

    jobs = config["resources"].get("jobs", {})

    assert (
        "gh_pipeline_job" in jobs
    ), "Expected job 'gh_pipeline_job' not found"


def test_expected_pipeline_present():
    config = load_bundle_config()

    pipelines = config["resources"].get("pipelines", {})

    assert (
        "gh_sdp_medallion" in pipelines
    ), "Expected pipeline 'gh_sdp_medallion' not found"