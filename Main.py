import discord
import asyncio
import time
import random
import re
import aiohttp

from config import bot_token, join_role, wlcm_chnl, mod_chnl, poll_chnl
from datetime import datetime
from discord.ext import commands

intents = discord.Intents().all()
intents.members = True

client = commands.Bot(command_prefix='!', intents=intents)
client.remove_command("help")

invites = {}

######################################### When user joins #######################################


@client.event
async def on_member_join(member):
    wlcmChannel = client.get_channel(wlcm_chnl)
    await wlcmChannel.send(f'Welcome {member.mention}........To the official FarmTech Server')

    role = member.guild.get_role(join_role)
    await member.add_roles(role)

    invites_before_join = invites[member.guild.id]
    invites_after_join = await member.guild.invites()

    for invite in invites_before_join:

        if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:

            joinEmbed = discord.Embed(
                title=f"{member} joined", description=f"Account Created on: `{member.created_at}` \n Invite Used: `{invite.code}` \n Invited by: `{invite.inviter}`", color=0xa333cc
            )

            await wlcmChannel.send(embed=joinEmbed)

            invites[member.guild.id] = invites_after_join

            return


@client.event
async def on_member_remove(member):
    invites[member.guild.id] = await member.guild.invites()

######################################### On ready #######################################

@client.event
async def on_ready():
    print(f'Bot connected as {client.user}')
    await client.change_presence(activity=discord.Game('Helping FarmTech Members'))

    for guild in client.guilds:
        invites[guild.id] = await guild.invites()


def find_invite_by_code(invite_list, code):
    for inv in invite_list:
        if inv.code == code:
            return inv

######################################### Kick Command #######################################


@client.command()
@commands.has_any_role("Admin")
@commands.has_permissions(kick_members=True)
async def kick(ctx, user: discord.Member, *, reason=None):
    if reason == None:
        await user.kick(reason=reason)
        await ctx.send(f"{user} have been kicked sucessfully")
    else:
        await user.kick(reason=reason)
        await ctx.send(f"{user} have been kicked sucessfully because {reason}")

    mod_channel = client.get_channel(mod_chnl)

    kick_embed = discord.Embed(title="Kick", color=discord.Color.dark_orange())
    kick_embed.add_field(
        name=f"{user} was kicked by", value=ctx.message.author, inline=False)
    kick_embed.add_field(
        name=f"{user} was kicked for", value=reason, inline=False)
    kick_embed.set_footer(
        text=f"{ctx.guild.name}  •  {datetime.strftime(datetime.now(), '%d.%m.%Y at %I:%M %p')}")

    await mod_channel.send(embed=kick_embed)

    await user.send(embed=discord.Embed(
        title='You Have Been Kicked From {}'.format(ctx.guild),
        description='**{}** Has Kicked You From this server.\n**Reason:**\n```{}```'.format(
            ctx.author.mention, reason),
        color=discord.Color.red()
    ).set_thumbnail(url=ctx.author.avatar_url))

################################### Ban Command ########################################


@client.command()
@commands.has_any_role("Mod")
@commands.has_permissions(ban_members=True)
async def ban(ctx, user: discord.Member, *, reason=None):
    if reason == None:
        await user.ban(reason=reason)
        await ctx.send(f"{user} have been bannned sucessfully")
    else:
        await user.ban(reason=reason)
        await ctx.send(f"{user} have been bannned sucessfully because of {reason}")

    mod_channel = client.get_channel(mod_chnl)

    ban_embed = discord.Embed(title="Ban", color=0xe44225)
    ban_embed.add_field(
        name=f"{user} was banned by", value=ctx.message.author, inline=False)
    ban_embed.set_footer(
        text=f"{ctx.guild.name}  •  {datetime.strftime(datetime.now(), '%d.%m.%Y at %I:%M %p')}")

    await mod_channel.send(embed=ban_embed)

######################################## Unban Command ########################################


@client.command(pass_context=True)
@commands.has_any_role("Admin")
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, user):
    member = str(user)
    member = member.replace("<", "")
    member = member.replace(">", "")
    member = member.replace("@", "")
    member = member.replace("!", "")
    member_unban = discord.Object(id=member)
    # user = client.get_user_info(member)
    await ctx.guild.unban(member_unban)
    await ctx.send(f"Unbanned {user}")

    member_mention = await client.fetch_user(member)
    mod_channel = client.get_channel(mod_chnl)

    unban_embed = discord.Embed(title="Unban", color=0xe44225)
    unban_embed.add_field(
        name=f"{member_mention} was unbanned by", value=ctx.message.author, inline=False)
    unban_embed.set_footer(
        text=f"{ctx.guild.name}  •  {datetime.strftime(datetime.now(), '%d.%m.%Y at %I:%M %p')}")

###################################### Unban using ID Command (Just for backup) #####################################


@client.command(pass_context=True)
@commands.has_any_role("Admin")
@commands.has_permissions(ban_members=True)
async def unbanMember(ctx, *, member):
    banned_users = await ctx.guild.bans()

    member_name, member_discriminator = member.split('#')
    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.channel.send(f"Unbanned {user.mention}")

    mod_channel = client.get_channel(mod_chnl)

    unban_embed = discord.Embed(title="Unban", color=0xe44225)
    unban_embed.add_field(
        name=f"{member} was unbanned by", value=ctx.message.author, inline=False)
    unban_embed.set_footer(
        text=f"{ctx.guild.name}  •  {datetime.strftime(datetime.now(), '%d.%m.%Y at %I:%M %p')}")
    await mod_channel.send(embed=unban_embed)

################################### Mute Command #######################################


@client.command()
async def mute(ctx, members: commands.Greedy[discord.Member], mute_minutes: int = 10, *, reason: str = "None"):
    """Mass mute members with an optional mute_minutes parameter to time it"""

    if not members:
        await ctx.send("You need to name someone to mute")
        return

    muted_role = get(ctx.guild.roles, name="Muted")

    for member in members:
        if ctx.author.bot == member:
            embed = discord.Embed(
                title="You can't mute me, Your not worthy enough")
            await ctx.send(embed=embed)
            continue
        await member.add_roles(muted_role, reason=reason)
        await ctx.send("{0.mention} has been muted by {1.mention} for *{2}*".format(member, ctx.author, reason))

    if mute_minutes > 0:
        await asyncio.sleep(mute_minutes * 60)
        for member in members:
            await member.remove_roles(muted_role, reason="time's up ")

################################### Poll Command #######################################


@client.command(pass_context=True, add_reactions=True)
async def poll(ctx, *, message):

    polls = discord.Embed(title="Idea", color=0x31d2dd)
    polls.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/810546790172590166/814071210233167892/Green_School_Science_Club_Logo_2.png")
    polls.add_field(name=message, value=ctx.message.author, inline=False)
    polls.set_footer(
        text=f"{ctx.guild.name}  •  {datetime.strftime(datetime.now(), '%d.%m.%Y at %I:%M %p')}")

    pollsChannel = client.get_channel(poll_chnl)

    reactmsg = await pollsChannel.send(embed=polls)
    await reactmsg.add_reaction("👍")
    await reactmsg.add_reaction("👎")

###################################### Clear Command ###################################


@client.command()
async def clear(ctx, amount=1):
    await ctx.channel.purge(limit=amount+1)

###################################### Nuke Command ####################################


@client.command()
@commands.has_any_role("Head")
@commands.has_permissions(ban_members=True)
async def nuke(ctx):
    embed = discord.Embed(
        color=0x2555e4,
        title=f":boom: Channel ({ctx.channel.name}) has been nuked :boom:",
        description=f"Nuked by: {ctx.author.name}#{ctx.author.discriminator}"
    )
    embed.set_footer(
        text=f"{ctx.guild.name}  •  {datetime.strftime(datetime.now(), '%d.%m.%Y at %I:%M %p')}")
    await ctx.channel.delete(reason="nuke")
    channel = await ctx.channel.clone(reason="nuke")
    await channel.send(embed=embed)

###################################### Ping Command #####################################


@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! Its `{round(client.latency * 1000)}ms`')

###################################### Echo Command ######################################


@client.command()
async def echo(ctx, *, arg):
    await ctx.send(arg)

###################################### Addrole Command ######################################


@client.command()
async def addrole(ctx, *, member: discord.Member = None, role: discord.Role):

    if member is None:
        member = ctx.message.author

    await member.add_roles(role)
    await ctx.send(f'{member} has been assigned the role {role}')

####################################### Embed Command ####################################


@client.command()
async def embed(ctx):

    await ctx.send("What is your embed Title?")

    def is_correct(m):
        return m.author.name == ctx.author.name
    try:
        title = await client.wait_for('message', check=is_correct, timeout=20.0)
    except:
        await ctx.send("Sorry that was too long...........Please try again")

    await ctx.send("What is your Message?")

    try:
        message = await client.wait_for('message', check=is_correct, timeout=20.0)
    except:
        await ctx.send("Sorry that was too long...........Please try again")

    await ctx.send("What colour should it be?")

    try:
        color = await client.wait_for('message', check=is_correct, timeout=20.0)
    except:
        await ctx.send("Sorry that was too long...........Please try again")

    color = color.content.lower()
    colors = {"green": discord.Colour.green(), "red": discord.Colour.red(), "blue": discord.Colour.blue(
    ), "purple": discord.Colour.purple(), "yellow": discord.Colour.gold()}

    await ctx.send("Where should we send it? [Use the channel ID]")

    try:
        channel = await client.wait_for('message', check=is_correct, timeout=20.0)
    except:
        await ctx.send("Sorry that was too long...........Please try again")

    embed = discord.Embed(title=title.content,
                          description=message.content, color=colors[color])
    channel = client.get_channel(int(channel.content))

    await channel.send(embed=embed)

######################################## Eval Command ####################################
@client.command(name="eval")
async def eval_fn(ctx, *, code):
    language_specifiers = ["python", "py", "javascript", "js", "html", "css", "php", "md", "markdown", "go", "golang", "c", "c++", "cpp", "c#", "cs", "csharp", "java", "ruby", "rb", "coffee-script", "coffeescript", "coffee", "bash", "shell", "sh", "json", "http", "pascal", "perl", "rust", "sql", "swift", "vim", "xml", "yaml"]
    loops = 0
    while code.startswith("`"):
        code = "".join(list(code)[1:])
        loops += 1
        if loops == 3:
            loops = 0
            break
    for language_specifier in language_specifiers:
        if code.startswith(language_specifier):
            code = code.lstrip(language_specifier)
    while code.endswith("`"):
        code = "".join(list(code)[0:-1])
        loops += 1
        if loops == 3:
            break
    code = "\n".join(f"    {i}" for i in code.splitlines()) #Adds an extra layer of indentation
    code = f"async def eval_expr():\n{code}" #Wraps the code inside an async function
    def send(text): #Function for sending message to discord if code has any usage of print function
        client.loop.create_task(ctx.send(text))
    env = {
        "bot": client,
        "client": client,
        "ctx": ctx,
        "print": send,
        "_author": ctx.author,
        "_message": ctx.message,
        "_channel": ctx.channel,
        "_guild": ctx.guild,
        "_me": ctx.me
    }
    env.update(globals())
    exec(code, env)
    eval_expr = env["eval_expr"]
    result = await eval_expr()
    if result:
        await ctx.send(result)

######################################### Meme Command ####################################


@client.command(pass_context=True)
async def meme(ctx):
    embed = discord.Embed(title="Meme", description=None)

    async with aiohttp.ClientSession() as cs:
        async with cs.get('https://www.reddit.com/r/ProgrammerHumor/new.json?sort=hot') as r:
            res = await r.json()
            embed.set_image(url=res['data']['children']
                            [random.randint(0, 25)]['data']['url'])
            await ctx.send(embed=embed, content=None)
        
 ######################################## Hack Command #####################################
@client.command(pass_context=True)
async def hack(ctx, member:discord.Member = None):
    if not member:
        await ctx.send("Please specify a member")
        return

    passwords=['imnothackedlmao','sendnoodles63','ilovenoodles','icantcode','christianmicraft','server','icantspell','hackedlmao','WOWTONIGHT','69'] 
    fakeips=['154.2345.24.743','255.255. 255.0','356.653.56','101.12.8.6053','255.255. 255.0']

    embed=discord.Embed(title=f"**Hacking: {member}** 0%", color=0x2f3136)
    m = await ctx.send(embed=embed)
    time.sleep(1)
    embed=discord.Embed(title=f"**Hacking: {member}** 19%", color=0x2f3136)
    await m.edit(embed=embed)
    time.sleep(1)
    embed=discord.Embed(title=f"**Hacking: {member}** 34%", color=0x2f3136)
    await m.edit(embed=embed)
    time.sleep(1)
    embed=discord.Embed(title=f"**Hacking: {member}** 55%", color=0x2f3136)
    await m.edit(embed=embed)
    time.sleep(1)
    embed=discord.Embed(title=f"**Hacking: {member}** 67%", color=0x2f3136)
    await m.edit(embed=embed)
    time.sleep(1)
    embed=discord.Embed(title=f"**Hacking: {member}** 84%", color=0x2f3136)
    await m.edit(embed=embed)
    time.sleep(1)
    embed=discord.Embed(title=f"**Hacking: {member}** 99%", color=0x2f3136)
    await m.edit(embed=embed)
    time.sleep(1)
    embed=discord.Embed(title=f"**Hacking: {member}** 100%", color=0x2f3136)
    await m.edit(embed=embed)
    time.sleep(3)
    embed=discord.Embed(title=f"{member} info ", description=f"*Email `{member.name}@hacked.com` Password `{random.choice(passwords)}`  IP `{random.choice(fakeips)}`*", color=0x2f3136)
    embed.set_footer(text="This is a joke pls dont worry haha. All the above given is fake")
    await m.edit(embed=embed)
    time.sleep(1)
 
################################################ Server Info Command ####################################################       
@client.command()
async def server(ctx):
        """Shows server info"""

        server = ctx.guild

        roles = str(len(server.roles))
        emojis = str(len(server.emojis))
        channels = str(len(server.channels))

        embeded = discord.Embed(title=server.name, description='Server Info', color=discord.Colour.blurple())
        embeded.set_thumbnail(url=server.icon_url)
        embeded.add_field(name="Created on:", value=server.created_at.strftime('%d %B %Y at %H:%M UTC+3'), inline=False)
        embeded.add_field(name="Server ID:", value=server.id, inline=False)
        embeded.add_field(name="Users on server:", value=server.member_count, inline=True)
        embeded.add_field(name="Server owner:", value=server.owner, inline=True)

        embeded.add_field(name="Server Region:", value=server.region, inline=True)
        embeded.add_field(name="Verification Level:", value=server.verification_level, inline=True)

        embeded.add_field(name="Role Count:", value=roles, inline=True)
        embeded.add_field(name="Emoji Count:", value=emojis, inline=True)
        embeded.add_field(name="Channel Count:", value=channels, inline=True)

        await ctx.send(embed=embeded)

############################################# User Info Command ###############################################
@client.command()
async def user(ctx, *, user: discord.Member = None):

        if user is None:
            user = ctx.author

        embed = discord.Embed(
            colour=discord.Colour.dark_green(),
        title=f"{user.name}'s (Nickname: {user.nick}) Stats and Information."
        )
        embed.set_footer(text=f"ID: {user.id}")
        embed.set_thumbnail(url=user.avatar_url_as(format="png"))
        embed.add_field(name="__**General information:**__", value=f"**Discord Name:** {user.name}\n"
                                                                   f"**Account created:** {user.created_at.__format__('%A %d %B %Y at %H:%M')}\n"
                                                                   f"**Status:** {user.status}\n"
                                                                   f"**Activity:** {user.activity}", inline=False)
        embed.add_field(name="__**Server-related information:**__", value=f"**Nickname:** {user.nick}\n"
                                                                          f"**Joined server:** {user.joined_at.__format__('%A %d %B %Y at %H:%M')}\n"
                                                                          f"**Roles:** {' '.join([r.mention for r in user.roles[1:]])}")
        return await ctx.send(embed=embed)


######################################## Message Delete Log #####################################

@client.command()
async def on_message_delete(ctx, message):
    delete_embed = discord.Embed(
        colour=message.author.color,
        timestamp=datetime.datetime.utcnow(),
        description='Message Deleted in channel {}'.format(message.channel.mention)).set_author(
        name=message.author,
        icon_url=message.author.avatar_url)
    delete_embed.add_field(name="Message", value=message)
    delete_embed.set_footer(text='Timezone: GMT+4',
                            icon_url=ctx.bot.user.avatar_url)

    global mod_channel
    await mod_channel.send(delete_embed)


######################################## Help Command #####################################


@client.command()
async def help(ctx):
    help_embed = discord.Embed(title="All the commands of FarmTechBot", url="https://www.farmtech.gq",
                               description="To get this message use `!help`", color=0x25e432)
    help_embed.set_author(name="Help")
    help_embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/810546790172590166/814071210233167892/Green_School_Science_Club_Logo_2.png")
    help_embed.add_field(name="1. User Commands",
                         value="Commands all users can use", inline=False)
    help_embed.add_field(
        name="`!poll`", value="To add a poll with your idea", inline=True)
    help_embed.add_field(
        name="`!echo`", value="To echo any message", inline=True)
    help_embed.add_field(
        name="`!ping`", value="To find out ping", inline=True)
    help_embed.add_field(
        name="`!meme`", value="You know what this does", inline=True)

    help_embed.add_field(
        name="`!hack`", value="Hack your friends with this command", inline=True)
    
    help_embed.add_field(name="2. Mod Commands",
                         value="Commands only Mod/Admin/Head can use", inline=False)
    help_embed.add_field(name="`!ban`", value="To ban a user", inline=True)
    help_embed.add_field(
        name="`!clear`", value="To delete mulitple messages", inline=True)
    help_embed.add_field(name="3. Admin Commands",
                         value="Commands only Admin/Head can use", inline=False)
    help_embed.add_field(
        name="`!kick`", value="To directly kick a member", inline=True)
    help_embed.add_field(
        name="`!unban`", value="To unban a member", inline=True)

    help_embed.add_field(name="3. Head Commands",
                         value="Commands only Heads can use", inline=False)
    help_embed.add_field(
        name="`!nuke`", value="To nuke a channel", inline=True)
    help_embed.add_field(
        name="`!embed`", value="To send an embed", inline=True)
    help_embed.add_field(
        name="`!uptime`", value="To find out the uptime of the bot", inline=True)

    help_embed.set_footer(
        text=f"{ctx.guild.name}  •  {datetime.strftime(datetime.now(), '%d.%m.%Y at %I:%M %p')}")
    await ctx.send(embed=help_embed)

######################################### Uptime Command ########################################


@client.command(pass_context=True)
async def uptime(ctx):
    now = datetime.utcnow()
    elapsed = now - starttime
    seconds = elapsed.seconds
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    await ctx.send("I have been online for `{}d {}h {}m {}s` since my last restart".format(elapsed.days, hours, minutes, seconds))


starttime = datetime.utcnow()

######################################### Client Run ########################################
client.run(bot_token)
