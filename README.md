# ssh_decrypt_automation tool

### What is this?

This tool automates the process of dumping decrypted iOS apps for jailbroken devices.

### Disclaimer

- Check out [LICENSE](LICENSE) before using this software.
- **Do not use `Clutch` or `bfdecrypt` for piracy!**
- I am not responsible for any damage or data lost that might occur for using this software.

**You've been warned**

### Compatibility

Tested with:

| Device               | iOS Version | Jailbreak                        |
|----------------------|-------------|----------------------------------|
| iPhone XR      (A12) | 15.1        | XinaA15 1.1.6.2                  |
| iPad Mini 5    (A12) | 15.1        | XinaA15 1.1.6.2                  |
| iPhone XR      (A12) | 14.7.1      | unc0ver 8.0.2                    |
| iPhone SE 2016 (A9)  | 15.7.5      | palera1n 2.0.0 Beta 6 (rootless) |

This tool should work with rootful and rootless jailbreaks (at the moment, bfdecrypt is the only decryption method supported for rootless jailbreaks).

| Operating System            | Python Version  |
|-----------------------------|-----------------|
| macOS Monterey 12.5 (ARM64) | 3.9.6           |
| Debian 11           (ARM64) | 3.10.4          |
| Windows 11          (ARM64) | 3.11.2 (x86-64) |

**Note**: At the moment, paramiko is not compatible with the ARM64 version of Python 3 for Windows.

### Dependencies 

1. [Python](https://www.python.org/downloads/) >= 3.9
   - If you're on Windows, you'll need to add python to PATH under installer options.
2. [paramiko](https://pypi.org/project/paramiko/)
3. [Clutch](https://github.com/NyaMisty/Clutch/)
4. [bfdecrypt](https://level3tjg.me/repo/depictions/?p=com.level3tjg.bfdecrypt)
   - bfdecrypt requires [altList](https://github.com/opa334/AltList) from the [BigBoss](http://apt.thebigboss.org/repofiles/cydia/) or [opa334](https://opa334.github.io/) repository.
5. SSH client for your PC and SSH server for your iOS device.
   - If you're using XinaA15, make sure to activate `open SSH server` under the `Option` tab.
   - Most Linux distros have an SSH client installed by default.
   - Windows (10, 11) and macOS will have an SSH client installed by default.

**Notes:**
- You'll need `Clutch` or `bfdecrypt` (or both, if you'd like).
- If you already have a version of bfdecrypt working on your device, it should work just fine with this tool.

### Usage

- Open your preferred terminal
- Clone this repo

<pre>
$ git clone https://github.com/cdelaof26/ssh_decrypt_automation_tool.git

# If you don't have git, click "Code" -> "Download ZIP"
</pre>

- Provide a copy of Clutch or bfdecrypt (or both)

<pre>
#   Clutch:
#  * You can skip this if you don't want to use Clutch.
#
# Download the latest version from: 
#     https://github.com/NyaMisty/Clutch/releases
# Copy "Clutch_troll" to /path/to/ssh_decrypt_automation_tool

#   bfdecrypt:
#  * You can skip this if you don't want to use bfdecrypt.
#
# Download the latest version from: 
#     https://www.ios-repo-updates.com/repository/level3tjg/package/com.level3tjg.bfdecrypt/
# Copy "com.level3tjg.bfdecrypt.deb" to /path/to/ssh_decrypt_automation_tool
# Rename "com.level3tjg.bfdecrypt.deb" as "bfdecrypt.deb"
</pre>

- Move into project directory

<pre>
$ cd ssh_decrypt_automation_tool
</pre>

- Install dependencies
<pre>
# You might need elevated privileges!

$ pip install -r requirements.txt
# or
$ pip3 install -r requirements.txt
</pre>

Run using python

<pre>
# If you're on Linux or macOS
$ python3 main.py

# If you're on Windows
$ python main.py
</pre>

### FAQ

- **How do I find my iOS device IP?**
1. Open the Settings App
2. Go to Wi-Fi section
3. Click on the `i` icon of your Wi-Fi network
4. Under `IPV4 ADDRESS` section, copy `IP ADDRESS` field

**Note: Your PC must be connected to the same network**

- **I keep getting "Please, consider changing ssh default password!" message, how do I change root password?**
1. Open your preferred terminal
2. Run: `ssh <user>@<your_ios_device_ip>`
   - e.g: `ssh root@10.0.1.5` or `ssh mobile@192.168.1.150`
3. Enter `alpine` as the password
4. Run: `passwd`
5. Enter your password
   - You won't see anything typed on the screen (this is normal)
   - Type your new password and then press enter
6. Confirm your password by re-typing it and then pressing enter

- **I can't find the option to dump apps, where is it?**

1. Connect your iOS device
2. Select `3. Select decrypt utility (needed to decrypt apps)` in the main menu
3. Select your preferred option
   - `Fallback` means that if the first decryption method fails, the second one will be used

- **I don't want to enter the IP address, username, or password each time I use this software, is there any solution?**

Yes:
1. Run the project
2. Connect your iOS device
3. Select `S. Setting` on the main menu
4. Enable / disable features as you wish
   - **Note: the username and password are saved as plain text!**
5. Done

- **Should I use `Clutch` or `bfdecrypt`?**

Depends on which works better for you, for me: `bfdecrypt`

| App name  | Clutch  | bfdecrypt |
|-----------|---------|-----------|
| Terraria  | Success | Success   |
| Apollo    | Failed  | Failed    |
| RedditApp | Failed  | Success   |
| WhatsApp  | Failed  | Success   |
| Telegram  | Failed  | Success   |
| Discord   | Failed  | Success   |

- **My app keeps failing when dumping, what can I do?**

Unfortunately, some applications might fail to decrypt using both `Clutch` and `bfdecrypt` decryption methods. 

### Changelog

### v0.0.4_1
- Fixed bug where `decrypt method` won't be saved if the option 
  is selected from the main menu

### v0.0.4
- Added support for bfdecrypt
- Fixed _Windows experience_

### v0.0.3
- Minor bug fixes
- Fixed bug where the script couldn't connect (Time out!)
  and it keeps trying until "too many attempts" error is raised
- Fixed bug where the script would crash when attempting 
  to delete temporary data but there isn't a cache directory

### v0.0.2
- Improved app detection

### v0.0.1
- Initial project
