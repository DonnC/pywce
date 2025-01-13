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
    version="0.0.1",
    author="Donald Chinhuru",
    author_email="donychinhuru@gmail.com",
    description="Python WhatsApp Cloud Engine - a template-driven engine for easily building WhatsApp chatbots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DonnC/pywce",
    license="MIT",
    packages=find_packages(include=["pywce*"]),
    python_requires=">=3.9",
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: ChatBot :: Chat",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/DonnC/pywce/issues",
        "Source Code": "https://github.com/DonnC/pywce",
        "Documentation": "https://github.com/DonnC/pywce#readme",
    },
    keywords=["whatsapp", "chatbot", "yaml", "automation", "template", "hooks"],
    test_suite="tests",
)