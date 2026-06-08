from pathlib import Path

NOTEBOOKS = [
    "notebooks/01_Ingestion_Job.py",
    "notebooks/08_Ingestion_Repos.py",
    "notebooks/09_Ingestion_Users.py",
    "notebooks/pipeline/02_SDP_Bronze.py",
    "notebooks/pipeline/03_SDP_Silver.py",
    "notebooks/pipeline/04_SDP_Gold.py",
    "notebooks/pipeline/10_SDP_Bronze_Repos.py",
    "notebooks/pipeline/11_SDP_Bronze_Users.py",
    "notebooks/pipeline/12_SDP_Silver_Repos.py",
    "notebooks/pipeline/13_SDP_Silver_Users.py",
    "notebooks/pipeline/14_SDP_Gold_Enriched.py",
]

def test_all_notebooks_exist():
    missing = [
        notebook for notebook in NOTEBOOKS if not Path(notebook).exists()
    ]
    assert not missing, f"Missing notebooks: {missing}"