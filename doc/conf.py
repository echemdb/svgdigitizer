project = 'svgdigitizer'
copyright = '2021-2024, the svgdigitizer authors'
author = 'the svgdigitizer authors'

release = '0.12.5'

extensions = [
        "sphinx.ext.autodoc",
        "sphinx.ext.todo",
        "myst_nb",
        "sphinx_design"
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.myst': 'myst-nb',

}

templates_path = ['_templates']

exclude_patterns = ['generated', 'Thumbs.db', '.DS_Store', 'README.md', 'news', '.ipynb_checkpoints', '*.ipynb']

todo_include_todos = True

html_theme = 'sphinx_rtd_theme'

html_static_path = []

myst_heading_anchors = 2

# Add Edit on GitHub links
html_context = {
    'display_github': True,
    'github_user': 'echemdb',
    'github_repo': 'svgdigitizer',
    'github_version': 'master/doc/',
}

# repology.org only passes the check locally but not in the Github CI. see #169
linkcheck_ignore = [
    "https://repology.org/*",
]
