import pathlib
import os
import tools.bundle_management as bm
import tools.app_data as app_data
import tools.ios_app as ios_apps
import paramiko
import socket
import tools.utils as utils
import getpass
import plistlib
from paramiko.channel import ChannelFile
from socket import gaierror
from time import sleep
from re import findall, sub


# Utilities for connection

is_rootless = False
remote_bin_install_path = ""
remote_lib_install_path = ""
bfdecrypt_settings_f = ""


def connect(ip: str, username: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(ip, username=username, password=password, timeout=30)

    global is_rootless
    global remote_bin_install_path
    global remote_lib_install_path
    global bfdecrypt_settings_f
    ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(f"ls {ios_apps.ROOTLESS_PREFIX}")
    output = read_output(ssh_stdout)
    if output and len(output) > 0:
        is_rootless = True
        remote_bin_install_path = os.path.join(ios_apps.ROOTLESS_PREFIX, ios_apps.BIN_INSTALL_PATH)
        remote_lib_install_path = os.path.join(ios_apps.ROOTLESS_PREFIX, ios_apps.LIB_INSTALL_PATH)
        bfdecrypt_settings_f = ios_apps.BFDECRYPT_SETTINGS_PATH_ROOTLESS + ios_apps.BFDECRYPT_SETTINGS
    else:
        remote_bin_install_path = ios_apps.BIN_INSTALL_PATH
        remote_lib_install_path = ios_apps.LIB_INSTALL_PATH
        bfdecrypt_settings_f = ios_apps.BFDECRYPT_SETTINGS_PATH + ios_apps.BFDECRYPT_SETTINGS

    return client


def disconnect(client: paramiko.SSHClient):
    print("Closing connection... ", end="", flush=True)
    if client:
        sleep(5)
        client.close()
        print("Done")
    else:
        print("No connection was opened")


def is_client_darwin(client: paramiko.SSHClient) -> bool:
    ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command("uname")
    return findall("Darwin", read_output(ssh_stdout)) != []


def disconnect_sftp(sftp_client: paramiko.SFTPClient):
    if sftp_client:
        sleep(5)
        sftp_client.close()


def setup_connection(ask_to_setup_new_idevice=True) -> list:
    utils.clear_terminal()
    print("    Connection setup")
    tmp_ip = app_data.read_ip_file()
    if not tmp_ip:
        ip = None
    else:
        ip = tmp_ip

    tmp_up = app_data.read_up_file()
    if not tmp_up or len(tmp_up) != 2:
        username = None
        password = None
    else:
        username = tmp_up[0]
        password = tmp_up[1]

    client = None

    if tmp_ip and tmp_up and ask_to_setup_new_idevice:
        print("\nDo you want to setup a new device?")
        print("1. Yes")
        print(f"2. No, connect to {ip}")
        if utils.choose(["1", "2"], [True, False]):
            ip, username, password = None, None, None
            ios_apps.clear_cache()

    attempts = 0

    while client is None and attempts < 3:
        if ip is None:
            print("\nEnter the iOS device IP:")
            ip = input("> ")
            if not ip:
                ip = None
                continue

        if username is None or password is None:
            print("\nEnter your credentials")
            print("    Do you want to login with root/alpine?")
            print("1. Yes")
            print("2. No, let me enter my username and password")

            if utils.choose(["1", "2"], [True, False]):
                username, password = "root", "alpine"
            else:
                print("\nEnter your username")
                username = input("> ")
                if not username:
                    username = None
                    continue

                print("\nEnter your password")
                password = getpass.getpass("> ")

        try:
            print("\nTrying connection... ", end="", flush=True)
            client = connect(ip, username, password)
        except socket.timeout:
            print("Time out!")
            client = None
            ip = None
            attempts += 1
            continue
        except (paramiko.ssh_exception.NoValidConnectionsError, gaierror):
            print(f"Failed to find host '{ip}'")
            client = None
            ip = None
            attempts += 1
            continue
        except paramiko.ssh_exception.AuthenticationException:
            print("Failed to authenticate!")
            client = None
            username = None
            password = None
            attempts += 1
            continue

    if not client:
        print("\n    Please check your internet connection, username and password")
        print("    If you need more assistance, check README.md file\n")
        raise InterruptedError("Too many attempts")

    print("Connection success!")

    if password == "alpine":
        print("\n    Please, consider changing ssh default password!")

    if not is_client_darwin(client):
        print("\n    Looks like you're not connected to an iOS device...")
        disconnect(client)
        return [None, None, None, None]

    return [client, username, password, ip]


def read_output(ssh_stdout: ChannelFile) -> str:
    data = ssh_stdout.read()
    if data:
        return data.decode("utf-8")

    return ""


def put_clutch_troll(client: paramiko.SSHClient) -> bool:
    if not app_data.does_clutch_exist():
        utils.clear_terminal()
        print("    Clutch_troll not found...")
        print("1. Provide a copy")
        print("2. Abort installation")
        print("Select an option")
        if utils.choose(["1", "2"], [True, False]):
            app_data.get_file_copy(True)
            return put_clutch_troll(client)
        else:
            return False

    ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(f"cd {ios_apps.MOBILE_DOCUMENTS}; ls")
    output = read_output(ssh_stdout)
    if "Clutch_troll" not in output:
        try:
            sftp_client = client.open_sftp()
            sftp_client.put(app_data.CLUTCH_EXECUTABLE, ios_apps.MOBILE_DOCUMENTS + "Clutch_troll")
            disconnect_sftp(sftp_client)
            client.exec_command(f"cd {ios_apps.MOBILE_DOCUMENTS}; chmod +x Clutch_troll")
            return True
        except FileNotFoundError:
            print("It's not possible copy Clutch_troll!")
            return False

    client.exec_command(f"cd {ios_apps.MOBILE_DOCUMENTS}; chmod +x Clutch_troll")

    return True


def install_bfdecrypt(client: paramiko.SSHClient) -> bool:
    utils.clear_terminal()
    if not app_data.does_bfdecrypt_exist():
        utils.clear_terminal()
        print("    bfdecrypt deb not found...")
        print("1. Provide a copy")
        print("2. Abort installation")
        print("Select an option")
        if utils.choose(["1", "2"], [True, False]):
            app_data.get_file_copy(False)
            return install_bfdecrypt(client)
        else:
            return False

    print("Installing... ", end="", flush=True)

    sftp_client = client.open_sftp()
    try:
        sftp_client.put(app_data.BFDECRYPT_DEB, ios_apps.MOBILE_DOCUMENTS + app_data.BFDECRYPT_DEB.name)
    except FileNotFoundError:
        if app_data.BFDECRYPT_DEB.exists():
            print(f"    w h a t?\n\"{ios_apps.MOBILE_DOCUMENTS}\" doesn't exist, this might be a Mac")
        else:
            print(f"{app_data.BFDECRYPT_DEB} doesn't exist")
        return False

    disconnect_sftp(sftp_client)

    ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(
        f"cd {ios_apps.MOBILE_DOCUMENTS}; dpkg -i {app_data.BFDECRYPT_DEB.name}"
    )

    output = read_output(ssh_stderr)
    if "com.spark.libsparkapplist" in output:
        print("Failed!")
        print("    \"libsparkapplist\" is required!")
        print("        If you need assistance, please check README.md")
        client.exec_command("dpkg --remove com.level3tjg.bfdecrypt")
        return False

    print("Success")

    return True


def is_bfdecrypt_installed(client: paramiko.SSHClient) -> bool:
    attempts = 0
    found_ms_dir = False
    while True:
        if not found_ms_dir and attempts < len(ios_apps.MOBILE_SUBSTRATE_PATHS):
            try:
                ms_dir = ios_apps.MOBILE_SUBSTRATE_PATHS[attempts]
                ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(
                    f"cd {ms_dir}; ls"
                )

                error = read_output(ssh_stderr)
                if "no such file or directory" in error.lower():
                    raise FileNotFoundError
                else:
                    found_ms_dir = True
            except FileNotFoundError:
                attempts+=1
                continue

        if found_ms_dir:
            output = read_output(ssh_stdout)
            if ios_apps.MS_BFDECRYPT_SETTINGS in output:
                return True
            else:
                print("Failed to find the bfdecrypt settings file! Are you sure it is installed?")
        else:
            print("Failed to find the MobileSubstrate directory!")
        
        print("\n1. Attempt to find bfdecrypt again")
        print("2. Install bfdecrypt")
        print("3. Cancel")
        print("Select an option")
        option = utils.choose(["1", "2", "3"])

        attempts = 0
        found_ms_dir = False
        if option == "1":
            continue
        elif option == "2":
            if not install_bfdecrypt(client):
                input("\nPress enter to continue... ")
        else:
            return False

def is_uiopen_installed(client: paramiko.SSHClient) -> bool:
    ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(f"PATH={remote_bin_install_path}:$PATH uiopen --help")
    output = read_output(ssh_stdout)

    if "--bundleid" in output:
        return True
    else:
        print(f"\nThe Procursus version of {ios_apps.UIOPEN_NAME} was not found on the device.")
        print(f"1. Install it to {remote_bin_install_path}")
        print("2. Cancel")
        print("Select an option")
        option = utils.choose(["1", "2"])

        if option == "1":
            client.exec_command(f"mkdir -p {remote_bin_install_path}")
            client.exec_command(f"mkdir -p {remote_lib_install_path}")

            sftp_client = client.open_sftp()
            local_lib_path = os.path.join(ios_apps.UIOPEN_LOCAL_PATH, "lib")
            for local_lib_file in os.listdir(local_lib_path):
                lib_file = os.path.join(local_lib_path, local_lib_file)
                if os.path.isfile(lib_file):
                    sftp_client.put(lib_file, os.path.join(remote_lib_install_path, local_lib_file))
            remote_uiopen_file = os.path.join(remote_bin_install_path, ios_apps.UIOPEN_NAME)
            sftp_client.put(os.path.join(ios_apps.UIOPEN_LOCAL_PATH, ios_apps.UIOPEN_NAME), remote_uiopen_file)
            fix_file_permissions(client, "u+x", remote_uiopen_file, use_sudo=is_rootless)
            disconnect_sftp(sftp_client)
            
            return is_uiopen_installed(client)
        elif option == "2":
            return False
        else:
            return False


def is_idevice_ready(client: paramiko.SSHClient) -> bool:
    check_clutch = app_data.DumpUtility.CLUTCH.name in app_data.decrypt_method
    check_bfdecrypt = app_data.DumpUtility.BFDECRYPT.name in app_data.decrypt_method

    ready = True
    if check_clutch:
        ready = ready and put_clutch_troll(client)

    if check_bfdecrypt:
        ready = ready and is_bfdecrypt_installed(client)

    ready = ready and is_uiopen_installed(client)

    return ready


def list_bundle_ids(client: paramiko.SSHClient, find_documents: bool) -> list:
    if find_documents:
        ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(f"cd {ios_apps.APPLICATION_DOCUMENTS}; ls")
    else:
        ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(f"cd {ios_apps.APPLICATION_BUNDLES}; ls")

    output = read_output(ssh_stdout)

    return bm.find_plists(output, find_documents)


def find_app_executables(client: paramiko.SSHClient, listed_apps: list):
    for app in listed_apps:
        app_path = app.ios_device_plist_path.replace("/iTunesMetadata.plist", "")
        ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(f"cd {app_path}; ls")
        output = read_output(ssh_stdout)
        executable_name = findall(r".+\.app", output)
        if executable_name:
            app.app_executable = executable_name[0].replace(".app", "")


def document_plist_to_local_path(plist: str) -> pathlib.Path:
    local_plist_name = plist.replace("/.com.apple.mobile_container_manager.metadata.plist", "")
    local_plist_name = "d_" + local_plist_name.replace(ios_apps.APPLICATION_DOCUMENTS, "") + ".plist"
    return ios_apps.LOCAL_CACHE_DIR.joinpath(local_plist_name)


def retrieve_apps_plists(client: paramiko.SSHClient, listed_applications: list, documents_plists: list):
    if not ios_apps.LOCAL_CACHE_DIR.exists():
        ios_apps.LOCAL_CACHE_DIR.mkdir()

    sftp_client = client.open_sftp()

    for app in listed_applications:
        app.local_plist_path = ios_apps.LOCAL_CACHE_DIR.joinpath(app.bundle_id + ".plist")
        if app.local_plist_path.exists():
            continue

        try:
            remote_file = sftp_client.open(app.ios_device_plist_path, "rb")
            utils.write_binary_file(app.local_plist_path, remote_file.read())
        except FileNotFoundError:
            pass

    for plist in documents_plists:
        local_plist_path = document_plist_to_local_path(plist)
        if local_plist_path.exists():
            continue

        try:
            remote_file = sftp_client.open(plist, "rb")
            utils.write_binary_file(local_plist_path, remote_file.read())
        except FileNotFoundError:
            pass

    disconnect_sftp(sftp_client)


def link_documents_plist(listed_applications: list, documents_plists: list):
    for plist in documents_plists:
        if isinstance(plist, pathlib.Path):
            local_plist_path = plist
        else:
            local_plist_path = document_plist_to_local_path(plist)

        contents = utils.read_plist_file(local_plist_path)

        for app in listed_applications:
            if contents["MCMMetadataIdentifier"] == app.app_bundle:
                app.docs_bundle_id = local_plist_path.name.replace(".plist", "").replace("d_", "")


def retrieve_apps_names(client: paramiko.SSHClient, listed_applications: list, documents_plists: list):
    files_in_cache = ios_apps.is_there_any_cache()
    download_plist = files_in_cache == 0 or files_in_cache != (len(listed_applications) + len(documents_plists))

    if download_plist:
        retrieve_apps_plists(client, listed_applications, documents_plists)
    else:
        for app in listed_applications:
            app.local_plist_path = ios_apps.LOCAL_CACHE_DIR.joinpath(app.bundle_id + ".plist")

    for app in listed_applications:
        plist_data = utils.read_plist_file(app.local_plist_path)
        if not plist_data:
            continue

        try:
            app.app_name = plist_data["itemName"]
            app.app_bundle = plist_data["softwareVersionBundleId"]
            app.app_version = plist_data["bundleShortVersionString"]
        except KeyError:
            continue

    link_documents_plist(listed_applications, documents_plists)


def list_apps(client: paramiko.SSHClient) -> list:
    print("\nListing apps... ", end="", flush=True)
    listed_applications = list_bundle_ids(client, False)
    plist_documents = list_bundle_ids(client, True)
    retrieve_apps_names(client, listed_applications, plist_documents)
    find_app_executables(client, listed_applications)
    print("Done")

    return listed_applications


def decrypt_app_with_clutch(client: paramiko.SSHClient, app: ios_apps.AppInfo) -> str:
    cmd = f"cd {ios_apps.MOBILE_DOCUMENTS} && ./Clutch_troll -d {app.app_bundle}"
    ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(cmd)

    output = read_output(ssh_stdout) + "\n" + read_output(ssh_stderr)  # Somehow output is getting into stderr

    if "FAILED" not in output:  # FAILED was not found, meaning that app was decrypted
        decrypted = findall(f"DONE: /private/var/mobile/Documents/Dumped/{app.app_bundle}.*", output)
        if decrypted:
            return str(decrypted[0]).replace("DONE: ", "")

    output = f"Command:    {cmd}\n" \
             f"App:        {app.app_name}\n" \
             f"AppExec:    {app.app_executable}\n" \
             f"AppVersion: {app.app_version}\n" \
             f"AppBundle:  {app.app_bundle}\n" \
             f"AppPath:    {app.bundle_id}\n" \
             f"Clutch output:\n" + output
    app_data.write_log(output)
    return ""


def modify_bfdecrypt_plist(client: paramiko.SSHClient, apps: list) -> bool:
    sftp_client = client.open_sftp()

    bfdecrypt_settings = ios_apps.LOCAL_CACHE_DIR.joinpath(ios_apps.BFDECRYPT_SETTINGS)

    settings_file = sftp_client.open(bfdecrypt_settings_f, "rb")
    utils.write_binary_file(bfdecrypt_settings, settings_file.read())

    file_content = utils.read_plist_file(bfdecrypt_settings)
    selected_apps = []
    for app in apps:
        selected_apps.append(app.app_bundle)
    file_content['selectedApplications'] = selected_apps

    success = False
    if utils.write_binary_file(bfdecrypt_settings, plistlib.dumps(file_content)):
        sftp_client.put(bfdecrypt_settings, bfdecrypt_settings_f)
        success = True

    disconnect_sftp(sftp_client)
    return success


def fix_file_permissions(client: paramiko.SSHClient, permissions: str, file_name: str, use_sudo: bool = False) -> bool:
    if use_sudo:
        sudo_str = "sudo "
    else:
        sudo_str = ""

    ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(
        f"{sudo_str}chmod {permissions} {file_name}", get_pty=True
    )

    if use_sudo:
        print("\nEnter the sudo password")
        password = getpass.getpass("> ")
        ssh_stdin.write(password + '\n')
        ssh_stdin.flush()

    output = read_output(ssh_stderr)
    if output and len(output) > 0:
        return False
    return True


def revert_plist(client: paramiko.SSHClient):  # Revert to avoid re-decrypting if user opens normally
    client.exec_command(f"killall Preferences")
    modify_bfdecrypt_plist(client, list())
    client.exec_command(f"PATH={remote_bin_install_path}:$PATH uiopen 'prefs:root=bfdecrypt'")
    sleep(3)
    client.exec_command(f"killall Preferences")


def decrypt_app_with_bfdecrypt(client: paramiko.SSHClient, app: ios_apps.AppInfo) -> str:
    client.exec_command(f"killall \"{app.app_executable}\"")
    client.exec_command(f"killall Preferences")
    sleep(1)
    client.exec_command(f"PATH={remote_bin_install_path}:$PATH uiopen 'prefs:root=bfdecrypt'")

    documents_path = f"{ios_apps.APPLICATION_DOCUMENTS + app.docs_bundle_id}/Documents/"

    retries = 0
    last_ipa_size = 0
    consecutive_same_sizes = 0
    decrypted = False

    sleep(3)
    client.exec_command(f"PATH={remote_bin_install_path}:$PATH uiopen --bundleid {app.app_bundle}")

    while retries < 30:
        ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(f"du {documents_path}/{ios_apps.BFDECRYPT_IPA_NAME}")
        s_output = read_output(ssh_stdout)
        next_ipa_size = findall(r"\d+", s_output)
        if next_ipa_size and len(next_ipa_size) > 0:
            if last_ipa_size == int(next_ipa_size[0]):
                consecutive_same_sizes+=1
                if consecutive_same_sizes == 3:
                    decrypted = True
                    break
            else:
                last_ipa_size = int(next_ipa_size[0])
            print(f"File size: {int(next_ipa_size[0])}")
        retries+=1
        sleep(3)

    if decrypted:
        client.exec_command(f"killall \"{app.app_executable}\"")
        return f"{documents_path}/{ios_apps.BFDECRYPT_IPA_NAME}"

    return ""


def download_app(client: paramiko.SSHClient, app: ios_apps.AppInfo, ipa_path: str) -> str:
    if not app_data.DOWNLOADED_APPS.exists():
        app_data.DOWNLOADED_APPS.mkdir()

    local_file_name = app_data.DOWNLOADED_APPS.joinpath(app.app_executable.replace(" ", "_") + "_" + app.app_version + ".ipa")

    sftp_client = client.open_sftp()
    try:
        sftp_client.get(ipa_path, local_file_name)
        client.exec_command(f"rm \"{ipa_path}\"")

        return local_file_name.name
    except FileNotFoundError:
        return ""
    finally:
        disconnect_sftp(sftp_client)


def dump_app(client: paramiko.SSHClient, app: ios_apps.AppInfo, multiple_apps: bool):
    utils.clear_terminal()
    print(f"Preparing to dump \"{app.app_name}\" ({app.app_version})...")

    modify_plist_success = True
    if not multiple_apps and app_data.DumpUtility.BFDECRYPT.name in app_data.decrypt_method:
        modify_plist_success = modify_bfdecrypt_plist(client, [app])

    if modify_plist_success:
        ipa_path = ""
        attempt_clutch_first = app_data.decrypt_method.startswith(app_data.DumpUtility.CLUTCH.name)
        clutch_attempted = False
        bfdecrypt_attempted = False

        attempts = 0
        if app_data.DumpUtility.CLUTCH.name in app_data.decrypt_method:
            attempts += 1

        if app_data.DumpUtility.BFDECRYPT.name in app_data.decrypt_method:
            attempts += 1

        for _ in range(attempts):  # Two attempts to decrypt as maximum
            if not clutch_attempted and app_data.DumpUtility.CLUTCH.name in app_data.decrypt_method and attempt_clutch_first:
                print(f"Dumping {app.app_bundle} ({app_data.DumpUtility.CLUTCH.name})...", end="", flush=True)

                clutch_attempted = True
                ipa_path = decrypt_app_with_clutch(client, app)
            elif not bfdecrypt_attempted and app_data.DumpUtility.BFDECRYPT.name in app_data.decrypt_method:
                print(f"Dumping {app.app_bundle} ({app_data.DumpUtility.BFDECRYPT.name})...\n", end="", flush=True)

                attempt_clutch_first = True  # Just in case if clutch is secondly tried
                bfdecrypt_attempted = True
                ipa_path = decrypt_app_with_bfdecrypt(client, app)

            if ipa_path:
                print("Success")
                if not multiple_apps and app_data.DumpUtility.BFDECRYPT.name in app_data.decrypt_method:  # Revert plist
                    revert_plist(client)

                print("Downloading... ", end="", flush=True)
                downloaded = download_app(client, app, ipa_path)
                if downloaded:
                    print("File saved as", downloaded)
                    break
                else:
                    print("Download failed!")
            else:
                print(f"Error while decrypting ipa!")
    else:
        print("Error modifying the bfdecrypt plist file!")


def dump_multiple_apps(client: paramiko.SSHClient, apps: list):
    modify_plist_success = True
    if app_data.DumpUtility.BFDECRYPT.name in app_data.decrypt_method:
        modify_plist_success = modify_bfdecrypt_plist(client, apps)

    if modify_plist_success:
        for app in apps:
            dump_app(client, app, True)

        if app_data.DumpUtility.BFDECRYPT.name in app_data.decrypt_method:
            revert_plist(client)
    else:
        print("Error modifying the bfdecrypt plist file!")
