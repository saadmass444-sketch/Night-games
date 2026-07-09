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

# 3. Dynamic ANIMATED GIF Wheel Generator
def generate_spinning_wheel_gif(players, output_path="roulette.gif"):
    """Generates a custom animated spinning GIF with active player slices."""
    size = (500, 500)
    num_players = len(players)
    
    # Base asset if empty
    if num_players == 0:
        img = Image.new("RGBA", size, (44, 47, 51, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 50, 450, 450], fill=(35, 39, 42, 255), outline=(114, 137, 218, 255), width=4)
        img.save(output_path)
        return

    colors = [
        (230, 57, 70, 255), (241, 250, 238, 255), (29, 53, 87, 255),
        (69, 123, 157, 255), (233, 196, 106, 255), (244, 162, 97, 255)
    ]
    slice_angle = 360.0 / num_players
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # Step A: Draw a single flat wheel image template
    base_wheel = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_base = ImageDraw.Draw(base_wheel)
    
    for i, player in enumerate(players):
        start_ang = i * slice_angle
        end_ang = (i + 1) * slice_angle
        fill_color = colors[i % len(colors)]
        
        draw_base.pieslice([40, 40, 460, 460], start=start_ang, end=end_ang, fill=fill_color, outline=(0, 0, 0, 255), width=2)
        
        # Write text name on the base slice frame
        mid_angle = math.radians(start_ang + (slice_angle / 2))
        text_x = 250 + 120 * math.cos(mid_angle)
        text_y = 250 + 120 * math.sin(mid_angle)
        name_text = player.display_name[:8]
        text_color = (0, 0, 0, 255) if fill_color[1] > 200 else (255, 255, 255, 255)
        draw_base.text((text_x, text_y), name_text, fill=text_color, font=font, anchor="mm")
        
    draw_base.ellipse([35, 35, 465, 465], outline=(255, 215, 0, 255), width=4)
    draw_base.ellipse([225, 225, 275, 275], fill=(255, 215, 0, 255), outline=(0, 0, 0, 255), width=2)

    # Step B: Spin the canvas to compile sequential frames
    frames = []
    total_frames = 16  # Creates a smooth fast spin cycle
    
    for frame_idx in range(total_frames):
        # Calculate changing spin angles
        rotation_angle = (frame_idx * (360 / total_frames) * 2) % 360
        
        # Rotate base asset wheel layer
        rotated_wheel = base_wheel.rotate(-rotation_angle, resample=Image.BICUBIC, center=(250, 250))
        
        # Composite structural background frame
        frame_canvas = Image.new("RGBA", size, (44, 47, 51, 255))
        frame_canvas.alpha_composite(rotated_wheel)
        
        # Superimpose static top pin indicator point (Static arrow doesn't rotate)
        draw_static = ImageDraw.Draw(frame_canvas)
        draw_static.polygon([(250, 28), (240, 5), (260, 5)], fill=(255, 0, 0, 255))
        
        # Convert frame layer back to standard RGB values for output formatting
        frames.append(frame_canvas.convert("RGB"))

    # Save frames out together as an automated looping GIF file
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=60,  # Milliseconds per frame (fast spin animation style)
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
    embed = discord.Embed(
        title="⭐ - Games Commands",
        color=discord.Color.from_rgb(243, 156, 18),
    )
    if bot.user and bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(name="الألعاب الجماعية ❯", value="حساب , عواصم , فكاك , اعلام , تخمين , كت , روليت", inline=False)
    embed.add_field(name="اوامر البوت ❯", value="بروفايل , نقاط , توب", inline=False)
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
            title="🎯 | نظام الروليت الملكي (Roulette)",
            description=f"**اللاعبين المسجلين:** `{len(self.players)}/1000`\n⏳ المتبقي على البدء: **{self.timeout_secs} ثانية**",
            color=discord.Color.from_rgb(106, 90, 205)
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

    @discord.ui.button(label="المتجر", style=discord.ButtonStyle.blurple, custom_id="shop_btn", emoji="🏪")
    async def shop_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🏪 متجر الروليت قريباً!", ephemeral=True)


class TurnActionView(discord.ui.View):
    def __init__(self, current_player, players_list):
        super().__init__(timeout=15.0)
        self.current_player = current_player
        self.players_list = players_list
        self.action_chosen = None  
        self.target_member = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.current_player:
            await interaction.response.send_message("❌ الدور ليس دورك!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="عشوائي", style=discord.ButtonStyle.success, emoji="🎲")
    async def random_target(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.action_chosen = "random"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="انسحاب", style=discord.ButtonStyle.danger, emoji="🏳️")
    async def surrender(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.action_chosen = "leave"
        await interaction.response.defer()
        self.stop()


# ----------------- [ ROULETTE COMMAND CORE ] -----------------

@bot.command(name="روليت")
async def roulette_game(ctx):
    lobby = RouletteLobbyView(ctx, timeout_secs=35)
    
    embed = discord.Embed(
        title="🎯 | نظام الروليت الملكي (Roulette)",
        description=f"**اللاعبين المسجلين:** `0/1000`\n⏳ المتبقي على البدء: **35 ثانية**",
        color=discord.Color.from_rgb(106, 90, 205)
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
                title="🎯 | نظام الروليت الملكي (Roulette)",
                description=f"**اللاعبين المسجلين:** `{len(lobby.players)}/1000`\n⏳ المتبقي على البدء: **{remaining} ثانية**",
                color=discord.Color.from_rgb(106, 90, 205)
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
            color=discord.Color.from_rgb(106, 90, 205)
        )
        round_embed.set_thumbnail(url=current_turn_player.display_avatar.url)
        
        # Build dynamic rotating GIF containing current round players
        generate_spinning_wheel_gif(active_players, "round_wheel.gif")
        round_file = discord.File("round_wheel.gif", filename="wheel.gif")
        round_embed.set_image(url="attachment://wheel.gif")
        
        action_view = TurnActionView(current_turn_player, active_players)
        round_msg = await ctx.send(embed=round_embed, view=action_view, file=round_file)
        
        await action_view.wait()
        
        if action_view.action_chosen is None or action_view.action_chosen == "leave":
            if current_turn_player in active_players:
                active_players.remove(current_turn_player)
            await ctx.send(f"💀 غادر أو خسِر {current_turn_player.mention} هذه الجولة.")
        else:
            opponents = [p for p in active_players if p != current_turn_player]
            victim = random.choice(opponents) if opponents else current_turn_player
            if victim in active_players:
                active_players.remove(victim)
                await ctx.send(f"🔴 رصاصة الروليت طردت {victim.mention}! جاري تجهيز الجولة التالية...")

        round_counter += 1
        await asyncio.sleep(4)

    if len(active_players) == 1:
        ultimate_winner = active_players[0]
        add_points(str(ultimate_winner.id), 50)
        
        win_embed = discord.Embed(
            title="🏆 بطل الروليت الملكي!",
            description=f"كفووو! نجح {ultimate_winner.mention} بالصمود للنهاية!\nحصل على **50 نقطة مكافأة** 💰",
            color=discord.Color.gold()
        )
        await ctx.send(embed=win_embed)


# --- TRIVIA CHECKS ---
@bot.command(name="حساب")
async def math_game(ctx):
    await ctx.send("🔢 اكتب معادلتك الحسابية!")

@bot.command(name="نقاط")
async def check_points(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user_stats = data.get(str(member.id), {"points": 0, "wins": 0})
    await ctx.send(f"💰 رصيد {member.mention}: **{user_stats['points']}** نقطة.")

TOKEN = os.getenv("DISCORD_TOKEN") or 'YOUR_FALLBACK_TOKEN'
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"Bot failed: {e}")
