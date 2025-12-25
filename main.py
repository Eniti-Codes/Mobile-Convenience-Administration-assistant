import discord
from discord import app_commands
from discord.ext import commands
from typing import Union
import random
import json
import time
import os


#== CONFIGURATION & GLOBALS ==
CONFIG_FILE = 'config.json'
GUILD_SETTINGS_FILE = 'guild_settings.json'
START_TIME = time.time()

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

config = load_config()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Volatile storage (clears on restart)
last_deleted_messages = {} 


#== HELPER FUNCTIONS (Settings & Files) ==
def load_guild_settings():
    """Loads all guild-specific settings from JSON."""
    if not os.path.exists(GUILD_SETTINGS_FILE):
        with open(GUILD_SETTINGS_FILE, 'w') as f:
            json.dump({}, f)
        return {}
    try:
        with open(GUILD_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: {GUILD_SETTINGS_FILE} corrupted. Creating backup.")
        os.rename(GUILD_SETTINGS_FILE, GUILD_SETTINGS_FILE + '.bak')
        return {}

def save_guild_settings(settings):
    temp_file = GUILD_SETTINGS_FILE + '.tmp'
    try:
        with open(temp_file, 'w') as f:
            json.dump(settings, f, indent=4)
        os.replace(temp_file, GUILD_SETTINGS_FILE)
    except Exception as e:
        print(f"Failed to save settings: {e}")


#== PERMISSION CHECKS ==
def is_manage_guild():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.manage_guild
    return app_commands.check(predicate)

def is_manage_channel():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.manage_channels
    return app_commands.check(predicate)

def is_command_enabled():
    async def predicate(interaction: discord.Interaction):
        cmd = interaction.command.name
        return config.get('enabled_commands', {}).get(cmd, False)
    return app_commands.check(predicate)


#== BOT INITIALIZATION (Syncing & Startup) ==
async def setup_hook():
    """Runs before the bot starts; handles command syncing."""
    try:
        synced_global = await bot.tree.sync()
        print(f"Synced {len(synced_global)} commands globally.")
        
        # Specific Guild sync (for testing/instant updates)
        guild_id = config.get('guild_id')
        if guild_id:
            target = discord.Object(id=int(guild_id))
            synced_guild = await bot.tree.sync(guild=target)
            print(f"Synced {len(synced_guild)} commands to test guild: {guild_id}")
    except Exception as e:
        print(f"Sync error: {e}")

bot.setup_hook = setup_hook

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    
    act_cfg = config.get('bot_activity', {})
    act_type = act_cfg.get('type', 'playing').lower()
    name = act_cfg.get('name', "Mobile Administration")
    url = act_cfg.get('url')

    activity_map = {
        "playing": discord.Game(name=name),
        "streaming": discord.Streaming(name=name, url=url) if url else discord.Game(name=name),
        "listening": discord.Activity(type=discord.ActivityType.listening, name=name),
        "watching": discord.Activity(type=discord.ActivityType.watching, name=name),
        "competing": discord.Activity(type=discord.ActivityType.competing, name=name)
    }

    activity = activity_map.get(act_type, discord.Game(name=name))
    await bot.change_presence(activity=activity)
    print(f"Status set to: {act_type} {name}")


#== SYSTEM EVENTS (Cleanup & Tracking) ==
@bot.event
async def on_message_delete(message):
    global last_deleted_messages
    
    if message.guild and not message.author.bot:
        raw_content = message.content if message.content else "[No Text Content]"
        clean_content = (raw_content[:1000] + '...') if len(raw_content) > 1000 else raw_content
        
        last_deleted_messages[message.guild.id] = {
            'author_id': message.author.id,
            'channel_id': message.channel.id,
            'content': clean_content
        }

        try:
            print(f"[EVENT] Message Deleted in Guild: {message.guild.id} | Content Stored.")
        except:
            pass


@bot.event
async def on_guild_channel_delete(channel):
    """Cleanup settings if a designated report channel is deleted."""
    if not isinstance(channel, discord.TextChannel): return
    
    settings = load_guild_settings()
    gid = str(channel.guild.id)
    
    if gid in settings and settings[gid].get('report_channel_id') == str(channel.id):
        print(f"Cleaning up deleted report channel in {gid}")
        del settings[gid]['report_channel_id']
        if not settings[gid]: del settings[gid]
        save_guild_settings(settings)


@bot.event
async def on_guild_remove(guild):
    """Cleanup all settings when leaving a guild."""
    settings = load_guild_settings()
    if str(guild.id) in settings:
        print(f"Removing all data for Guild: {guild.name}")
        del settings[str(guild.id)]
        save_guild_settings(settings)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if config.get('dm_forwarding', False):
        if message.guild is None:
            fb_id = config.get('feedback_channel_id')
            if fb_id:
                channel = bot.get_channel(int(fb_id))
                if channel:
                    embed = discord.Embed(
                        title="📩 New DM Feedback",
                        description=message.content,
                        color=discord.Color.blue()
                    )
                    embed.set_author(name=f"{message.author} ({message.author.id})", 
                                     icon_url=message.author.display_avatar.url)
                    await channel.send(embed=embed)
                    try:
                        print(f"[DM] Message from {message.author.id} forwarded.")
                    except: pass

    await bot.process_commands(message)


#== ERROR HANDLING ==
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    import traceback
    traceback.print_exc()
    
    msg = "Oops! I've run into a fox while trying to execute that command!"
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)



#== SLASH COMMANDS ==
#--- Slash Command:DM  ---
@bot.tree.command(name='dm', description='Sends a DM to a member via Mention or ID (Mutual Servers Only).')
@is_manage_guild()
@is_command_enabled()
async def send_dm(interaction: discord.Interaction, user: Union[discord.Member, discord.User], message: str = "No message provided."):
    target_member = None
    
    for guild in bot.guilds:
        member = guild.get_member(user.id)
        if member:
            target_member = member
            break

    if not target_member:
        return await interaction.response.send_message(
            "Security Check Failed: This user does not share a server with the bot.", 
            ephemeral=True
        )

    try:
        await target_member.send(message)
        await interaction.response.send_message(f"Sent a DM to {target_member} (ID: {target_member.id}).", ephemeral=True)
        
    except discord.Forbidden:
        await interaction.response.send_message(f"Could not DM! {target_member.mention}. They likely have DMs disabled for non-friends.", ephemeral=True)


# --- Slash Command:Say (delete and re-send) ---
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


#--- Slash Command:Purge  ---
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


# --- Slash Command:Embed ---
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


# --- Slash Command:Report User ---
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


# --- Slash Command:Botinfo (Technical Info) ---
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


#--- Slash Command:Nickname  ---
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


#--- Slash Command:Slowmode  ---
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


# --- Slash Command:Member Count ---
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


#--- Slash Command:Last Deleted  ---
@bot.tree.command(name='last-deleted', description='Shows the last deleted non-bot message in this server.')
@is_manage_channel()
@is_command_enabled()
async def last_deleted(interaction: discord.Interaction):
    global last_deleted_messages
    
    data = last_deleted_messages.get(interaction.guild_id)

    if data:
        embed = discord.Embed(
            title="Last Deleted Message",
            color=0xC0C0C0 
        )
        
        embed.add_field(name="Channel:", value=f"<#{data['channel_id']}>", inline=True)
        embed.add_field(name="User:", value=f"<@{data['author_id']}>", inline=True)
        embed.add_field(name="Message:", value=data['content'], inline=True)

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(
            "No messages have been deleted in this server since the bot started.", 
            ephemeral=True
        )


#--- Slash Command:Delete Channel  ---
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


# --- Slash Command:Clone Channel ---
@bot.tree.command(name='clone-channel', description='Creates an exact copy of the specified text channel.')
@is_manage_guild()
@is_manage_channel() 
@is_command_enabled()
@app_commands.describe(
    channel='The channel to clone. Defaults to the current channel.',
    new_name='Optional: The name for the new cloned channel.'
)
async def clone_channel(interaction: discord.Interaction, channel: discord.TextChannel = None, new_name: str = None):
    """
    Duplicates a channel. All permission/requirement errors are 
    handled by the global 'on_app_command_error' handler.
    """
    target_channel = channel or interaction.channel
    
    # We defer because cloning involves copying permissions/overwrites, 
    # which can occasionally take longer than the 3-second slash command limit.
    await interaction.response.defer(ephemeral=True)

    cloned_channel = await target_channel.clone(
        name=new_name or f'{target_channel.name}-copy'
    )
    
    await interaction.followup.send(
        f"Successfully cloned! {target_channel.mention} to {cloned_channel.mention}.",
        ephemeral=True
    )


# --- Slash Command:Set Report Channel ---
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


# --- Slash Command:Rate ---
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


# --- Slash Command:Avatar ---
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


# --- Slash Command:Emodify (Text to Regional Indicator Emojis) ---
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


if __name__ == "__main__":
    TOKEN = config.get('token')
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: No token found in config.json.")