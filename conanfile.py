import os

from conans import ConanFile, tools


class LibV8Conan(ConanFile):
    name = "libv8"
    version = "11.5"
    # Optional metadata
    license = "BSD"
    homepage = "https://github.com/v8/v8"
    url = "https://github.com/v8/v8"
    description = "v8"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = {"shared": False}
    no_copy_source = True

    @property
    def gn_arch(self):
        arch_map = {
            "x86_64": "x64",
            "armv8": "arm64"
        }

        arch = str(self.settings.arch)
        return arch_map.get(arch, arch)

    def build_requirements(self):
        if not tools.which("ninja"):
            self.build_requires("ninja/1.10.0")

    def _set_environment_vars(self):
        """set the environment variables, such that the google tooling is found (including the bundled python2)"""
        os.environ["PATH"] = os.path.join(self.source_folder, "depot_tools") + os.pathsep + os.environ["PATH"]
        os.environ["DEPOT_TOOLS_PATH"] = os.path.join(self.source_folder, "depot_tools")
        if tools.os_info.is_windows:
            os.environ["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"
        if tools.os_info.is_macos and self.gn_arch == "arm64":
            os.environ["VPYTHON_BYPASS"] = "manually managed python not supported by chrome operations"

    def source(self):
        tools.Git(folder="depot_tools").clone("https://chromium.googlesource.com/chromium/tools/depot_tools.git",
                                              shallow=True)
        self._set_environment_vars()
        self.run("fetch v8")

        # with tools.chdir("v8"):
        #     # self.run("git checkout {}".format(self.version))
        #     self.run("gclient sync")

    def _gen_arguments(self):
        # Refer to v8/infra/mb/mb_config.pyl
        is_debug = "true" if str(self.settings.build_type) == "Debug" else "false"
        is_clang = "true" if ("clang" in str(self.settings.compiler).lower()) else "false"
        is_shared = "true" if self.options.shared == True else "false"
        gen_arguments = [
            f"is_debug={is_debug}",
            f"is_component_build={is_shared}",
            "symbol_level=0",
            # cc_wrapper="ccache"
            "treat_warnings_as_errors=false",
            "use_custom_libcxx=false",
            "v8_enable_i18n_support=false",
            "v8_use_external_startup_data=false",
            "v8_enable_gdbjit=false",
            "v8_enable_pointer_compression=false",
            "v8_enable_webassembly=false",
            "v8_enable_31bit_smis_on_64bit_arch=false",
            "v8_trace_maps=false",
            "v8_use_siphash=false"
        ]

        return gen_arguments

    def build(self):
        v8_source_root = os.path.join(self.source_folder, "v8")
        self._set_environment_vars()

        with tools.chdir(v8_source_root):
            args = self._gen_arguments()
            args_gn_file = os.path.join(self.build_folder, "args.gn")
            with open(args_gn_file, "w") as f:
                f.write("\n".join(args))

            generator_call = "gn gen {folder}".format(folder=self.build_folder)

            self.run("python --version")
            print(generator_call)
            self.run(generator_call)
            self.run("ninja -C {folder} v8".format(folder=self.build_folder))

    def package(self):
        self.copy(pattern="v8.dll", dst="bin", keep_path=False)
        self.copy(pattern="v8_libbase.dll", dst="bin", keep_path=False)
        self.copy(pattern="v8_libplatform.dll", dst="bin", keep_path=False)
        self.copy(pattern="third_party_zlib.dll", dst="bin", keep_path=False)
        self.copy(pattern="third_party_zlib.dll.lib", dst="lib", keep_path=False)
        self.copy(pattern="v8.dll.lib", dst="lib", keep_path=False)
        self.copy(pattern="v8_libbase.dll.lib", dst="lib", keep_path=False)
        self.copy(pattern="v8_libplatform.dll.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.h", dst="include", src="v8/include", keep_path=True)

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["v8_libplatform.dll.lib", "v8.dll.lib", "v8_libbase.dll.lib"]
        else:
            self.cpp_info.libs = ["v8_libplatform", "v8", "v8_libbase"]
