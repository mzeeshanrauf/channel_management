from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="channel_management",
    version="1.0.0",
    description="DU Channel Partner Management App for ERPNext v16",
    author="ErpTronix",
    author_email="info@erptronix.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
