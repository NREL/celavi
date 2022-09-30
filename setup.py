import setuptools

name = "celavi"
version = "1.3.1"

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name=name,
    version=version,
    author="Annika Eberle",
    author_email="annika.eberle@nrel.gov",
    description="Codebase for the Circular Economy Lifecycle Assessment and VIsualization (CELAVI) project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["celavi"],
    install_requires=[
        "pytest",
        "mypy",
        "black",
        "sphinx",
        "pandas",
        "matplotlib",
        "numpy",
        "networkx",
        "graphviz",
        "simpy",
	    "networkx-query",
        "olca-ipc==0.0.10",
        "pyutilib",
        "joblib",
        "plotly",
        "kaleido",
        "scikit-learn",
        "PyYAML",
        "sphinx-rtd-theme"
    ]
)
