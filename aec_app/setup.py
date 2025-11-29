from setuptools import setup, find_packages

setup(
    name="aec_app",  # trùng tên folder src/AEC
    version="0.1",
    packages=find_packages(where="src"),  # tìm package trong src
    package_dir={"": "src"},              # root package là src
    install_requires=[
        "toga-core~=0.5.0",
        "toga-winforms~=0.5.0",  # nếu chạy Windows
        "numpy",
        "pyaec"

    ],
    entry_points={
        "console_scripts": [
            "aec_app = AEC.main:main"  # trỏ đúng package __main__.py
        ]
    }
)