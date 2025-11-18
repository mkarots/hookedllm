"""Generate API reference pages for mkdocs."""

from pathlib import Path
import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

# Define modules to document
modules = [
    "hookedllm",
    "hookedllm.core",
    "hookedllm.hooks",
    "hookedllm.config",
    "hookedllm.providers",
]

# Generate pages for each module
for module in modules:
    parts = module.split(".")
    
    # Create file path
    doc_path = Path("api") / Path(*parts) / "index.md"
    
    # Create nav entry
    nav[parts] = doc_path.as_posix()
    
    # Generate the page
    with mkdocs_gen_files.open(doc_path, "w") as fd:
        fd.write(f"# {parts[-1]}\n\n")
        fd.write(f"::: {module}\n")
    
    # Mark as generated
    mkdocs_gen_files.set_edit_path(doc_path, Path("..") / ".." / "src" / Path(*parts) / "__init__.py")

# Note: Navigation is handled by mkdocs.yml nav section
# This script generates the API reference pages

