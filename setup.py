from cx_Freeze import setup, Executable

setup(
    name="onepage",
    version="0.1",
    description="Generate faction html for onepagerules",
    executables=[Executable("onepage.py")],
)
