import discord
from discord import app_commands
from discord.ext import commands
import random
import json

CONFIG_FILE = 'config.json'
def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)
config = load_config()

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
    # --- END SET BOT ACTIVITY ---

        # --- UPDATE: Slash Command Syncing using Guild ID from config.json ---
    try:
        guild_id = config.get('guild_id') # Get guild_id from config
        if guild_id:
            # Ensure the guild_id is an integer for discord.Object
            target_guild = discord.Object(id=int(guild_id)) 
            synced = await bot.tree.sync(guild=target_guild)
            print(f"Synced {len(synced)} slash commands to guild ID: {guild_id}")
        else:
            # If guild_id is not in config.json, sync globally (takes longer)
            synced = await bot.tree.sync() 
            print(f"Synced {len(synced)} slash commands globally (might take up to an hour to appear).")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")
    # --- END UPDATE: Slash Command Syncing ---


# Apply the permissions check to all commands
def is_manage_guild():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.manage_guild
    return app_commands.check(predicate)

def is_manage_channel():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.manage_channels
    return app_commands.check(predicate)

    # --- Global Slash Command Error Handler
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

        # Check if the command exists in our config and if it's enabled
        if command_name in config['enabled_commands']:
            return config['enabled_commands'][command_name]
        else:
            return False # Default to disabled.
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
    # If no member is provided, default to the user who invoked the command
    target_member = member or interaction.user

    # Get the avatar URL. `display_avatar.url` is preferred as it handles
    # guild-specific avatars and defaults gracefully.
    avatar_url = target_member.display_avatar.url

    # Create an Embed to make the message look nice
    embed = discord.Embed(
        title=f"{target_member.display_name}'s Avatar",
        color=discord.Color.blue() # You can choose any color
    )
    embed.set_image(url=avatar_url)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)

                #Slash Command:Slowmode
@bot.tree.command(name='slowmode', description='Sets the slow mode delay for this channel.')
@is_manage_channel()
@is_command_enabled()
@app_commands.describe(seconds='The slow mode delay in seconds (0 to disable).')
async def slowmode(interaction: discord.Interaction, seconds: int):
    """Sets the slow mode delay for the current channel."""
    if 0 <= seconds <= 21600:  # Discord slow mode limit
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
    
    # Check if the bot has permissions to change nicknames
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
    # Note: Adding fields directly via command arguments can be complex due to Discord's limits
    # and the number of arguments. For advanced embeds, consider multi-step or modals.
)
@app_commands.default_permissions(manage_messages=True) # Usually embed creation requires message management
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

    # Basic permission check: does the bot have permission to send embeds in the target channel?
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