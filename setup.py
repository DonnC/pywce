from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pywce",
    version="0.0.1",
    author="Donald Chinhuru",
    author_email="donychinhuru@gmail.com",
    description='Python WhatsApp cloud engine based off templates',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DonnC/pywce",
    license="MIT",
    packages=find_packages(include=['pywce']),
    install_requires=["munch", "requests", "pyopenssl"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    test_suite='tests'
)
