from pathlib import Path
import yaml


def load_bundle_config():
    bundle_file = Path("databricks.yml")

    with open(bundle_file, "r") as f:
        return yaml.safe_load(f)


def test_all_bundle_notebooks_exist():
    config = load_bundle_config()

    notebook_paths = []

    # Job notebooks
    jobs = config["resources"].get("jobs", {})

    for job in jobs.values():
        for task in job.get("tasks", []):
            notebook_task = task.get("notebook_task")

            if notebook_task:
                notebook_paths.append(
                    notebook_task["notebook_path"]
                )

    # Pipeline notebooks
    pipelines = config["resources"].get("pipelines", {})

    for pipeline in pipelines.values():
        for library in pipeline.get("libraries", []):

            notebook = library.get("notebook")

            if notebook:
                notebook_paths.append(
                    notebook["path"]
                )

    missing = []

    for notebook in notebook_paths:
        notebook_file = Path(
            notebook.replace("./", "")
        )

        if not notebook_file.exists():
            missing.append(notebook)

    assert not missing, (
        f"Missing notebook references: {missing}"
    )