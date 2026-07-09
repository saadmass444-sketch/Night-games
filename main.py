import discord
from discord.ext import commands
import random
import asyncio
import json
import os
import math
from PIL import Image, ImageDraw, ImageFont

# 1. Initialize Bot & Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

DB_FILE = os.path.join(os.path.dirname(__file__), "database.json")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")

# 2. Database Helper Functions
def load_data():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_points(user_id: str, amount: int):
    data = load_data()
    if user_id not in data:
        data[user_id] = {"points": 0, "wins": 0}
    data[user_id]["points"] += amount
    data[user_id]["wins"] += 1
    save_data(data)

# 3. Dynamic LOGO-THEMED (Night & روليت) Spinning GIF Generator
def generate_spinning_wheel_gif(players, output_path="roulette.gif"):
    """Generates an animated spinning GIF using the logo template, swapping Ashn to Night."""
    num_players = len(players)
    
    # Dimensions of your logo template
    template_size = (1024, 512)
    
    # Load background logo template or fallback if it's missing
    if os.path.exists(LOGO_PATH):
        base_template = Image.open(LOGO_PATH).convert("RGBA")
    else:
        # Fallback background color if logo.png isn't uploaded yet
        base_template = Image.new("RGBA", template_size, (50, 54, 62, 255))
    
    # Prepare canvas to hide "Ashn" and place "Night"
    draw_template = ImageDraw.Draw(base_template)
    
    # Mask over old "Ashn" area with matching background color (approximate coordinates)
    draw_template.rectangle([640, 110, 750, 170], fill=(50, 54, 62, 255))
    
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
        
    # Draw new branding text "Night"
    draw_template.text((685, 135), "Night", fill=(255, 255, 255, 255), font=font, anchor="mm")

    # Center circle coordinates of the metallic wheel ring inside your logo
    # center_x = 490, center_y = 245, radius = 135
    wheel_size = (270, 270)
    
    if num_players == 0:
        # Save static image with changed text if no players joined yet
        base_template.convert("RGB").save(output_path)
        return

    # Deep royal theme colors matching the metallic logo palette
    colors = [
        (43, 37, 73, 255),    # Dark Metallic Purple
        (94, 82, 135, 255),   # Muted Violet
        (140, 132, 170, 255), # Steel Purple
        (201, 172, 114, 255), # Metallic Center Gold
        (24, 22, 38, 255)     # Deep Dark Shadow
    ]
    
    slice_angle = 360.0 / num_players

    # Draw the dynamic player wheel layer independently so we can spin it
    wheel_layer = Image.new("RGBA", wheel_size, (0, 0, 0, 0))
    draw_wheel = ImageDraw.Draw(wheel_layer)
    
    for i, player in enumerate(players):
        start_ang = i * slice_angle
        end_ang = (i + 1) * slice_angle
        fill_color = colors[i % len(colors)]
        
        # Draw wheel slices inside its boundary square
        draw_wheel.pieslice([5, 5, 265, 265], start=start_ang, end=end_ang, fill=fill_color, outline=(20, 20, 30, 255), width=2)
        
        # Calculate dynamic usernames overlay placement
        mid_angle = math.radians(start_ang + (slice_angle / 2))
        text_x = 135 + 75 * math.cos(mid_angle)
        text_y = 135 + 75 * math.sin(mid_angle)
        name_text = player.display_name[:7]
        
        text_color = (13, 10, 26, 255) if fill_color == (201, 172, 114, 255) else (255, 255, 255, 255)
        draw_wheel.text((text_x, text_y), name_text, fill=text_color, font=font, anchor="mm")
        
    # Small aesthetic central gold axis pin
    draw_wheel.ellipse([115, 115, 155, 155], fill=(201, 172, 114, 255), outline=(0, 0, 0, 255), width=1)

    # Compile animation frames by spinning the custom player wheel
    frames = []
    total_frames = 12
    
    for frame_idx in range(total_frames):
        rotation_angle = (frame_idx * (360 / total_frames) * 2) % 360
        rotated_inner_wheel = wheel_layer.rotate(-rotation_angle, resample=Image.BICUBIC, center=(135, 135))
        
        # Create a fresh canvas copy from our custom template framework
        frame_canvas = base_template.copy()
        
        # Place the spinning wheel perfectly inside the logo's central chrome framework
        frame_canvas.alpha_composite(rotated_inner_wheel, dest=(490 - 135, 245 - 135))
        
        frames.append(frame_canvas.convert("RGB"))

    # Output frames together as a high-fidelity custom brand GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=65,
        loop=0
    )


# 4. Bot Ready Event
@bot.event
async def on_ready():
    print(f"🤖 البوت جاهز للعمل باسم: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="الألعاب العربية | !العاب"))

# 5. Games Help Menu
@bot.command(name="العاب")
async def help_games(ctx):
    embed = discord.Embed(title="⭐ - Games Commands", color=discord.Color.from_rgb(94, 82, 135))
    if bot.user and bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.add_field(name="الألعاب الجماعية ❯", value="حساب , عواصم , فكاك , اعلام , تخمين , كت , روليت", inline=False)
    await ctx.send(embed=embed)


# ----------------- [ ROULETTE INTERFACES ] -----------------

class RouletteLobbyView(discord.ui.View):
    def __init__(self, ctx, timeout_secs=35):
        super().__init__(timeout=timeout_secs + 5)
        self.ctx = ctx
        self.players = []
        self.timeout_secs = timeout_secs

    async def update_lobby_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎯 | نظام الروليت الملكي (Night Roulette)",
            description=f"**اللاعبين المسجلين:** `{len(self.players)}/1000`\n⏳ المتبقي على البدء: **{self.timeout_secs} ثانية**",
            color=discord.Color.from_rgb(94, 82, 135)
        )
        
        generate_spinning_wheel_gif(self.players, "lobby_wheel.gif")
        file = discord.File("lobby_wheel.gif", filename="wheel.gif")
        embed.set_image(url="attachment://wheel.gif")
        
        await interaction.response.edit_message(embed=embed, view=self, attachments=[file])

    @discord.ui.button(label="دخول", style=discord.ButtonStyle.green, custom_id="join_btn", emoji="👥")
    async def join_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            return await interaction.response.send_message("❌ أنت مسجل بالفعل في هذه الجولة!", ephemeral=True)
        self.players.append(interaction.user)
        await self.update_lobby_message(interaction)

    @discord.ui.button(label="خروج", style=discord.ButtonStyle.red, custom_id="leave_btn", emoji="🚪")
    async def leave_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            return await interaction.response.send_message("❌ أنت لست مسجلاً أساساً!", ephemeral=True)
        self.players.remove(interaction.user)
        await self.update_lobby_message(interaction)


# ----------------- [ ROULETTE COMMAND CORE ] -----------------

@bot.command(name="روليت")
async def roulette_game(ctx):
    lobby = RouletteLobbyView(ctx, timeout_secs=35)
    
    embed = discord.Embed(
        title="🎯 | نظام الروليت الملكي (Night Roulette)",
        description=f"**اللاعبين المسجلين:** `0/1000`\n⏳ المتبقي على البدء: **35 ثانية**",
        color=discord.Color.from_rgb(94, 82, 135)
    )
    
    generate_spinning_wheel_gif([], "lobby_wheel.gif")
    file = discord.File("lobby_wheel.gif", filename="wheel.gif")
    embed.set_image(url="attachment://wheel.gif")
    
    lobby_msg = await ctx.send(embed=embed, view=lobby, file=file)

    for remaining in range(30, -1, -5):
        await asyncio.sleep(5)
        if len(lobby.players) >= 1000:
            break
        lobby.timeout_secs = remaining
        try:
            edit_embed = discord.Embed(
                title="🎯 | نظام الروليت الملكي (Night Roulette)",
                description=f"**اللاعبين المسجلين:** `{len(lobby.players)}/1000`\n⏳ المتبقي على البدء: **{remaining} ثانية**",
                color=discord.Color.from_rgb(94, 82, 135)
            )
            generate_spinning_wheel_gif(lobby.players, "lobby_wheel.gif")
            loop_file = discord.File("lobby_wheel.gif", filename="wheel.gif")
            edit_embed.set_image(url="attachment://wheel.gif")
            await lobby_msg.edit(embed=edit_embed, view=lobby, attachments=[loop_file])
        except Exception:
            break

    for child in lobby.children:
        child.disabled = True
    try:
        await lobby_msg.edit(view=lobby)
    except Exception:
        pass

    active_players = lobby.players.copy()
    if len(active_players) < 2:
        return await ctx.send("❌ تم إلغاء الجولة لعدم توفر لاعبين كافيين!")

    round_counter = 1

    while len(active_players) > 1:
        current_turn_player = random.choice(active_players)
        players_list_str = " | ".join([f"`{idx+1} - {p.display_name}`" for idx, p in enumerate(active_players)])
        
        round_embed = discord.Embed(
            title=f"الجولة {round_counter} - الدور لـ {current_turn_player.display_name}",
            description=f"{current_turn_player.mention} ، **لديك 15 ثانية لاختيار تصرف أو اللعب عشوائياً!**\n\n**المتواجدين بالعجلة:**\n{players_list_str}",
            color=discord.Color.from_rgb(94, 82, 135)
        )
        
        generate_spinning_wheel_gif(active_players, "round_wheel.gif")
        round_file = discord.File("round_wheel.gif", filename="wheel.gif")
        round_embed.set_image(url="attachment://wheel.gif")
        
        class TempView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=15.0)
                self.chosen = "random"
            @discord.ui.button(label="عشوائي", style=discord.ButtonStyle.success)
            async def rand(self, inter, btn):
                self.chosen = "random"
                await inter.response.defer()
                self.stop()

        tv = TempView()
        await ctx.send(embed=round_embed, view=tv, file=round_file)
        await tv.wait()
        
        opponents = [p for p in active_players if p != current_turn_player]
        victim = random.choice(opponents) if opponents else current_turn_player
        if victim in active_players:
            active_players.remove(victim)
            await ctx.send(f"🔴 رصاصة الروليت طردت {victim.mention}!")

        round_counter += 1
        await asyncio.sleep(4)

    if len(active_players) == 1:
        await ctx.send(f"🏆 الفائز هو {active_players[0].mention}!")

TOKEN = os.getenv("DISCORD_TOKEN") or 'YOUR_FALLBACK_TOKEN'
bot.run(TOKEN)
