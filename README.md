# Mobile-Convenience-Administration-assistant
**Your Go-To Discord Bot for On-the-Go Server Management**

This bot was created to assist with the **mobile administrators**. Tired of navigating complex UIs and endless command lists while on your phone? This bot focuses on essential, high-impact administrative tasks, providing crucial convenience without the overwhelming bloat of mainstream bots.

It's built to **complement your existing moderation tools**, not replace them. You likely already have bots for logging, leveling, or advanced moderation—this bot fills the critical gaps in the Discord mobile UI, making everyday admin tasks quicker and more intuitive.

---

### Core Features (Current)

* **Direct Message (DM):** Designed strictly for **moderation purposes**, allowing server moderators to send friendly, private reminders to users without needing to issue formal warnings or strikes.
* **Delete Channel:** Swiftly remove channels, perfect for accidental creations or cleanup.
* **Last Deleted Message:** A vital tool for **server moderators** to quickly retrieve the content of the last deleted message, aiding in moderation checks and incident review.
* **Embed:** Create **fully customizable and rich embeds** directly through the bot, bypassing clunky off-platform webhooks and saving you precious time.
* **Slow Mode:** Effortlessly adjust slow mode settings for channels on the fly.
* **Purge:** Efficiently clear message history in channels with a simple command.
* **Nickname:** Allows **moderators** to quickly change a user's nickname if it's inappropriate or needs adjustment.
* **Avatar:** Easily view a user's avatar in full resolution.

---

### Command Permissions

To ensure security and proper usage, each command has specific permission requirements:

* **DM:** `Manage Server`
* **Delete Channel:** `Manage Server`
* **Last Deleted Message:** `Manage Channel`
* **Avatar:** No specific permissions required (anyone can use).
* **Slow Mode:** `Manage Channel`
* **Nickname:** `Manage Channel`
* **Embed:** `Manage Server`
* **Purge:** `Manage Channel`

---

### Future Enhancements (Planned)

* **Bot Info:** Provides essential information about the bot itself, such as its version. (No specific permissions required; anyone will be able to use).

* **Fixing the activities:** Currently the activities do not function whatsoever. Because I'm currently learning how Discord works with it. I'm just trying to pull it over what I know from JavaScript. It's not working out. :(

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
### Additional information
    
Secure & Permission-Controlled: All administrative commands are strictly locked down. Top-level administrative commands require Discord's "Manage Server" permission, while lower-end commands require "Manage Channel" permission. This ensures only your most trusted administrators and moderators can utilize its powerful features, preventing misuse. Attempts by unauthorized users to execute these commands will result in an error.

### Developed by

[Eniti-Codes](https://github.com/Eniti-Codes?tab=repositories)

-----
