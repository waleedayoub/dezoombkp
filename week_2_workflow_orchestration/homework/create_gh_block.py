from prefect.filesystems import GitHub

block = GitHub(
    repository="https://github.com/waleedayoub/data-engineering-zoomcamp",
)
block.get_directory(
    "week_2_workflow_orchestration/flows"
)  # specify a subfolder of repo
block.save("test")
