/*!
 * GodSeal AI 操作面板（免建置，可直接嵌入任何 HTML 網站）
 * 用法：
 *   <div id="godseal-ai"></div>
 *   <script src="godseal-ai-widget.js" defer></script>
 * 可用 data-api 指定後端網址：<div id="godseal-ai" data-api="https://..."></div>
 */
(function () {
  "use strict";
  var IMG_BASE = "https://kycat2026-ui.github.io/kysemantic-vac/godseal/img/godseal_";
  var DEFAULT_API = "https://lsxpcvaitgtskyogligj.supabase.co/functions/v1/godseal-api";
  var SUPABASE_URL = "https://lsxpcvaitgtskyogligj.supabase.co";
  var SUPABASE_PUBLIC_KEY = "sb_publishable__Rxiox30Ka1KDigkTjmrgw_tNau3lRK";

  var CSS = [
    ".gs-ai{--gs-bg:#0e0b09;--gs-card:#16110d;--gs-gold:#c4a062;--gs-text:#eadfca;--gs-dim:#a08d70;",
    "font-family:'Noto Serif TC','PingFang TC',serif;background:var(--gs-bg);color:var(--gs-text);",
    "border:1px solid #3a3020;border-radius:14px;padding:20px;max-width:760px;margin:24px auto;line-height:1.6}",
    ".gs-ai h2{margin:0 0 4px;color:var(--gs-gold);letter-spacing:.12em;font-size:1.4rem}",
    ".gs-ai .gs-sub{color:var(--gs-dim);font-size:.9rem;margin:0 0 14px}",
    ".gs-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:14px}",
    ".gs-sig{background:var(--gs-card);border:1px solid #2a2433;border-radius:8px;padding:6px;text-align:center;font-size:.78rem;transition:.3s}",
    ".gs-sig b{display:block;color:var(--gs-text);font-size:.9rem}",
    ".gs-sig img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:6px;display:block;margin-bottom:4px}",
    ".gs-sig.off{opacity:.35}",
    ".gs-sig.on{border-color:var(--gs-gold);box-shadow:0 0 14px rgba(216,180,90,.55);transform:translateY(-2px)}",
    ".gs-auth{margin:12px 0;padding:12px;background:var(--gs-card);border:1px solid #3a3020;border-radius:8}",
    ".gs-auth input{box-sizing:border-box;width:100%;margin:4px 0;padding:9px;background:#0e0b09;color:var(--gs-text);border:1px solid #3a3020;border-radius:6px;font:inherit}",
    ".gs-auth-status{font-size:.82rem;color:var(--gs-dim);margin-bottom:6px}",
    ".gs-ai textarea{width:100%;box-sizing:border-box;min-height:80px;background:var(--gs-card);color:var(--gs-text);",
    "border:1px solid #3a3020;border-radius:8px;padding:10px;font:inherit;resize:vertical}",
    ".gs-ai button{margin-top:10px;background:var(--gs-gold);color:#1a1408;border:0;border-radius:8px;padding:10px 18px;",
    "font:inherit;font-weight:700;cursor:pointer}",
    ".gs-ai button:disabled{opacity:.5;cursor:default}",
    ".gs-ai button.gs-ghost{background:transparent;color:var(--gs-gold);border:1px solid var(--gs-gold);margin-left:8px}",
    ".gs-out{margin-top:16px;background:var(--gs-card);border-radius:10px;padding:14px;display:none}",
    ".gs-seq{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:6px 0 10px}",
    ".gs-seq span{border:1px solid var(--gs-gold);border-radius:20px;padding:2px 10px;font-size:.85rem}",
    ".gs-tag{display:inline-block;font-size:.75rem;border-radius:4px;padding:1px 8px;margin-left:6px}",
    ".gs-tag.experimental{background:#4a3a12;color:#f3d48a}.gs-tag.verified{background:#123a22;color:#8af3b0}",
    ".gs-tag.invalid{background:#4a1212;color:#f38a8a}",
    ".gs-inc{font-size:1.1rem;color:var(--gs-gold);margin:4px 0}",
    ".gs-warn{color:var(--gs-dim);font-size:.8rem;margin-top:8px}",
    ".gs-err{color:#f38a8a;margin-top:10px}",
  ].join("");

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function mount(root) {
    var api = (root.getAttribute("data-api") || DEFAULT_API).replace(/\/$/, "");
    var sigils = [];
    var last = null;
    var authClient = window.supabase && window.supabase.createClient
      ? window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLIC_KEY)
      : null;
    var currentSession = null;

    root.innerHTML = "";
    var box = el("section", "gs-ai");
    box.appendChild(el("h2", null, "GodSeal AI"));
    box.appendChild(el("p", "gs-sub", "輸入你想創造的符印效果，AI 會從 16 枚符印中選擇並排列。"));
    var authBox = el("div", "gs-auth");
    var authStatus = el("div", "gs-auth-status", authClient ? "保存作品需要登入。" : "登入元件載入失敗，請重新整理頁面。");
    var email = el("input"); email.type = "email"; email.placeholder = "電子郵件"; email.autocomplete = "email";
    var password = el("input"); password.type = "password"; password.placeholder = "密碼（至少 6 位）"; password.autocomplete = "current-password";
    var signIn = el("button", null, "登入"); signIn.type = "button";
    var signUp = el("button", "gs-ghost", "建立帳號"); signUp.type = "button";
    var signOut = el("button", "gs-ghost", "登出"); signOut.type = "button"; signOut.style.display = "none";
    authBox.appendChild(authStatus); authBox.appendChild(email); authBox.appendChild(password);
    authBox.appendChild(signIn); authBox.appendChild(signUp); authBox.appendChild(signOut);
    box.appendChild(authBox);
    var grid = el("div", "gs-grid");
    box.appendChild(grid);
    var ta = el("textarea");
    ta.placeholder = "例如：建立光明守護結界";
    ta.maxLength = 2000;
    box.appendChild(ta);
    var go = el("button", null, "啟動 AI");
    var save = el("button", "gs-ghost", "保存作品");
    save.style.display = "none";
    box.appendChild(go);
    box.appendChild(save);
    var err = el("div", "gs-err");
    box.appendChild(err);

    function updateAuth(session) {
      currentSession = session || null;
      var loggedIn = !!(currentSession && currentSession.access_token);
      authStatus.textContent = loggedIn ? "已登入：" + (currentSession.user.email || "帳戶") + "。可保存私人作品。" : "尚未登入。保存作品前請先登入或建立帳號。";
      email.style.display = loggedIn ? "none" : "";
      password.style.display = loggedIn ? "none" : "";
      signIn.style.display = loggedIn ? "none" : "";
      signUp.style.display = loggedIn ? "none" : "";
      signOut.style.display = loggedIn ? "" : "none";
      save.disabled = !loggedIn;
    }
    if (authClient) {
      authClient.auth.getSession().then(function (r) { updateAuth(r.data.session); });
      authClient.auth.onAuthStateChange(function (_event, session) { updateAuth(session); });
      signIn.addEventListener("click", async function () {
        err.textContent = "";
        var r = await authClient.auth.signInWithPassword({ email: email.value.trim(), password: password.value });
        if (r.error) err.textContent = r.error.message;
      });
      signUp.addEventListener("click", async function () {
        err.textContent = "";
        var r = await authClient.auth.signUp({ email: email.value.trim(), password: password.value });
        if (r.error) err.textContent = r.error.message;
        else if (!r.data.session) authStatus.textContent = "帳號已建立，請先到電子郵件收取驗證連結，再回來登入。";
      });
      signOut.addEventListener("click", async function () {
        var r = await authClient.auth.signOut();
        if (r.error) err.textContent = r.error.message;
      });
    }
    var out = el("div", "gs-out");
    box.appendChild(out);
    root.appendChild(box);

    function renderGrid(activeIds) {
      grid.innerHTML = "";
      sigils.forEach(function (s) {
        var placeholder = s.name.indexOf("待匯入") === 0;
        var c = el("div", "gs-sig" + (placeholder ? " off" : "") +
          (activeIds && activeIds.indexOf(s.id) >= 0 ? " on" : ""));
        if (!placeholder) {
          var im = document.createElement("img");
          im.src = s.image_url || IMG_BASE + (s.id < 10 ? "0" : "") + s.id + ".webp"; im.alt = s.name; im.loading = "lazy";
          c.appendChild(im);
        }
        c.appendChild(el("b", null, placeholder ? "#" + s.id : s.name));
        c.appendChild(document.createTextNode(placeholder ? "待匯入" : s.chinese_name));
        grid.appendChild(c);
      });
    }

    fetch(api + "/sigils").then(function (r) { return r.json(); }).then(function (d) {
      sigils = d.sigils || [];
      renderGrid([]);
    }).catch(function () { err.textContent = "無法載入符印資料。"; });

    go.addEventListener("click", function () {
      var prompt = ta.value.trim();
      if (!prompt) return;
      go.disabled = true; go.textContent = "AI 分析中…";
      err.textContent = ""; save.style.display = "none";
      fetch(api + "/interpret", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt }),
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (!d.success) throw new Error(d.error || "AI 處理失敗");
        last = { prompt: prompt, data: d };
        showResult(d);
      }).catch(function (e) {
        err.textContent = e.message || "GodSeal AI 暫時無法連線。";
      }).finally(function () {
        go.disabled = false; go.textContent = "啟動 AI";
      });
    });

    function showResult(d) {
      var seq = d.sequence, plan = d.plan;
      out.innerHTML = "";
      var h = el("div", null, "符印序列");
      h.appendChild(el("span", "gs-tag " + seq.status,
        { verified: "官方核准", experimental: "實驗性", invalid: "無效" }[seq.status]));
      out.appendChild(h);
      var row = el("div", "gs-seq");
      seq.sigils.forEach(function (s, i) {
        if (i) row.appendChild(document.createTextNode("→"));
        row.appendChild(el("span", null, s.name + "・" + s.chinese_name));
      });
      out.appendChild(row);
      if (plan.incantation) out.appendChild(el("div", "gs-inc", plan.incantation));
      if (plan.translation) out.appendChild(el("div", null, plan.translation));
      if (plan.narrative) out.appendChild(el("p", null, plan.narrative));
      if (seq.warnings && seq.warnings.length) out.appendChild(el("div", "gs-warn", "※ " + seq.warnings.join("；")));
      out.appendChild(el("div", "gs-warn", "模型：" + d.provider + " / " + d.model));
      out.style.display = "block";
      // 依序點亮符印
      var lit = [];
      seq.sigil_ids.forEach(function (id, i) {
        setTimeout(function () { lit.push(id); renderGrid(lit); }, 350 * (i + 1));
      });
      if (seq.status !== "invalid") save.style.display = "inline-block";
    }

    save.addEventListener("click", async function () {
      if (!last) return;
      var p = last.data.plan;
      var sessionResult = authClient ? await authClient.auth.getSession() : null;
      var session = sessionResult && sessionResult.data.session;
      if (!session || !session.access_token) {
        err.textContent = "請先登入，作品才會以私人方式保存。";
        updateAuth(null);
        return;
      }
      save.disabled = true;
      fetch(api + "/creations", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + session.access_token },
        body: JSON.stringify({
          prompt: last.prompt, sigil_ids: last.data.sequence.sigil_ids,
          incantation: p.incantation, translation: p.translation, narrative: p.narrative,
          provider: last.data.provider, model: last.data.model,
        }),
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (!d.success) throw new Error(d.error || "保存失敗");
        save.textContent = "已保存 ✓";
        save.disabled = false;
      }).catch(function (e) {
        err.textContent = e.message; save.disabled = false;
      });
    });
  }

  function init() {
    if (!document.getElementById("gs-ai-style")) {
      var st = document.createElement("style");
      st.id = "gs-ai-style"; st.textContent = CSS;
      document.head.appendChild(st);
    }
    var roots = document.querySelectorAll("#godseal-ai,[data-godseal-ai]");
    Array.prototype.forEach.call(roots, mount);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
