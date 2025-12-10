import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import time
import os

CONFIG_FILE = 'config.json'
def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)
config = load_config()

START_TIME = time.time()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

last_deleted_message = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.tree.sync()

# --- SET BOT ACTIVITY HERE ---
    activity_type_str = config['bot_activity'].get('type', 'playing').lower()
    activity_name = config['bot_activity'].get('name', None)
    activity_url = config['bot_activity'].get('url', None)

    activity = None
    if activity_name:
        if activity_type_str == "playing":
            activity = discord.Game(name=activity_name)
        elif activity_type_str == "streaming":
            if activity_url:
                activity = discord.Streaming(name=activity_name, url=activity_url)
            else:
                print("Warning: Streaming activity requires a 'url' in config.json. Defaulting to Playing.")
                activity = discord.Game(name=activity_name)
        elif activity_type_str == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=activity_name)
        elif activity_type_str == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=activity_name)
        elif activity_type_str == "competing":
            activity = discord.Activity(type=discord.ActivityType.competing, name=activity_name)
        else:
            print(f"Unknown activity type '{activity_type_str}' in config.json. Defaulting to Playing.")
            activity = discord.Game(name=activity_name)

    if activity:
        await bot.change_presence(activity=activity)
        print(f"Bot activity set to: {activity_type_str.capitalize()} {activity_name}")


# --- Event: Channel Delete Cleanup ---
@bot.event
async def on_guild_channel_delete(channel):
    """
    Checks if a deleted channel was the configured report channel
    for its guild and removes the setting if it was.
    """
    if not channel.guild or not isinstance(channel, discord.TextChannel):
        return

    guild_id_str = str(channel.guild.id)
    
    settings = load_guild_settings()

    # 2. Check if this guild has settings and if the deleted channel ID matches the report ID
    guild_settings = settings.get(guild_id_str)
    
    if guild_settings and guild_settings.get('report_channel_id') == str(channel.id):
        
        print(f"Cleanup: Report channel for Guild ID {guild_id_str} was deleted. Removing setting.")
        
        del guild_settings['report_channel_id']
        
        if not guild_settings:
            del settings[guild_id_str]
        
        save_guild_settings(settings)

# --- Event: Guild Remove Cleanup ---
@bot.event
async def on_guild_remove(guild):
    """
    Cleans up all settings associated with a guild when the bot is removed from it.
    """
    guild_id_str = str(guild.id)
    
    settings = load_guild_settings()

    # Check if the guild ID exists in the settings file
    if guild_id_str in settings:
        
        print(f"Cleanup: Bot removed from Guild ID {guild_id_str} ('{guild.name}'). Removing all settings.")
        
        del settings[guild_id_str]
        
        save_guild_settings(settings)


        # --- Slash Command Syncing ---
async def setup_hook():
    try:
        synced_global = await bot.tree.sync()
        print(f"Successfully synced {len(synced_global)} slash commands globally.")
        
        guild_id = config.get('guild_id')
        if guild_id:
            target_guild = discord.Object(id=int(guild_id))  
            synced_guild = await bot.tree.sync(guild=target_guild)
            print(f"Successfully synced {len(synced_guild)} slash commands to guild ID: {guild_id}.")

    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

bot.setup_hook = setup_hook


# --- GUILD SETTINGS FILE HANDLING ---
GUILD_SETTINGS_FILE = 'guild_settings.json'

def load_guild_settings():
    """
    Loads all guild-specific settings from the JSON file.
    Creates the file with an empty dictionary if it does not exist.
    """
    if not os.path.exists(GUILD_SETTINGS_FILE):
        print(f"Creating new {GUILD_SETTINGS_FILE}.")
        with open(GUILD_SETTINGS_FILE, 'w') as f:
            json.dump({}, f)
        return {}
        
    try:
        with open(GUILD_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: {GUILD_SETTINGS_FILE} is corrupted. Backing it up and starting with empty settings.")
        if os.path.exists(GUILD_SETTINGS_FILE):
            os.rename(GUILD_SETTINGS_FILE, GUILD_SETTINGS_FILE + '.corrupted_backup')
        return {}

def save_guild_settings(settings):
    """Saves all guild-specific settings to the JSON file."""
    with open(GUILD_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)


# Apply the permissions check to all commands
def is_manage_guild():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.manage_guild
    return app_commands.check(predicate)

def is_manage_channel():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.manage_channels
    return app_commands.check(predicate)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):

    print(f"Unhandled error in command '{interaction.command.name}' invoked by {interaction.user}:")
    import traceback
    traceback.print_exc()

    user_error_message = (
        "Oops! I've run into an fox while trying to execute that command!"
    )
    try:
        if interaction.response.is_done():
            await interaction.followup.send(user_error_message, ephemeral=True)
        else:
            await interaction.response.send_message(user_error_message, ephemeral=True)
    except discord.Forbidden:
        print(f"Could not send ephemeral error message to {interaction.user.name} ({interaction.user.id}).")
    except Exception as e:
        print(f"Failed to send error message to user: {e}")

       
def is_command_enabled():
    async def predicate(interaction: discord.Interaction):
        command_name = interaction.command.name

        if command_name in config['enabled_commands']:
            return config['enabled_commands'][command_name]
        else:
            return False
    return app_commands.check(predicate)



              #Slash Command:DM
@bot.tree.command(name='dm', description='Sends a direct message to a member.')
@is_manage_guild()
@is_command_enabled()
async def send_dm(interaction: discord.Interaction, member: discord.Member, message: str = "No message provided."):
    """Sends a direct message to the specified member."""
    try:
        await member.send(message)
        await interaction.response.send_message(f"Sent a DM to {member.mention}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(f"Could not DM {member.mention}. They might have DMs disabled.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred while trying to DM {member.mention}: {e}", ephemeral=True)

# --- Slash Command: Emodify (Text to Regional Indicator Emojis) ---
REGIONAL_INDICATORS = {
    'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪', 'f': '🇫', 'g': '🇬',
    'h': '🇭', 'i': '🇮', 'j': '🇯', 'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳',
    'o': '🇴', 'p': '🇵', 'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹', 'u': '🇺',
    'v': '🇻', 'w': '🇼', 'x': '🇽', 'y': '🇾', 'z': '🇿',
    '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣', '4': '4️⃣',
    '5': '5️⃣', '6': '6️⃣', '7': '7️⃣', '8': '8️⃣', '9': '9️⃣',
    '!': '❗', '?': '❓', ' ': '  ', 
}

@bot.tree.command(name='emodify', description='Converts text to regional indicator emojis.')
@is_command_enabled()
@app_commands.describe(text='The text to convert to emojis.')
async def emodify(interaction: discord.Interaction, text: str):
    """Converts the given text to regional indicator emojis."""
    
    await interaction.response.defer()

    emojified_text = ""
    for char in text.lower():
        emoji = REGIONAL_INDICATORS.get(char, char) 
        emojified_text += emoji + " " 
        
    if len(emojified_text) > 2000:
        await interaction.followup.send("The resulting emoji text is too long for Discord's message limit (2000 characters).", ephemeral=True)
        return
        
    await interaction.followup.send(emojified_text)


# --- Slash Command: Say (delete and re-send) ---
@bot.tree.command(name='say', description='Deletes your command and sends the message you want to say.')
@is_manage_channel() 
@is_command_enabled()
@app_commands.describe(message=':/')
async def say_command(interaction: discord.Interaction, message: str):
    """Deletes the interaction message and sends the user's message as the bot."""
    
    await interaction.response.defer(ephemeral=True, thinking=True)
    
    try:
        await interaction.channel.send(message)
        await interaction.delete_original_response() 
        
    except discord.Forbidden:
        await interaction.followup.send("I sent the message, but I couldn't delete the command execution message. I might lack **Manage Messages** permission.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


               #Slash Command:Delete Channel
@bot.tree.command(name='delete-channel', description='Deletes the specified channel.')
@is_manage_guild()
@is_command_enabled()
async def delete_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Deletes the specified channel."""
    try:
        await channel.delete(reason=f"Deleted by {interaction.user.name} via /delete-channel")
        await interaction.response.send_message(f'Successfully deleted channel: {channel.name}', ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have the necessary permissions to delete this channel.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message(f"Channel not found: {channel.name}", ephemeral=True)
    except app_commands.AppCommandError as e:
        await interaction.response.send_message(f"An application command error occurred: {e}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)

@bot.event
async def on_message_delete(message):
    global last_deleted_message
    if not message.author.bot:
        last_deleted_message = {
            'author': message.author.name,
            'content': message.content
        }
        print(f"Message deleted: {message.author.name}: {message.content}")

                     #Slash Command:Last Deleted
@bot.tree.command(name='last-deleted', description='Shows the last deleted non-bot message publicly.')
@is_manage_channel()
@is_command_enabled()
async def last_deleted(interaction: discord.Interaction):
    """Shows the author and content of the last deleted non-bot message publicly."""
    global last_deleted_message
    if last_deleted_message:
        author = last_deleted_message['author']
        content = last_deleted_message['content']
        await interaction.response.send_message(f"**Last Deleted Message:**\n**Author:** {author}\n**Content:** {content}")
    else:
        await interaction.response.send_message("No non-bot messages have been deleted since the bot started.")

        # --- Slash Command: Avatar ---
@bot.tree.command(name="avatar", description="Displays a user's avatar.")
@is_command_enabled()
@app_commands.describe(member="The user whose avatar you want to see. Defaults to yourself.")
async def avatar_command(interaction: discord.Interaction, member: discord.Member = None):
    """
    Displays a user's avatar.
    """
    target_member = member or interaction.user

    avatar_url = target_member.display_avatar.url

    embed = discord.Embed(
        title=f"{target_member.display_name}'s Avatar",
        color=discord.Color.blue()
    )
    embed.set_image(url=avatar_url)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- Slash Command: Member Count ---
@bot.tree.command(name='member_count', description='Displays the total member count and user/bot breakdown.')
@is_command_enabled()
async def member_count(interaction: discord.Interaction):
    """
    Displays the total member count, excluding bots and as a separate category.
    """
    
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    # Count members and bots
    total_members = interaction.guild.member_count
    
    user_members = sum(1 for member in interaction.guild.members if not member.bot)
    
    bot_members = total_members - user_members

    embed = discord.Embed(
        title=f"👥 Member Count for {interaction.guild.name}",
        color=discord.Color.gold()
    )

    embed.add_field(name="Total Members", value=f"**{total_members}**", inline=False)
    embed.add_field(name="Non-Bot Users", value=f"**{user_members}**", inline=True)
    embed.add_field(name="Bots", value=f"**{bot_members}**", inline=True)

    await interaction.response.send_message(embed=embed)

                #Slash Command:Slowmode
@bot.tree.command(name='slowmode', description='Sets the slow mode delay for this channel.')
@is_manage_channel()
@is_command_enabled()
@app_commands.describe(seconds='The slow mode delay in seconds (0 to disable).')
async def slowmode(interaction: discord.Interaction, seconds: int):
    """Sets the slow mode delay for the current channel."""
    if 0 <= seconds <= 21600: 
        await interaction.channel.edit(slowmode_delay=seconds)
        if seconds > 0:
            await interaction.response.send_message(f"Set slow mode in this channel to {seconds} seconds.", ephemeral=True)
        else:
            await interaction.response.send_message("Disabled slow mode in this channel.", ephemeral=True)
    else:
        await interaction.response.send_message("Slow mode delay must be between 0 and 21600 seconds.", ephemeral=True)


    # --- Helper function to convert hex color string to Discord Color object ---
def hex_to_discord_color(hex_string: str) -> discord.Color:
    """Converts a hex color string (e.g., 'FF0000', '#FF0000') to a discord.Color object."""
    hex_string = hex_string.lstrip('#')
    try:
        return discord.Color(int(hex_string, 16))
    except ValueError:
        return discord.Color.default()



        # Slash Command: Change User Nickname
@bot.tree.command(name="nickname", description="Changes the nickname of a specified user.")
@is_manage_channel()
@is_command_enabled()
@app_commands.describe(
    user="The user whose nickname you want to change.",
    new_nickname="The new nickname for the user. Leave empty to remove nickname."
)
async def change_nickname(interaction: discord.Interaction, user: discord.Member, new_nickname: str = None):
    
    if not interaction.guild.me.guild_permissions.manage_nicknames:
        await interaction.response.send_message("I don't have permission to manage nicknames in this server.", ephemeral=True)
        return

    if interaction.guild.me.top_role <= user.top_role and user != interaction.guild.owner:
        await interaction.response.send_message("I cannot change the nickname of a user with a higher or equal role.", ephemeral=True)
        return

    try:
        old_nickname = user.nick if user.nick else user.name
        await user.edit(nick=new_nickname)
        if new_nickname:
            await interaction.response.send_message(f"Changed {old_nickname}'s nickname to **{new_nickname}**.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Removed {old_nickname}'s nickname.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have the necessary permissions to change that user's nickname. Make sure my role is above theirs.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

# --- Slash Command: Botinfo (Technical Info) ---
def format_uptime(seconds):
    """Converts seconds into a human-readable duration string."""
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
        
    return ", ".join(parts) if parts else "Less than 1 second"

@bot.tree.command(name='botinfo', description='Displays technical information about the bot.')
@is_manage_guild()
@is_command_enabled()
async def botinfo(interaction: discord.Interaction):
    """Gives technical information about the bot (uptime, ping, server count, invite link, etc.)."""

    # Calculate Uptime
    current_time = time.time()
    uptime_seconds = current_time - START_TIME 
    uptime_string = format_uptime(uptime_seconds)

    ping_ms = round(bot.latency * 1000)
    
    guild_count = len(bot.guilds)
    total_users = sum(guild.member_count for guild in bot.guilds) 
    dpy_version = discord.__version__

    invite_link = config.get('invite_url')

    embed = discord.Embed(
        title=f"{bot.user.name} Bot Info",
        description="A summary of the bot's current operational status.",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="🟢 Uptime", value=uptime_string, inline=False)
    embed.add_field(name="⚡ Ping (Latency)", value=f"{ping_ms}ms", inline=True)
    embed.add_field(name="💻️ Discord.py Version", value=dpy_version, inline=True)
    embed.add_field(name="🌍 Servers", value=str(guild_count), inline=True)
    embed.add_field(name="👥 Total Users", value=str(total_users), inline=True)

    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=f"Bot ID: {bot.user.id}")

    if invite_link:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite Bot", url=invite_link, style=discord.ButtonStyle.link))
        
        await interaction.response.send_message(embed=embed, view=view)
    else:

        await interaction.response.send_message(embed=embed)


# --- Slash Command: Set Report Channel ---
@bot.tree.command(name='set-report-channel', description='Sets the channel where user reports will be sent for this server.')
@is_manage_guild()
@is_command_enabled()
@app_commands.describe(channel='The text channel to receive reports.')
async def set_report_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Sets the designated report channel for the current guild."""
    guild_id_str = str(interaction.guild_id)
    channel_id_str = str(channel.id)

    if not channel.permissions_for(interaction.guild.me).send_messages or \
       not channel.permissions_for(interaction.guild.me).embed_links:
        await interaction.response.send_message(
            f"I don't have permission to send messages and embeds in {channel.mention}.",
            ephemeral=True
        )
        return
        
    settings = load_guild_settings()
    
    # Store the setting under the guild's ID
    if guild_id_str not in settings:
        settings[guild_id_str] = {}
        
    settings[guild_id_str]['report_channel_id'] = channel_id_str
    
    save_guild_settings(settings)
    
    await interaction.response.send_message(
        f"✅ This channel ({channel.mention}) has been set as the official Report Channel for this server.",
        ephemeral=True
    )

# --- Slash Command: Report User ---
# Cooldown: 1 use per 60 seconds, tracked per user.
@bot.tree.command(name='report', description='Reports a user to the moderators.')
@is_command_enabled()
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
@app_commands.describe(
    member='The user you wish to report.',
    reason='The reason for the report.',
    message_link='Optional: A link to the specific message being reported.'
)
async def report_user(
    interaction: discord.Interaction, 
    member: discord.Member, 
    reason: str, 
    message_link: str = None
):
    """
    Sends a report about a user to a designated moderator channel, including an optional message link.
    """
    guild_id_str = str(interaction.guild_id)
    settings = load_guild_settings()
    
    # 2. Check if the report channel is configured for this guild
    report_channel_id = settings.get(guild_id_str, {}).get('report_channel_id')

    if not report_channel_id:
        await interaction.response.send_message(
            "⚠️ **The report channel has not been set for this server.** A moderator must use `/set-report-channel` first.", 
            ephemeral=True
        )
        return

    report_channel = interaction.guild.get_channel(int(report_channel_id))
    
    if not report_channel:
        await interaction.response.send_message(
            f"⚠️ The configured report channel (ID: `{report_channel_id}`) was not found. Please ask a moderator to re-configure it.",
            ephemeral=True
        )
        return
    
    if member == interaction.user:
        await interaction.response.send_message(
            "You cannot report yourself!",
            ephemeral=True
        )
        return

    report_embed = discord.Embed(
        title="New User Report!",
        color=discord.Color.red(),
        timestamp=interaction.created_at
    )
    
    report_embed.add_field(name="Reported User", value=f"{member.mention} (`{member.id}`)", inline=False)
    report_embed.add_field(name="Reported By", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
    report_embed.add_field(name="Channel", value=interaction.channel.mention, inline=False)
    report_embed.add_field(name="Reason", value=reason, inline=False)

    if message_link:
     report_embed.add_field(name="Message Link", value=f"[Jump to Message]({message_link})", inline=False)
    
    report_embed.set_thumbnail(url=member.display_avatar.url)
    
    try:
        await report_channel.send(embed=report_embed)
        
        await interaction.response.send_message(
            f"Successfully reported {member.mention} for **{reason}**." + 
            (" The message link was included." if message_link else "") +
            " Thank you!",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            f"I cannot send the report to the configured channel ({report_channel.mention}). Check my permissions in that channel.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"An unexpected error occurred while processing the report: {e}",
            ephemeral=True
        )


# --- Slash Command: Embed ---
@bot.tree.command(name="embed", description="Creates and sends a custom embed message.")
@is_manage_guild()
@is_command_enabled()
@app_commands.describe(
    channel="The channel to send the embed in (defaults to current).",
    title="The main title of the embed.",
    description="The main content of the embed.",
    color="Hex color code for the embed (e.g., FF0000 or #FF0000).",
    image_url="URL for a large image displayed at the bottom of the embed.",
    thumbnail_url="URL for a small image displayed in the top right corner.",
    footer_text="Text for the footer of the embed.",
    footer_icon_url="URL for the icon next to the footer text."
)
@app_commands.default_permissions(manage_messages=True)
async def embed_command(
    interaction: discord.Interaction,
    channel: discord.TextChannel = None,
    title: str = None,
    description: str = None,
    color: str = None,
    image_url: str = None,
    thumbnail_url: str = None,
    footer_text: str = None,
    footer_icon_url: str = None
):
    target_channel = channel or interaction.channel

    if not target_channel.permissions_for(interaction.guild.me).send_messages or \
       not target_channel.permissions_for(interaction.guild.me).embed_links:
        await interaction.response.send_message(
            f"I don't have permission to send messages or embed links in {target_channel.mention}.",
            ephemeral=True
        )
        return

    # Check if the user has permission to manage messages (for general embed creation)
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "You need 'Manage Messages' permission to use this command.",
            ephemeral=True
        )
        return

    embed = discord.Embed()

    if title:
        embed.title = title
    if description:
        embed.description = description
    if color:
        embed.color = hex_to_discord_color(color)
    if image_url:
        embed.set_image(url=image_url)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    if footer_text:
        if footer_icon_url:
            embed.set_footer(text=footer_text, icon_url=footer_icon_url)
        else:
            embed.set_footer(text=footer_text)

    if not title and not description and not image_url and not thumbnail_url and not footer_text:
        await interaction.response.send_message(
            "Please provide at least a `title`, `description`, `image_url`, `thumbnail_url`, or `footer_text` for the embed.",
            ephemeral=True
        )
        return

    try:
        await target_channel.send(embed=embed)
        await interaction.response.send_message(f"Embed sent to {target_channel.mention}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(
            f"I don't have permission to send messages or embed links in {target_channel.mention}.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"An error occurred while sending the embed: {e}",
            ephemeral=True
        )

        # --- Rate Slash Command ---
@bot.tree.command(name="rate", description="Get a random rating out of 10 for your text.")
@is_command_enabled()
@app_commands.describe(text="The text you want to get a rating for.")
async def rate(interaction: discord.Interaction, text: str):
    """
    Rates the given text with a random number out of 10.
    """
    rating = random.randint(0, 10)
    response_message = f"I'd rate '{text}' a **{rating}/10**! :star:"

    await interaction.response.send_message(response_message)

        # --- Purge Slash Command ---
@bot.tree.command(name='purge', description='Deletes a specified number of messages.')
@is_manage_channel()
@is_command_enabled()
@app_commands.describe(amount='The number of messages to delete.')
async def purge(interaction: discord.Interaction, amount: int):
    """Deletes a specified number of messages from the current channel."""
    if amount > 0:
        await interaction.response.defer(ephemeral=True) # Acknowledge the command as purge can take time
        deleted = await interaction.channel.purge(limit=amount + 1) # +1 to account for the command message itself
        await interaction.followup.send(f"Successfully purged {len(deleted) - 1} messages.", ephemeral=True)
    else:
        await interaction.response.send_message("Please specify a number of messages greater than 0 to purge.", ephemeral=True)

config = load_config()
TOKEN = config.get('token')
bot.run(TOKEN)
