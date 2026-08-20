####
# test_platform.py:
#
# Tests for `fprime_find_platform_file` (cmake/platform/platform.cmake).
#
####
import re
import shutil
import tempfile
from pathlib import Path

import pytest

from . import cmake
from . import settings

SOURCE_CMAKE_LISTS = settings.DATA_DIR / "TestPlatformResolution" / "CMakeLists.txt"
PLATFORM_PATTERN = re.compile(r"\[test\] PLATFORM_FILE=(.+)")


def run_platform_case(platform, project_platform=None, options=None):
    """Run CMake generation and return the selected platform file and stderr."""
    with tempfile.TemporaryDirectory() as source_root, tempfile.TemporaryDirectory() as build_root:
        source_directory = Path(source_root)
        build_directory = Path(build_root)
        shutil.copy2(SOURCE_CMAKE_LISTS, source_directory / "CMakeLists.txt")

        expected = None
        if project_platform is not None:
            expected = source_directory / project_platform
            expected.parent.mkdir(parents=True, exist_ok=True)
            expected.write_text("# test platform\n", encoding="utf-8")

        cmake_options = {
            "FPRIME_FRAMEWORK_PATH": str(settings.FRAMEWORK_PATH),
            "FPRIME_PLATFORM": platform,
        }
        if options:
            cmake_options.update(options)

        return_code, stdout, stderr = cmake.run_cmake(
            source_directory, build_directory, cmake_options
        )
        matches = [PLATFORM_PATTERN.search(line) for line in stdout]
        platform_files = [Path(match.group(1)).resolve() for match in matches if match]
        return (
            return_code,
            platform_files[0] if platform_files else None,
            expected.resolve() if expected is not None else None,
            stderr,
        )


@pytest.mark.parametrize(
    ("platform", "relative_path"),
    [
        ("ProjectDirect", "cmake/platform/ProjectDirect.cmake"),
        ("ProjectLibrary", "lib/TestLibrary/cmake/platform/ProjectLibrary.cmake"),
        (
            "ProjectSubdirectory",
            "TestSubdirectory/cmake/platform/ProjectSubdirectory.cmake",
        ),
    ],
)
def test_platform_project_locations(platform, relative_path):
    """Supported project-relative platform locations are discovered."""
    return_code, platform_file, expected, _ = run_platform_case(
        platform, project_platform=relative_path
    )
    assert return_code == 0, "CMake generation failed"
    assert platform_file == expected


def test_platform_framework_fallback():
    """The framework platform directory remains the final fallback."""
    return_code, platform_file, _, _ = run_platform_case("Linux")
    expected = (settings.FRAMEWORK_PATH / "cmake/platform/Linux.cmake").resolve()
    assert return_code == 0, "CMake generation failed"
    assert platform_file == expected


@pytest.mark.parametrize(
    ("legacy_variable", "platform"),
    [
        ("FPRIME_PROJECT_ROOT", "LegacyProjectRoot"),
        ("FPRIME_LIBRARY_LOCATIONS", "LegacyLibrary"),
    ],
)
def test_platform_ignores_legacy_search_variables(legacy_variable, platform):
    """Removed compatibility variables no longer contribute platform locations."""
    with tempfile.TemporaryDirectory() as legacy_root:
        legacy_file = Path(legacy_root) / "cmake/platform" / f"{platform}.cmake"
        legacy_file.parent.mkdir(parents=True)
        legacy_file.write_text("# legacy platform\n", encoding="utf-8")
        return_code, platform_file, _, stderr = run_platform_case(
            platform, options={legacy_variable: legacy_root}
        )

    assert return_code != 0, f"{legacy_variable} should not resolve a platform"
    assert platform_file is None
    assert "No platform config for" in "".join(stderr)
