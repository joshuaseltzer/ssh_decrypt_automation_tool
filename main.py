import tools.ssh_connection as ssh_connection
import tools.app_data as settings
import tools.utils as utils
import argparse


client, username, password, ip = None, None, None, None
listed_applications = None
auto_dump, interrupted = False, False


parser = argparse.ArgumentParser(description="This tool automates the process of dumping multiple iOS apps at once in jailbroken devices.")
parser.add_argument(
    "-a",
    "--app_bundle_id",
    help="The application bundle ID (e.g. com.google.ios.youtube) that you would like to decrypt. When this option is not specified, the tool is launched in interactive mode. Note: this option is only valid when specifying the ip_address, username, and password arguments or if saved settings for an existing device already exist.",
    type=str
)
parser.add_argument(
    "-i",
    "--ip_address",
    help="The IP address of the device to connect to when decrypting the specified app_bundle_id. Note: this option will override the saved IP address for future uses of this tool.",
    type=str
)
parser.add_argument(
    "-u",
    "--username",
    help="The SSH username to use when decrypting the specified app_bundle_id. Note: this option will override the saved username for future uses of this tool. The password argument is required if this argument is used.",
    type=str
)
parser.add_argument(
    "-p",
    "--password",
    help="The SSH password to use when decrypting the specified app_bundle_id. Note: this option will override the saved password for future uses of this tool. The username argument is required when this argument is used.",
    type=str
)
parser.add_argument(
    "-b",
    "--bfdecrypt",
    help="Use bfdecrypt when decrypting the specified app_bundle_id. Note: this option will override the saved decryption utility for future uses of this tool.",
    action="store_true"
)
parser.add_argument(
    "-c",
    "--clutch",
    help="Use Clutch when decrypting the specified app_bundle_id. Note: this option will override the saved decryption utility for future uses of this tool.",
    action="store_true"
)
args = parser.parse_args()
if args.app_bundle_id:
    auto_dump = True
    if args.ip_address:
        settings.save_ip_file(args.ip_address)
    if args.username and args.password:
        settings.save_up_file(args.username, args.password)
    if args.bfdecrypt and args.clutch:
        settings.select_decrypt_utility("4")
    elif args.bfdecrypt:
        settings.select_decrypt_utility("2")
    elif args.clutch:
        settings.select_decrypt_utility("1")


def connect(setup_new_device):
    global client, username, password, ip, listed_applications
    client, username, password, ip = ssh_connection.setup_connection(setup_new_device)
    if client is not None:
        listed_applications = ssh_connection.list_apps(client)


if settings.AUTHENTICATE_ON_STARTUP.exists() or auto_dump:
    connect(False)
    utils.clear_terminal()


settings.read_decrypt_method_config()
if auto_dump:
    if client is None:
        print(f'Failed to dump {args.app_bundle_id}: Could not connect to the device')
    elif listed_applications is None or len(listed_applications) == 0:
        print(f'Failed to dump {args.app_bundle_id}: the listed applications could not be determined or there are none installed')
    elif not settings.decrypt_method:
        print(f'Failed to dump {args.app_bundle_id}: A decryption utility was not specified or previously saved')
    else:
        found_app = False
        for app in listed_applications:
            if app.app_bundle == args.app_bundle_id:
                found_app = True
                break
        if found_app:
            ssh_connection.dump_app(client, app, False)
        else:
            print(f'Failed to dump {args.app_bundle_id}: Could not find the specified application on the device, are you sure it is installed?')
else:
    while True:
        try:
            print("    Welcome to ssh decrypt automation tool")
            print("        By WholesomeThoughts26\n")
            print("  Main menu")
            options = ["1", "E"]

            try:
                # Check if client is alive
                if client is not None:
                    client.exec_command("ls")
            except AttributeError:
                client, username, password, ip = None, None, None, None
                listed_applications = None

            if client is None:
                print("1. Connect to iOS device")
            else:
                options.append("2")
                options.append("3")

                print(f"1. Disconnect from '{ip}'")
                if listed_applications is None:
                    print("2. List apps")
                else:
                    print("2. Re-list apps")

                if not settings.decrypt_method:
                    print("3. Select decrypt utility (needed to decrypt apps)")
                else:
                    print("3. Dump app")
                    print("4. Dump multiple apps")
                    options.append("4")

                print("S. Settings")
                options.append("S")

            print("E. Exit")
            print("Select an option")

            option = utils.choose(options)

            if option == "1":
                if client is None:
                    connect(True)
                else:
                    ssh_connection.disconnect(client)
                    client, username, password, ip = None, None, None, None

            if option == "2":
                utils.clear_terminal()
                listed_applications = ssh_connection.list_apps(client)

            if option == "3":
                if not settings.decrypt_method:
                    settings.select_decrypt_utility()
                elif ssh_connection.is_idevice_ready(client):
                    app = utils.select_apps(listed_applications, False)
                    if app is not None:
                        ssh_connection.dump_app(client, app, False)

            if option == "4":
                if ssh_connection.is_idevice_ready(client):
                    ssh_connection.dump_multiple_apps(client, utils.select_apps(listed_applications, True))

            if option == "S":
                settings.show_settings_menu(username, password, ip)

            if option == "E":
                break

            input("\nPress enter to continue... ")
            utils.clear_terminal()
        except KeyboardInterrupt:
            interrupted = client is not None
            break

if client is not None:
    if interrupted:
        print("  Please don't interrupt disconnection process!")
    ssh_connection.disconnect(client)
