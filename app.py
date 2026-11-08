
import hashlib
import json
import os
import re
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from flask import (
    Flask, request, redirect, url_for, session,
    jsonify, render_template_string, send_from_directory
)
from markupsafe import Markup
from werkzeug.utils import secure_filename
from openpyxl import Workbook, load_workbook

# SETTINGS
BASE = Path(__file__).resolve().parent
INVENTORY_DIR = Path(os.environ.get("INVENTORY_DIR", BASE)).expanduser()
if not INVENTORY_DIR.is_absolute():
    INVENTORY_DIR = BASE / INVENTORY_DIR
INVENTORY_DIR = INVENTORY_DIR.resolve()
UPLOADS = INVENTORY_DIR / "uploads"
EXCEL = INVENTORY_DIR / "laptops.xlsx"
DB = BASE / "chats.db"

UPLOADS.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change123")
WHATSAPP_NUMBER = re.sub(
    r"\D", "", os.environ.get("WHATSAPP_NUMBER", "03183703386")
)
if WHATSAPP_NUMBER.startswith("0"):
    WHATSAPP_NUMBER = "92" + WHATSAPP_NUMBER[1:]
WHATSAPP = WHATSAPP_NUMBER

COLUMNS = [
    "ID", "Brand", "Model", "Processor", "Generation",
    "RAM", "SSD", "Screen", "Price", "Condition",
    "Availability", "Images", "Description"
]

ALLOWED = {"jpg", "jpeg", "png", "webp"}


def normalize_phone_number(value):
    digits = re.sub(r"\D", "", value)
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = "92" + digits[1:]
    return digits


SITE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#10101b">
  <title>{{ title }} · AK Apple Store</title>
  <style>
    :root{color-scheme:dark;--ink:#f7f6ff;--muted:#a3a2b7;--bg:#10101b;--panel:#191927;--line:rgba(255,255,255,.1);--violet:#9b7bff;--lime:#d8ff72;--cyan:#68e8ef}
    *{box-sizing:border-box}
    html{scroll-behavior:smooth}
    body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    a{color:inherit;text-decoration:none}
    button,input,select,textarea{font:inherit}
    button,a,input,select,textarea{-webkit-tap-highlight-color:transparent}
    button{cursor:pointer}
    .announcement{padding:9px 20px;text-align:center;background:var(--lime);color:#171a0e;font-size:12px;font-weight:750;letter-spacing:.04em}
    .site-header{position:sticky;top:0;z-index:20;background:rgba(16,16,27,.88);backdrop-filter:blur(18px);border-bottom:1px solid var(--line)}
    .nav{max-width:1220px;height:76px;padding:0 24px;margin:auto;display:flex;align-items:center;justify-content:space-between;gap:24px}
    .brand{display:inline-flex;align-items:center;gap:10px;font-weight:850;font-size:20px;letter-spacing:-.06em}
    .brand-mark{width:32px;height:32px;display:grid;place-items:center;border-radius:11px;background:linear-gradient(145deg,var(--violet),#6242cf);box-shadow:0 5px 24px #8f6aff55}
    .brand-mark svg{width:19px}
    .nav-links{display:flex;align-items:center;gap:30px;color:#c5c3d4;font-size:13px;font-weight:600}
    .nav-links a:hover{color:var(--lime)}
    .nav-actions{display:flex;align-items:center;gap:12px}
    .menu-toggle{display:none;border:1px solid var(--line);border-radius:11px;padding:9px 12px;color:var(--ink);background:var(--panel)}
    .button{display:inline-flex;align-items:center;justify-content:center;gap:9px;border:0;border-radius:12px;padding:12px 17px;background:var(--lime);color:#171a0e;font-size:13px;font-weight:800;transition:transform .2s,box-shadow .2s,background .2s}
    .button:hover{transform:translateY(-2px);box-shadow:0 9px 28px #d8ff7230}
    .button-secondary{background:rgba(255,255,255,.08);color:var(--ink);border:1px solid var(--line)}
    .button-secondary:hover{background:rgba(255,255,255,.13)}
    .button-small{padding:9px 12px;font-size:12px}
    main{min-height:60vh}
    .container{max-width:1220px;padding:0 24px;margin:0 auto}
    .eyebrow{display:inline-flex;align-items:center;gap:8px;color:var(--lime);font-size:11px;font-weight:800;letter-spacing:.13em;text-transform:uppercase}
    .eyebrow:before{content:"";width:20px;height:1px;background:currentColor}
    .muted{color:var(--muted)}
    .site-footer{margin-top:90px;padding:30px 24px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
    .footer-inner{max-width:1220px;margin:auto;display:flex;align-items:center;justify-content:space-between;gap:16px}
    .hero{position:relative;overflow:hidden;padding:70px 0 80px;background:radial-gradient(ellipse at 75% 48%,#7248ca30,transparent 37%),radial-gradient(ellipse at 12% 90%,#36c1c025,transparent 32%)}
    .hero:after{content:"";position:absolute;inset:0;pointer-events:none;opacity:.22;background-image:radial-gradient(#fff 1px,transparent 1px);background-size:35px 35px;mask-image:linear-gradient(90deg,transparent 25%,#000)}
    .hero-inner{position:relative;z-index:1;max-width:1220px;padding:0 24px;margin:auto;display:grid;grid-template-columns:1.04fr .96fr;align-items:center;gap:42px}
    .hero-copy{max-width:610px}
    .hero h1{max-width:650px;margin:20px 0 18px;font-size:clamp(46px,6.6vw,78px);line-height:.98;letter-spacing:-.075em}
    .hero h1 span{color:var(--lime)}
    .hero-copy>p{max-width:490px;margin:0;color:#b9b7ca;font-size:16px}
    .hero-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:30px}
    .trust-row{display:flex;flex-wrap:wrap;gap:20px;margin-top:34px;color:#cac8d8;font-size:11px;font-weight:650}
    .trust-row span{display:flex;align-items:center;gap:7px}
    .trust-row b{color:var(--lime);font-size:14px}
    .hero-visual{position:relative;min-height:390px;display:grid;place-items:center;perspective:900px}
    .glow{position:absolute;width:310px;height:310px;border-radius:50%;background:#a27cff38;filter:blur(55px);animation:breathe 5s ease-in-out infinite}
    .laptop-art{position:relative;width:min(410px,90%);transform:rotateY(-12deg) rotateX(5deg);animation:float 6s ease-in-out infinite;filter:drop-shadow(0 28px 30px #0008)}
    .laptop-screen{height:245px;padding:10px;border:2px solid #83839c;border-bottom:0;border-radius:18px 18px 5px 5px;background:linear-gradient(145deg,#292a3c,#10101b 68%);position:relative}
    .screen-glass{height:100%;overflow:hidden;position:relative;border-radius:10px;background:radial-gradient(ellipse at 70% 25%,#b4ff7730,transparent 35%),linear-gradient(135deg,#242039,#141426 65%)}
    .screen-top{height:24px;padding:0 11px;display:flex;align-items:center;gap:4px;background:#ffffff0b}
    .screen-top i{width:5px;height:5px;border-radius:50%;background:#ff7991}
    .screen-top i:nth-child(2){background:#ffc96f}.screen-top i:nth-child(3){background:#aaff7c}
    .screen-content{padding:24px}
    .screen-pill{width:65px;height:6px;border-radius:8px;background:var(--lime);opacity:.8}
    .screen-title{width:78%;height:22px;margin-top:14px;border-radius:5px;background:linear-gradient(90deg,#fff,#a49abf);opacity:.9}
    .screen-title.short{width:48%;margin-top:7px}
    .screen-cards{display:flex;gap:9px;margin-top:22px}
    .screen-card{height:82px;flex:1;padding:9px;border:1px solid #ffffff15;border-radius:9px;background:linear-gradient(135deg,#ffffff12,#ffffff04)}
    .screen-card:before,.screen-card:after{content:"";display:block;width:60%;height:5px;margin-top:7px;border-radius:4px;background:#ffffff77}
    .screen-card:after{width:85%;background:#ffffff30}
    .laptop-base{height:14px;margin:0 -22px;border-radius:2px 2px 15px 15px;background:linear-gradient(180deg,#c1c1d0,#59596c 48%,#292938);clip-path:polygon(5% 0,95% 0,100% 80%,87% 100%,13% 100%,0 80%)}
    .float-card{position:absolute;z-index:2;padding:13px 15px;border:1px solid #ffffff1a;border-radius:14px;background:#1a1928e8;box-shadow:0 15px 45px #0005;backdrop-filter:blur(10px);animation:float 5s ease-in-out infinite}
    .float-card small{display:block;color:var(--muted);font-size:10px}
    .float-card strong{display:block;margin-top:2px;font-size:13px}
    .float-icon{display:inline-grid;width:25px;height:25px;place-items:center;margin-right:8px;border-radius:8px;background:#d8ff7220;color:var(--lime)}
    .float-one{top:33px;right:5px}.float-two{bottom:42px;left:-4px;animation-delay:-2.3s}
    .section{padding:30px 0 0}
    .section-heading{display:flex;align-items:end;justify-content:space-between;gap:18px;margin:0 0 24px}
    .section-heading h2{margin:8px 0 0;font-size:32px;letter-spacing:-.05em}
    .shop-tools{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
    .field,.select{min-height:43px;padding:10px 13px;border:1px solid var(--line);border-radius:11px;background:#191927;color:var(--ink);outline:none}
    .field:focus,.select:focus,textarea:focus{border-color:var(--violet);box-shadow:0 0 0 3px #9b7bff25}
    .search-field{width:min(270px,100%)}
    .filter-row{display:flex;gap:8px;overflow:auto;padding:2px 0 16px}
    .filter-chip{flex:none;padding:8px 13px;border:1px solid var(--line);border-radius:99px;background:transparent;color:#c7c5d6;font-size:12px;font-weight:650}
    .filter-chip.active,.filter-chip:hover{border-color:var(--lime);background:#d8ff7218;color:var(--lime)}
    .product-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
    .product-card{overflow:hidden;position:relative;border:1px solid var(--line);border-radius:18px;background:linear-gradient(145deg,#1d1d2c,#171722);transition:transform .25s,border-color .25s,box-shadow .25s}
    .product-card:hover{transform:translateY(-5px);border-color:#9b7bff80;box-shadow:0 18px 45px #0004}
    .product-media{height:220px;position:relative;display:grid;place-items:center;overflow:hidden;background:radial-gradient(ellipse at 48% 65%,#8d71df26,transparent 54%),linear-gradient(135deg,#222235,#181824)}
    .product-media img{width:100%;height:100%;object-fit:contain;padding:22px}
    .product-media .laptop-mini{width:62%;max-width:250px;filter:drop-shadow(0 14px 14px #0007);transition:transform .3s}
    .product-card:hover .laptop-mini{transform:translateY(-5px) scale(1.03)}
    .laptop-mini .laptop-screen{height:130px;padding:6px;border-radius:11px 11px 3px 3px}
    .laptop-mini .screen-glass{border-radius:6px}
    .laptop-mini .screen-top{height:12px;padding:0 5px;gap:2px}
    .laptop-mini .screen-top i{width:3px;height:3px}
    .laptop-mini .screen-content{padding:12px}
    .laptop-mini .screen-pill{width:35px;height:4px}
    .laptop-mini .screen-title{height:10px;margin-top:7px}
    .laptop-mini .screen-title.short{margin-top:4px}
    .laptop-mini .screen-cards{gap:4px;margin-top:10px}
    .laptop-mini .screen-card{height:41px;padding:4px;border-radius:5px}
    .laptop-mini .screen-card:before,.laptop-mini .screen-card:after{height:3px;margin-top:3px}
    .laptop-mini .laptop-base{height:8px;margin:0 -12px}
    .stock-tag{position:absolute;top:14px;left:14px;padding:6px 9px;border:1px solid #d8ff7240;border-radius:99px;background:#d8ff7216;color:var(--lime);font-size:10px;font-weight:750}
    .favorite{position:absolute;top:12px;right:12px;width:34px;height:34px;border:1px solid #ffffff20;border-radius:50%;background:#11111bcc;color:white;font-size:16px}
    .favorite.active{color:#ff7991}
    .product-info{padding:17px}
    .product-brand{color:var(--violet);font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
    .product-info h3{margin:5px 0;font-size:19px;letter-spacing:-.035em}
    .spec-line{min-height:21px;color:var(--muted);font-size:12px}
    .product-bottom{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:15px;padding-top:13px;border-top:1px solid var(--line)}
    .price{font-size:18px;font-weight:800;letter-spacing:-.04em}
    .card-actions{display:flex;align-items:center;gap:7px}
    .text-link{color:var(--lime);font-size:12px;font-weight:750}
    .empty-state{grid-column:1/-1;padding:55px 20px;text-align:center;border:1px dashed #ffffff2c;border-radius:18px;color:var(--muted)}
    .empty-state strong{display:block;margin-bottom:7px;color:var(--ink);font-size:18px}
    .benefits{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:56px 0 5px}
    .benefit{padding:18px;border:1px solid var(--line);border-radius:15px;background:#ffffff05}
    .benefit b{display:block;margin:7px 0 3px;font-size:14px}.benefit p{margin:0;color:var(--muted);font-size:12px}
    .benefit-icon{font-size:19px;color:var(--lime)}
    .product-layout{display:grid;grid-template-columns:1.05fr .95fr;gap:52px;padding-top:54px}
    .gallery-main{height:470px;display:grid;place-items:center;overflow:hidden;border:1px solid var(--line);border-radius:22px;background:radial-gradient(ellipse at 50% 65%,#8d71df2b,transparent 55%),#191927}
    .gallery-main img{width:100%;height:100%;object-fit:contain;padding:25px}
    .gallery-main .laptop-art{width:75%}
    .thumbs{display:flex;gap:10px;margin-top:12px}
    .thumb{width:72px;height:64px;overflow:hidden;border:1px solid var(--line);border-radius:10px;background:#191927;cursor:pointer}
    .thumb img{width:100%;height:100%;object-fit:cover}
    .product-detail h1{margin:10px 0;font-size:clamp(34px,4vw,50px);line-height:1.02;letter-spacing:-.065em}
    .detail-price{margin:18px 0;font-size:29px;font-weight:850;color:var(--lime)}
    .detail-description{color:#bab8ca}
    .spec-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:25px 0}
    .spec{padding:13px;border:1px solid var(--line);border-radius:12px;background:#ffffff05}
    .spec small{display:block;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.09em}
    .spec b{display:block;margin-top:3px;font-size:13px}
    .detail-actions{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}
    .form-card,.panel{padding:22px;border:1px solid var(--line);border-radius:17px;background:#191927}
    .form-card h3,.panel h2{margin:0 0 14px}
    .order-form{margin-top:22px}
    .form-error{padding:10px 12px;border:1px solid #ff93a344;border-radius:10px;background:#ff93a310;color:#ffb1bc;font-size:13px}
    .form-row{display:flex;gap:10px}
    .form-row .field{flex:1;min-width:0}
    .auth-wrap{max-width:450px;margin:66px auto;padding:0 20px}
    .auth-card{padding:28px;border:1px solid var(--line);border-radius:20px;background:#191927}
    .auth-card h1{margin:9px 0 20px;font-size:30px;letter-spacing:-.05em}
    .stack{display:grid;gap:12px}.stack label{display:grid;gap:6px;color:var(--muted);font-size:12px}
    .order-admin-card{padding:18px 0;border-bottom:1px solid var(--line)}
    .order-admin-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}
    .order-admin-heading h3{margin:6px 0;font-size:17px}
    .order-status{padding:6px 10px;border:1px solid #d8ff7240;border-radius:99px;color:var(--lime);font-size:11px;font-weight:750}
    .order-admin-details{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:13px 0}
    .order-admin-details span{min-width:0;color:#e5e3ef;font-size:13px;overflow-wrap:anywhere}
    .order-admin-details b{display:block;margin-bottom:3px;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.08em}
    .order-admin-details a{color:var(--lime)}
    .order-status-form{display:flex;align-items:end;gap:9px}
    .order-status-form label{display:grid;gap:5px;color:var(--muted);font-size:11px}
    .admin-wrap{max-width:1100px;margin:42px auto;padding:0 20px}
    .admin-heading{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}
    .admin-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:22px}
    .admin-form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
    .inventory-item{padding:12px 0;border-bottom:1px solid var(--line);font-size:13px}
    .chat-list{display:flex;flex-direction:column;gap:8px}.chat-list a{padding:11px;border:1px solid var(--line);border-radius:10px;background:#ffffff05;font-size:13px}
    dialog{width:min(560px,calc(100% - 28px));padding:0;border:1px solid #ffffff25;border-radius:20px;background:#191927;color:var(--ink);box-shadow:0 28px 100px #000b}
    dialog::backdrop{background:#07070dcc;backdrop-filter:blur(6px)}
    .modal-inner{padding:24px}.modal-close{float:right;border:1px solid var(--line);border-radius:9px;padding:7px 10px;background:#ffffff0a;color:var(--ink)}
    .modal-inner h2{margin:20px 0 5px}.modal-inner p{color:var(--muted)}
    .modal-specs{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 20px}
    .modal-specs span{padding:7px 10px;border:1px solid var(--line);border-radius:99px;color:#d4d1e2;font-size:11px}
    .toast{position:fixed;right:20px;bottom:20px;z-index:50;padding:12px 16px;border:1px solid var(--line);border-radius:12px;background:#262538;box-shadow:0 10px 30px #0007;opacity:0;transform:translateY(12px);transition:.2s;pointer-events:none}
    .toast.show{opacity:1;transform:translateY(0)}
    @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
    @keyframes breathe{0%,100%{opacity:.65;transform:scale(.94)}50%{opacity:1;transform:scale(1.08)}}
    @media(max-width:850px){.hero-inner{grid-template-columns:1fr .85fr;gap:10px}.hero h1{font-size:clamp(42px,8vw,64px)}.hero-visual{min-height:330px}.product-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.product-layout{gap:28px}.gallery-main{height:380px}}
    @media(max-width:650px){.nav{height:66px;padding:0 18px}.menu-toggle{display:block}.nav-actions>.button{display:none}.nav-links{display:none;position:absolute;top:65px;left:0;right:0;padding:16px 20px 20px;background:#14141f;border-bottom:1px solid var(--line);flex-direction:column;align-items:stretch;gap:0}.nav-links.open{display:flex}.nav-links a{padding:12px 4px;border-bottom:1px solid var(--line)}.container{padding:0 18px}.hero{padding:48px 0 56px}.hero-inner{grid-template-columns:1fr}.hero-visual{min-height:300px;max-width:500px;width:100%;margin:0 auto}.laptop-art{width:min(360px,82%)}.laptop-screen{height:205px}.float-one{right:0}.float-two{left:0}.hero-copy>p{font-size:14px}.trust-row{gap:13px}.section-heading{align-items:flex-start;flex-direction:column}.section-heading h2{font-size:28px}.shop-tools{width:100%}.search-field{flex:1;min-width:0}.select{max-width:135px}.product-grid{grid-template-columns:1fr}.product-media{height:235px}.benefits{grid-template-columns:1fr;margin-top:38px}.product-layout{grid-template-columns:1fr;padding-top:25px}.gallery-main{height:310px}.product-detail h1{font-size:38px}.admin-grid{grid-template-columns:1fr}.admin-form-grid{grid-template-columns:1fr}.footer-inner{align-items:flex-start;flex-direction:column}.form-row{flex-direction:column}.form-row .button{width:100%}.order-admin-details{grid-template-columns:1fr}.order-status-form{align-items:stretch;flex-direction:column}.order-status-form .button{width:100%}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
  </style>
</head>
<body>
  <div class="announcement">COMPLIMENTARY DELIVERY · TESTED TECH · ZERO GUESSWORK</div>
  <header class="site-header">
    <nav class="nav" aria-label="Main navigation">
      <a class="brand" href="{{ url_for('home') }}"><span class="brand-mark" style="font-size:11px;letter-spacing:-.08em">AK</span>Apple Store<span style="color:var(--lime)">.</span></a>
      <div class="nav-links" id="nav-links"><a href="{{ url_for('home') }}#shop">Shop MacBooks</a><a href="{{ url_for('home') }}#why-nova">Why AK Apple</a><a href="{{ url_for('login') }}">Seller portal</a></div>
      <div class="nav-actions"><a class="button button-small" href="{{ url_for('home') }}#shop">Find your laptop <span aria-hidden="true">↗</span></a><button class="menu-toggle" id="menu-toggle" aria-expanded="false" aria-controls="nav-links">Menu</button></div>
    </nav>
  </header>
  <main>{{ content }}</main>
  <footer class="site-footer"><div class="footer-inner"><a class="brand" href="{{ url_for('home') }}"><span class="brand-mark" style="font-size:11px;letter-spacing:-.08em">AK</span>Apple Store<span style="color:var(--lime)">.</span></a><span>Your next Mac starts here.</span><span>© {{ year }} AK Apple Store</span></div></footer>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>
  <script>
    const menuToggle = document.getElementById('menu-toggle');
    const navLinks = document.getElementById('nav-links');
    menuToggle?.addEventListener('click', () => {
      const open = navLinks.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', String(open));
    });
    let toastTimer;
    function showToast(message) {
      const toast = document.getElementById('toast');
      toast.textContent = message;
      toast.classList.add('show');
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
    }
    document.querySelectorAll('[data-favorite]').forEach(button => {
      const id = button.dataset.favorite;
      const saved = new Set(JSON.parse(localStorage.getItem('nova-favorites') || '[]'));
      const update = () => {
        button.classList.toggle('active', saved.has(id));
        button.setAttribute('aria-pressed', String(saved.has(id)));
        button.textContent = saved.has(id) ? '♥' : '♡';
      };
      update();
      button.addEventListener('click', () => {
        saved.has(id) ? saved.delete(id) : saved.add(id);
        localStorage.setItem('nova-favorites', JSON.stringify([...saved]));
        update();
        showToast(saved.has(id) ? 'Saved to your favorites' : 'Removed from favorites');
      });
    });
    document.querySelectorAll('[data-quick-view]').forEach(button => {
      button.addEventListener('click', () => {
        const dialog = document.getElementById('quick-view');
        const product = JSON.parse(button.dataset.quickView);
        dialog.querySelector('[data-modal-brand]').textContent = product.brand;
        dialog.querySelector('[data-modal-title]').textContent = product.name;
        dialog.querySelector('[data-modal-price]').textContent = product.price;
        dialog.querySelector('[data-modal-description]').textContent = product.description || 'Carefully selected tech, ready for its next chapter.';
        dialog.querySelector('[data-modal-specs]').replaceChildren(...product.specs.map(spec => {
          const item = document.createElement('span');
          item.textContent = spec;
          return item;
        }));
        dialog.querySelector('[data-modal-link]').href = product.url;
        dialog.showModal();
      });
    });
    document.querySelector('[data-modal-close]')?.addEventListener('click', () => document.getElementById('quick-view').close());
    document.querySelectorAll('[data-gallery-image]').forEach(button => {
      button.addEventListener('click', () => {
        const main = document.querySelector('[data-gallery-main]');
        if (main) main.src = button.dataset.galleryImage;
      });
    });
  </script>
</body>
</html>
"""


def render_page(title, template, **context):
    content = render_template_string(template, **context)
    return render_template_string(
        SITE_TEMPLATE, title=title, content=Markup(content),
        year=datetime.now().year,
        whatsapp_link=f"https://wa.me/{WHATSAPP}",
        whatsapp_display=(
            "0" + WHATSAPP[2:] if WHATSAPP.startswith("92") else WHATSAPP
        )
    )


# EXCEL
def init_excel():
    if not EXCEL.exists():
        wb = Workbook()
        ws = wb.active
        ws.title = "Laptops"
        ws.append(COLUMNS)
        wb.save(EXCEL)


def get_products():
    init_excel()
    wb = load_workbook(EXCEL, read_only=True, data_only=True)
    ws = wb["Laptops"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    products = []
    if not rows:
        return products

    headers = rows[0]

    for row in rows[1:]:
        if not row or not row[0]:
            continue

        p = dict(zip(headers, row))
        for column in COLUMNS:
            if p.get(column) is None:
                p[column] = ""
        p["ID"] = str(p["ID"])
        p["Images"] = [
            x.strip() for x in str(p.get("Images") or "").split(",")
            if x.strip()
        ]

        try:
            p["Price"] = int(float(p.get("Price") or 0))
        except (ValueError, TypeError):
            p["Price"] = 0

        products.append(p)

    return products


def inventory_version(products=None):
    if products is None:
        products = get_products()

    excel_stat = EXCEL.stat()
    files = [["laptops.xlsx", excel_stat.st_mtime_ns, excel_stat.st_size]]
    for product in products:
        for image in product["Images"]:
            image_path = UPLOADS / Path(image).name
            try:
                image_stat = image_path.stat()
            except FileNotFoundError:
                files.append([image, None, None])
            else:
                files.append([image, image_stat.st_mtime_ns, image_stat.st_size])

    content = json.dumps(files, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def save_product(data):
    init_excel()
    wb = load_workbook(EXCEL)
    ws = wb["Laptops"]

    for i in range(2, ws.max_row + 1):
        if str(ws.cell(i, 1).value) == str(data["ID"]):
            ws.delete_rows(i)
            break

    ws.append([data.get(c, "") for c in COLUMNS])
    wb.save(EXCEL)
    wb.close()


# ORDER DATABASE
def connection():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connection() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS customers(
            chat_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            product_id TEXT
        )
        """)
        customer_columns = {
            row["name"] for row in con.execute("PRAGMA table_info(customers)")
        }
        if "product_id" not in customer_columns:
            con.execute("ALTER TABLE customers ADD COLUMN product_id TEXT")
        con.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL
        )
        """)


def product_by_id(product_id):
    return next(
        (product for product in get_products() if product["ID"] == product_id),
        None
    )


init_db()


# ADMIN LOGIN
def admin_only(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USER
            and request.form.get("password") == ADMIN_PASSWORD
        ):
            session["admin"] = True
            return redirect("/admin")

        error = "That username and password don't match. Please try again."
    else:
        error = ""

    html = """
    <section class="auth-wrap"><div class="auth-card">
      <span class="eyebrow">Seller portal</span><h1>Welcome back.</h1>
      {% if error %}<p role="alert" style="color:#ff93a3">{{ error }}</p>{% endif %}
      <form class="stack" method="post">
        <label>Username<input class="field" name="username" autocomplete="username" required></label>
        <label>Password<input class="field" name="password" type="password" autocomplete="current-password" required></label>
        <button class="button" type="submit">Sign in ↗</button>
      </form>
    </div></section>
    """
    return render_page("Seller sign in", html, error=error)


@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect("/admin/login")


# CUSTOMER WEBSITE
@app.route("/")
def home():
    q = request.args.get("q", "").lower()
    products = get_products()

    products = [
        p for p in products
        if str(p.get("Availability", "")).lower()
        in ("available", "in stock", "yes", "demo listing")
        and (
            not q or q in " ".join(str(v) for v in p.values()).lower()
        )
    ]

    html = """
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-copy">
          <span class="eyebrow">Your next great idea starts here</span>
          <h1>Power up.<br><span>Stand out.</span></h1>
          <p>Find the laptop that moves at your speed. Curated picks, honest specs, and a real person ready to help you choose.</p>
          <div class="hero-actions">
            <a class="button" href="#shop">Explore the collection <span aria-hidden="true">↘</span></a>
            <a class="button button-secondary" href="#why-nova">The AK Apple difference</a>
          </div>
          <div class="trust-row"><span><b>✳</b> Hand-picked tech</span><span><b>✓</b> Every spec, upfront</span><span><b>↗</b> Seller support</span></div>
        </div>
        <div class="hero-visual" aria-label="Illustration of a laptop with product highlights">
          <div class="glow"></div>
          <div class="laptop-art" aria-hidden="true"><div class="laptop-screen"><div class="screen-glass"><div class="screen-top"><i></i><i></i><i></i></div><div class="screen-content"><div class="screen-pill"></div><div class="screen-title"></div><div class="screen-title short"></div><div class="screen-cards"><div class="screen-card"></div><div class="screen-card"></div><div class="screen-card"></div></div></div></div></div><div class="laptop-base"></div></div>
          <div class="float-card float-one"><span class="float-icon">✦</span><small>YOUR NEXT UPGRADE</small><strong>Made for more.</strong></div>
          <div class="float-card float-two"><small>THE AK APPLE STANDARD</small><strong>✓ Quality, checked</strong></div>
        </div>
      </div>
    </section>
    <section class="container section" id="shop" data-inventory-version="{{ inventory_version }}">
      <div class="section-heading">
        <div><span class="eyebrow">The collection</span><h2>Find your next machine.</h2></div>
        <div class="shop-tools">
          <form id="search-form" role="search"><input class="field search-field" id="product-search" name="q" value="{{ q }}" placeholder="Search brand, model, specs" aria-label="Search laptops"></form>
          <select class="select" id="sort-products" aria-label="Sort laptops"><option value="featured">Featured</option><option value="price-low">Price: low to high</option><option value="price-high">Price: high to low</option><option value="name">Name: A to Z</option></select>
        </div>
      </div>
      {% if brands %}
      <div class="filter-row" aria-label="Filter by brand">
        <button type="button" class="filter-chip active" data-brand-filter="all">All laptops</button>
        {% for brand in brands %}<button type="button" class="filter-chip" data-brand-filter="{{ brand|lower }}">{{ brand }}</button>{% endfor %}
      </div>
      {% endif %}
      <div class="product-grid" id="product-grid" aria-live="polite">
        {% for p in products %}
        <article class="product-card" data-name="{{ (p.Brand ~ ' ' ~ p.Model ~ ' ' ~ p.Processor ~ ' ' ~ p.RAM ~ ' ' ~ p.SSD)|lower }}" data-brand="{{ p.Brand|lower }}" data-price="{{ p.Price }}" data-featured="{{ loop.index0 }}">
          <div class="product-media">
            {% if p.Images %}<img src="{{ url_for('uploaded_file', filename=p.Images[0]) }}" alt="{{ p.Brand }} {{ p.Model }} laptop" loading="lazy">
            {% else %}
            <svg class="laptop-mini" viewBox="0 0 400 260" role="img" aria-label="Laptop illustration"><defs><linearGradient id="screen" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#baff70"/><stop offset=".48" stop-color="#8d74ed"/><stop offset="1" stop-color="#30304c"/></linearGradient><linearGradient id="base" x2="0" y2="1"><stop stop-color="#d5d4e4"/><stop offset="1" stop-color="#626276"/></linearGradient></defs><rect x="61" y="25" width="278" height="184" rx="14" fill="#77778b"/><rect x="68" y="32" width="264" height="169" rx="9" fill="#181827"/><rect x="77" y="41" width="246" height="151" rx="5" fill="#202037"/><circle cx="200" cy="48" r="2" fill="#b9b8cb"/><rect x="96" y="62" width="55" height="6" rx="3" fill="#d8ff72"/><rect x="96" y="78" width="122" height="15" rx="4" fill="url(#screen)"/><rect x="96" y="99" width="79" height="7" rx="3" fill="#86839f"/><rect x="96" y="123" width="65" height="48" rx="6" fill="#a186fb" opacity=".8"/><rect x="169" y="123" width="65" height="48" rx="6" fill="#d8ff72" opacity=".8"/><rect x="242" y="123" width="65" height="48" rx="6" fill="#65dce8" opacity=".8"/><path d="M37 213h326l30 19c4 3 2 9-5 9H12c-7 0-9-6-5-9l30-19Z" fill="url(#base)"/><path d="M163 214h74l8 7h-90l8-7Z" fill="#77778b"/></svg>
            {% endif %}
            <span class="stock-tag">{{ p.Availability }}</span>
            <button type="button" class="favorite" data-favorite="{{ p.ID }}" aria-label="Save {{ p.Brand }} {{ p.Model }} to favorites" aria-pressed="false">♡</button>
          </div>
          <div class="product-info">
            <div class="product-brand">{{ p.Brand }}</div><h3>{{ p.Model }}</h3>
            <div class="spec-line">{{ p.Processor }}{% if p.Generation %} · {{ p.Generation }}{% endif %}</div>
            <div class="spec-line">{{ p.RAM }} RAM{% if p.SSD %} · {{ p.SSD }} SSD{% endif %}{% if p.Condition %} · {{ p.Condition }}{% endif %}</div>
            <div class="product-bottom">
              <span class="price">Indicative · Rs. {{ "{:,}".format(p.Price) }}</span>
              <div class="card-actions">
                <button type="button" class="button button-secondary button-small" data-quick-view='{{ {"brand": p.Brand, "name": p.Model, "price": "Indicative · Rs. " ~ "{:,}".format(p.Price), "description": p.Description, "specs": [p.Processor, p.RAM ~ " RAM", p.SSD ~ " SSD", p.Screen], "url": url_for("product", product_id=p.ID)}|tojson }}'>Quick view</button>
                <a class="text-link" href="{{ url_for('product', product_id=p.ID) }}">Details ↗</a>
              </div>
            </div>
          </div>
        </article>
        {% else %}
        <div class="empty-state" id="empty-state"><strong>Your next favorite is almost here.</strong>We’re refreshing the collection. Check back soon or message us for help finding a specific laptop.</div>
        {% endfor %}
        {% if products %}<div class="empty-state" id="filter-empty" hidden><strong>No matches this time.</strong>Try another search or choose a different brand.</div>{% endif %}
      </div>
      <div class="benefits" id="why-nova">
        <div class="benefit"><span class="benefit-icon">✦</span><b>Only the good stuff</b><p>Thoughtful picks, clearly described. No spec-sheet scavenger hunts.</p></div>
        <div class="benefit"><span class="benefit-icon">◈</span><b>Know before you buy</b><p>See the details that matter and get a straight answer from the seller.</p></div>
        <div class="benefit"><span class="benefit-icon">↗</span><b>Here when you need us</b><p>Ask a question before you buy with direct seller chat.</p></div>
      </div>
    </section>
    <dialog id="quick-view" aria-labelledby="modal-title">
      <div class="modal-inner"><button type="button" class="modal-close" data-modal-close aria-label="Close quick view">✕</button><span class="eyebrow" data-modal-brand></span><h2 id="modal-title" data-modal-title></h2><strong class="detail-price" data-modal-price></strong><p data-modal-description></p><div class="modal-specs" data-modal-specs></div><a class="button" data-modal-link href="#">View full details ↗</a></div>
    </dialog>
    <script>
      const grid = document.getElementById('product-grid');
      const cards = [...grid.querySelectorAll('.product-card')];
      const search = document.getElementById('product-search');
      const sort = document.getElementById('sort-products');
      const empty = document.getElementById('filter-empty');
      let activeBrand = 'all';
      function updateProducts() {
        const query = search.value.trim().toLowerCase();
        let visible = 0;
        cards.forEach(card => {
          const matches = card.dataset.name.includes(query) && (activeBrand === 'all' || card.dataset.brand === activeBrand);
          card.hidden = !matches;
          if (matches) visible++;
        });
        const order = sort.value;
        cards.sort((a,b) => order === 'price-low' ? Number(a.dataset.price)-Number(b.dataset.price) : order === 'price-high' ? Number(b.dataset.price)-Number(a.dataset.price) : order === 'name' ? a.dataset.name.localeCompare(b.dataset.name) : 0).forEach(card => grid.insertBefore(card, empty));
        if (empty) empty.hidden = visible > 0;
      }
      search?.addEventListener('input', updateProducts);
      sort?.addEventListener('change', updateProducts);
      document.querySelectorAll('[data-brand-filter]').forEach(button => button.addEventListener('click', () => {
        activeBrand = button.dataset.brandFilter;
        document.querySelectorAll('[data-brand-filter]').forEach(chip => chip.classList.toggle('active', chip === button));
        updateProducts();
      }));
      const currentVersion = document.getElementById('shop')?.dataset.inventoryVersion;
      if (currentVersion) {
        setInterval(async () => {
          try {
            const response = await fetch('{{ url_for("inventory_version_api") }}', {cache: 'no-store'});
            if (!response.ok) throw new Error(`Inventory check failed (${response.status})`);
            const data = await response.json();
            if (data.version !== currentVersion) location.reload();
          } catch (error) {
            console.error('Could not check for inventory updates:', error);
          }
        }, 15000);
      }
    </script>
    """
    brands = sorted({str(p.get("Brand") or "") for p in products if p.get("Brand")})
    return render_page(
        "Laptops, thoughtfully chosen", html, products=products,
        brands=brands, q=q, inventory_version=inventory_version(products)
    )


@app.route("/api/inventory/version")
def inventory_version_api():
    return jsonify(version=inventory_version())


# PRODUCT DETAILS
@app.route("/product/<product_id>")
def product(product_id):
    p = product_by_id(product_id)
    if not p:
        return "Laptop not found", 404

    return render_product_page(p)


def render_product_page(p, error="", values=None):
    values = values or {}
    available = str(p.get("Availability", "")).lower() in (
        "available", "in stock", "yes"
    )
    html = """
    <section class="container product-layout">
      <div>
        <div class="gallery-main">
          {% if p.Images %}<img data-gallery-main src="{{ url_for('uploaded_file', filename=p.Images[0]) }}" alt="{{ p.Brand }} {{ p.Model }} laptop">
          {% else %}
          <svg class="laptop-art" viewBox="0 0 400 260" role="img" aria-label="Laptop illustration"><defs><linearGradient id="screen-detail" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#baff70"/><stop offset=".48" stop-color="#8d74ed"/><stop offset="1" stop-color="#30304c"/></linearGradient><linearGradient id="base-detail" x2="0" y2="1"><stop stop-color="#d5d4e4"/><stop offset="1" stop-color="#626276"/></linearGradient></defs><rect x="61" y="25" width="278" height="184" rx="14" fill="#77778b"/><rect x="68" y="32" width="264" height="169" rx="9" fill="#181827"/><rect x="77" y="41" width="246" height="151" rx="5" fill="#202037"/><circle cx="200" cy="48" r="2" fill="#b9b8cb"/><rect x="96" y="62" width="55" height="6" rx="3" fill="#d8ff72"/><rect x="96" y="78" width="122" height="15" rx="4" fill="url(#screen-detail)"/><rect x="96" y="99" width="79" height="7" rx="3" fill="#86839f"/><rect x="96" y="123" width="65" height="48" rx="6" fill="#a186fb" opacity=".8"/><rect x="169" y="123" width="65" height="48" rx="6" fill="#d8ff72" opacity=".8"/><rect x="242" y="123" width="65" height="48" rx="6" fill="#65dce8" opacity=".8"/><path d="M37 213h326l30 19c4 3 2 9-5 9H12c-7 0-9-6-5-9l30-19Z" fill="url(#base-detail)"/><path d="M163 214h74l8 7h-90l8-7Z" fill="#77778b"/></svg>
          {% endif %}
        </div>
        {% if p.Images|length > 1 %}<div class="thumbs">{% for img in p.Images %}<button type="button" class="thumb" data-gallery-image="{{ url_for('uploaded_file', filename=img) }}" aria-label="View product image {{ loop.index }}"><img src="{{ url_for('uploaded_file', filename=img) }}" alt="" loading="lazy"></button>{% endfor %}</div>{% endif %}
      </div>
      <div class="product-detail">
        <a class="text-link" href="{{ url_for('home') }}#shop">← Back to collection</a>
        <div style="margin-top:24px"><span class="eyebrow">{{ p.Brand }} · {{ p.Availability }}</span></div>
        <h1>{{ p.Model }}</h1>
        <div class="product-brand">{{ p.Condition }}{% if p.Generation %} · {{ p.Generation }}{% endif %}</div>
        <div class="detail-price">Indicative · Rs. {{ "{:,}".format(p.Price) }}</div>
        {% if p.Description %}<p class="detail-description">{{ p.Description }}</p>{% else %}<p class="detail-description">Thoughtfully selected, carefully described, and ready for your next big idea.</p>{% endif %}
        <div class="spec-grid">
          <div class="spec"><small>Processor</small><b>{{ p.Processor or "—" }}</b></div>
          <div class="spec"><small>Memory</small><b>{{ p.RAM or "—" }}</b></div>
          <div class="spec"><small>Storage</small><b>{{ p.SSD or "—" }}</b></div>
          <div class="spec"><small>Display</small><b>{{ p.Screen or "—" }}</b></div>
        </div>
        <div class="detail-actions">
          {% if available %}<a class="button" href="#order-form">Order this MacBook ↘</a>{% endif %}
          <a class="button button-secondary" href="{{ whatsapp_link }}" target="_blank" rel="noopener noreferrer">Questions? WhatsApp us ↗</a>
        </div>
        {% if available %}
        <div class="form-card order-form" id="order-form">
          <h3>Place an order request</h3>
          <p class="muted" style="margin-top:-7px">Cash on delivery. We’ll confirm stock, condition, delivery, and final price on WhatsApp.</p>
          {% if error %}<p class="form-error" role="alert">{{ error }}</p>{% endif %}
          <form class="stack" method="post" action="{{ url_for('create_order', product_id=p.ID) }}">
            <label>Your name<input class="field" name="customer_name" maxlength="100" autocomplete="name" value="{{ values.get('customer_name','') }}" required></label>
            <label>Your WhatsApp number<input class="field" name="customer_phone" type="tel" maxlength="24" autocomplete="tel" placeholder="03xx xxxxxxx" value="{{ values.get('customer_phone','') }}" required></label>
            <label>Delivery address<textarea class="field" name="delivery_address" rows="3" maxlength="500" autocomplete="street-address" required>{{ values.get('delivery_address','') }}</textarea></label>
            <label>Quantity<select class="select" name="quantity">{% for quantity in range(1,6) %}<option value="{{ quantity }}" {% if values.get('quantity','1')|string == quantity|string %}selected{% endif %}>{{ quantity }}</option>{% endfor %}</select></label>
            <button class="button" type="submit">Continue to WhatsApp order ↗</button>
          </form>
        </div>
        {% else %}
        <div class="form-card"><h3>Currently unavailable</h3><p class="muted">This laptop is not marked available in the inventory sheet. Message us on WhatsApp to ask about restocking.</p></div>
        {% endif %}
      </div>
    </section>
    """
    return render_page(
        f"{p['Brand']} {p['Model']}", html, p=p, available=available,
        error=error, values=values,
        whatsapp_link=f"https://wa.me/{WHATSAPP}"
    )


@app.route("/order/<product_id>", methods=["POST"])
def create_order(product_id):
    product = product_by_id(product_id)
    if not product:
        return "Laptop not found", 404

    if str(product.get("Availability", "")).lower() not in (
        "available", "in stock", "yes"
    ):
        return render_product_page(
            product, error="This laptop is no longer available to order.",
            values=request.form
        ), 409

    name = request.form.get("customer_name", "").strip()[:100]
    phone = request.form.get("customer_phone", "").strip()[:24]
    address = request.form.get("delivery_address", "").strip()[:500]
    try:
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        quantity = 0

    error = ""
    if not name:
        error = "Enter your name to continue."
    elif len(re.sub(r"\D", "", phone)) < 9:
        error = "Enter a valid phone number so we can confirm your order."
    elif len(address) < 8:
        error = "Enter a complete delivery address."
    elif not 1 <= quantity <= 5:
        error = "Choose a quantity between 1 and 5."
    elif product["Price"] <= 0:
        error = "This item has no valid listed price. Please contact the seller."

    if error:
        return render_product_page(
            product, error=error,
            values={
                "customer_name": name,
                "customer_phone": phone,
                "delivery_address": address,
                "quantity": str(quantity or 1),
            }
        ), 400

    order_id = uuid.uuid4().hex[:12].upper()
    total_price = product["Price"] * quantity
    created_at = datetime.now().isoformat(timespec="seconds")
    with connection() as con:
        con.execute(
            """INSERT INTO orders(
                id,product_id,product_name,customer_name,customer_phone,
                delivery_address,quantity,unit_price,total_price,status,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,'Pending',?)""",
            (
                order_id, product["ID"], f"{product['Brand']} {product['Model']}",
                name, phone, address, quantity, product["Price"], total_price,
                created_at,
            )
        )

    return redirect(url_for("order_confirmation", order_id=order_id))


@app.route("/order/confirmation/<order_id>")
def order_confirmation(order_id):
    with connection() as con:
        order = con.execute(
            "SELECT * FROM orders WHERE id=?", (order_id,)
        ).fetchone()
    if not order:
        return "Order not found", 404

    message = (
        f"AK Apple Store order request {order['id']}\\n"
        f"Laptop: {order['product_name']}\\n"
        f"Quantity: {order['quantity']}\\n"
        f"Indicative total: Rs. {order['total_price']:,}\\n"
        f"Customer: {order['customer_name']}\\n"
        f"Customer WhatsApp: {order['customer_phone']}\\n"
        f"Delivery address: {order['delivery_address']}\\n"
        "Payment: Cash on delivery\\n"
        "Please confirm stock, configuration, final price, and delivery."
    )
    whatsapp_url = f"https://wa.me/{WHATSAPP}?text={quote(message)}"
    html = """
    <section class="auth-wrap"><div class="auth-card">
      <span class="eyebrow">Order request saved</span>
      <h1>One last step.</h1>
      <p>Your request <strong>#{{ order.id }}</strong> is saved. It is not confirmed until the seller replies on WhatsApp.</p>
      <div class="spec-grid">
        <div class="spec"><small>Laptop</small><b>{{ order.product_name }}</b></div>
        <div class="spec"><small>Quantity</small><b>{{ order.quantity }}</b></div>
        <div class="spec"><small>Indicative total</small><b>Rs. {{ "{:,}".format(order.total_price) }}</b></div>
        <div class="spec"><small>Payment</small><b>Cash on delivery</b></div>
      </div>
      <p class="muted">WhatsApp will open with your order details ready. Tap Send there to notify AK Apple Store at {{ whatsapp_display }}. No payment is taken online.</p>
      <a class="button" href="{{ whatsapp_url }}" target="_blank" rel="noopener noreferrer">Send order on WhatsApp ↗</a>
      <p><a class="text-link" href="{{ url_for('home') }}">Continue shopping</a></p>
    </div></section>
    """
    return render_page(
        f"Order {order_id}", html, order=order, whatsapp_url=whatsapp_url
    )


# ADMIN DASHBOARD
@app.route("/admin")
@admin_only
def dashboard():
    html = """
    <section class="admin-wrap">
      <div class="admin-heading"><div><span class="eyebrow">Seller portal</span><h1>Inventory, in control.</h1></div><a class="button button-secondary" href="{{ url_for('logout') }}">Sign out</a></div>
      <div class="admin-grid">
        <div class="panel"><h2>Add or update a laptop</h2>
          <form class="stack" method="post" action="{{ url_for('add_product') }}" enctype="multipart/form-data">
            <div class="admin-form-grid">{% for field in fields %}
              <label>{{ field }}<input class="field" name="{{ field }}" placeholder="{{ field }}" {% if field in ['ID','Brand','Model','Price'] %}required{% endif %}></label>
            {% endfor %}</div>
            <label>Availability<select class="select" name="Availability"><option>Available</option><option>Out of Stock</option></select></label>
            <label>Product photos<input class="field" type="file" name="images" multiple accept=".jpg,.jpeg,.png,.webp"></label>
            <button class="button" type="submit">Save laptop ↗</button>
          </form>
        </div>
        <div class="panel"><h2>Current inventory · {{ products|length }}</h2>
          {% for p in products %}<div class="inventory-item"><strong>{{ p.Brand }} {{ p.Model }}</strong><br><span class="muted">Rs. {{ "{:,}".format(p.Price) }} · {{ p.Availability }}</span></div>
          {% else %}<p class="muted">No laptops listed yet. Add the first one using the form.</p>{% endfor %}
          <a class="button button-secondary button-small" style="margin-top:18px" href="{{ url_for('admin_orders') }}">View orders ↗</a>
        </div>
      </div>
      <div class="panel" style="margin-top:18px">
        <h2>Connected inventory files</h2>
        <p class="muted">Edit the spreadsheet or add linked photos in these folders. The storefront checks for changes every 15 seconds.</p>
        <p class="muted" style="font-size:12px">Spreadsheet: <code>{{ excel_path }}</code><br>Photos: <code>{{ photos_path }}</code></p>
        <p class="muted" style="font-size:12px">To show a photo, enter its exact filename in that laptop's Images cell. Separate multiple filenames with commas.</p>
      </div>
    </section>
    """
    fields = [
        "ID", "Brand", "Model", "Processor", "Generation",
        "RAM", "SSD", "Screen", "Price", "Condition", "Description"
    ]
    return render_page(
        "Seller dashboard", html, fields=fields, products=get_products(),
        excel_path=str(EXCEL), photos_path=str(UPLOADS)
    )


@app.route("/admin/orders")
@admin_only
def admin_orders():
    with connection() as con:
        orders = con.execute(
            "SELECT * FROM orders ORDER BY created_at DESC"
        ).fetchall()

    html = """
    <section class="admin-wrap">
      <div class="admin-heading"><div><span class="eyebrow">Seller portal</span><h1>Customer orders.</h1></div><a class="button button-secondary" href="{{ url_for('dashboard') }}">← Inventory</a></div>
      <div class="panel" style="margin-top:22px"><h2>Order requests · {{ orders|length }}</h2>
        {% for order in orders %}
        <article class="order-admin-card">
          <div class="order-admin-heading"><div><span class="eyebrow">#{{ order.id }}</span><h3>{{ order.product_name }}</h3></div><span class="order-status">{{ order.status }}</span></div>
          <div class="order-admin-details">
            <span><b>Customer</b>{{ order.customer_name }}</span>
            <span><b>WhatsApp</b><a href="https://wa.me/{{ order.customer_whatsapp }}" target="_blank" rel="noopener noreferrer">{{ order.customer_phone }} ↗</a></span>
            <span><b>Quantity</b>{{ order.quantity }}</span>
            <span><b>Indicative total · COD</b>Rs. {{ "{:,}".format(order.total_price) }}</span>
            <span><b>Delivery address</b>{{ order.delivery_address }}</span>
            <span><b>Received</b>{{ order.created_at }}</span>
          </div>
          <form method="post" action="{{ url_for('update_order_status', order_id=order.id) }}" class="order-status-form">
            <label>Status<select class="select" name="status">
              {% for status in statuses %}<option {% if status == order.status %}selected{% endif %}>{{ status }}</option>{% endfor %}
            </select></label>
            <button class="button button-secondary button-small" type="submit">Update status</button>
          </form>
        </article>
        {% else %}<p class="muted">No orders yet. New customer requests will appear here.</p>{% endfor %}
      </div>
    </section>
    """
    enriched_orders = []
    for row in orders:
        order = dict(row)
        order["customer_whatsapp"] = normalize_phone_number(
            order["customer_phone"]
        )
        enriched_orders.append(order)
    return render_page(
        "Customer orders", html, orders=enriched_orders,
        statuses=("Pending", "Confirmed", "Completed", "Cancelled")
    )


@app.route("/admin/orders/<order_id>/status", methods=["POST"])
@admin_only
def update_order_status(order_id):
    status = request.form.get("status", "")
    if status not in ("Pending", "Confirmed", "Completed", "Cancelled"):
        return "Invalid order status", 400

    with connection() as con:
        cursor = con.execute(
            "UPDATE orders SET status=? WHERE id=?", (status, order_id)
        )
        if cursor.rowcount == 0:
            return "Order not found", 404

    return redirect(url_for("admin_orders"))


@app.route("/admin/add", methods=["POST"])
@admin_only
def add_product():
    product_id = request.form.get("ID", "").strip()
    if not product_id:
        return "ID required", 400

    old = next(
        (p for p in get_products() if p["ID"] == product_id),
        None
    )

    images = []
    for f in request.files.getlist("images"):
        if not f or not f.filename:
            continue

        filename = secure_filename(f.filename)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ALLOWED:
            continue

        name = uuid.uuid4().hex + "." + ext
        f.save(UPLOADS / name)
        images.append(name)

    data = {k: request.form.get(k, "") for k in COLUMNS}
    data["ID"] = product_id
    data["Availability"] = request.form.get(
        "Availability", "Available"
    )
    data["Images"] = ",".join(
        images or (old["Images"] if old else [])
    )

    save_product(data)
    return redirect("/admin")


# Legacy chat data is retained in SQLite, but the chat screens and API are no longer routed.
@admin_only
def admin_chats():
    html = """
    <section class="admin-wrap"><div class="admin-heading"><div><span class="eyebrow">Seller portal</span><h1>Customer conversations.</h1></div><a class="button button-secondary" href="{{ url_for('dashboard') }}">← Inventory</a></div>
      <div class="admin-grid">
        <div class="panel"><h2>Your customers</h2><div class="chat-list" id="list"></div></div>
        <div class="panel"><h2>Messages</h2><div class="chat-product" id="chat-product" aria-live="polite"><div><strong>Select a conversation</strong><p>Current laptop details and availability will appear here.</p></div></div><p class="chat-status" id="admin-chat-status" role="status" aria-live="polite"></p><div class="chat-box" id="messages" aria-live="polite"></div>
          <form class="form-row" id="reply" style="margin-top:12px">
            <input class="field" id="answer" placeholder="Write a reply" aria-label="Write a reply" required>
            <button class="button" id="reply-button" type="submit">Send ↗</button>
          </form>
        </div>
      </div>
    </section>
    <script>
    let selected=new URLSearchParams(location.search).get('id');
    let last=0;
    const adminStatus=document.getElementById('admin-chat-status');
    function setAdminError(message=''){adminStatus.textContent=message;}
    async function load(){
      const response=await fetch('{{ url_for("admin_chat_list") }}',{cache:'no-store'});
      const data=await response.json();
      if(!response.ok)throw new Error(data.error||'Could not load customer chats.');
      const box=document.getElementById('list');
      const listKey=JSON.stringify(data);
      if(box.dataset.listKey!==listKey){
        box.dataset.listKey=listKey;
        box.replaceChildren();
        data.forEach(chat=>{
          const link=document.createElement('a');
          link.href='{{ url_for("admin_chats") }}?id='+encodeURIComponent(chat.chat_id);
          const name=document.createElement('strong');
          name.textContent=chat.name;
          const product=document.createElement('span');
          product.textContent=chat.product_name
            ? chat.product_name+' · '+chat.availability
            : chat.product_id?'Laptop no longer in inventory':'General inquiry · no linked laptop';
          link.append(name,product);
          box.appendChild(link);
        });
      }
      if(selected){
        const chat=data.find(item=>item.chat_id===selected);
        if(!chat)throw new Error('This customer chat was not found.');
        updateAdminProduct(chat);
        const messageResponse=await fetch('{{ url_for("admin_messages", chat_id="CHAT_ID") }}'.replace('CHAT_ID',encodeURIComponent(selected)),{cache:'no-store'});
        const messages=await messageResponse.json();
        if(!messageResponse.ok)throw new Error(messages.error||'Could not load this conversation.');
        messages.forEach(message=>{
          if(message.id>last){
            const item=document.createElement('p');
            item.className='chat-message '+(message.sender==='admin'?'admin':'customer');
            const sender=document.createElement('strong');
            sender.textContent=message.sender==='admin'?'AK Apple Store':chat.name;
            const content=document.createElement('span');
            content.textContent=message.message;
            item.append(sender,content);
            document.getElementById('messages').appendChild(item);
            last=message.id;
          }
        });
        const messageBox=document.getElementById('messages');
        messageBox.scrollTop=messageBox.scrollHeight;
      }else{
        updateAdminProduct(null);
      }
    }
    function updateAdminProduct(chat){
      const panel=document.getElementById('chat-product');
      const contextKey=JSON.stringify(chat&&{
        product_id:chat.product_id,
        product_name:chat.product_name,
        availability:chat.availability,
        available:chat.available
      });
      if(panel.dataset.contextKey===contextKey)return;
      panel.dataset.contextKey=contextKey;
      panel.replaceChildren();
      const details=document.createElement('div');
      const title=document.createElement('strong');
      const description=document.createElement('p');
      const badge=document.createElement('span');
      badge.className='chat-product-status';
      if(chat&&chat.product_name){
        title.textContent=chat.product_name;
        description.textContent='Availability is read live from laptops.xlsx. Confirm the exact unit and indicative price with the customer.';
        badge.textContent=chat.availability;
        if(!chat.available)badge.classList.add('unavailable');
      }else if(chat&&chat.product_id){
        title.textContent='Laptop no longer listed';
        description.textContent='This item was removed from laptops.xlsx. The conversation remains available.';
        badge.textContent='Not in inventory';
        badge.classList.add('unavailable');
      }else{
        title.textContent=chat?'General store inquiry':'Select a conversation';
        description.textContent=chat?'No specific laptop is linked to this conversation.':'Current laptop details and availability will appear here.';
        badge.textContent='Live inventory';
      }
      details.append(title,description);
      panel.append(details,badge);
    }
    document.getElementById('reply').addEventListener('submit',async e=>{
      e.preventDefault();
      const input=document.getElementById('answer');
      const button=document.getElementById('reply-button');
      if(!selected){setAdminError('Select a customer before sending a reply.');return;}
      if(!input.value.trim())return;
      button.disabled=true;
      setAdminError('');
      try{
        const response=await fetch('{{ url_for("admin_reply") }}',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({chat_id:selected,message:input.value})
        });
        const data=await response.json();
        if(!response.ok)throw new Error(data.error||'Reply could not be sent.');
        input.value='';
        await load();
      }catch(error){setAdminError(error.message);}
      finally{button.disabled=false;input.focus();}
    });
    async function pollChats(){
      try{await load();setAdminError('');}
      catch(error){setAdminError(error.message);}
    }
    pollChats();setInterval(pollChats,2500);
    </script>
    """
    return render_page("Customer chats", html)


@admin_only
def admin_chat_list():
    with connection() as con:
        rows = con.execute("""
        SELECT c.chat_id,c.name,c.product_id,MAX(m.id) last_message
        FROM customers c LEFT JOIN messages m
        ON c.chat_id=m.chat_id
        GROUP BY c.chat_id ORDER BY last_message DESC
        """).fetchall()

    products = {product["ID"]: product for product in get_products()}
    chats = []
    for row in rows:
        chat = dict(row)
        product = products.get(chat["product_id"])
        chat["product_name"] = (
            f'{product["Brand"]} {product["Model"]}' if product else None
        )
        chat["availability"] = (
            str(product.get("Availability") or "Status not set")
            if product else "Not in inventory"
        )
        chat["available"] = chat["availability"].lower() in (
            "available", "in stock", "yes"
        )
        chats.append(chat)

    return jsonify(chats)


@admin_only
def admin_messages(chat_id):
    with connection() as con:
        rows = con.execute(
            "SELECT * FROM messages WHERE chat_id=? ORDER BY id",
            (chat_id,)
        ).fetchall()

    return jsonify([dict(r) for r in rows])


@admin_only
def admin_reply():
    data = request.json or {}
    chat_id = data.get("chat_id", "")
    message = data.get("message", "").strip()[:2000]

    if not message:
        return jsonify(error="Empty message"), 400

    with connection() as con:
        exists = con.execute(
            "SELECT 1 FROM customers WHERE chat_id=?", (chat_id,)
        ).fetchone()

        if not exists:
            return jsonify(error="Unknown customer"), 404

        con.execute(
            "INSERT INTO messages(chat_id,sender,message,created_at) VALUES (?,?,?,?)",
            (chat_id, "admin", message, datetime.now().isoformat())
        )

    return jsonify(ok=True)


# IMAGE ROUTE
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOADS, filename)


# RUN WEBSITE
if __name__ == "__main__":
    init_excel()
    init_db()

    print("Laptop Store running at http://127.0.0.1:5000")
    print("Admin: http://127.0.0.1:5000/admin/login")

    import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5053))
    app.run(host="0.0.0.0", port=port)
