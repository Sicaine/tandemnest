/* Progressive enhancement only. Every page is complete and readable without
   this file: it adds clipboard buttons and live calculator results to markup
   that already works. No analytics, no network requests, no cookies. */
(function () {
  "use strict";

  // These forms exist for their inputs, not to be submitted. Without this,
  // Enter in a single-input form reloads the page and discards the result.
  document.querySelectorAll("form.tool").forEach(function (form) {
    form.addEventListener("submit", function (event) { event.preventDefault(); });
  });

  document.querySelectorAll("[data-copy-target]").forEach(function (button) {
    button.hidden = !navigator.clipboard;
    button.addEventListener("click", function () {
      var field = document.getElementById(button.getAttribute("data-copy-target"));
      if (!field) return;
      navigator.clipboard.writeText(field.value).then(function () {
        var original = button.textContent;
        button.textContent = "Copied";
        setTimeout(function () { button.textContent = original; }, 1600);
      }).catch(function () {
        field.select();
      });
    });
  });

  function num(el) { var v = parseFloat(el && el.value); return isFinite(v) ? v : 0; }

  function money(v) {
    if (!isFinite(v)) return "\u2014";
    if (Math.abs(v) >= 1000) return "$" + v.toLocaleString(undefined, { maximumFractionDigits: 0 });
    if (Math.abs(v) >= 1) return "$" + v.toFixed(2);
    return "$" + v.toFixed(4);
  }

  var HOURS_PER_MONTH = 730;

  /* Two billing models, because they answer different questions.
     per-second : you rent only while the GPU is generating. Total cost is
                  linear in volume, so there is no break-even volume at all --
                  whichever side has the lower per-token rate wins everywhere.
     always-on  : you keep an endpoint up 730 h/month regardless of traffic.
                  Cost is fixed, so a genuine break-even volume exists. */
  function initBreakeven(root) {
    var ids = ["tokens", "outShare", "gpuPrice", "gpuCount", "tps", "util",
               "apiIn", "apiOut", "mode"];
    var f = {};
    ids.forEach(function (k) { f[k] = root.querySelector("#f-" + k); });
    var outIds = ["selfCost", "apiCost", "selfPerM", "apiPerM", "breakeven",
                  "hours", "capacity", "verdict"];
    var o = {};
    outIds.forEach(function (k) { o[k] = root.querySelector("#o-" + k); });

    function recompute() {
      var tokensM   = Math.max(0, num(f.tokens));
      var outShare  = Math.min(Math.max(num(f.outShare), 0), 100) / 100;
      var gpus      = Math.max(1, Math.round(num(f.gpuCount)) || 1);
      var gpuHourly = Math.max(0, num(f.gpuPrice)) * gpus;
      var tps       = Math.max(0, num(f.tps)) * gpus;
      var util      = Math.min(Math.max(num(f.util), 1), 100) / 100;
      var apiIn     = Math.max(0, num(f.apiIn));
      var apiOut    = Math.max(0, num(f.apiOut));
      var alwaysOn  = f.mode && f.mode.value === "always-on";

      /* Blended API rate for the stated input/output mix. */
      var apiPerM = outShare * apiOut + (1 - outShare) * apiIn;
      var apiCost = tokensM * apiPerM;

      /* Effective generation rate after utilisation losses. */
      var effectiveTps = tps * util;
      var monthlyCapacityM = effectiveTps * 3600 * HOURS_PER_MONTH / 1e6;

      /* Self-hosted cost per million tokens is set by rate, not by volume. */
      var selfPerM = effectiveTps > 0
        ? (gpuHourly / 3600) * (1e6 / effectiveTps)
        : Infinity;

      var hoursNeeded = effectiveTps > 0 ? (tokensM * 1e6) / effectiveTps / 3600 : Infinity;
      var selfCost, breakevenText;

      if (alwaysOn) {
        selfCost = gpuHourly * HOURS_PER_MONTH;
        var breakevenM = apiPerM > 0 ? selfCost / apiPerM : Infinity;
        breakevenText = isFinite(breakevenM)
          ? breakevenM.toLocaleString(undefined, { maximumFractionDigits: 1 }) + " M tokens/month"
          : "\u2014";
      } else {
        selfCost = isFinite(selfPerM) ? selfPerM * tokensM : Infinity;
        breakevenText = selfPerM < apiPerM
          ? "no crossover: renting wins at every volume"
          : "no crossover: the API wins at every volume";
      }

      /* Report the EFFECTIVE cost per million, not the marginal rate. Under
         always-on billing you pay a fixed monthly sum, so dividing by actual
         volume is what the reader is comparing against the API's rate. In
         per-second mode the two are identical. */
      var selfEffectivePerM = tokensM > 0 ? selfCost / tokensM : selfPerM;

      o.selfCost.textContent = money(selfCost);
      o.apiCost.textContent  = money(apiCost);
      o.selfPerM.textContent = money(selfEffectivePerM);
      o.apiPerM.textContent  = money(apiPerM);
      o.hours.textContent    = isFinite(hoursNeeded)
        ? hoursNeeded.toLocaleString(undefined, { maximumFractionDigits: 0 }) + " GPU-hours"
        : "\u2014";
      o.breakeven.textContent = breakevenText;

      /* Capacity reality check: can this hardware even serve the volume? */
      if (!isFinite(monthlyCapacityM) || monthlyCapacityM <= 0) {
        o.capacity.textContent = "Enter a throughput figure to check capacity.";
      } else if (tokensM > monthlyCapacityM) {
        o.capacity.textContent = "Not enough capacity: " + gpus + " GPU(s) at this throughput can serve about "
          + monthlyCapacityM.toLocaleString(undefined, { maximumFractionDigits: 1 })
          + " M tokens/month. Add GPUs or raise throughput.";
      } else if (alwaysOn) {
        o.capacity.textContent = "Capacity headroom: using "
          + (monthlyCapacityM > 0 ? (100 * tokensM / monthlyCapacityM).toFixed(1) : "0")
          + "% of what these GPUs could generate if kept busy.";
      } else {
        o.capacity.textContent = "Capacity is sufficient: about "
          + monthlyCapacityM.toLocaleString(undefined, { maximumFractionDigits: 1 })
          + " M tokens/month available.";
      }

      if (tokensM <= 0) {
        o.verdict.textContent = "Enter a monthly token volume to compare the two options.";
        return;
      }
      if (!isFinite(selfCost)) {
        o.verdict.textContent = "Enter a throughput in tokens per second to model self-hosting.";
        return;
      }
      var cheaper = selfCost < apiCost ? "Renting the GPU" : "The hosted API";
      var diff = Math.abs(apiCost - selfCost);
      var pct = Math.max(selfCost, apiCost) > 0
        ? (100 * diff / Math.max(selfCost, apiCost)).toFixed(0) : "0";
      var verdict = cheaper + " is cheaper by " + money(diff)
        + " per month (" + pct + "%), at " + money(selfEffectivePerM) + " vs "
        + money(apiPerM) + " per million tokens.";

      /* A cost advantage you cannot physically deliver is not an advantage.
         Say so rather than letting the headline stand unqualified. */
      if (monthlyCapacityM > 0 && tokensM > monthlyCapacityM && selfCost < apiCost) {
        verdict += " But this hardware cannot actually serve that volume, so the"
          + " comparison is hypothetical until you add GPUs or raise throughput.";
      }
      o.verdict.textContent = verdict;
    }

    root.addEventListener("input", recompute);
    root.addEventListener("change", recompute);
    root.querySelectorAll(".nojs").forEach(function (el) { el.hidden = true; });
    root.querySelectorAll("[data-js-only]").forEach(function (el) { el.hidden = false; });
    recompute();
  }

  // Invoked last: `var` declarations above are hoisted but not yet assigned
  // until execution reaches them, so calling earlier would read undefined.
  var tool = document.getElementById("gpu-vs-api");
  if (tool) initBreakeven(tool);
})();

/* Bitcoin address validation in the browser. Same rules as the build-time
   validator: BIP-173 bech32, BIP-350 bech32m, and Base58Check. Nothing here
   touches the network -- the address never leaves the page. */
(function () {
  "use strict";
  var root = document.getElementById("btc-check");
  if (!root) return;

  var CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l";
  var B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  var GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];
  var BECH32 = 1, BECH32M = 0x2bc830a3;

  function polymod(values) {
    var chk = 1;
    for (var i = 0; i < values.length; i++) {
      var top = chk >>> 25;
      chk = ((chk & 0x1ffffff) << 5) ^ values[i];
      for (var j = 0; j < 5; j++) if ((top >>> j) & 1) chk ^= GEN[j];
    }
    return chk >>> 0;
  }

  function hrpExpand(hrp) {
    var out = [], i;
    for (i = 0; i < hrp.length; i++) out.push(hrp.charCodeAt(i) >>> 5);
    out.push(0);
    for (i = 0; i < hrp.length; i++) out.push(hrp.charCodeAt(i) & 31);
    return out;
  }

  function convertBits(data, from, to, pad) {
    var acc = 0, bits = 0, out = [], maxv = (1 << to) - 1;
    for (var i = 0; i < data.length; i++) {
      acc = (acc << from) | data[i];
      bits += from;
      while (bits >= to) { bits -= to; out.push((acc >>> bits) & maxv); }
    }
    if (pad) { if (bits) out.push((acc << (to - bits)) & maxv); }
    else if (bits >= from || ((acc << (to - bits)) & maxv)) return null;
    return out;
  }

  function checkSegwit(addr) {
    if (addr.length > 90) return { ok: false, why: "Longer than the 90-character bech32 limit." };
    if (addr !== addr.toLowerCase() && addr !== addr.toUpperCase())
      return { ok: false, why: "Mixed upper and lower case. bech32 forbids this." };
    var s = addr.toLowerCase(), pos = s.lastIndexOf("1");
    if (pos < 1 || pos + 7 > s.length) return { ok: false, why: "No valid separator position." };
    var hrp = s.slice(0, pos), dataPart = s.slice(pos + 1), data = [];
    for (var i = 0; i < dataPart.length; i++) {
      var v = CHARSET.indexOf(dataPart[i]);
      if (v < 0) return { ok: false, why: "Character '" + dataPart[i] + "' is not in the bech32 alphabet." };
      data.push(v);
    }
    if (hrp !== "bc")
      return { ok: false, why: "Human-readable part is '" + hrp + "', not 'bc'. This is not a Bitcoin mainnet address." };
    var constant = polymod(hrpExpand(hrp).concat(data));
    var version = data[0];
    if (version > 16) return { ok: false, why: "Witness version " + version + " is out of range." };
    var wanted = version === 0 ? BECH32 : BECH32M;
    if (constant !== wanted) {
      var used = constant === BECH32 ? "bech32" : (constant === BECH32M ? "bech32m" : "neither scheme");
      var need = version === 0 ? "bech32" : "bech32m";
      return {
        ok: false,
        why: constant === BECH32 || constant === BECH32M
          ? "Checksum is valid " + used + ", but witness v" + version + " requires " + need +
            " (BIP-350). This is the Taproot checksum trap."
          : "Checksum does not validate under either bech32 or bech32m. The address is corrupted."
      };
    }
    var program = convertBits(data.slice(1, data.length - 6), 5, 8, false);
    if (program === null) return { ok: false, why: "Witness program has non-zero padding bits." };
    if (program.length < 2 || program.length > 40)
      return { ok: false, why: "Witness program is " + program.length + " bytes; must be 2 to 40." };
    if (version === 0 && program.length !== 20 && program.length !== 32)
      return { ok: false, why: "Witness v0 program must be 20 or 32 bytes, got " + program.length + "." };
    if (version === 1 && program.length !== 32)
      return { ok: false, why: "Taproot (v1) program must be 32 bytes, got " + program.length + "." };
    var kind = version === 0
      ? (program.length === 20 ? "P2WPKH (SegWit v0)" : "P2WSH (SegWit v0)")
      : (version === 1 ? "P2TR (Taproot)" : "SegWit v" + version);
    return {
      ok: true, kind: kind, scheme: version === 0 ? "bech32 (BIP-173)" : "bech32m (BIP-350)",
      bytes: program.length, version: version
    };
  }

  function b58decode(s) {
    var bytes = [0], i, j;
    for (i = 0; i < s.length; i++) {
      var v = B58.indexOf(s[i]);
      if (v < 0) return null;
      for (j = 0; j < bytes.length; j++) bytes[j] *= 58;
      bytes[0] += v;
      var carry = 0;
      for (j = 0; j < bytes.length; j++) {
        bytes[j] += carry; carry = bytes[j] >> 8; bytes[j] &= 0xff;
      }
      while (carry) { bytes.push(carry & 0xff); carry >>= 8; }
    }
    for (i = 0; i < s.length && s[i] === "1"; i++) bytes.push(0);
    return new Uint8Array(bytes.reverse());
  }

  function sha256(bytes) { return crypto.subtle.digest("SHA-256", bytes); }

  function checkBase58(addr) {
    var raw = b58decode(addr);
    if (raw === null) return Promise.resolve({ ok: false, why: "Contains a character outside the Base58 alphabet (0, O, I and l are excluded)." });
    if (raw.length !== 25) return Promise.resolve({ ok: false, why: "Decodes to " + raw.length + " bytes; a Base58Check address must be exactly 25." });
    var payload = raw.slice(0, 21), checksum = raw.slice(21);
    return sha256(payload).then(sha256).then(function (digest) {
      var want = new Uint8Array(digest).slice(0, 4);
      for (var i = 0; i < 4; i++) {
        if (want[i] !== checksum[i]) return { ok: false, why: "Base58Check checksum does not match. The address is mistyped or corrupted." };
      }
      if (payload[0] === 0x00) return { ok: true, kind: "P2PKH (legacy)", scheme: "Base58Check", bytes: 20, version: null };
      if (payload[0] === 0x05) return { ok: true, kind: "P2SH", scheme: "Base58Check", bytes: 20, version: null };
      return { ok: false, why: "Version byte 0x" + payload[0].toString(16) + " is not a Bitcoin mainnet address." };
    });
  }

  function validate(addr) {
    addr = addr.trim();
    if (!addr) return Promise.resolve(null);
    if (/\s/.test(addr)) return Promise.resolve({ ok: false, why: "Contains whitespace." });
    var lower = addr.toLowerCase();
    if (lower.indexOf("tb1") === 0 || lower.indexOf("bcrt1") === 0 || /^[mn2]/.test(addr))
      return Promise.resolve({ ok: false, why: "This looks like a testnet or regtest address, not mainnet." });
    if (lower.indexOf("bc1") === 0) return Promise.resolve(checkSegwit(addr));
    if (addr[0] === "1" || addr[0] === "3") return checkBase58(addr);
    return Promise.resolve({ ok: false, why: "Unrecognised address format. Bitcoin mainnet addresses start with 1, 3 or bc1." });
  }

  var input = root.querySelector("#f-address");
  var out = root.querySelector("#o-result");
  root.querySelectorAll(".nojs").forEach(function (el) { el.hidden = true; });
  root.querySelectorAll("[data-fill]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      input.value = btn.getAttribute("data-fill");
      run();
    });
  });

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function run() {
    var value = input.value;
    validate(value).then(function (result) {
      if (result === null) { out.innerHTML = ""; return; }
      if (result.ok) {
        out.innerHTML = '<p class="verdict">Valid Bitcoin mainnet address.</p>' +
          '<dl class="kv"><dt>Format</dt><dd>' + esc(result.kind) + "</dd>" +
          "<dt>Checksum scheme</dt><dd>" + esc(result.scheme) + "</dd>" +
          (result.version !== null ? "<dt>Witness version</dt><dd>" + esc(result.version) + "</dd>" : "") +
          "<dt>Program length</dt><dd>" + esc(result.bytes) + " bytes</dd></dl>" +
          '<p class="note">A valid checksum means the address is well formed and not mistyped. ' +
          "It does not tell you who controls it. Always confirm the recipient separately.</p>";
      } else {
        out.innerHTML = '<p class="warn"><strong>Not a valid Bitcoin mainnet address.</strong><br>' +
          esc(result.why) + "</p>";
      }
    });
  }

  input.addEventListener("input", run);
})();
