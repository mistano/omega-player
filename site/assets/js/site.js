/* Omega Player — site vitrine. Aucune bibliotheque, aucun appel reseau.
   Le contenu est lisible sans ce script ; il ajoute le recit au defilement.
   Tout ce qui bouge passe par transform / opacity ou par des classes ; ce qui
   suit le defilement en continu est en CSS (animation-timeline), pas ici. */
(function () {
  "use strict";
  var root = document.documentElement;
  var calme = window.matchMedia("(prefers-reduced-motion: reduce)");
  var reduit = calme.matches;
  function tous(sel, dans) { return Array.prototype.slice.call((dans || document).querySelectorAll(sel)); }

  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* stockage indisponible */ } }

  /* Choix de langue explicite : il gagne sur la detection automatique. */
  document.querySelectorAll("[data-lang]").forEach(function (a) {
    a.addEventListener("click", function () { store("omega-lang", a.getAttribute("data-lang")); });
  });
  var menu = document.querySelector("[data-lang-menu]");
  if (menu) {
    document.addEventListener("click", function (e) { if (menu.open && !menu.contains(e.target)) menu.open = false; });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.open) { menu.open = false; menu.querySelector("summary").focus(); }
    });
  }

  /* Titre du heros : mot par mot quand la langue separe ses mots par des
     espaces, en un seul bloc sinon (japonais, chinois). */
  var titre = document.querySelector("[data-split]");
  if (titre && !reduit && /\s/.test(titre.textContent.trim())) {
    var texte = titre.textContent.trim();
    titre.setAttribute("aria-label", texte);
    titre.textContent = "";
    texte.split(/\s+/).forEach(function (mot, i) {
      var m = document.createElement("span"), w = document.createElement("span");
      m.className = "split-mask"; m.setAttribute("aria-hidden", "true");
      w.className = "split-word"; w.style.setProperty("--i", i); w.textContent = mot;
      m.appendChild(w); titre.appendChild(m); titre.appendChild(document.createTextNode(" "));
    });
  }
  document.querySelectorAll("[data-intro]").forEach(function (el, i) { el.style.setProperty("--delay", (0.35 + i * 0.12) + "s"); });
  requestAnimationFrame(function () { requestAnimationFrame(function () { root.classList.add("is-loaded"); }); });

  /* En-tete : fond opaque une fois le heros quitte. */
  var top = document.querySelector("[data-top]");

  /* Manifeste : chaque mot s'allume a mesure que le paragraphe traverse
     l'ecran. Intl.Segmenter coupe aussi le japonais et le chinois. */
  var mots = [];
  var manif = document.querySelector("[data-words]");
  if (manif && !reduit) {
    var brut = manif.textContent.trim();
    var morceaux = [];
    if (window.Intl && Intl.Segmenter) {
      var seg = new Intl.Segmenter(root.lang, { granularity: "word" });
      for (var s of seg.segment(brut)) morceaux.push(s.segment);
    } else {
      morceaux = brut.split(/(\s+)/);
    }
    manif.setAttribute("aria-label", brut);
    manif.textContent = "";
    var conteneur = document.createElement("span");
    conteneur.setAttribute("aria-hidden", "true");
    morceaux.forEach(function (p) {
      if (!p.trim()) { conteneur.appendChild(document.createTextNode(p)); return; }
      var sp = document.createElement("span"); sp.className = "wd"; sp.textContent = p;
      conteneur.appendChild(sp); mots.push(sp);
    });
    manif.appendChild(conteneur);
  }
  var allumes = -1;

  /* Recit : l'etape qui croise le milieu de l'ecran pilote le plateau. Le
     telephone fait un tour sur lui-meme et change d'ecran quand il montre
     son dos ; le decor et la lueur suivent par l'attribut data-etape. */
  var etapes = tous("[data-step]");
  var plateau = document.querySelector("[data-plateau]");
  var scene = document.querySelector("[data-stage]");
  var corps = scene && scene.querySelector(".tel__corps");
  var vues = scene ? tous("picture", scene) : [];
  var points = tous(".story__dots li");
  var lueurs = tous(".story__flou img");
  var active = -1, tour = null, echange = 0;
  function bascule(liste, n) { liste.forEach(function (e, i) { e.classList.toggle("is-on", i === n); }); }
  function activer(n) {
    if (n === active || n < 0) return;
    var sens = n > active ? 1 : -1, premier = active < 0;
    active = n;
    etapes.forEach(function (e, i) { e.classList.toggle("is-active", i === n); });
    bascule(points, n); bascule(lueurs, n);
    if (plateau) plateau.setAttribute("data-etape", n);
    clearTimeout(echange);
    if (tour) tour.cancel();
    if (premier || reduit || !corps || !corps.animate || !plateau.offsetParent) { bascule(vues, n); return; }
    tour = corps.animate([{ transform: "rotateY(0deg)" }, { transform: "rotateY(" + sens * 360 + "deg)" }],
      { duration: 950, easing: "cubic-bezier(.65,0,.35,1)" });
    echange = setTimeout(function () { bascule(vues, n); }, 475);
  }
  if (etapes.length) activer(0);
  if (etapes.length && "IntersectionObserver" in window) {
    var milieu = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) { if (e.isIntersecting) activer(etapes.indexOf(e.target)); });
    }, { rootMargin: "-50% 0px -50% 0px" });
    etapes.forEach(function (e) { milieu.observe(e); });
  }

  /* Scenes en volume : le pointeur fait tourner le rig, donc tous les calques
     a la fois, chacun selon sa profondeur. Seulement avec une souris, et
     seulement pour les scenes a l'ecran. transform est ecrit directement :
     une variable CSS heritee recalculerait le style de chaque calque. */
  var rigs = tous("[data-rig]");
  var px = 0, py = 0, tx = 0, ty = 0, rigEnAttente = false;
  function tourner() {
    rigEnAttente = false;
    tx += (px - tx) * 0.07; ty += (py - ty) * 0.07;
    var t = "rotateY(" + (tx * 10).toFixed(2) + "deg) rotateX(" + (-ty * 7).toFixed(2) + "deg)";
    rigs.forEach(function (r) { if (r.vu) r.style.transform = t; });
    if (Math.abs(px - tx) > 0.002 || Math.abs(py - ty) > 0.002) { rigEnAttente = true; requestAnimationFrame(tourner); }
  }
  if (rigs.length && !reduit && "IntersectionObserver" in window && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    var guet = new IntersectionObserver(function (entrees) { entrees.forEach(function (e) { e.target.vu = e.isIntersecting; }); });
    rigs.forEach(function (r) { guet.observe(r); });
    window.addEventListener("pointermove", function (e) {
      px = (e.clientX / window.innerWidth - 0.5) * 2;
      py = (e.clientY / window.innerHeight - 0.5) * 2;
      if (!rigEnAttente) { rigEnAttente = true; requestAnimationFrame(tourner); }
    }, { passive: true });
  }

  /* Heros : les ecrans suivants du telephone ne sont demandes qu'une fois la
     page chargee, puis ils se relaient tant que le heros est a l'ecran. */
  var heros = document.querySelector("[data-cycle]");
  if (heros && !reduit) {
    window.addEventListener("load", function () {
      setTimeout(function () {
        var ecran = heros.querySelector(".tel__ecran"), k = 0, vu = true;
        JSON.parse(heros.getAttribute("data-cycle")).forEach(function (chemin) {
          var p = document.createElement("picture");
          [["avif", "image/avif"], ["webp", "image/webp"]].forEach(function (f) {
            var src = document.createElement("source"); src.type = f[1]; src.srcset = chemin + "." + f[0]; p.appendChild(src);
          });
          var im = document.createElement("img");
          im.width = 720; im.height = 1280; im.alt = ""; im.decoding = "async"; im.src = chemin + ".jpg";
          p.appendChild(im); ecran.appendChild(p);
        });
        var ecrans = tous("picture", ecran);
        if ("IntersectionObserver" in window) {
          new IntersectionObserver(function (es) { vu = es[es.length - 1].isIntersecting; }).observe(heros);
        }
        setInterval(function () {
          var suivant = (k + 1) % ecrans.length;
          if (!vu || document.hidden || !ecrans[suivant].querySelector("img").complete) return;
          k = suivant; bascule(ecrans, k);
        }, 4200);
      }, 2000);
    });
  }

  var enAttente = false;
  function demander() { if (!enAttente) { enAttente = true; requestAnimationFrame(image); } }

  function image() {
    enAttente = false;
    var h = window.innerHeight, y = window.scrollY;
    if (top) top.classList.toggle("is-scrolled", y > 40);

    if (mots.length) {
      var r = manif.getBoundingClientRect();
      if (r.bottom > 0 && r.top < h) {
        var p = (h * 0.85 - r.top) / (r.height + h * 0.35);
        var n = Math.max(0, Math.min(mots.length, Math.round(p * mots.length)));
        if (n !== allumes) {
          for (var i = Math.max(0, Math.min(n, allumes)); i < Math.max(n, allumes); i++) mots[i].classList.toggle("on", i < n);
          allumes = n;
        }
      }
    }

    majAddition(y, h);
  }
  window.addEventListener("scroll", demander, { passive: true });
  window.addEventListener("resize", demander, { passive: true });

  /* Addition : un ticket de caisse vivant. Chaque fonction vue s'imprime :
     elle prend le rang suivant sur la piste, la piste avance d'une ligne
     (transition CSS sur transform), les lignes plus anciennes remontent et
     s'estompent (data-age). Le compteur rebondit, le total marque le coup,
     mais il reste a zero : aucun chiffre ne defile. Plusieurs fonctions
     vues d'un coup s'impriment l'une apres l'autre ; un gros arrivage
     (saut par ancre, rechargement en milieu de page) est pose sans cascade,
     sauf les deux dernieres lignes. Tout le mouvement est en transform et
     opacity ; en mouvement reduit, meme contenu, pose d'un coup. */
  var panneau = document.querySelector("[data-bill-panel]");
  var compteur = document.querySelector("[data-bill-count]");
  var rouleau = document.querySelector("[data-bill-roll]");
  var zeroTotal = document.querySelector("[data-bill-zero]");
  var eclat = document.querySelector("[data-bill-eclat]");
  var vus = {}, imprimees = [], file = [], impression = 0;
  var nbVus = 0;
  var debut = document.querySelector(".story");
  var fin = document.querySelector(".price");
  function ages() {
    var n = imprimees.length;
    imprimees.forEach(function (l, k) { l.setAttribute("data-age", Math.min(3, n - 1 - k)); });
  }
  function imprimer(c, anime) {
    var ligne = panneau && panneau.querySelector('[data-bill-item="' + c + '"]');
    nbVus++;
    if (compteur) compteur.textContent = nbVus;
    if (!ligne || !rouleau) return;
    ligne.style.transform = "translateY(" + (imprimees.length * 100) + "%)";
    imprimees.push(ligne);
    ages();
    rouleau.style.transform = "translateY(calc(" + (-imprimees.length) + " * var(--lh)))";
    if (!anime || reduit || !ligne.animate) return;
    /* La ligne sort de la fente un peu plus vite que le papier, l'encre se pose. */
    ligne.animate([{ opacity: 0, transform: "translateY(" + (imprimees.length * 100 - 50) + "%) scaleY(.5)" },
      { opacity: 1, transform: ligne.style.transform }], { duration: 520, easing: "cubic-bezier(.16,1,.3,1)" });
    if (compteur) compteur.animate([{ transform: "scale(1)" }, { transform: "scale(1.55) translateY(-3px)", offset: 0.35 }, { transform: "scale(1)" }],
      { duration: 480, easing: "cubic-bezier(.34,1.56,.64,1)" });
    if (zeroTotal) zeroTotal.animate([{ transform: "scale(1)" }, { transform: "scale(1.32) rotate(-7deg)", offset: 0.3 }, { transform: "scale(.94) rotate(1deg)", offset: 0.65 }, { transform: "none" }],
      { duration: 560, easing: "ease-out" });
    if (eclat) eclat.animate([{ opacity: 0 }, { opacity: 1, offset: 0.25 }, { opacity: 0 }], { duration: 700, easing: "ease-out" });
  }
  function suivante() {
    impression = 0;
    if (!file.length) return;
    /* Gros arrivage : tout sauf les deux dernieres lignes est pose d'un coup. */
    while (file.length > 2) imprimer(file.shift(), false);
    imprimer(file.shift(), true);
    demander();
    if (file.length) impression = setTimeout(suivante, reduit ? 0 : 420);
  }
  function ajouter(cles) {
    cles.split(" ").forEach(function (c) {
      if (!c || vus[c]) return;
      vus[c] = true; file.push(c);
    });
    if (!impression) suivante();
  }
  function majAddition(y, h) {
    if (!panneau || !debut || !fin) return;
    var a = debut.getBoundingClientRect().top < h * 0.6;
    var z = fin.getBoundingClientRect().top < h * 0.9;
    panneau.classList.toggle("is-shown", a && !z && (nbVus > 0 || file.length > 0));
  }

  /* Sections hors de l'ecran : leurs animations en boucle sont mises en pause
     (regle .hors de la feuille de style). */
  if ("IntersectionObserver" in window) {
    var veille = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) { e.target.classList.toggle("hors", !e.isIntersecting); });
    }, { rootMargin: "10% 0px" });
    tous("main > *").forEach(function (el) { veille.observe(el); });
  }

  /* Revelations : une fois, a l'entree dans l'ecran. */
  var cibles = document.querySelectorAll("[data-reveal], [data-bill]");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        if (el.hasAttribute("data-reveal")) el.classList.add("is-in");
        if (el.hasAttribute("data-bill")) ajouter(el.getAttribute("data-bill"));
        var zero = el.closest(".zero");
        if (zero) zero.classList.add("is-in");
        io.unobserve(el);
        demander();
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.15 });
    cibles.forEach(function (el) { io.observe(el); });
    /* Decalage dans un meme groupe (cartes, zeros, paragraphes). */
    document.querySelectorAll(".where__grid, .zeros, .privacy__text, .source__copy, .price__copy, .bobines__tete").forEach(function (g) {
      Array.prototype.forEach.call(g.querySelectorAll("[data-reveal]"), function (el, i) { el.style.setProperty("--delay", (i * 0.09) + "s"); });
    });
  } else {
    cibles.forEach(function (el) { el.classList.add("is-in"); });
  }

  /* Videos : aucune balise <video> dans la page. Elle est creee au clic, donc
     rien ne se charge ni ne joue avant ; une seule joue a la fois. Sans ce
     script les vignettes restent des liens vers les fichiers. */
  var enCours = null;
  function creer(lien) {
    var v = document.createElement("video"), im = lien.querySelector("img");
    v.controls = true; v.playsInline = true; v.preload = "auto";
    if (im && im.currentSrc) v.poster = im.currentSrc;
    v.setAttribute("aria-label", (lien.querySelector(".bob__titre, .sr") || lien).textContent.trim());
    v.src = lien.href;
    return v;
  }
  function jouer(v) {
    if (enCours && enCours !== v) enCours.pause();
    enCours = v;
    var p = v.play();
    if (p && p.catch) p.catch(function () { /* lecture refusee : les commandes restent */ });
  }
  /* Le film principal a deux vignettes (16:9 sur ordinateur, 9:16 sur
     mobile), la feuille de style n'en montre qu'une. Au clic, la jumelle
     disparait et le cadre garde le format choisi, meme si l'ecran change. */
  tous("[data-film]").forEach(function (lien) {
    lien.addEventListener("click", function (e) {
      e.preventDefault();
      var v = creer(lien), film = lien.closest(".film");
      if (film) film.classList.add(lien.getAttribute("data-format") === "9:16" ? "film--916" : "film--169");
      tous("[data-film]", lien.parentNode).forEach(function (l) { if (l !== lien) l.parentNode.removeChild(l); });
      lien.parentNode.replaceChild(v, lien);
      v.focus(); jouer(v);
      if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (es) { if (!es[es.length - 1].isIntersecting) v.pause(); }).observe(v);
      }
    });
  });
  var salle = document.querySelector("[data-salle]");
  if (salle && salle.showModal) {
    var toile = salle.querySelector("[data-salle-ecran]");
    tous("[data-bobine]").forEach(function (lien) {
      lien.addEventListener("click", function (e) {
        e.preventDefault();
        var v = creer(lien);
        toile.textContent = ""; toile.appendChild(v);
        salle.setAttribute("aria-label", v.getAttribute("aria-label"));
        salle.showModal(); jouer(v);
      });
    });
    salle.addEventListener("close", function () {
      var v = toile.querySelector("video");
      if (v) { v.pause(); v.removeAttribute("src"); v.load(); }
      toile.textContent = "";
    });
    salle.addEventListener("click", function (e) { if (e.target === salle || e.target === toile) salle.close(); });
    salle.querySelector("[data-salle-fermer]").addEventListener("click", function () { salle.close(); });
  }

  /* Rail de videos : le defilement lateral doit se deviner. Fondu sur le bord
     ou il reste du contenu (classes fond-g / fond-d, physiques), fleches sur
     ordinateur (peut-prev / peut-next, logiques : l'arabe est inverse par la
     feuille de style), et une invitation unique, un aller-retour, a la premiere
     entree du rail a l'ecran. Mouvement reduit : pas d'invitation, le reste
     demeure. Le contenu reste atteignable au doigt, a la molette et au clavier. */
  var rail = document.querySelector("[data-rail]");
  var piste = rail && rail.querySelector("[data-rail-piste]");
  if (piste) {
    var sens = 1, invite = false, majEnCours = false;
    var sensLu = function () { sens = window.getComputedStyle(piste).direction === "rtl" ? -1 : 1; };
    var maj = function () {
      majEnCours = false;
      if (invite) return;
      sensLu();
      var max = piste.scrollWidth - piste.clientWidth, x = Math.abs(piste.scrollLeft);
      var debut = x > 4, fin = x < max - 4;
      rail.classList.toggle("peut-prev", debut);
      rail.classList.toggle("peut-next", fin);
      rail.classList.toggle("fond-g", sens === 1 ? debut : fin);
      rail.classList.toggle("fond-d", sens === 1 ? fin : debut);
    };
    var planifier = function () { if (!majEnCours) { majEnCours = true; requestAnimationFrame(maj); } };
    piste.addEventListener("scroll", planifier, { passive: true });
    window.addEventListener("resize", planifier);
    maj();
    var touche = false;
    var pas = function (dir) {
      touche = true;
      sensLu();
      piste.scrollBy({ left: dir * sens * Math.max(240, piste.clientWidth * 0.8), behavior: reduit ? "auto" : "smooth" });
    };
    var bp = rail.querySelector("[data-rail-prev]"), bn = rail.querySelector("[data-rail-next]");
    if (bp) bp.addEventListener("click", function () { pas(-1); });
    if (bn) bn.addEventListener("click", function () { pas(1); });

    /* Invitation : une seule fois, annulee au moindre geste du visiteur. */
    ["pointerdown", "wheel", "touchstart", "keydown"].forEach(function (n) {
      piste.addEventListener(n, function () { touche = true; }, { passive: true });
    });
    var inviter = function () {
      tous(".bob", piste).forEach(function (c) { c.classList.add("is-in"); });
      if (reduit || touche || piste.scrollWidth <= piste.clientWidth + 8 || Math.abs(piste.scrollLeft) > 4) return;
      var amp = Math.min(84, piste.clientWidth * 0.14), duree = 1700, t0 = null;
      sensLu();
      invite = true;
      piste.style.scrollSnapType = "none"; piste.style.scrollBehavior = "auto";
      var fin = function () {
        piste.style.scrollSnapType = ""; piste.style.scrollBehavior = "";
        invite = false; maj();
      };
      var image = function (t) {
        if (touche) { fin(); return; }
        if (t0 === null) t0 = t;
        var k = Math.min(1, (t - t0) / duree), s = Math.sin(Math.PI * k);
        piste.scrollLeft = sens * amp * s * s;
        if (k < 1) requestAnimationFrame(image); else { piste.scrollLeft = 0; fin(); }
      };
      requestAnimationFrame(image);
    };
    if ("IntersectionObserver" in window) {
      var vu = new IntersectionObserver(function (es) {
        if (!es.some(function (e) { return e.isIntersecting; })) return;
        vu.disconnect();
        window.setTimeout(inviter, reduit ? 0 : 900);
      }, { threshold: 0.45 });
      vu.observe(piste);
    } else {
      tous(".bob", piste).forEach(function (c) { c.classList.add("is-in"); });
    }
  }

  calme.addEventListener && calme.addEventListener("change", function () { location.reload(); });
  demander();
})();
