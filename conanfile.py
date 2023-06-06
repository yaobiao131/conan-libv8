import os

from conan.tools.cmake import CMakeToolchain, CMake
from conan.tools.files import patch
from conans import ConanFile


class LibV8Conan(ConanFile):
    name = "libv8"
    version = "11.5"
    # Optional metadata
    license = "MIT"
    homepage = "https://github.com/nodejs/node"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Node.js JavaScript runtime"
    exports_sources = "patches/*.patch"
    settings = "os", "compiler", "build_type", "arch"

    scm = {
        "type": "git",
        "url": "https://github.com/bnoordhuis/v8-cmake.git"
    }

    def source(self):
        patch(self, patch_file=os.path.join(self.source_folder, "patches/0001-Add-Install-To-Cmake.patch"))

    def generate(self):
        tc = CMakeToolchain(self, 'Ninja')
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        libs = ["v8_libbase", "v8_libplatform", "v8_initializers", "v8_inspector", "v8_base_without_compiler",
                "v8_compiler", "v8_torque_generated", "v8_libsampler", "v8_snapshot"]
        if self.settings.os == "Windows":
            libs.append("dbghelp")
            libs.append("winmm")
        self.cpp_info.libs = libs
