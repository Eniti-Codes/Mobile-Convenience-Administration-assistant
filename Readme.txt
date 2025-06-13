Here is your setup for the config.json file. 
This file is here to explain everything on what these are supposed to be for.

If you have cloned my repo or just downloaded the zip file, you should already have a config.json file.

This means all you need to do is follow the instructions below and get your bot up and running.

{
  "enabled_commands": {
    "nickname": true,   // Set to true to enable the /nickname command, false to disable.
    "avatar": true,     // Set to true to enable the /avatar command, false to disable.
    "info": false,      // Set to true to enable the /info command, false to disable.
    "dm": true,         // Set to true to enable the /dm command, false to disable.
    "delete-channel": true, // Set to true to enable the /delete-channel command, false to disable. (Use with caution!)
    "last-deleted": true,   // Set to true to enable the /last-deleted command, false to disable.
    "embed": true,      // Set to true to enable the /embed command, false to disable.
    "slowmode": true,   // Set to true to enable the /slowmode command, false to disable.
    "rate": true,       // Set to true to enable the /rate command, false to disable.
    "purge": true       // Set to true to enable the /purge command, false to disable. (Use with caution!)
  },
  "bot_activity": {
    "type": "playing",    // Options: "playing", "streaming", "listening", "watching", "competing".
    "name": "with community members", // The text displayed as the bot's activity.
    "url": null           // Required ONLY for "streaming" type (e.g., "https://twitch.tv/your_channel"). Set to null otherwise.
  },
  "guild_id": "YOUR_GUILD_ID_HERE", // Your Discord Server ID. Right-click your server icon > Copy ID (Developer Mode must be enabled).
  "token": "YOUR_BOT_TOKEN"         // Your bot's unique token from Discord Developer Portal. KEEP THIS SECRET!
}