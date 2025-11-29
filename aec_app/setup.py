from setuptools import setup, find_packages

setup(
    name="src/AEC",  # trùng tên folder src/AEC
    version="0.1",
    packages=find_packages(where="AEC"),  # tìm package trong src
    package_dir={"": "AEC"},              # root package là src
    install_requires=[
        "toga",
        "toga-winforms",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "aec_app = AEC.__main__:main"  # trỏ đúng package __main__.py
        ]
    }
)