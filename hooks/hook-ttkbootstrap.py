"""PyInstaller hook for ttkbootstrap — exclude unused theme image resources."""
from PyInstaller.utils.hooks import collect_data_files

# Only collect data files, exclude all theme images and unused theme directories
datas = collect_data_files(
    "ttkbootstrap",
    excludes=[
        "**/*.png", "**/*.gif", "**/*.jpg",
        "**/lumen/**",    "**/litera/**",  "**/minty/**",
        "**/pulse/**",    "**/united/**",  "**/morph/**",
        "**/cerculean/**", "**/journal/**", "**/sandstone/**",
        "**/superhero/**", "**/solar/**",   "**/cyborg/**",
    ],
)
