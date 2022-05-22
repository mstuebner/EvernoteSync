from setuptools import setup, find_packages

setup(
    name="Evernote File Importer",
    version="0.3.0",
    author="Matthias Stuebner",
    author_email="mstuebner@gmail.com",
    url="https://pypi.org/edeediong-resume",
    description="An application that monitors a directory structure and automatically imports files into Evernote",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["pydantic", "watchdog", "evernote3", "pylint", "pytest", "zc.lockfile"],
)