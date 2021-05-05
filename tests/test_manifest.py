
import os
import time
import shutil
import tempfile
import unittest
from deliver.pkgs import DevRepoManager, PackageInstaller
from .util import TestBase, DeveloperPkgRepo, early


class TestManifest(TestBase):

    def setUp(self):
        root = tempfile.mkdtemp(prefix="rez_deliver_test_")
        install_path = os.path.join(root, "install")
        release_path = os.path.join(root, "release")
        dev_repo_path = os.path.join(root, "developer")

        self.root = root
        self.install_path = install_path
        self.release_path = release_path
        self.dev_repo_path = dev_repo_path
        self.dev_repo = DeveloperPkgRepo(dev_repo_path)
        self.settings = {
            "packages_path": [install_path, release_path],
            "local_packages_path": install_path,
            "release_packages_path": release_path,
            "plugins": {
                "command": {"deliver": {
                    "dev_repository_roots": [dev_repo_path]
                }}
            }
        }
        super(TestManifest, self).setUp()

        self.installer = PackageInstaller(DevRepoManager())

    def tearDown(self):
        # from rez.serialise import clear_file_caches
        retries = 5
        if os.path.exists(self.root):
            for i in range(retries):
                try:
                    shutil.rmtree(self.root)
                    break
                except Exception:
                    if i < (retries - 1):
                        time.sleep(0.2)

    def test_resolve_1(self):
        self.dev_repo.add("foo", version="1")
        self.dev_repo.add("bar", version="1", requires=["foo"])

        self.installer.resolve("bar")

        manifest = self.installer.manifest()
        self.assertEqual("foo-1", manifest[0].name)
        self.assertEqual("bar-1", manifest[1].name)

    def test_resolve_2(self):
        self.dev_repo.add("foo", version="1")
        self.dev_repo.add("goo", version="1")
        self.dev_repo.add("bar", version="1", variants=[["foo"], ["goo"]])

        self.installer.resolve("bar")

        manifest = self.installer.manifest()
        self.assertEqual("foo-1", manifest[0].name)
        self.assertEqual(("bar-1", 0), (manifest[1].name, manifest[1].index))
        self.assertEqual("goo-1", manifest[2].name)
        self.assertEqual(("bar-1", 1), (manifest[3].name, manifest[3].index))

    def test_resolve_with_os(self):
        # need to install bar first so the wildcard request can be expanded.
        installed_repo = DeveloperPkgRepo(self.install_path)
        installed_repo.add("bar", version="x")

        self.dev_repo.add("foo", version="1", variants=[["bar-*"]])
        self.installer.resolve("foo")

        manifest = self.installer.manifest()
        self.assertTrue(manifest[-2].name.startswith("bar-"))
        self.assertEqual(("foo-1", 0), (manifest[-1].name, manifest[-1].index))

    def test_resolve_with_variants(self):
        self.dev_repo.add("python", version="2.7")
        self.dev_repo.add("python", version="3.7")
        self.dev_repo.add("foo", variants=[["python-2"], ["python-3"]])
        self.installer.resolve("foo")

        manifest = self.installer.manifest()
        self.assertEqual(4, len(manifest))
        for req in manifest:
            self.assertEqual(self.installer.Ready, req.status)

    def test_resolve_early_build(self):

        @early()
        def bar_requires():
            if building:
                return []
            else:
                return ["!ehh"]

        with self.dev_repo.enable_out_early():
            self.dev_repo.add("foo", requires=["bar", "ehh"])
            self.dev_repo.add("bar", requires=bar_requires)
            self.dev_repo.add("ehh")

        self.installer.resolve("foo")
        manifest = self.installer.manifest()
        self.assertEqual(3, len(manifest))
        for req in manifest:
            self.assertEqual(self.installer.Ready, req.status)

    def test_resolve_with_installed(self):
        installed_repo = DeveloperPkgRepo(self.install_path)
        installed_repo.add("bar")
        installed_repo.add("foo", version="1", variants=[["bar"]])

        self.dev_repo.add("foo", version="2", variants=[["bar"]])

        self.installer.resolve("foo")
        manifest = self.installer.manifest()
        foo_request = next(r for r in manifest if r.name == "foo-2")
        self.assertEqual(self.installer.Ready, foo_request.status)


if __name__ == "__main__":
    unittest.main()
