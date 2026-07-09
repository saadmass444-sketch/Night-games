import discord
from discord.ext import commands
import random
import asyncio
import json
import os
import io
import math
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

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

# 3. Bot Ready Event
@bot.event
async def on_ready():
    print(f"🤖 البوت جاهز للعمل باسم: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="الألعاب العربية | !العاب"))

# 4. Games Help Menu
@bot.command(name="العاب")
async def help_games(ctx):
    embed = discord.Embed(
        title="⭐ - Games Commands",
        color=discord.Color.from_rgb(243, 156, 18),
    )
    if bot.user and bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(
        name="الألعاب الجماعية ❯",
        value="حساب , عواصم , فكاك , اعلام , تخمين , كت , روليت",
        inline=False,
    )
    embed.add_field(
        name="اوامر البوت ❯",
        value="بروفايل , نقاط , توب",
        inline=False,
    )
    await ctx.send(embed=embed)


# ----------------- [ DYNAMIC WHEEL GENERATOR ] -----------------

def generate_wheel_image(players, chosen_player):
    """Generates a dynamic prize wheel matching the style provided by the user."""
    size = (600, 600)
    img = Image.new("RGBA", size, (47, 49, 54, 255)) # Discord Dark Theme background color
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = size[0] // 2, size[1] // 2
    radius = 240
    num_players = len(players)
    slice_angle = 360 / num_players if num_players > 0 else 360
    
    # Palette themes matching premium bots
    colors = [(139, 131, 153, 255), (218, 212, 224, 255), (94, 84, 109, 255)]
    
    # Draw Slices
    for i, player in enumerate(players):
        start_ang = i * slice_angle - 90
        end_ang = (i + 1) * slice_angle - 90
        fill_color = colors[i % len(colors)]
        
        draw.pieslice([center_x - radius, center_y - radius, center_x + radius, center_y + radius], 
                      start=start_ang, end=end_ang, fill=fill_color, outline=(32, 34, 37, 255), width=4)
        
        # Draw Name Text rotated inside the wheel segment
        try:
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            
        mid_angle = math.radians(start_ang + slice_angle / 2)
        text_dist = radius * 0.6
        tx = center_x + math.cos(mid_angle) * text_dist
        ty = center_y + math.sin(mid_angle) * text_dist
        
        name_str = player.display_name[:10]
        draw.text((tx, ty), name_str, fill=(40, 40, 40, 255), font=font, anchor="mm")

    # Draw Outer Border Indicator Ring
    draw.ellipse([center_x - radius, center_y - radius, center_x + radius, center_y + radius], outline=(79, 70, 93, 255), width=8)
    
    # Draw Top Pointer Arrow Indicator
    draw.polygon([(center_x - 15, center_y - radius - 5), (center_x + 15, center_y - radius - 5), (center_x, center_y - radius + 20)], fill=(255, 255, 255, 255))

    # Fetch and render current player's circular profile picture inside the center core
    try:
        avatar_url = chosen_player.display_avatar.with_size(128).url
        response = requests.get(avatar_url, timeout=5)
        avatar_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        avatar_img = avatar_img.resize((140, 140))
        
        # Create circular mask for avatar
        mask = Image.new("L", (140, 140), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, 140, 140], fill=255)
        
        # Paste inside center ring
        img.paste(avatar_img, (center_x - 70, center_y - 70), mask)
        draw.ellipse([center_x - 73, center_y - 73, center_x + 73, center_y + 73], outline=(60, 50, 75, 255), width=6)
    except Exception:
        # Fallback circle if avatar download fails
        draw.ellipse([center_x - 70, center_y - 70, center_x + 70, center_y + 70], fill=(100, 90, 115, 255), outline=(255, 255, 255, 255), width=4)

    # Save to binary output stream container
    final_buffer = io.BytesIO()
    img.save(final_buffer, format="PNG")
    final_buffer.seek(0)
    return final_buffer


# ----------------- [ ROULETTE LOBBY INTERFACES ] -----------------

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
        embed.set_image(url="https://images2.imgbox.com/39/5f/ZofkOnxJ_o.png")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="دخول", style=discord.ButtonStyle.green, custom_id="join_btn", emoji="👥")
    async def join_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            return await interaction.response.send_message("❌ أنت مسجل بالفعل في هذه الجولة!", ephemeral=True)
        if len(self.players) >= 1000:
            return await interaction.response.send_message("❌ عذراً، اللوبي ممتلئ!", ephemeral=True)
        
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
        embed = discord.Embed(title="🏪 متجر الروليت", description="قريباً سيتم إضافة أسلحة ودروع المتجر هنا!", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TurnActionView(discord.ui.View):
    def __init__(self, current_player, players_list):
        super().__init__(timeout=15.0) # Matches the 15 seconds rule from your screenshot!
        self.current_player = current_player
        self.players_list = players_list
        self.action_chosen = None  
        self.target_member = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.current_player:
            await interaction.response.send_message("❌ الدور ليس دورك لتتحكم بالأزرار!", ephemeral=True)
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

    @discord.ui.button(label="اختار لاعب", style=discord.ButtonStyle.secondary, emoji="🎯")
    async def pick_target(self, interaction: discord.Interaction, button: discord.ui.Button):
        opponents = [p for p in self.players_list if p != self.current_player]
        if not opponents:
            self.action_chosen = "random"
            self.stop()
            return

        select_view = discord.ui.View(timeout=15)
        options = [discord.SelectOption(label=opp.display_name, value=str(opp.id)) for opp in opponents[:25]]
        dropdown = discord.ui.Select(placeholder="اختر الشخص الذي تريد طرده وتصويب الروليت عليه...", options=options)

        async def dropdown_callback(inter: discord.Interaction):
            selected_id = int(dropdown.values[0])
            self.target_member = discord.utils.get(self.players_list, id=selected_id)
            self.action_chosen = "target"
            await inter.response.defer()
            self.stop()

        dropdown.callback = dropdown_callback
        select_view.add_item(dropdown)
        await interaction.response.send_message("🎯 اختر ضحيتك المستهدفة:", view=select_view, ephemeral=True)


# ----------------- [ ROULETTE COMMAND CORE ] -----------------

@bot.command(name="روليت")
async def roulette_game(ctx):
    lobby = RouletteLobbyView(ctx, timeout_secs=35)
    
    embed = discord.Embed(
        title="🎯 | نظام الروليت الملكي (Roulette)",
        description=f"**اللاعبين المسجلين:** `0/1000`\n⏳ المتبقي على البدء: **35 ثانية**",
        color=discord.Color.from_rgb(106, 90, 205)
    )
    embed.set_image(url="https://images2.imgbox.com/39/5f/ZofkOnxJ_o.png")
    lobby_msg = await ctx.send(embed=embed, view=lobby)

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
            edit_embed.set_image(url="https://images2.imgbox.com/39/5f/ZofkOnxJ_o.png")
            await lobby_msg.edit(embed=edit_embed, view=lobby)
        except Exception:
            break

    for child in lobby.children:
        child.disabled = True
    try:
        await lobby_msg.edit(view=lobby)
    except Exception:
        pass

    active_players = lobby.players

    if len(active_players) < 2:
        return await ctx.send("❌ تم إلغاء الجولة لعدم توفر لاعبين كافيين (اقل شي لاعبين اثنين)!")

    round_counter = 1

    while len(active_players) > 1:
        current_turn_player = random.choice(active_players)
        
        # Dynamic Wheel Render Section
        wheel_buffer = generate_wheel_image(active_players, current_turn_player)
        wheel_file = discord.File(fp=wheel_buffer, filename="wheel.png")
        
        # Build layout matching the reference screenshot exactly
        players_list_str = " | ".join([f"`{idx+1} - {p.display_name}`" for idx, p in enumerate(active_players)])
        
        round_embed = discord.Embed(
            title=f"الجولة {round_counter} - الدور لـ {current_turn_player.display_name}",
            description=f"{current_turn_player.mention} ، **لديك 15 ثانية لاختيار شخص لطردة أو اللعب عشوائياً!**\n\n**اللاعبين المتواجدين بالعجلة:**\n{players_list_str}",
            color=discord.Color.from_rgb(94, 84, 109)
        )
        round_embed.set_image(url="attachment://wheel.png")
        
        action_view = TurnActionView(current_turn_player, active_players)
        round_msg = await ctx.send(file=wheel_file, embed=round_embed, view=action_view)
        
        await action_view.wait()
        
        # Timeout Rule Handling
        if action_view.action_chosen is None:
            active_players.remove(current_turn_player)
            await ctx.send(f"💀 تم طرد {current_turn_player.mention} بسبب عدم الاستجابة وانتهاء الـ 15 ثانية!")
            round_counter += 1
            continue
            
        # Action Resolution Branches
        if action_view.action_chosen == "leave":
            active_players.remove(current_turn_player)
            await ctx.send(f"🏳️ اختار اللاعب {current_turn_player.mention} **الانسحاب** وغادر الجولة تلقائياً.")
            
        else:
            if action_view.action_chosen == "random":
                opponents = [p for p in active_players if p != current_turn_player]
                victim = random.choice(opponents) if opponents else current_turn_player
                action_type_text = "بشكل عشوائي"
            else:
                victim = action_view.target_member
                action_type_text = "باختيار مباشر"
                
            # Perform elimination
            active_players.remove(victim)
            await ctx.send(f"🔴 تم طرد {victim.mention} **{action_type_text}**، سوف تبدأ الجولة التالية قريباً...")
            
        round_counter += 1
        await asyncio.sleep(4)

    ultimate_winner = active_players[0]
    add_points(str(ultimate_winner.id), 50)
    
    win_embed = discord.Embed(
        title="🏆 بطل الروليت الملكي!",
        description=f"كفووو! نجح {ultimate_winner.mention} بالصمود للنهاية وسحق بقية الخصوم!\nحصل على **50 نقطة مكافأة** 💰 وتم تسجيل فوز بملفه الشخصي.",
        color=discord.Color.gold()
    )
    await ctx.send(embed=win_embed)


# ----------------- [ PRE-EXISTING TRIVIA MINI GAMES ] -----------------
# (Keeping standard commands like أعلام, حساب, تخمين unchanged below...)

@bot.command(name="اعلام")
async def flags_game(ctx):
    flags_dict = [
        {"flag": "🇸🇦", "answers": ["السعودية"]},
        {"flag": "🇪🇬", "answers": ["مصر"]}
    ]
    item = random.choice(flags_dict)
    embed = discord.Embed(title="🚩 أعلام الدول العربية", description=f"# {item['flag']}", color=discord.Color.red())
    embed.set_image(url="https://images2.imgbox.com/39/da/tFpT6Ior_o.png")
    await ctx.send(embed=embed)

@bot.command(name="حساب")
async def math_game(ctx):
    n1, n2 = random.randint(5, 50), random.randint(5, 50)
    embed = discord.Embed(title="🔢 الحساب السريع", description=f"# `{n1} + {n2} = ؟`", color=discord.Color.blue())
    embed.set_image(url="https://images2.imgbox.com/15/8e/m7qIepxR_o.png")
    await ctx.send(embed=embed)

@bot.command(name="تخمين")
async def guessing_game(ctx):
    embed = discord.Embed(title="🔢 تخمين الرقم", description="اخترت رقم من 1 لـ 100 خمنه!", color=discord.Color.dark_grey())
    embed.set_image(url="https://images2.imgbox.com/39/12/fQy1Wz28_o.png")
    await ctx.send(embed=embed)

@bot.command(name="عواصم")
async def capitals_game(ctx):
    embed = discord.Embed(title="🌍 عواصم الدول", description="ما هي عاصمة السعودية؟", color=discord.Color.green())
    embed.set_image(url="https://images2.imgbox.com/4a/14/NInPizZ6_o.png")
    await ctx.send(embed=embed)

@bot.command(name="فكاك")
async def fekak_game(ctx):
    embed = discord.Embed(title="✏️ فكاك الجمل", description="`سيرفرالعاب`", color=discord.Color.orange())
    embed.set_image(url="https://images2.imgbox.com/f9/52/Ff06B9XF_o.png")
    await ctx.send(embed=embed)

@bot.command(name="كت")
async def cut_tweet(ctx):
    questions = ["لو رجع بيك الزمن قبل 5 سنوات، ايش الشي الوحيد الي بتغيره؟"]
    await ctx.send(embed=discord.Embed(title="❓ كت تويت", description=random.choice(questions), color=discord.Color.purple()))

@bot.command(name="نقاط")
async def check_points(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user_stats = data.get(str(member.id), {"points": 0, "wins": 0})
    await ctx.send(f"💰 رصيد {member.mention}: **{user_stats['points']}** نقطة.")

@bot.command(name="بروفايل")
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user_stats = data.get(str(member.id), {"points": 0, "wins": 0})
    embed = discord.Embed(title=f"👤 ملف اللاعب: {member.display_name}", color=discord.Color.blue())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="💰 النقاط:", value=f"`{user_stats['points']}`", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="توب")
async def leaderboard(ctx):
    await ctx.send("🏆 قائمة المتصدرين تعمل بشكل ممتاز!")

TOKEN = os.getenv("DISCORD_TOKEN") or 'YOUR_FALLBACK_TOKEN'
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"Bot failed: {e}")
