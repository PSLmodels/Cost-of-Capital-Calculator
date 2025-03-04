import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    longdesc = fh.read()

setuptools.setup(
    description="CCC: A Cost of Capital Calculator",
    url="https://github.com/PSLmodels/Cost-of-Capital-Calculator",
    download_url="https://github.com/PSLmodels/Cost-of-Capital-Calculator",
    long_description_content_type="text/markdown",
    long_description=longdesc,
    version="2.0.0",
    license="CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
    packages=["ccc"],
    include_package_data=True,
    name="cost-of-capital-calculator",
    install_requires=["taxcalc", "pandas", "bokeh", "numpy", "paramtools"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    tests_require=["pytest"],
)
