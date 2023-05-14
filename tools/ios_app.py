from pathlib import Path

# Utilities for apps management

LOCAL_CACHE_DIR = Path().cwd().joinpath("cache")
APPLICATION_BUNDLES = "/var/containers/Bundle/Application/"
APPLICATION_DOCUMENTS = "/var/mobile/Containers/Data/Application/"
MOBILE_DOCUMENTS = "/var/mobile/Documents/"

MOBILE_SUBSTRATE_PATH_ROOT = "/Library/MobileSubstrate/DynamicLibraries/"
MOBILE_SUBSTRATE_PATH_XINA = "/var/Library/MobileSubstrate/DynamicLibraries/"
MOBILE_SUBSTRATE_PATH_ROOTLESS = "/var/jb/Library/MobileSubstrate/DynamicLibraries/"
MOBILE_SUBSTRATE_PATHS = [MOBILE_SUBSTRATE_PATH_ROOTLESS, MOBILE_SUBSTRATE_PATH_ROOT, MOBILE_SUBSTRATE_PATH_XINA]

MS_BFDECRYPT_SETTINGS = "bfdecrypt.plist"
MS_BFDECRYPT_SETTINGS_ROOT_F = MOBILE_SUBSTRATE_PATH_ROOT + MS_BFDECRYPT_SETTINGS
MS_BFDECRYPT_SETTINGS_XINA_F = MOBILE_SUBSTRATE_PATH_XINA + MS_BFDECRYPT_SETTINGS
MS_BFDECRYPT_SETTINGS_ROOTLESS_F = MOBILE_SUBSTRATE_PATH_ROOTLESS + MS_BFDECRYPT_SETTINGS
MS_BFDECRYPT_SETTINGS_F = [MS_BFDECRYPT_SETTINGS_ROOTLESS_F, MS_BFDECRYPT_SETTINGS_ROOT_F, MS_BFDECRYPT_SETTINGS_XINA_F]

BFDECRYPT_SETTINGS_PATH = "/var/mobile/Library/Preferences/"
BFDECRYPT_SETTINGS = "com.level3tjg.bfdecrypt.plist"
BFDECRYPT_SETTINGS_F = BFDECRYPT_SETTINGS_PATH + BFDECRYPT_SETTINGS
BFDECRYPT_IPA_NAME = "decrypted-app.ipa"

ROOTLESS_PREFIX = "/var/jb"
BIN_INSTALL_PATH = "/usr/local/bin/"
LIB_INSTALL_PATH = "/usr/local/lib/"
UIOPEN_NAME = "uiopen"
UIOPEN_LOCAL_PATH = "uiopen_2.1.6-1"


def is_there_any_cache() -> int:
    global LOCAL_CACHE_DIR
    if LOCAL_CACHE_DIR.exists():
        return len(list(LOCAL_CACHE_DIR.iterdir()))

    return 0


def clear_cache():
    global LOCAL_CACHE_DIR
    if not LOCAL_CACHE_DIR.exists():
        return

    for cache in LOCAL_CACHE_DIR.iterdir():
        cache.unlink()


# This class holds various information about
# installed apps

class AppInfo:
    def __init__(self, bundle_id: str, ios_device_plist_path: str):
        self.bundle_id: str = bundle_id
        self.bundle_path: str = ios_device_plist_path
        self.docs_bundle_id: str = ""

        self.ios_device_plist_path: str = ios_device_plist_path
        self.local_plist_path: Path
        self.app_executable: str = ""
        self.app_name: str = ""
        self.app_bundle: str = ""
        self.app_version: str = ""
