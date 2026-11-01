from pathlib import Path

from ingestion.loaders import load_files

DATA = Path(__file__).resolve().parent.parent / "data"


def test_loads_sample_data_with_sources_and_metadata():
    files = {f.file_path: f for f in load_files(DATA)}
    java = files["code/RewardExpirationService.java"]
    assert java.source == "code"
    assert java.metadata == {"language": "java", "class": "RewardExpirationService"}
    assert files["incidents/INC-101.md"].source == "incidents"
