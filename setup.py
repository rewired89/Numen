from setuptools import setup, find_packages

setup(
    name="numen",
    version="0.1.0",
    description="Specialized AI mathematical reasoning engine for cross-domain problem solving",
    author="Nyx Cybersecurity",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "sympy>=1.12",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "networkx>=3.1",
        "fastapi>=0.100.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "black>=23.0.0", "mypy>=1.4.0"],
    },
)
