# Mobile-Convenience-Administration-assistant
**Your Go-To Discord Bot for On-the-Go Server Management**

This bot was created to assist with the **mobile administrators**. Tired of navigating complex UIs and endless command lists while on your phone? This bot focuses on essential, high-impact administrative tasks, providing crucial convenience without the overwhelming bloat of mainstream bots.

It's built to **complement your existing moderation tools**, not replace them. You likely already have bots for logging, leveling, or advanced moderation—this bot fills the critical gaps in the Discord mobile UI, making everyday admin tasks quicker and more intuitive.

---

### Core Features (Current)
* **DM:** Designed strictly for **moderation purposes**, allowing server moderators to send friendly, private reminders to users without needing to issue formal warnings or strikes.
* **Say:** Allows a user to make the bot send a specific message to the channel, essentially acting as the bot.
* **Purge:** Efficiently clear message history in channels with a simple command.
* **Embed:** Create **fully customizable and rich embeds** directly through the bot, bypassing clunky off-platform webhooks and saving you precious time.
* **Report:** Allows any server member to Report another user or message to the server moderators/administrators.
* **Boinfo:** Displays information about the bot itself (e.g., uptime, server count, owner). Access to this detailed Bot Info
* **Nickname:** Allows **moderators** to quickly change a user's nickname if it's inappropriate or needs adjustment.
* **SlowMode:** Effortlessly adjust slow mode settings for channels on the fly.
* **Member_count:** Displays the current Member Count of the server.
* **Last-Deleted:** A vital tool for **server moderators** to quickly retrieve the content of the last deleted message, aiding in moderation checks and incident review.
* **Clone-Channel:** Allows you to clone your channel permissions and rename your clone channel
* **Delete-Channel:** Swiftly remove channels, perfect for accidental creations or cleanup.
* **Set-Report-Channel:** Configures which specific channel on the server new user Reports will be sent to.
* **Rate:** A fun random number generator to rate words in Discord.
* **Avatar:** Easily view a user's avatar in full resolution.
* **Emodify:** Converts a specified piece of text into emojis (e.g. spelling out a word using regional indicator emojis).
---


### Command Permissions

To ensure security and proper usage, each command has specific permission requirements:

* **DM:** `Manage Server`
* **Say:** `Manage Channel`
* **Purge:** `Manage Channel`
* **Embed:** `Manage Server`
* **Report:** `No specific permissions required (anyone can use).`
* **Boinfo:** `Manage Server`
* **Nickname:** `Manage Channel`
* **SlowMode:** `Manage Channel`
* **Member_count:** `No specific permissions required (anyone can use).`
* **Last-Deleted:** `Manage Channel`
* **Clone-Channel:** `Manage Channel` `Manage Server`
* **Delete-Channel:** `Manage Server`
* **Set-Report-Channel:** `Manage Server`
* **Rate:** `No Pacific No specific permission required (anyone can use)`
* **Avatar:** `No specific permissions required (anyone can use).`
* **Emodify:** `No specific permissions required (anyone can use).`
---

### Setup Instructions

Getting your Mobile Convenience Administration Assistant up and running is straightforward. Follow these steps to self-host your bot:

1.  **Prerequisites:**

      * **Python 3:** Ensure you have Python 3.8 or newer installed on your system.
      * **Discord Bot Token:** Create a new application and bot on the [Discord Developer Portal](https://discord.com/developers/applications) and obtain your bot's token.
      * **Server ID (Optional but Recommended):** If you want your bot's commands to register immediately in a specific server, obtain the ID of that server. Enable Discord Developer Mode in your user settings (`User Settings -> Advanced -> Developer Mode`) to easily copy server IDs.
      * **Intents:** In the Discord Developer Portal, under your bot's settings, enable the necessary **Privileged Gateway Intents** (at minimum, `MESSAGE CONTENT INTENT` and `MEMBERS INTENT` are often required for many Discord bot functionalities).

2.  **Clone the Repository:**

    ```bash
    git clone https://github.com/Eniti-Codes/Mobile-Convenience-Administration-Assistant.git
    cd Mobile-Convenience-Administration-Assistant
    ```

    (Note: Adjust the repository URL if your bot is hosted under a different name or organization.)

3.  **Install Dependencies:**
    This bot only requires `discord.py` to be installed. It's recommended to use a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install discord.py
    ```

4.  **Configuration (Directly in `main.py`):**

      * Open the `main.py` file in your text editor.
      * **At the very top of `main.py`**, locate the line where the bot token is defined and replace the placeholder with your actual Discord bot token.
      * **Immediately under the token line**, find `testing_guild_ID =` and replace the placeholder with your specific Discord server ID if you want commands to sync instantly to that server. If left empty or incorrect, commands will take up to an hour to globally sync to all servers your bot is in.

5.  **Run the Bot:**

    ```bash
    python3 main.py

    
---

Since it’s a Python bot using only the `discord.py` library and no complex dependency files, we can make these instructions even shorter and more direct.

Here is the refined guide for your users to get the bot running on Termux using the ZIP download method.

---

## Running the Bot on Termux

### 1. Prepare the Environment
Open Termux and run these commands to update your system and install Python:

```bash
pkg update && pkg upgrade -y
pkg install python unzip -y

```

### 2. Get the Files
1. Go to the **Releases** tab on the project page.
2. Download the **zip**.
3. In Termux, give it access to your files and move to your download folder:
```bash
termux-setup-storage
cd ~/storage/downloads

```


4. Unzip the folder and enter it:
```bash
unzip [Your-Downloaded-File].zip
cd [Extracted-Folder-Name]

```



### 3. Install the Discord Library
Since the bot only requires the Discord gateway library, run this command:

```bash
pip install discord.py

```

### 4. Launch the Bot
Open your configuration file `config.json` to paste your Bot Token, then start the bot:

```bash
python main.py

```


### 4. Stay Online

To make sure your bot doesn't disconnect when you close the Termux app:

* Pull down your Android notification bar.
* Find the Termux notification.
* Tap **Acquire WakeLock**. This prevents Android from putting the app to sleep.

---

### Additional information
    
Secure & Permission-Controlled: All administrative commands are strictly locked down. Top-level administrative commands require Discord's "Manage Server" permission, while lower-end commands require "Manage Channel" permission. This ensures only your most trusted administrators and moderators can utilize its powerful features, preventing misuse. Attempts by unauthorized users to execute these commands will result in an error.

### Developed by
Eniti-Codes
-----
