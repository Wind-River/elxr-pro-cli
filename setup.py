import glob
import setuptools

NAME = "elxr-pro"

INSTALL_REQUIRES = open("requirements.txt").read().rstrip("\n").split("\n")


def split_link_deps(reqs_filename):
    """Read requirements reqs_filename and split into pkgs and links

    :return: list of package defs and link defs
    """
    pkgs = []
    links = []
    for line in open(reqs_filename).readlines():
        if line.startswith("git") or line.startswith("http"):
            links.append(line)
        else:
            pkgs.append(line)
    return pkgs, links

TEST_REQUIRES, TEST_LINKS = split_link_deps("requirements.test.txt")

def _get_data_files():
    return [
        ("/etc/elxr-advantage", ["eaclient.conf"]),
        ("/usr/share/keyrings", glob.glob("keyrings/*")),
    ]

setuptools.setup(
    name=NAME,
    # This version does not matter, it is not used anywhere but in unit tests
    # AND IT IS OVER 8000
    version="8001",
    packages=setuptools.find_packages(
        exclude=[
            "*.testing",
            "tests.*",
            "*.tests",
            "tests",
            "features",
            "features.*",
        ]
    ),
    data_files=_get_data_files(),
    install_requires=INSTALL_REQUIRES,
    dependency_links=TEST_LINKS,
    extras_require=dict(test=TEST_REQUIRES),
    author="eLxr Pro Team",
    author_email="elxr-pro-core-dev@windriver.com",
    description=("Manage eLxr Pro support entitlements"),
    license="Apache2",
    url="https://elxr.pro",
    entry_points={
        "console_scripts": [
            "elxr-pro=eaclient.cli:main",
        ]
    },
)
