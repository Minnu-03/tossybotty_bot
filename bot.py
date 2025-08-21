import os
import uuid
import random
import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, User
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    InlineQueryHandler
)
from telegram.error import Conflict
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import json
import requests
from groq import Groq # Import the Groq library

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This token should be kept confidential.
TOKEN = "8260847467:AAHxVuDpo2AoqtWcgYlIWlTQ9loKzylWcE8"

# Initialize Groq client
try:
    groq_client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    AI_ENABLED = True
    logger.info("Groq client initialized successfully.")
except Exception as e:
    logger.warning(f"Failed to initialize Groq client: {e}")
    AI_ENABLED = False

# Savage coin flip responses (fallback)
coin_responses = [
    "Heads? The closest you'll come to a brainstorm is a light drizzle 💀",
    "Tails! I'm just impressed you can operate a phone honestly 😭",
    "Heads... you're like a participation trophy, everyone gets one but nobody wants it 🤡",
    "Tails! Plot twist: you were gonna ignore the result anyway 🙄",
    "Heads? A glowstick has a brighter future than you ☠️",
    "Tails! This is what rock bottom looks like, asking bots for guidance 📉",
    "Heads... if you need a coin to decide, the answer is always therapy 💊",
    "Tails! Your ancestors fought wars and you cant pick what to eat? 🗿",
    "Heads? Hold still, I'm trying to imagine you with a personality 🤖",
    "Tails! You're proof that evolution can go in reverse 🐵"
]

# 8-Ball responses (even more savage) - fallback
magic8_responses = [
    "Yes... but your judgment is still worse than a broken GPS 🎱",
    "No... and honestly neither should half your life choices 💀",
    "Maybe... if you had more than two brain cells to work with 🧠",
    "Absolutely not... what kind of question was that seriously? 🤦‍♂️",
    "Signs point to yes... signs also point to you needing adult supervision 🔍",
    "Reply hazy... just like your understanding of common sense 🌫️",
    "Don't count on it... just like everyone stopped counting on you 📉",
    "It is certain... that you'll find a way to mess this up anyway 💯",
    "Ask again later... when you learn how to form intelligent questions 🔄",
    "Better not tell you now... you'd probably cry about it 😭"
]

# Roast responses for random messages (fallback)
roast_responses = [
    "Did you just send me a random message? The audacity is unreal 💀",
    "I'm a coin flip bot not your therapist, try /toss instead 🤖",
    "Bro really thought I'd respond to that nonsense with kindness 🙄",
    "This isn't a chat room, it's a roasting chamber. /toss or leave 🔥",
    "I don't speak broke, try a proper command 💸",
    "Your message makes less sense than pineapple on pizza 🍕",
    "Hold still, I'm trying to imagine you with a personality 🎭",
    "I gave out all my trophies a while ago but here's a participation award 🏆",
    "The closest you'll come to a brainstorm is a light drizzle ☔",
    "I don't want to rain on your parade, I want a typhoon 🌪️"
]

# Brutal roasts for the /roast command (fallback)
brutal_roasts = [
    "You asked to be roasted? The mirror already does that daily 💀",
    "I'd roast you but you're already burnt from life's disappointments 🔥",
    "You're like a participation trophy, everyone gets one but nobody wants it 🏆",
    "If stupidity was a superpower, you'd be the entire Justice League 🦸‍♂️",
    "I get so emotional when you're not around. The emotion is happiness by the way 😊",
    "I'm not arguing, I'm just explaining why I'm right in a way you can understand 🧠",
    "The jerk store called, they ran out of you 📞",
    "Yes I talk like an idiot, how else would you understand me? 🤡",
    "When God made you, you must have been at the bottom of his to-do list 📝",
    "A glowstick has a brighter future than you and lasts longer too 💡",
    "You can be anything you want, except good looking 🪞",
    "Taking a picture of you would put a virus on my phone 📱",
    "I know I make stupid choices but you're the worst of all my choices 💔",
    "You're the reason the divorce rate is so high 💍",
    "Are you at a loss for words or did you exhaust your entire vocabulary? 📚"
]

# AI Helper Functions
async def generate_ai_response(prompt, response_type="general", fallback_list=None):
    """Generate AI response with fallback to random responses using Groq."""
    if not AI_ENABLED:
        return random.choice(fallback_list) if fallback_list else "AI is currently unavailable, using my backup sass 🤖"
    
    try:
        # Craft prompts based on response type
        if response_type == "coin_flip":
            ai_prompt = f"""You are a savage, sarcastic Telegram bot. A user just got {prompt} on a coin flip. 
            Respond with maximum attitude and sass. Be brutally funny but not offensive. 
            Keep it under 100 characters. Include relevant emojis. Make it sound like you're roasting them for needing a coin flip to make decisions.
            Examples: "Heads? The closest you'll come to a brainstorm is a light drizzle 💀", "Tails! Plot twist: you were gonna ignore the result anyway 🙄" """
            
        elif response_type == "magic_8ball":
            ai_prompt = f"""You are a savage, sarcastic magic 8-ball bot. The user asked: "{prompt}"
            Give a typical magic 8-ball answer (yes/no/maybe/unclear) but with maximum sass and attitude. 
            Be brutally funny but not offensive. Keep it under 120 characters. Include emojis.
            Examples: "Yes... but your judgment is still worse than a broken GPS 🎱", "Maybe... if you had more than two brain cells to work with 🧠" """
            
        elif response_type == "roast":
            ai_prompt = f"""You are a savage roast bot. The user asked to be roasted. 
            Generate an absolutely brutal but funny roast. Be creative and savage but not offensive or mean-spirited. 
            Keep it under 150 characters. Include fire emojis and skull emojis.
            Make it about their life choices, decision-making skills, or general existence."""
            
        elif response_type == "random_message":
            ai_prompt = f"""You are a savage Telegram bot. A user sent you a random message: "{prompt}"
            Respond with maximum sass for them sending random text instead of using proper commands.
            Be brutally funny but not offensive. Keep it under 100 characters. Include relevant emojis.
            Tell them to use proper commands like /toss or get roasted."""
        
        elif response_type == "creativity_rating":
             ai_prompt = f"Rate the creativity of this roast completion: '{prompt}' Give a savage rating."
             
        elif response_type == "regret_scenario":
            ai_prompt = f"Generate a regret scenario for this decision: '{prompt}'. Show how it could have gone better if they chose differently."

        elif response_type == "confession_judgment":
            ai_prompt = f"Rate the stupidity level (1-10) of this confession and give a savage judgment: '{prompt}'"

        else:
            ai_prompt = prompt

        # Generate response using Groq client
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": ai_prompt,
                }
            ],
            model="llama-3.1-8b-instant", # You can change this to another Groq model
        )
        ai_text = chat_completion.choices[0].message.content.strip()
        
        # Ensure response isn't too long
        if len(ai_text) > 200:
            ai_text = ai_text[:197] + "..."
            
        return ai_text
        
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        # Fallback to random response
        return random.choice(fallback_list) if fallback_list else "My AI brain is taking a coffee break, here's my backup sass 🤖"
    
# --- In-memory data stores ---
# User stats storage
user_stats = {}
# Stores the last command timestamp for rate limiting
command_timestamps = defaultdict(list)
# Stores active roast battles in each chat
roast_battles = {}
# Admins list - replace with your actual user IDs
ADMINS = [
    123456789
]

# --- Bot's Command Rate Limiter ---
RATE_LIMIT_PER_MINUTE = 30


def is_rate_limited(user_id):
    """
    Checks if a user is exceeding the command rate limit.
    """
    now = datetime.now()
    # Remove timestamps older than 1 minute
    command_timestamps[user_id] = [
        t for t in command_timestamps[user_id] if (now - t) < timedelta(minutes=1)
    ]
    # Add new timestamp
    command_timestamps[user_id].append(now)
    return len(command_timestamps[user_id]) > RATE_LIMIT_PER_MINUTE


def get_user_stats(user_id):
    """
    Retrieves or initializes user stats.
    """
    if user_id not in user_stats:
        user_stats[user_id] = {
            'tosses': 0, 'heads': 0, 'tails': 0,
            'questions': 0, 'roasts_received': 0,
            'predictions': 0, 'dice_rolls': 0,
            'first_seen': datetime.now().strftime('%Y-%m-%d'),
            'last_seen': datetime.now().strftime('%Y-%m-%d'),
            'current_streak': 0, 'best_streak': 0,
            'challenge_active': None, 'challenge_progress': 0,
            'challenge_start': None, 'daily_usage_count': 0,
            'consecutive_heads': 0, 'consecutive_dice_sixes': 0,
            'mood_guesses': 0, 'mood_correct': 0,
            'roast_completions': 0, 'confessions': 0,
            'regrets_generated': 0
        }
    return user_stats[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🪙 Flip Coin", callback_data='toss'), InlineKeyboardButton("🎱 Magic 8-Ball", callback_data='8ball')],
        [InlineKeyboardButton("📊 My Stats", callback_data='stats'), InlineKeyboardButton("🔥 Roast Me", callback_data='roast')],
        [InlineKeyboardButton("🎯 Daily Challenges", callback_data='challenges'), InlineKeyboardButton("🏆 Leaderboards", callback_data='leaderboard')],
        [InlineKeyboardButton("🎮 Mini Games", callback_data='games'), InlineKeyboardButton("📋 All Commands", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_msg = f"🤖 Welcome to the Savage Bot, {user.first_name}!\n\nI'm here to make decisions for you because clearly you can't and roast you in the process.\n\n🪙 /toss - Flip coins like a pro procrastinator\n🎱 /8ball <question> - Ask me anything (regret guaranteed)\n📊 /stats - See your failure statistics\n📋 /help - Full command list because memory is hard\n\nOr click the buttons below, perfect for the lazy:"

    await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')

async def toss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    user_id = update.effective_user.id
    stats = get_user_stats(user_id)

    result = random.choice(["Heads", "Tails"])
    
    # Generate AI response instead of random
    msg = await generate_ai_response(result, "coin_flip", coin_responses)

    # Update stats
    stats['tosses'] += 1
    stats['heads' if result == "Heads" else 'tails'] += 1
    stats['last_seen'] = datetime.now().strftime('%Y-%m-%d')

    # Check for streaks
    if result == "Heads":
        stats['consecutive_heads'] += 1
        if stats['consecutive_heads'] > stats['best_streak']:
            stats['best_streak'] = stats['consecutive_heads']
    else:
        stats['consecutive_heads'] = 0

    # Check challenge progress
    if stats['challenge_active'] == 'luck_test':
        if stats['consecutive_heads'] >= 5:
            await update.message.reply_text("🎉 CHALLENGE COMPLETE! You actually got 5 heads in a row. I'm genuinely shocked 😱")
            stats['challenge_active'] = None
            stats['challenge_progress'] = 0

    # Add some variety with coin animation
    animation_msg = await update.message.reply_text("🪙 Flipping...")
    await asyncio.sleep(1)
    await animation_msg.edit_text("🔄 Still flipping...")
    await asyncio.sleep(1)
    await animation_msg.edit_text(f"**{result}!** {msg}")

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    user_id = update.effective_user.id
    stats = get_user_stats(user_id)

    dice_result = random.randint(1, 6)
    stats['dice_rolls'] += 1

    # Track consecutive 6s
    if dice_result == 6:
        stats['consecutive_dice_sixes'] += 1
    else:
        stats['consecutive_dice_sixes'] = 0

    # Check challenge progress
    if stats['challenge_active'] == 'dice_luck' and stats['consecutive_dice_sixes'] >= 3:
        await update.message.reply_text("🎉 IMPOSSIBLE! You rolled three 6s in a row. The universe must be broken 🌌")
        stats['challenge_active'] = None
        stats['challenge_progress'] = 0
        return

    # Generate AI response for dice roll
    dice_roasts_fallback = [
        f"🎲 You rolled a {dice_result}! Congrats on your incredible luck, not really",
        f"🎲 {dice_result}! Even random numbers are disappointed in you",
        f"🎲 Got a {dice_result}! Your dice rolling skills match your life choices"
    ]
    
    ai_response = await generate_ai_response(f"The user rolled a {dice_result} on a dice", "general", dice_roasts_fallback)
    await update.message.reply_text(f"🎲 {ai_response}")

async def magic8ball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    stats['questions'] += 1

    if not context.args:
        await update.message.reply_text("Ask me a question, genius! Example: /8ball Should I eat pizza?")
        return

    question = " ".join(context.args)
    
    # Generate AI response instead of random
    answer = await generate_ai_response(question, "magic_8ball", magic8_responses)

    # Judge question quality for challenges
    stupid_questions = ['should i', 'will i', 'am i', 'do i', 'can i']
    if stats['challenge_active'] == 'question_master':
        if any(stupid in question.lower() for stupid in stupid_questions):
            quality_judgment = "Question quality: Absolutely terrible 📉"
        else:
            quality_judgment = "Question quality: Still garbage but slightly creative 🗑️"

        stats['challenge_progress'] += 1
        if stats['challenge_progress'] >= 15:
            await update.message.reply_text(f"🎱 **Question:** {question}\n**Answer:** {answer}\n\n{quality_judgment}\n\n🎉 CHALLENGE COMPLETE! You asked 15 questions. Most were stupid but hey, you tried 🎭")
            stats['challenge_active'] = None
            stats['challenge_progress'] = 0
            return
        else:
            remaining = 15 - stats['challenge_progress']
            await update.message.reply_text(f"🎱 **Question:** {question}\n**Answer:** {answer}\n\n{quality_judgment}\n\n🎯 Challenge Progress: {remaining} more questions to go")
            return

    await update.message.reply_text(f"🎱 **Question:** {question}\n**Answer:** {answer}")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    stats['predictions'] += 1

    if not context.args or "or" not in " ".join(context.args):
        await update.message.reply_text("Use: /predict pizza or burger - Give me options to roast!")
        return

    options_text = " ".join(context.args)
    options = [opt.strip() for opt in options_text.split(" or ")]

    if len(options) != 2:
        await update.message.reply_text("I can only handle 2 options at a time. Unlike you, I have limits 🙄")
        return

    choice = random.choice(options)
    
    # Generate AI response for the prediction
    prediction_prompt = f"I'm choosing {choice} between {options[0]} and {options[1]} for the user"
    ai_response = await generate_ai_response(prediction_prompt, "general", [f"But let's be real, you'll probably ignore this and regret it later 💀"])
    
    await update.message.reply_text(f"🎯 I choose: **{choice}**\n\n{ai_response}")

async def random_picker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    if not context.args:
        await update.message.reply_text("Give me a list! Example: /random pizza burger tacos sushi")
        return

    choices = context.args
    pick = random.choice(choices)
    
    # Generate AI response
    picker_prompt = f"I picked {pick} from the user's list: {', '.join(choices)}"
    ai_response = await generate_ai_response(picker_prompt, "general", ["You're welcome for saving you from decision paralysis 🤡"])
    
    await update.message.reply_text(f"🎪 From your list of questionable choices, I pick: **{pick}**\n\n{ai_response}")


async def roast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an AI-generated roast based on user's input."""
    if not AI_ENABLED:
        await update.message.reply_text("The AI service is currently unavailable. Try again later.")
        return

    user_text = " ".join(context.args)
    if not user_text:
        await update.message.reply_text("Please provide something to roast, e.g., `/roast your fashion sense`")
        return

    full_prompt = (
        f"You are a savage bot with a sarcastic and dark sense of humor. "
        f"Generate a brutal roast for me. The roast should be based on the following text: '{user_text}'. "
        f"The response should be strictly a roast and nothing else."
    )

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            model="llama-3.1-8b-instant",  # You can change this to another Groq model
        )
        text_response = chat_completion.choices[0].message.content
        if not text_response:
            text_response = random.choice(fallbacks["roast"])
    except Exception as e:
        logger.error(f"Error while generating roast with Groq AI: {e}")
        text_response = random.choice(fallbacks["roast"])
        
    await update.message.reply_text(text_response)

    # Update user stats
    user_id = update.effective_user.id
    if user_id in user_stats:
        user_stats[user_id]["roasts_received"] += 1
    else:
        user_stats[user_id] = {"roasts_received": 1}

async def challenges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    user_id = update.effective_user.id
    stats = get_user_stats(user_id)

    if stats['challenge_active']:
        progress_msg = f"You already have a challenge active: **{stats['challenge_active'].replace('_', ' ').title()}**\n\nProgress: {stats['challenge_progress']}/target"
        await update.message.reply_text(progress_msg)
        return

    keyboard = [
        [InlineKeyboardButton("🏃‍♂️ Decision Survivor", callback_data='challenge_survivor')],
        [InlineKeyboardButton("🍀 Luck Test (5 Heads)", callback_data='challenge_luck')],
        [InlineKeyboardButton("🎲 Dice Luck (3 Sixes)", callback_data='challenge_dice')],
        [InlineKeyboardButton("🎱 Question Master", callback_data='challenge_questions')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    challenges_msg = "🎯 **DAILY CHALLENGES** 🎯\n\nPick your poison:\n\n🏃‍♂️ **Decision Survivor** - Make 10 decisions without using me today\n🍀 **Luck Test** - Get 5 heads in a row\n🎲 **Dice Luck** - Roll three 6s in a row\n🎱 **Question Master** - Ask me 15 different questions\n\nWarning: Most people fail miserably 😈"

    await update.message.reply_text(challenges_msg, reply_markup=reply_markup)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    if not user_stats:
        await update.message.reply_text("No data yet! Come back when people have actually used this bot 📊")
        return

    # Calculate shame rankings
    most_indecisive = max(user_stats.items(), key=lambda x: x[1]['tosses'])
    biggest_masochist = max(user_stats.items(), key=lambda x: x[1]['roasts_received'])
    worst_decision_maker = max(user_stats.items(), key=lambda x: x[1]['predictions'])
    longest_streak = max(user_stats.items(), key=lambda x: x[1]['best_streak'])

    leaderboard_msg = f"""🏆 **HALL OF SHAME** 🏆

👑 **Most Indecisive Human**
User {most_indecisive[0]}: {most_indecisive[1]['tosses']} coin flips

🎭 **Biggest Glutton for Punishment**
User {biggest_masochist[0]}: {biggest_masochist[1]['roasts_received']} roasts survived

🤡 **Worst Decision Maker**
User {worst_decision_maker[0]}: {worst_decision_maker[1]['predictions']} decisions outsourced

🔥 **Longest Lucky Streak**
User {longest_streak[0]}: {longest_streak[1]['best_streak']} heads in a row

Remember: These are not achievements to be proud of 💀"""

    await update.message.reply_text(leaderboard_msg)

async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    keyboard = [
        [InlineKeyboardButton("🎭 Guess My Mood", callback_data='game_mood')],
        [InlineKeyboardButton("🔥 Complete the Roast", callback_data='game_roast')],
        [InlineKeyboardButton("😭 Regret Generator", callback_data='game_regret')],
        [InlineKeyboardButton("🙏 Confession Sunday", callback_data='game_confession')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    games_msg = "🎮 **MINI GAMES** 🎮\n\nChoose your method of psychological destruction:\n\n🎭 **Guess My Mood** - Figure out how savage I'm feeling (1-10)\n🔥 **Complete the Roast** - Finish my insults, get rated\n😭 **Regret Generator** - Tell me a decision, watch me destroy your life\n🙏 **Confession Sunday** - Admit your failures, get judged"

    await update.message.reply_text(games_msg, reply_markup=reply_markup)

async def mood_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    current_mood = random.randint(1, 10)
    context.user_data['current_mood'] = current_mood

    mood_clues = [
        "I just saw someone use Internet Explorer voluntarily",
        "Someone asked me if I'm real",
        "A user thanked me for being helpful",
        "I witnessed someone put pineapple on pizza",
        "Someone tried to outsmart me today",
        "I had to explain what a coin flip is",
        "A user actually followed my advice",
        "Someone asked me to solve their relationship problems"
    ]

    clue = random.choice(mood_clues)
    await update.message.reply_text(f"🎭 **GUESS MY MOOD GAME**\n\nClue: {clue}\n\nHow savage am I feeling right now? (Reply with a number 1-10)\n1 = Mildly annoyed\n10 = Absolutely nuclear ☢️")

async def complete_roast_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    roast_starters = [
        "You're so stupid that...",
        "You're so ugly that...",
        "You're so poor that...",
        "You're so lazy that...",
        "You're so unlucky that...",
        "You're so boring that...",
        "You're so bad at decisions that..."
    ]

    starter = random.choice(roast_starters)
    context.user_data['roast_starter'] = starter

    await update.message.reply_text(f"🔥 **COMPLETE THE ROAST GAME**\n\n{starter}\n\nFinish this roast! I'll rate your creativity (spoiler: it'll probably suck) 💀")

async def regret_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    await update.message.reply_text("😭 **REGRET GENERATOR ACTIVATED**\n\nTell me about a decision you made recently. I'll show you how it could've gone worse.\n\nExample: 'I decided to eat pizza for breakfast'\n\nGo ahead, destroy your own peace of mind 🎭")
    context.user_data['waiting_for_regret'] = True

async def confession_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    await update.message.reply_text("🙏 **CONFESSION SUNDAY**\n\nTime to admit your worst life choices. I'll rate the stupidity level from 1-10.\n\nConfess your sins and let me judge you accordingly.\n\nExample: 'I once tried to microwave ice cream to make it softer'\n\nYour turn to disappoint me 😈")
    context.user_data['waiting_for_confession'] = True

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    stats = get_user_stats(user_id)

    total_tosses = stats['tosses']
    win_rate = (stats['heads'] / total_tosses * 100) if total_tosses > 0 else 0

    stats_msg = f"""📊 **{user_name}'s Hall of Shame** 📊

🪙 **Coin Tosses:** {total_tosses}
📈 **Heads:** {stats['heads']} | **Tails:** {stats['tails']}
🎯 **Luck Rate:** {win_rate:.1f}% (still terrible)
🎱 **Questions Asked:** {stats['questions']}
🔥 **Roasts Survived:** {stats['roasts_received']}
🎯 **Decisions Outsourced:** {stats['predictions']}
🎲 **Dice Rolled:** {stats['dice_rolls']}
🏆 **Best Streak:** {stats['best_streak']} heads in a row
📅 **First Disappointment:** {stats['first_seen']}

**Analysis:** You've wasted your time here {total_tosses + stats['questions'] + stats['roasts_received']} times. Impressive dedication to procrastination! 🎭

💡 Forgot commands? Try /help
"""

    await update.message.reply_text(stats_msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    help_msg = """📋 **SAVAGE BOT COMMAND CENTER** 📋

🎮 **GAMES & FUN:**
🪙 /toss - Flip a coin with maximum attitude
🎱 /8ball <question> - Ask the magic 8-ball anything
🎲 /dice - Roll a dice and get roasted
🎯 /predict <option1> or <option2> - Let me choose for you
🎪 /random <item1> <item2> <item3>... - Pick from your list

🔥 **DESTRUCTION MODE:**
🔥 /roast - Get absolutely obliterated
🔥 /roastfriend @user - Tag a friend for me to roast
🔥 /roastbattle @user - Start an insult war!
🤡 /failpredict <decision> - Predict how a decision will backfire
💀 Send random text - Auto-roast for being dumb

🏆 **CHALLENGES & GAMES:**
🎯 /challenges - Daily challenges to fail at
🏆 /leaderboard - See who's the biggest loser
🎮 /games - Mini games for extra suffering

📊 **INFO & STATS:**
📊 /stats - See your pathetic usage statistics
📋 /help - Show this menu because memory equals trash
🏠 /start - Go back to main menu
⚙️ /admin - Admin menu for bot management

💡 **EXAMPLES:**
• /8ball Should I skip work today?
• /predict pizza or salad
• /random netflix youtube tiktok instagram

**PRO TIP:** Too lazy to type? Use /start for clickable buttons! 🤖

Remember: I'm not just a bot, I'm your personal roast master 💀🔥"""

    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def handle_random_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle random text messages with savage responses or game inputs"""
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    message_text = update.message.text
    chat_id = update.effective_chat.id

    # Check if a roast battle is active and it's the user's turn
    if chat_id in roast_battles and roast_battles[chat_id]['turn'] == user_id:
        battle = roast_battles[chat_id]

        if message_text.startswith('/'):
            await update.message.reply_text("It's your turn to roast, not to use a command! 🙄")
            return

        # Record the roast insult
        battle['roasts'].append({'user_id': user_id, 'text': message_text})

        # Determine the next player
        next_player_id = battle['players'][1] if battle['players'][0] == user_id else battle['players'][0]
        battle['turn'] = next_player_id

        # Check if a roast battle has finished
        if len(battle['roasts']) >= 6: # Let's say 3 roasts each
            # Simple "winner" selection (can be improved later)
            winner_id = random.choice(battle['players'])
            winner_username = await context.bot.get_chat_member(chat_id, winner_id)
            await update.message.reply_text(f"🔥 The Roast Battle has ended! And the winner is... @{winner_username.user.username}!\n\nEveryone else, you lose. 🤡")
            del roast_battles[chat_id]
        else:
            try:
                next_player = await context.bot.get_chat_member(chat_id, next_player_id)
                next_player_tag = f"@{next_player.user.username}" if next_player.user.username else next_player.user.full_name
                await update.message.reply_text(f"Alright, good try. It's now {next_player_tag}'s turn to roast!")
            except Exception:
                await update.message.reply_text("Looks like the next player isn't in this chat anymore. Roast Battle ended.")
                del roast_battles[chat_id]
        return

    # Check if it's a mood guess
    if 'current_mood' in context.user_data:
        try:
            guess = int(message_text)
            actual_mood = context.user_data['current_mood']
            stats['mood_guesses'] += 1

            if guess == actual_mood:
                stats['mood_correct'] += 1
                await update.message.reply_text(f"🎉 Holy shit! You actually got it right. My mood was {actual_mood}/10. Beginner's luck I guess 🎭")
            else:
                difference = abs(guess - actual_mood)
                if difference <= 2:
                    await update.message.reply_text(f"Close but no cigar! I was feeling {actual_mood}/10, you guessed {guess}. Almost there, almost 🎯")
                else:
                    await update.message.reply_text(f"Not even close! I was {actual_mood}/10 savage, you guessed {guess}. Your psychic abilities are non-existent 💀")

            del context.user_data['current_mood']
            return
        except ValueError:
            await update.message.reply_text("I asked for a number between 1-10. Reading comprehension isn't your strong suit 📚")
            return

    # Check if it's a roast completion
    if 'roast_starter' in context.user_data:
        completion = update.message.text
        starter = context.user_data['roast_starter']
        stats['roast_completions'] += 1

        # Generate AI response for rating creativity
        rating_prompt = f"Rate the creativity of this roast completion: '{starter} {completion}' Give a savage rating."
        creativity_ratings_fallback = [
            "Creativity Level: Absolutely zero 📉",
            "Creativity Level: My grandmother could do better 👵",
            "Creativity Level: Did you even try? 🤷‍♂️",
            "Creativity Level: Surprisingly not terrible 📈",
            "Creativity Level: Actually decent, I'm shocked 😱"
        ]
        
        rating = await generate_ai_response(rating_prompt, "general", creativity_ratings_fallback)
        await update.message.reply_text(f"🔥 **YOUR ROAST:**\n{starter} {completion}\n\n{rating}\n\nThanks for participating in your own destruction 💀")

        del context.user_data['roast_starter']
        return

    # Check for regret generator input
    if 'waiting_for_regret' in context.user_data:
        decision = update.message.text
        stats['regrets_generated'] += 1

        # Generate AI regret scenario instead of random
        regret_prompt = f"Generate a regret scenario for this decision: '{decision}'. Show how it could have gone better if they chose differently."
        regret_scenarios_fallback = [
            f"What if you hadn't {decision.lower()}? You could've been a millionaire by now 💰",
            f"Imagine if you chose differently. You'd probably be living your best life instead of talking to a bot 🏖️",
            f"That decision to {decision.lower()} probably ruined your entire timeline. Butterfly effect is real 🦋",
            f"Alternative universe you is laughing at this decision while being successful and happy 🌌",
            f"Plot twist: If you hadn't {decision.lower()}, you would've met your soulmate today 💕"
        ]

        regret = await generate_ai_response(regret_prompt, "general", regret_scenarios_fallback)
        await update.message.reply_text(f"😭 **REGRET GENERATOR RESULTS:**\n\n{regret}\n\nFeel better now? Probably not 🎭")

        del context.user_data['waiting_for_regret']
        return

    # Check for confession
    if 'waiting_for_confession' in context.user_data:
        confession = update.message.text
        stats['confessions'] += 1

        # Generate AI judgment instead of random
        judgment_prompt = f"Rate the stupidity level (1-10) of this confession and give a savage judgment: '{confession}'"
        judgments_fallback = [
            f"Stupidity Level: {random.randint(1, 10)}/10. That's impressively dumb 🤡",
            f"Stupidity Level: {random.randint(1, 10)}/10. I've seen worse but this is still bad 📉",
            f"Stupidity Level: {random.randint(1, 10)}/10. Your life choices concern me 😬",
            f"Stupidity Level: {random.randint(1, 10)}/10. Natural selection missed you 🧬"
        ]

        judgment = await generate_ai_response(judgment_prompt, "general", judgments_fallback)
        await update.message.reply_text(f"🙏 **CONFESSION RECEIVED:**\n\n{confession}\n\n**DIVINE JUDGMENT:** {judgment}\n\nYour sins have been noted and mocked 📝")

        del context.user_data['waiting_for_confession']
        return

    # Regular random message roasting with AI
    stats['roasts_received'] += 1
    response = await generate_ai_response(message_text, "random_message", roast_responses)
    await update.message.reply_text(response)

async def toss_callback(query, context):
    user_id = query.from_user.id
    stats = get_user_stats(user_id)

    result = random.choice(["Heads", "Tails"])
    
    # Generate AI response instead of random
    msg = await generate_ai_response(result, "coin_flip", coin_responses)

    # Update stats
    stats['tosses'] += 1
    stats['heads' if result == "Heads" else 'tails'] += 1
    stats['last_seen'] = datetime.now().strftime('%Y-%m-%d')

    # Check for streaks
    if result == "Heads":
        stats['consecutive_heads'] += 1
        if stats['consecutive_heads'] > stats['best_streak']:
            stats['best_streak'] = stats['consecutive_heads']
    else:
        stats['consecutive_heads'] = 0

    await query.edit_message_text(f"**{result}!** {msg}")

async def roast_callback(query, context):
    user_id = query.from_user.id
    stats = get_user_stats(user_id)
    stats['roasts_received'] += 1

    # Generate AI roast instead of random
    roast_msg = await generate_ai_response("Generate a savage roast", "roast", brutal_roasts)
    await query.edit_message_text(f"🔥 **ROAST ACTIVATED** 🔥\n\n{roast_msg}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()

    if is_rate_limited(query.from_user.id):
        await query.edit_message_text("Chill out, you're sending too many commands! ⏳")
        return

    if query.data == 'toss':
        await toss_callback(query, context)
    elif query.data == '8ball':
        await query.edit_message_text("🎱 Use /8ball <your question> to ask me something!")
    elif query.data == 'stats':
        user_id = query.from_user.id
        user_name = query.from_user.first_name
        stats = get_user_stats(user_id)

        total_tosses = stats['tosses']

        stats_msg = f"📊 **{user_name}'s Quick Stats:**\n🪙 Tosses: {total_tosses}\n🔥 Roasts: {stats['roasts_received']}"
        await query.edit_message_text(stats_msg)
    elif query.data == 'roast':
        await roast_callback(query, context)
    elif query.data == 'challenges':
        await challenges_callback(query, context)
    elif query.data == 'leaderboard':
        await leaderboard_callback(query, context)
    elif query.data == 'games':
        await games_callback(query, context)
    elif query.data.startswith('challenge_'):
        await handle_challenge_selection(query, context)
    elif query.data.startswith('game_'):
        await handle_game_selection(query, context)
    elif query.data == 'help':
        help_msg = """📋 **QUICK COMMAND REFERENCE** 📋

🎮 **MAIN COMMANDS:**
• /toss - Savage coin flip
• /8ball <question> - Magic 8-ball
• /dice - Roll dice plus roast
• /predict <A> or <B> - Choose for you
• /random <list> - Pick from options
• /roast - Get destroyed
• /stats - Your shame stats
• /challenges - Daily challenges
• /games - Mini games
• /help - Full command list
• /start - Back to main menu

Type any command or get auto-roasted! 💀"""
        await query.edit_message_text(help_msg)

async def challenges_callback(query, context):
    user_id = query.from_user.id
    stats = get_user_stats(user_id)

    if stats['challenge_active']:
        progress_msg = f"You already have a challenge active: **{stats['challenge_active'].replace('_', ' ').title()}**\n\nProgress: {stats['challenge_progress']}/target"
        await query.edit_message_text(progress_msg)
        return

    challenges_msg = "🎯 **DAILY CHALLENGES** 🎯\n\nPick your poison and prepare to fail:\n\n🏃‍♂️ **Decision Survivor** - Make 10 decisions without using me today\n🍀 **Luck Test** - Get 5 heads in a row\n🎲 **Dice Luck** - Roll three 6s in a row\n🎱 **Question Master** - Ask me 15 different questions\n\nMost people fail miserably 😈"
    await query.edit_message_text(challenges_msg)

async def leaderboard_callback(query, context):
    if not user_stats:
        await query.edit_message_text("No data yet! Come back when people have actually used this bot 📊")
        return

    # Calculate shame rankings (simplified for button)
    most_indecisive = max(user_stats.items(), key=lambda x: x[1]['tosses'])
    biggest_masochist = max(user_stats.items(), key=lambda x: x[1]['roasts_received'])

    leaderboard_msg = f"🏆 **HALL OF SHAME** 🏆\n\n👑 **Most Indecisive Human**\nUser {most_indecisive[0]}: {most_indecisive[1]['tosses']} coin flips\n\n🎭 **Biggest Glutton for Punishment**\nUser {biggest_masochist[0]}: {biggest_masochist[1]['roasts_received']} roasts survived\n\nThese are not achievements to be proud of 💀"

    await query.edit_message_text(leaderboard_msg)

async def games_callback(query, context):
    games_msg = "🎮 **MINI GAMES** 🎮\n\nChoose your method of psychological destruction:\n\n🎭 **Guess My Mood** - Figure out how savage I'm feeling (1-10)\n🔥 **Complete the Roast** - Finish my insults, get rated\n😭 **Regret Generator** - Tell me a decision, watch me destroy your life\n🙏 **Confession Sunday** - Admit your failures, get judged"
    await query.edit_message_text(games_msg)

async def handle_challenge_selection(query, context):
    user_id = query.from_user.id
    stats = get_user_stats(user_id)

    if stats['challenge_active']:
        progress_msg = f"You already have a challenge active: **{stats['challenge_active'].replace('_', ' ').title()}**\n\nProgress: {stats['challenge_progress']}/target"
        await query.edit_message_text(progress_msg)
        return

    if query.data == 'challenge_survivor':
        stats['challenge_active'] = 'decision_survivor'
        stats['challenge_start'] = datetime.now().strftime('%Y-%m-%d')
        stats['challenge_progress'] = 0
        await query.edit_message_text("🏃‍♂️ **DECISION SURVIVOR CHALLENGE ACTIVATED**\n\nYour mission: Make 10 decisions today without using me. I'll be watching... and judging when you inevitably come back 💀")

    elif query.data == 'challenge_luck':
        stats['challenge_active'] = 'luck_test'
        stats['challenge_progress'] = 0
        await query.edit_message_text("🍀 **LUCK TEST CHALLENGE ACTIVATED**\n\nGet 5 heads in a row! Start flipping with /toss. Warning: This might take forever 🪙")

    elif query.data == 'challenge_dice':
        stats['challenge_active'] = 'dice_luck'
        stats['challenge_progress'] = 0
        await query.edit_message_text("🎲 **DICE LUCK CHALLENGE ACTIVATED**\n\nRoll three 6s in a row! Use /dice to start. Prepare for disappointment 🎯")

    elif query.data == 'challenge_questions':
        stats['challenge_active'] = 'question_master'
        stats['challenge_progress'] = 0
        await query.edit_message_text("🎱 **QUESTION MASTER CHALLENGE ACTIVATED**\n\nAsk me 15 different questions using /8ball. I'll judge each one brutally 😈")

async def handle_game_selection(query, context):
    if query.data == 'game_mood':
        await mood_game_callback(query, context)
    elif query.data == 'game_roast':
        await complete_roast_game_callback(query, context)
    elif query.data == 'game_regret':
        await regret_game_callback(query, context)
    elif query.data == 'game_confession':
        await confession_game_callback(query, context)

async def mood_game_callback(query, context):
    current_mood = random.randint(1, 10)
    context.user_data['current_mood'] = current_mood

    mood_clues = [
        "I just saw someone use Internet Explorer voluntarily",
        "Someone asked me if I'm real",
        "A user thanked me for being helpful",
        "I witnessed someone put pineapple on pizza",
        "Someone tried to outsmart me today",
        "I had to explain what a coin flip is",
        "A user actually followed my advice",
        "Someone asked me to solve their relationship problems"
    ]

    clue = random.choice(mood_clues)
    await query.edit_message_text(f"🎭 **GUESS MY MOOD GAME**\n\nClue: {clue}\n\nHow savage am I feeling right now? Reply with a number 1-10\n1 = Mildly annoyed\n10 = Absolutely nuclear ☢️")

async def complete_roast_game_callback(query, context):
    roast_starters = [
        "You're so stupid that...",
        "You're so ugly that...",
        "You're so poor that...",
        "You're so lazy that...",
        "You're so unlucky that...",
        "You're so boring that...",
        "You're so bad at decisions that..."
    ]

    starter = random.choice(roast_starters)
    context.user_data['roast_starter'] = starter

    await query.edit_message_text(f"🔥 **COMPLETE THE ROAST GAME**\n\n{starter}\n\nFinish this roast! I'll rate your creativity (spoiler: it'll probably suck) 💀")

async def regret_game_callback(query, context):
    context.user_data['waiting_for_regret'] = True
    await query.edit_message_text("😭 **REGRET GENERATOR ACTIVATED**\n\nTell me about a decision you made recently. I'll show you how it could've gone worse.\n\nExample: 'I decided to eat pizza for breakfast'\n\nGo ahead, destroy your own peace of mind 🎭")

async def confession_game_callback(query, context):
    context.user_data['waiting_for_confession'] = True
    await query.edit_message_text("🙏 **CONFESSION SUNDAY**\n\nTime to admit your worst life choices. I'll rate the stupidity level from 1-10.\n\nConfess your sins and let me judge you accordingly.\n\nExample: 'I once tried to microwave ice cream to make it softer'\n\nYour turn to disappoint me 😈")

# --- New Features ---
async def roastfriend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Roasts a tagged friend in a chat.
    """
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    if not context.args or not context.args[0].startswith('@'):
        await update.message.reply_text(
            "Who are you trying to roast, a ghost? Tag a friend, genius! Example: `/roastfriend` @john"
        )
        return

    target_user_tag = context.args[0]

    # Generate AI roast for friend instead of random
    friend_roast_prompt = f"Generate a savage roast for {target_user_tag} who was tagged by their friend"
    roasts_fallback = [
        f"Hey {target_user_tag}, I'd roast you, but my code's not designed to handle a personality deficit of your magnitude.",
        f"Just saw {target_user_tag}'s last decision. It explains a lot, honestly. 🤦‍♂️",
        f"I've seen smarter things than {target_user_tag} and they were all lint-covered buttons on the floor.",
        f"{target_user_tag}? More like a participation trophy in the grand race of life.",
    ]
    
    roast_response = await generate_ai_response(friend_roast_prompt, "general", roasts_fallback)
    await update.message.reply_text(roast_response)

async def roastbattle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Starts a Roast Battle between two users in a chat.
    """
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    chat_id = update.effective_chat.id
    player1 = update.effective_user

    if chat_id in roast_battles:
        await update.message.reply_text(
            "There's already a roast battle happening. Don't be a spectator, join in! Oh wait, you can't. 💀"
        )
        return

    if not context.args or not context.args[0].startswith('@'):
        await update.message.reply_text(
            "To start a battle, tag your opponent! Example: `/roastbattle` @john"
        )
        return

    try:
        # Get the second user from the context.args and the chat members
        opponent_username = context.args[0].lstrip('@')
        opponent_chat_member = await context.bot.get_chat_member(chat_id, user_id=opponent_username)
        opponent_user = opponent_chat_member.user
    except Exception:
        await update.message.reply_text(
            "I can't find that user. Are you sure they exist? Or maybe they're just too insignificant to find."
        )
        return

    if opponent_user.id == player1.id:
        await update.message.reply_text("You can't battle yourself. That's called a midlife crisis, not a roast battle.")
        return

    roast_battles[chat_id] = {
        'players': [player1.id, opponent_user.id],
        'usernames': [player1.username, opponent_user.username],
        'turn': player1.id,  # Player 1 starts
        'roasts': []
    }

    await update.message.reply_text(
        f"🔥 **Roast Battle Started:** @{player1.username} vs @{opponent_user.username} 🔥\n\n"
        "Type your best insults! Bot will pick the winner.\n\n"
        f"It's @{player1.username}'s turn to start!"
    )

async def failpredict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Predicts how a user's decision will backfire.
    """
    if is_rate_limited(update.effective_user.id):
        await update.message.reply_text("Chill out, you're sending too many commands! ⏳")
        return

    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    stats['predictions'] += 1

    if not context.args:
        await update.message.reply_text(
            "Tell me about a decision you're making, and I'll predict its spectacular failure! Example: `/failpredict` I'm going to cook dinner tonight"
        )
        return

    decision = " ".join(context.args)

    # Generate AI failure prediction instead of random
    fail_prompt = f"Predict how this decision will hilariously backfire: '{decision}'"
    fail_responses_fallback = [
        f"You decided to {decision}? The food will probably come alive and roast you for your lack of culinary skills.",
        f"Predicting your {decision} will lead to a minor disaster... and a major regret.",
        f"Hmm, you're going to {decision}. I see a future where you're talking to me about how badly it went.",
        f"That decision to {decision} has a 99.9% chance of backfiring. The other 0.1% is for an alien invasion that saves you from your failure.",
        f"Your attempt at {decision} will be as successful as a screen door on a submarine. 💀"
    ]

    fail_prediction = await generate_ai_response(fail_prompt, "general", fail_responses_fallback)
    
    await update.message.reply_text(
        f"🔮 **PREDICTION OF FAILURE:** 🔮\n\n"
        f"{fail_prediction}"
    )

async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Provides admin commands.
    """
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("You are not authorized to use this command. 🤨")
        return

    admin_msg = (
        "⚙️ **ADMIN COMMANDS** ⚙️\n\n"
        "`/getstats` - Get a JSON dump of all user stats.\n"
        "`/cleardata` - Clear all in-memory data (use with caution!)."
    )

    await update.message.reply_text(admin_msg)


async def get_stats_dump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dumps all in-memory user stats as a JSON file for admins.
    """
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("You are not authorized to use this command. 🤨")
        return

    # Convert the dict to a formatted JSON string
    stats_json = json.dumps(user_stats, indent=4)
    await update.message.reply_document(
        document=bytes(stats_json, "utf-8"), filename="savage_bot_stats.json"
    )
    await update.message.reply_text("User stats data dumped to JSON file.")


async def clear_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clears all in-memory data for admins.
    """
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("You are not authorized to use this command. 🤨")
        return

    user_stats.clear()
    command_timestamps.clear()
    roast_battles.clear()

    await update.message.reply_text("All bot data has been cleared. Start over and try not to break me this time.")


# --- Inline Mode Handler ---
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query or ""
    results = []

    # Get a roast
    if "roast" in query.lower() or not query:
        roast_text = await generate_ai_response("Generate a savage roast", "roast", brutal_roasts)
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🔥 Get a Roast",
                input_message_content=InputTextMessageContent(
                    f"🔥 **ROAST ACTIVATED** 🔥\n\n{roast_text}"
                ),
            )
        )

    # Flip a coin
    if "toss" in query.lower() or not query:
        result = random.choice(["Heads", "Tails"])
        response_msg = await generate_ai_response(result, "coin_flip", coin_responses)
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🪙 Flip a Coin",
                input_message_content=InputTextMessageContent(
                    f"**{result}!** {response_msg}"
                ),
            )
        )

    # Magic 8-Ball
    if "8ball" in query.lower():
        question = query.replace("8ball", "", 1).strip()
        answer = await generate_ai_response(question, "magic_8ball", magic8_responses)
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"🎱 Ask the 8-Ball: '{question}'",
                input_message_content=InputTextMessageContent(
                    f"🎱 **Question:** {question}\n**Answer:** {answer}"
                ),
            )
        )

    await update.inline_query.answer(results)

def main():
    """
    Main function to set up and run the bot.
    """
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("toss", toss))
    application.add_handler(CommandHandler("dice", dice))
    application.add_handler(CommandHandler("8ball", magic8ball))
    application.add_handler(CommandHandler("predict", predict))
    application.add_handler(CommandHandler("random", random_picker))
    application.add_handler(CommandHandler("roast", roast))
    application.add_handler(CommandHandler("challenges", challenges))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("roastfriend", roastfriend))
    application.add_handler(CommandHandler("roastbattle", roastbattle))
    application.add_handler(CommandHandler("failpredict", failpredict))
    application.add_handler(CommandHandler("admin", admin_commands))
    application.add_handler(CommandHandler("getstats", get_stats_dump))
    application.add_handler(CommandHandler("cleardata", clear_data))
    application.add_handler(CommandHandler("games", games_menu))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(InlineQueryHandler(inline_query_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_random_message))
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except Conflict as e:
        print(f"Conflict error: {e}. Another instance of the bot is likely running.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
