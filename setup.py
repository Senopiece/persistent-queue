from setuptools import setup

setup(
    name="persistent_queue",
    version="1.0",
    description="A standalone module for persistent_queue.py",
    author="Vitaly Mahonin",
    author_email="nabuki@vk.com",
    py_modules=["persistent_queue"],
    package_data={
        "": ["*.pyi"],
    },
)
