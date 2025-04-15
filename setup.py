from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = [
        line.strip()
        for line in fh
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="pywce",
    version="2.2.0+1",
    author="Donald Chinhuru",
    author_email="donychinhuru@gmail.com",
    description="A templates-driven framework for building WhatsApp chatbots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DonnC/pywce",
    license="MIT",
    packages=find_packages(include=["pywce*"]),
    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require={
        "ai": ["openai", "docstring-parser"],
        "cache": ["cachetools"]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/DonnC/pywce/issues",
        "Source Code": "https://github.com/DonnC/pywce",
        "Documentation": "https://docs.page/donnc/wce",
    },
    keywords=["whatsapp", "chatbot", "ai", "yaml", "automation", "templates", "hooks"]
)
