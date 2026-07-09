import discord
from discord.ext import commands
import random
import asyncio
import json
import os

# 1. Initialize Bot & Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
    await bot.change_presence(activity=discord.Game(name="الألعاب العربية | !help_games"))


# 4. Games Help Menu (Command updated to !العاب)
@bot.command(name="العاب")
async def help_games(ctx):
    embed = discord.Embed(
        title="⭐ - Games Commands",
        color=discord.Color.from_rgb(243, 156, 18),
    )

    embed.add_field(
        name="الألعاب الجماعية ❯",
        value="حساب , عواصم , فكاك , اعلام , تخمين , كت",
        inline=False,
    )
    embed.add_field(
        name="اوامر البوت ❯",
        value="بروفايل , نقاط , توب",
        inline=False,
    )

    await ctx.send(embed=embed)


# ----------------- [ GAMES SECTION ] -----------------

# UPDATED GAME: تخمين الرقم السري مع 10 محاولات
@bot.command(name="تخمين")
async def guessing_game(ctx):
    secret_number = random.randint(1, 100)
    max_attempts = 10
    attempts_left = max_attempts

    await ctx.send(
        f"🔢 | **بدأت لعبة التخمين! لقد اخترت رقماً من 1 إلى 100.**\n"
        f"📬 | معاكم إجمالي **{max_attempts} محاولات** فقط لحزره! خمنوا الآن:"
    )

    def check(m):
        return m.channel == ctx.channel and not m.author.bot and m.content.strip().isdigit()

    timeout_duration = 45.0
    start_time = asyncio.get_event_loop().time()

    while attempts_left > 0:
        current_time = asyncio.get_event_loop().time()
        remaining_time = timeout_duration - (current_time - start_time)

        if remaining_time <= 0:
            await ctx.send(f"⏱️ | انتهى الوقت ولم يحزر أحد الرقم! الرقم الصحيح كان: **{secret_number}**")
            return

        try:
            msg = await bot.wait_for("message", check=check, timeout=remaining_time)
            guess = int(msg.content.strip())

            if guess == secret_number:
                add_points(str(msg.author.id), 20)
                await ctx.send(f"🎉 | كفوووو {msg.author.mention}! حزرت الرقم الصحيح وهو **{secret_number}** وجبت **20 نقطة** 💰")
                return

            attempts_left -= 1

            if attempts_left == 0:
                break

            if guess < secret_number:
                await ctx.send(f"❌ | الرقم {guess} خطأ! الرقم السري **أكبر** ⬆️ (المحاولات المتبقية: `{attempts_left}/{max_attempts}`)")
            else:
                await ctx.send(f"❌ | الرقم {guess} خطأ! الرقم السري **أصغر** ⬇️ (المحاولات المتبقية: `{attempts_left}/{max_attempts}`)")

        except asyncio.TimeoutError:
            await ctx.send(f"⏱️ | انتهى الوقت ولم يحزر أحد الرقم! الرقم الصحيح كان: **{secret_number}**")
            return

    await ctx.send(f"💀 | خلصت كل المحاولات! خسرتوا الجولة. الرقم الصحيح كان: **{secret_number}**")


# GAME 1: اعلام (Flags Game)
@bot.command(name="اعلام")
async def flags_game(ctx):
    flags_dict = [
        {"flag": "🇸🇦", "answers": ["السعودية", "المملكة العربية السعودية"]},
        {"flag": "🇪🇬", "answers": ["مصر", "جمهورية مصر العربية"]},
        {"flag": "🇦🇪", "answers": ["الامارات", "الإمارات", "الامارات العربية المتحدة"]},
        {"flag": "🇶🇦", "answers": ["قطر"]},
        {"flag": "🇰🇼", "answers": ["الكويت"]},
        {"flag": "🇧🇭", "answers": ["البحرين"]},
        {"flag": "🇴🇲", "answers": ["عمان", "عُمان"]},
        {"flag": "🇮🇶", "answers": ["العراق"]},
        {"flag": "🇯🇴", "answers": ["الاردن", "الأردن"]},
        {"flag": "🇵🇸", "answers": ["فلسطين"]},
        {"flag": "🇲🇦", "answers": ["المغرب"]},
        {"flag": "🇩🇿", "answers": ["الجزائر"]},
        {"flag": "🇹🇳", "answers": ["تونس"]},
        {"flag": "🇱🇧", "answers": ["لبنان"]},
        {"flag": "🇸🇾", "answers": ["سوريا"]},
    ]

    item = random.choice(flags_dict)
    await ctx.send(f"🚩 | **أسرع واحد يعرّف اسم هذه الدولة:**\n# {item['flag']}")

    def check(m):
        if m.channel != ctx.channel or m.author.bot:
            return False
        cleaned_user_ans = m.content.strip().replace("ة", "ه")
        for valid_ans in item["answers"]:
            if cleaned_user_ans == valid_ans.replace("ة", "ه"):
                return True
        return False

    try:
        msg = await bot.wait_for("message", check=check, timeout=15.0)
        add_points(str(msg.author.id), 15)
        await ctx.send(f"🎉 | كفو {msg.author.mention}! إجابة صحيحة، الدولة هي **{item['answers'][0]}** (+15 نقطة) 💰")
    except asyncio.TimeoutError:
        await ctx.send(f"⏱️ | انتهى الوقت! الدولة الصحيحة هي: **{item['answers'][0]}**")


# GAME 2: حساب (Quick Math)
@bot.command(name="حساب")
async def math_game(ctx):
    n1 = random.randint(5, 60)
    n2 = random.randint(5, 60)
    op = random.choice(["+", "-"])
    correct = n1 + n2 if op == "+" else n1 - n2

    await ctx.send(f"🔢 | **أسرع واحد يحسبها:**\n` {n1} {op} {n2} = ؟ `")

    def check(m):
        return m.channel == ctx.channel and not m.author.bot and m.content.strip() == str(correct)

    try:
        msg = await bot.wait_for("message", check=check, timeout=15.0)
        add_points(str(msg.author.id), 10)
        await ctx.send(f"🎉 | كفو {msg.author.mention}! إجابتك صحيحة وجبت **10 نقاط** 💰")
    except asyncio.TimeoutError:
        await ctx.send(f"⏱️ | انتهى الوقت! الإجابة الصحيحة هي: **{correct}**")


# GAME 3: عواصم (Capitals)
@bot.command(name="عواصم")
async def capitals_game(ctx):
    capitals_dict = {
        "السعودية": "الرياض",
        "مصر": "القاهرة",
        "الإمارات": "ابوظبي",
        "الكويت": "الكويت",
        "قطر": "الدوحة",
        "العراق": "بغداد",
        "المغرب": "الرباط",
        "تونس": "تونس",
        "الأردن": "عمان",
    }
    country, capital = random.choice(list(capitals_dict.items()))
    await ctx.send(f"🌍 | **ما هي عاصمة دولة:** __**{country}**__ ؟")

    def check(m):
        user_ans = m.content.strip().replace("ة", "ه").replace("أ", "ا")
        bot_ans = capital.replace("ة", "ه").replace("أ", "ا")
        return m.channel == ctx.channel and not m.author.bot and user_ans == bot_ans

    try:
        msg = await bot.wait_for("message", check=check, timeout=20.0)
        add_points(str(msg.author.id), 15)
        await ctx.send(f"🥇 | مبروك {msg.author.mention}! الإجابة صحيحة هي **{capital}**، حصلت على **15 نقطة**")
    except asyncio.TimeoutError:
        await ctx.send(f"⏱️ | انتهى الوقت ولم يعرف أحد الإجابة! العاصمة الصحيحة هي: **{capital}**")


# GAME 4: فكاك (Unscramble)
@bot.command(name="فكاك")
async def fekak_game(ctx):
    words_list = [
        {"masked": "سيرفرالعاب", "clean": "سيرفر العاب"},
        {"masked": "كوروناomg", "clean": "كورونا omg"},
        {"masked": "ديسكوردارابي", "clean": "ديسكورد عربي"},
        {"masked": "برمجةالبوتات", "clean": "برمجة البوتات"},
    ]
    chosen = random.choice(words_list)
    await ctx.send(f"✏️ | **فكك الكلمة التالية وضبط المسافات:**\n`{chosen['masked']}`")

    def check(m):
        return m.channel == ctx.channel and not m.author.bot and m.content.strip() == chosen['clean']

    try:
        msg = await bot.wait_for("message", check=check, timeout=20.0)
        add_points(str(msg.author.id), 10)
        await ctx.send(f"✨ | رهيب {msg.author.mention}! التفكيك الصحيح: **{chosen['clean']}** (+10 نقاط)")
    except asyncio.TimeoutError:
        await ctx.send(f"⏱️ | انتهى الوقت! الحل الصحيح هو: **{chosen['clean']}**")


# GAME 5: كت تويت (Random Question)
@bot.command(name="كت")
async def cut_tweet(ctx):
    questions = [
        "لو رجع بيك الزمن قبل 5 سنوات، ايش الشي الوحيد الي بتغيره؟",
        "اكثر صفة تكررها الناس في مدحك؟",
        "اكلة مستحيل تاكلها لو تموت جوع؟",
        "تفضل تعيش وحيد بمليون دولار، ولا تعيش مع عائلتك بوضع مادي متوسط؟",
        "ايش اخر شي نسخته (كوبي) بجوالك؟ بدون كذب 🧐",
    ]
    q = random.choice(questions)
    embed = discord.Embed(title="❓ | سؤال كت تويت للجميع", description=f"**{q}**", color=discord.Color.purple())
    await ctx.send(embed=embed)


# ----------------- [ DATA & STATS SECTION ] -----------------

@bot.command(name="نقاط")
async def check_points(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user_stats = data.get(str(member.id), {"points": 0, "wins": 0})
    await ctx.send(f"💰 | رصيد نقاط {member.mention} الحالي هو: **{user_stats['points']}** نقطة.")


@bot.command(name="بروفايل")
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user_stats = data.get(str(member.id), {"points": 0, "wins": 0})

    embed = discord.Embed(title=f"👤 ملف اللاعب: {member.display_name}", color=discord.Color.blue())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="💰 النقاط الإجمالية:", value=f"`{user_stats['points']}` ن", inline=True)
    embed.add_field(name="🏆 عدد المرات الفائز بها:", value=f"`{user_stats['wins']}` مرة", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="توب")
async def leaderboard(ctx):
    data = load_data()
    if not data:
        return await ctx.send("❌ لا توجد بيانات مسجلة في السيرفر حالياً.")

    sorted_players = sorted(data.items(), key=lambda item: item[1]["points"], reverse=True)[:10]

    leaderboard_text = ""
    for index, (user_id, stats) in enumerate(sorted_players, start=1):
        member = ctx.guild.get_member(int(user_id))
        name = member.display_name if member else f"مستخدم غادر ({user_id})"
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"#{index}"
        leaderboard_text += f"{medal} **{name}** — `{stats['points']}` نقطة ({stats['wins']} فوز)\n"

    embed = discord.Embed(title="🏆 قائمة متصدري السيرفر (Top 10)", description=leaderboard_text, color=discord.Color.gold())
    await ctx.send(embed=embed)


# ----------------- [ RUNTIME CONFIG ] -----------------
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise RuntimeError("Set the DISCORD_TOKEN environment variable before starting the bot.")

    print("Starting Night Games bot...")
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Bot failed to start: {e}")
        raise
