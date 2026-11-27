from setuptools import setup, find_packages

setup(
    name="yokai",
    version="0.1.1",
    url="https://github.com/paulscherrerinstitute/YokAI",
    description="LLM assistant for interactive IPython sessions",
    author="Paul Scherrer Institute",
    packages=find_packages(include=["yokai", "yokai.*"]),
    package_data={"yokai.briefing": ["*.md"]}
)


