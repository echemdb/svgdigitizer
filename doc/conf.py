project = 'svgdigitizer'
copyright = '2021, the svgdigitizer authors'
author = 'the svgdigitizer authors'

release = '0.5.0'


extensions = ["myst_parser", "sphinx.ext.autodoc", "sphinx.ext.todo"]

source_suffix = [".rst", ".md"]

templates_path = ['_templates']

exclude_patterns = ['generated', 'Thumbs.db', '.DS_Store', 'README.md', 'news']

todo_include_todos = True

html_theme = 'sphinx_rtd_theme'

html_static_path = []

# Add Edit on GitHub links
html_context = {
    'display_github': True,
    'github_user': 'echemdb',
    'github_repo': 'svgdigitizer',
    'github_version': 'master/doc/',
}
