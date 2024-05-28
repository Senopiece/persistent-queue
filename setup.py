from setuptools import setup, find_packages

setup(
    name="persistent_queue",
    version="1.0",
    description="A standalone module for persistent queue",
    author="Vitaly Mahonin",
    author_email="nabuki@vk.com",
    packages=find_packages(),
    package_data={
        "persistent_queue": ["*.pyi"],
    },
    include_package_data=True,
)
