// Validasi sisi klien. Validasi utama tetap di server (WTForms); skrip ini hanya memberi umpan balik lebih cepat.
//
// Kolom WAJIB vs OPSIONAL tidak ditentukan di sini. Sumbernya satu: validator di tapak/forms.py.
// Makro field() menulis atribut `required` HANYA untuk kolom wajib (label diberi *), dan kolom opsional
// diberi label "(opsional)". Skrip ini membaca atribut tersebut, jadi kolom opsional yang kosong selalu lolos.
//
// Yang ditambahkan skrip ini:
//  - pesan galat bahasa Indonesia untuk setiap jenis pelanggaran HTML5;
//  - isian wajib yang hanya berisi spasi dianggap kosong;
//  - grup radio (pilihan ukuran) divalidasi sebagai satu kolom;
//  - aturan antarkolom: kata sandi = ulangi kata sandi, kata sandi memuat huruf dan angka,
//    ukuran terbesar >= ukuran terkecil, harga maks >= harga min, tanggal akhir >= tanggal awal;
//  - konfirmasi sebelum menghapus (form[data-confirm]).
(function () {
  "use strict";

  // Pasangan "kolom akhir harus >= kolom awal": [nama kolom akhir, nama kolom awal, pesan].
  var RANGE_RULES = [
    ["size_max", "size_min", "Ukuran terbesar harus >= ukuran terkecil."],
    ["max_price", "min_price", "Harga maks harus >= harga min."],
    ["date_to", "date_from", "Tanggal akhir harus >= tanggal awal."]
  ];

  function message(el) {
    var v = el.validity;
    if (v.valueMissing) return el.type === "radio" ? (el.dataset.missing || "Pilih salah satu.") : (el.type === "file" ? "Pilih berkas." : "Kolom ini wajib diisi.");
    if (v.badInput) return "Harus berupa angka.";
    if (v.typeMismatch) return el.type === "email" ? "Format email tidak valid." : "Format tidak valid.";
    if (v.tooShort) return "Minimal " + el.getAttribute("minlength") + " karakter.";
    if (v.tooLong) return "Maksimal " + el.getAttribute("maxlength") + " karakter.";
    if (v.patternMismatch) return "Karakter tidak diizinkan.";
    if (v.rangeUnderflow || v.rangeOverflow) {
      if (el.min && el.max) return "Nilai harus " + el.min + " - " + el.max + ".";
      return v.rangeUnderflow ? "Nilai minimal " + el.min + "." : "Nilai maksimal " + el.max + ".";
    }
    if (v.stepMismatch) return "Harus bilangan bulat.";
    return el.validationMessage;
  }

  function sibling(el, name) {
    return el.form ? el.form.querySelector("[name=" + name + "]") : null;
  }

  // Aturan tambahan; mengembalikan pesan galat atau "".
  function customRule(el) {
    if (el.required && el.type !== "radio" && el.type !== "file" && el.type !== "checkbox" && el.value.trim() === "" && el.value !== "") {
      return "Kolom ini wajib diisi.";
    }
    if (el.name === "confirm") {
      var pw = sibling(el, "password");
      if (pw && el.value && el.value !== pw.value) return "Kata sandi tidak sama.";
    }
    if (el.name === "password" && sibling(el, "confirm")) {
      var s = el.value;
      if (s && !(/[A-Za-z]/.test(s) && /\d/.test(s))) return "Harus memuat huruf dan angka.";
    }
    for (var i = 0; i < RANGE_RULES.length; i++) {
      var r = RANGE_RULES[i];
      if (el.name === r[0]) {
        var from = sibling(el, r[1]);
        if (from && el.value !== "" && from.value !== "") {
          var a = el.type === "date" ? el.value : Number(el.value);
          var b = from.type === "date" ? from.value : Number(from.value);
          if (a < b) return r[2];
        }
      }
    }
    return "";
  }

  function holderOf(el) {
    return el.closest(".field") || el.closest("label") || el.parentElement;
  }

  function show(el, text) {
    var holder = holderOf(el);
    if (!holder) return;
    var note = holder.querySelector(".js-err");
    if (!note) {
      note = document.createElement("small");
      note.className = "err js-err";
      note.setAttribute("role", "alert");
      holder.appendChild(note);
    }
    // Hapus pesan server lama untuk kolom ini begitu pengguna memperbaikinya.
    if (!text) holder.querySelectorAll(".err:not(.js-err)").forEach(function (n) { n.remove(); });
    note.textContent = text;
    holder.classList.toggle("has-err", !!text);
  }

  // Validasi satu kolom. Untuk radio, seluruh grup dengan nama yang sama dianggap satu kolom.
  function check(el) {
    if (el.type === "hidden" || el.type === "submit" || el.type === "button" || el.disabled) return true;
    el.setCustomValidity("");
    var extra = el.validity.valid ? customRule(el) : "";
    if (extra) el.setCustomValidity(extra);
    var text = el.validity.valid ? "" : (extra || message(el));
    if (el.type === "radio") {
      el.form.querySelectorAll('input[type=radio][name="' + el.name + '"]').forEach(function (r) {
        if (r !== el) r.setCustomValidity("");
      });
    }
    show(el, text);
    return !text;
  }

  function fieldsOf(form) {
    var seen = {};
    return Array.prototype.filter.call(form.querySelectorAll("input,select,textarea"), function (el) {
      if (el.type !== "radio") return true;
      if (seen[el.name]) return false;
      seen[el.name] = true;
      return true;
    });
  }

  document.querySelectorAll("form[data-validate]").forEach(function (form) {
    form.setAttribute("novalidate", "");
    var onChange = function (e) {
      var el = e.target;
      if (!el.matches("input,select,textarea")) return;
      check(el);
      // Kolom pasangan ikut diperiksa ulang (misalnya ubah ukuran terkecil -> periksa ukuran terbesar).
      RANGE_RULES.forEach(function (r) {
        if (el.name === r[1]) { var to = sibling(el, r[0]); if (to && to.value !== "") check(to); }
      });
      if (el.name === "password") { var c = sibling(el, "confirm"); if (c && c.value) check(c); }
    };
    form.addEventListener("input", onChange);
    form.addEventListener("change", onChange);
    form.addEventListener("submit", function (e) {
      var first = null;
      fieldsOf(form).forEach(function (el) { if (!check(el) && !first) first = el; });
      if (first) {
        e.preventDefault();
        first.focus();
      }
    });
  });

  document.querySelectorAll("form[data-confirm]").forEach(function (f) {
    f.addEventListener("submit", function (e) { if (!window.confirm(f.dataset.confirm)) e.preventDefault(); });
  });
})();
