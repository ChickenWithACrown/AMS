import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import json
import os
import sys
import re
import time

from concurrent.futures import ThreadPoolExecutor
from dateutil.relativedelta import relativedelta
from PIL import Image, ImageTk, ImageDraw, ImageFont
import pyrebase
from dotenv import load_dotenv

from firebase_config import FirebaseManager
import threading

load_dotenv()

class AFJROTCApp:
    def _init_styles(self):
        # Modern color palette
        self.primary_color = "#2563eb"    # Vibrant blue
        self.primary_light = "#3b82f6"   # Lighter blue
        self.primary_dark = "#1d4ed8"    # Darker blue
        self.secondary_color = "#64748b"  # Cool gray
        self.accent_color = "#0ea5e9"    # Sky blue
        self.success_color = "#10b981"   # Emerald
        self.warning_color = "#f59e0b"   # Amber
        self.danger_color = "#ef4444"    # Red
        
        # Neutral colors
        self.bg_color = "#f8fafc"        # Lightest gray
        self.card_bg = "#ffffff"          # White
        self.border_color = "#e2e8f0"     # Light gray border
        self.text_primary = "#1e293b"     # Dark slate
        self.text_secondary = "#64748b"   # Slate
        self.text_light = "#94a3b8"       # Light slate
        
        # Typography
        self.font_family = "Inter" if 'Inter' in [f for f in tk.font.families()] else "Segoe UI"
        self.display_font = (self.font_family, 32, "bold")
        self.title_font = (self.font_family, 24, "bold")
        self.subtitle_font = (self.font_family, 16, "normal")
        self.button_font = (self.font_family, 14, "medium")
        self.text_font = (self.font_family, 14, "normal")
        self.small_text = (self.font_family, 12, "normal")
        
        # Spacing system (in pixels)
        self.space_xxs = 4
        self.space_xs = 8
        self.space_sm = 12
        self.space_md = 16
        self.space_lg = 24
        self.space_xl = 32
        self.space_xxl = 48
        
        # Border radius
        self.radius_sm = 6
        self.radius_md = 8
        self.radius_lg = 12
        self.radius_xl = 16
        
        # Shadows (for elevation)
        self.shadow_sm = ("2px 2px 4px rgba(0,0,0,0.05)", "2px 2px 4px rgba(0,0,0,0.1)")
        self.shadow_md = ("4px 4px 8px rgba(0,0,0,0.06)", "4px 4px 8px rgba(0,0,0,0.12)")
        self.shadow_lg = ("8px 8px 16px rgba(0,0,0,0.08)", "8px 8px 16px rgba(0,0,0,0.16)")
        
        # Configure CTk theme
        ctk.set_appearance_mode("light")
        
        # Base theme overrides
        theme = ctk.ThemeManager.theme
        
        # Button styles
        theme["CTkButton"]["corner_radius"] = self.radius_md
        theme["CTkButton"]["border_width"] = 0
        theme["CTkButton"]["fg_color"] = self.primary_color
        theme["CTkButton"]["hover_color"] = self.primary_dark
        theme["CTkButton"]["text_color"] = "#ffffff"
        theme["CTkButton"]["font"] = self.button_font
        theme["CTkButton"]["border_spacing"] = self.space_md
        
        # Entry styles
        theme["CTkEntry"]["corner_radius"] = self.radius_md
        theme["CTkEntry"]["border_width"] = 1
        theme["CTkEntry"]["fg_color"] = "#ffffff"
        theme["CTkEntry"]["border_color"] = self.border_color
        theme["CTkEntry"]["text_color"] = self.text_primary
        theme["CTkEntry"]["placeholder_text_color"] = self.text_light
        theme["CTkEntry"]["font"] = self.text_font
        
        # Label styles
        theme["CTkLabel"]["font"] = self.text_font
        theme["CTkLabel"]["text_color"] = self.text_primary
        
        # Frame styles
        theme["CTkFrame"]["corner_radius"] = self.radius_lg
        theme["CTkFrame"]["border_width"] = 0
        theme["CTkFrame"]["fg_color"] = self.card_bg
        
        # Configure ttk style
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TButton",
            font=self.button_font,
            padding=(self.space_md, self.space_sm),
            relief="flat",
            background=self.primary_color,
            foreground="#ffffff",
            borderwidth=0,
            focuscolor="none"
        )
        style.map("TButton",
            background=[("active", self.primary_dark)],
            foreground=[("active", "#ffffff")]
        )
        
        self.root.configure(background=self.bg_color)
        
        self.pad_x = self.space_md
        self.pad_y = self.space_sm
        self.pad_sm = self.space_sm
        self.pad_md = self.space_md
        self.pad_lg = self.space_lg
        
        self.button_height = 44
        self.input_height = 44
        self.icon_size = 20
        
    def __init__(self, root):
        self.root = root
        self.root.title("AFJROTC Management System (AMS)")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        self._init_styles()
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.firebase = FirebaseManager()
        self.current_user = None
        
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        self.events = {}
        self.jobs = {}
        self.cadets = {}
        self.fundraisers = {}
        self.contacts = {}
        self.upcoming_events = []
        self.fundraiser_participants = {}
        
        self.sidebar = None
        self.main_container = None
        self.content_frame = None
        self.auth_frame = None
        
        self.loading_frame = ctk.CTkFrame(self.root, fg_color="white")
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="Loading...", font=("Arial", 24), text_color=self.primary_color)
        
        try:
            if os.path.exists("logo.png"):
                self.logo_img = ctk.CTkImage(
                    light_image=Image.open("logo.png"),
                    dark_image=Image.open("logo.png"),
                    size=(100, 100)
                )
            else:
                self.logo_img = None
        except Exception as e:
            print(f"Error loading logo: {e}")
            self.logo_img = None
            
        self.edit_icon_text = "✏️"
        self.delete_icon_text = "❌"
        self.edit_icon = None
        self.delete_icon = None
        
        self.show_startup_screen()
        
    def create_icon(self, master, text, color):
        return ctk.CTkLabel(
            master=master,
            text=text,
            text_color=color,
            font=("Arial", 14)
        )
        
    def clear_content_frame(self):
        if hasattr(self, 'content_frame') and self.content_frame:
            for widget in self.content_frame.winfo_children():
                widget.destroy()
                
    def update_dashboard(self, force_update=False):
        try:
            if hasattr(self, '_updating_dashboard') and self._updating_dashboard:
                return
                
            self._updating_dashboard = True
            
            self._update_dashboard_stats()
            
            if hasattr(self, 'show_dashboard') and not hasattr(self, 'current_view') or self.current_view != 'dashboard':
                self.show_dashboard()
                
        except Exception as e:
            print(f"Error updating dashboard: {e}")
        finally:
            self._updating_dashboard = False
            
    def _update_dashboard_stats(self):
        try:
            if not hasattr(self, 'content_frame') or not self.content_frame:
                return
                
            if hasattr(self, 'cadets'):
                cadet_count = len(self.cadets)
                if hasattr(self, 'cadet_count_label'):
                    self.cadet_count_label.configure(text=str(cadet_count))
            
        except Exception as e:
            print(f"Error updating dashboard stats: {e}")
            
    def setup_realtime_listeners(self):
        if not hasattr(self, '_listeners') or not isinstance(self._listeners, dict):
            self._listeners = {}
        
        def create_callback(collection_name, update_methods=None):
            update_methods = update_methods or []
            
            def callback(message):
                try:
                    if message.get("event") in ["put", "patch"]:
                        data = message.get("data") or {}
                        
                        if hasattr(self, collection_name):
                            if isinstance(data, list):
                                setattr(self, collection_name, 
                                       {item.get('id', idx): item for idx, item in enumerate(data) if item})
                            else:
                                setattr(self, collection_name, data)
                        
                        for method_name in update_methods:
                            if hasattr(self, method_name):
                                self.root.after(0, getattr(self, method_name))
                                
                except Exception as e:
                    error_msg = f"Error in {collection_name} callback: {str(e)}"
                    print(error_msg)
                    self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            
            return callback
        
        try:
            listeners_config = {
                "cadets": ["update_cadets_display", "update_dashboard"],
                "jobs": ["update_jobs_display", "update_dashboard"],
                "events": ["update_calendar_display", "update_upcoming_events", "update_dashboard"],
                "fundraisers": ["update_fundraisers_display", "update_dashboard"],
                "contacts": ["update_contacts_display"]
            }
            
            for collection, methods in listeners_config.items():
                if collection in self._listeners:
                    try:
                        self._listeners[collection]()
                    except Exception as e:
                        print(f"Error removing {collection} listener: {e}")
                
                callback = create_callback(collection, methods)
                self._listeners[collection] = self.firebase.db.child(collection).stream(callback)
            
        except Exception as e:
            error_msg = f"Error setting up real-time listeners: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def cleanup(self):
        try:
            if hasattr(self, '_listeners'):
                for name, listener in self._listeners.items():
                    try:
                        if callable(listener):
                            listener()
                    except Exception as e:
                        print(f"Error cleaning up {name} listener: {e}")
                self._listeners.clear()
            
            if hasattr(self, 'executor'):
                try:
                    self.executor.shutdown(wait=False)
                except Exception as e:
                    print(f"Error shutting down executor: {e}")
            
            if hasattr(self, 'root'):
                for after_id in getattr(self, '_after_ids', []):
                    try:
                        self.root.after_cancel(after_id)
                    except:
                        pass
        
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            if hasattr(self, 'root') and self.root:
                try:
                    self.root.destroy()
                except:
                    pass
            
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.main_container, 
            fg_color=self.primary_color, 
            width=260,
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0, ipadx=0, ipady=0)
        self.sidebar.pack_propagate(False)
        
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(20, 15), padx=15, fill="x")
        
        if hasattr(self, 'logo_img'):
            logo_bg = ctk.CTkFrame(logo_frame, fg_color="#ffffff20", corner_radius=8)
            logo_bg.pack(pady=(0, 10), padx=10, fill="x")
            logo_label = ctk.CTkLabel(logo_bg, image=self.logo_img, text="")
            logo_label.pack(padx=10, pady=10)
            
        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(5, 0))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="AFJROTC",
            font=("Arial Bold", 22),
            text_color="#ffffff"
        )
        title_label.pack(side="left")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="AMS",
            font=("Arial Bold", 18),
            text_color=self.accent_color
        )
        subtitle_label.pack(side="left", padx=(5, 0))
        
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        nav_buttons = [
            ("🏠", "Dashboard", self.show_dashboard),
            ("👥", "Cadets", self.show_cadets),
            ("👕", "Uniforms", self.show_uniforms),
            ("📅", "Events", self.show_calendar),
            ("💰", "Fundraisers", self.show_fundraisers),
            ("📋", "Jobs", self.show_jobs),
            ("📞", "Contacts", self.show_contacts),
            ("📊", "Reports", self.show_reports)
        ]
        
        for icon, text, command in nav_buttons:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icon}  {text}",
                command=command,
                fg_color="transparent",
                hover_color="#1a4b8c",
                anchor="w",
                height=42,
                font=("Arial", 14, "bold"),
                text_color="#ffffff",
                corner_radius=6,
                border_spacing=10
            )
            btn.pack(fill="x", padx=5, pady=2)
        
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 15))
        
        settings_btn = ctk.CTkButton(
            bottom_frame,
            text="⚙️  Settings",
            command=self.show_settings,
            fg_color="#2c3e50",
            hover_color="#34495e",
            height=38,
            font=("Arial", 13, "bold"),
            text_color="#ffffff",
            corner_radius=6
        )
        settings_btn.pack(fill="x", pady=(0, 5))
        
        help_btn = ctk.CTkButton(
            bottom_frame,
            text="❓  Help",
            command=self.show_help,
            fg_color="#2c3e50",
            hover_color="#34495e",
            height=38,
            font=("Arial", 13, "bold"),
            text_color="#ffffff",
            corner_radius=6
        )
        help_btn.pack(fill="x", pady=(0, 10))
        
        logout_btn = ctk.CTkButton(
            bottom_frame,
            text="🚪  Logout",
            command=self.logout,
            fg_color="#8B0000",
            hover_color="#6B0000",
            height=42,
            font=("Arial Bold", 14),
            text_color="#ffffff",
            corner_radius=6
        )
        logout_btn.pack(fill="x", pady=(5, 0))
        
    def load_logo(self):
        try:
            if os.path.exists("logo.png"):
                return ctk.CTkImage(
                    light_image=Image.open("logo.png"),
                    dark_image=Image.open("logo.png"),
                    size=(100, 100)
                )
            return None
        except Exception as e:
            print(f"Error loading logo: {e}")
            return None

    def show_startup_screen(self):
        self.loading_frame.pack(fill="both", expand=True)
        self.loading_label.pack(expand=True)
        
        self.root.after(1000, self.check_session)

    def check_session(self):
        try:
            user = self.firebase.auth.current_user
            if user:
                self.current_user = user
                self.after_login()
            else:
                self.show_login()
        except Exception as e:
            print(f"Session check error: {e}")
            self.show_login()

    def show_login(self):
        """Display the modern login screen."""
        self.clear_auth_frame()
        
        # Main auth container with subtle gradient background
        self.auth_frame = ctk.CTkFrame(self.root, fg_color=self.bg_color)
        self.auth_frame.pack(fill="both", expand=True)
        
        # Center container for the login card
        center_frame = ctk.CTkFrame(self.auth_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Login card with subtle shadow
        card = ctk.CTkFrame(
            center_frame, 
            fg_color=self.card_bg,
            corner_radius=self.radius_xl,
            border_width=1,
            border_color=self.border_color
        )
        card.pack(padx=self.space_xl, pady=self.space_xl, ipadx=self.space_xl, ipady=self.space_xl)
        
        # Logo and welcome section
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(pady=(0, self.space_xl))
        
        # Logo with circular background
        if hasattr(self, 'logo_img'):
            logo_bg = ctk.CTkFrame(
                header_frame, 
                fg_color=f"{self.primary_color}15",  # 10% opacity
                width=80, 
                height=80,
                corner_radius=40
            )
            logo_bg.pack(pady=(0, self.space_md))
            logo_bg.pack_propagate(False)
            
            logo_label = ctk.CTkLabel(
                logo_bg, 
                image=self.logo_img, 
                text="",
                fg_color="transparent"
            )
            logo_label.pack(expand=True)
        
        # Title and subtitle
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack()
        
        ctk.CTkLabel(
            title_frame,
            text="Welcome Back",
            font=self.title_font,
            text_color=self.text_primary
        ).pack(pady=(0, self.space_xs))
        
        ctk.CTkLabel(
            title_frame,
            text="Sign in to continue to AFJROTC AMS",
            font=self.subtitle_font,
            text_color=self.text_secondary
        ).pack()
        
        # Login form
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, pady=(self.space_xl, 0))
        
        # Email field
        email_container = ctk.CTkFrame(form_frame, fg_color="transparent")
        email_container.pack(fill="x", pady=(0, self.space_md))
        
        ctk.CTkLabel(
            email_container, 
            text="Email Address", 
            font=self.small_text,
            text_color=self.text_primary,
            anchor="w"
        ).pack(fill="x", pady=(0, self.space_xs))
        
        self.email_entry = ctk.CTkEntry(
            email_container,
            placeholder_text="you@example.com",
            width=320,
            height=self.input_height,
            font=self.text_font,
            fg_color="#ffffff",
            border_color=self.border_color,
            border_width=1,
            text_color=self.text_primary,
            corner_radius=self.radius_md,
            placeholder_text_color=self.text_light
        )
        self.email_entry.pack(fill="x")
        
        # Password field
        password_container = ctk.CTkFrame(form_frame, fg_color="transparent")
        password_container.pack(fill="x", pady=(0, self.space_md))
        
        password_header = ctk.CTkFrame(password_container, fg_color="transparent")
        password_header.pack(fill="x")
        
        ctk.CTkLabel(
            password_header, 
            text="Password", 
            font=self.small_text,
            text_color=self.text_primary,
            anchor="w"
        ).pack(side="left")
        
        # Forgot password link (placeholder)
        ctk.CTkLabel(
            password_header,
            text="Forgot password?",
            font=(self.small_text[0], self.small_text[1], "underline"),
            text_color=self.primary_color,
            cursor="hand2",
            anchor="e"
        ).pack(side="right")
        
        self.password_entry = ctk.CTkEntry(
            password_container,
            placeholder_text="••••••••",
            width=320,
            height=self.input_height,
            font=self.text_font,
            show="•",
            fg_color="#ffffff",
            border_color=self.border_color,
            border_width=1,
            text_color=self.text_primary,
            corner_radius=self.radius_md,
            placeholder_text_color=self.text_light
        )
        self.password_entry.pack(fill="x", pady=(self.space_xs, 0))
        
        # Login button
        login_btn = ctk.CTkButton(
            form_frame,
            text="Sign In",
            command=self.handle_login,
            width="100%",
            height=self.button_height,
            font=self.button_font,
            fg_color=self.primary_color,
            hover_color=self.primary_dark,
            text_color="#ffffff",
            corner_radius=self.radius_md,
            border_spacing=self.space_md
        )
        login_btn.pack(pady=(self.space_xl, self.space_md))
        
        # Sign up prompt
        signup_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        signup_frame.pack()
        
        ctk.CTkLabel(
            signup_frame,
            text="Don't have an account?",
            font=self.small_text,
            text_color=self.text_secondary
        ).pack(side="left")
        
        signup_link = ctk.CTkLabel(
            signup_frame,
            text=" Create account",
            font=(self.small_text[0], self.small_text[1], "bold"),
            text_color=self.primary_color,
            cursor="hand2"
        )
        signup_link.pack(side="left")
        signup_link.bind("<Button-1>", lambda e: self.show_signup())
        
        # Set focus to email field after a short delay
        self.root.after(100, lambda: self.email_entry.focus())
        
        # Bind Enter key to login
        self.password_entry.bind("<Return>", lambda e: self.handle_login())

def show_signup(self):
    """Display the modern signup screen."""
    self.clear_auth_frame()
    
    # Main auth container with subtle gradient background
    self.auth_frame = ctk.CTkFrame(self.root, fg_color=self.bg_color)
    self.auth_frame.pack(fill="both", expand=True)
    
    # Center container for the signup card
    center_frame = ctk.CTkFrame(self.auth_frame, fg_color="transparent")
    center_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    # Signup card with subtle shadow
    card = ctk.CTkFrame(
        center_frame, 
        fg_color=self.card_bg,
        corner_radius=self.radius_xl,
        border_width=1,
        border_color=self.border_color
    )
    card.pack(padx=self.space_xl, pady=self.space_xl, ipadx=self.space_xl, ipady=self.space_xl)
    
    # Logo and welcome section
    header_frame = ctk.CTkFrame(card, fg_color="transparent")
    header_frame.pack(pady=(0, self.space_xl))
    
    # Logo with circular background
    if hasattr(self, 'logo_img'):
        logo_bg = ctk.CTkFrame(
            header_frame, 
            fg_color=f"{self.primary_color}15",
            width=80, 
            height=80,
            corner_radius=40
        )
        logo_bg.pack(pady=(0, self.space_md))
        logo_bg.pack_propagate(False)
        
        logo_label = ctk.CTkLabel(
            logo_bg, 
            image=self.logo_img, 
            text="",
            fg_color="transparent"
        )
        logo_label.pack(expand=True)
    
    # Title and subtitle
    title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    title_frame.pack()
    
    ctk.CTkLabel(
        title_frame,
        text="Create Account",
        font=self.title_font,
        text_color=self.primary_color
    ).pack(pady=(0, self.space_xs))
    
    ctk.CTkLabel(
        title_frame,
        text="Join AFJROTC AMS today",
        font=self.subtitle_font,
        text_color=self.text_secondary
    ).pack()
    
    # Signup form
    form_frame = ctk.CTkFrame(card, fg_color="transparent")
    form_frame.pack(fill="both", expand=True, pady=(self.space_xl, 0))
    
    # Name field
    name_container = ctk.CTkFrame(form_frame, fg_color="transparent")
    name_container.pack(fill="x", pady=(0, self.space_md))
    
    ctk.CTkLabel(
        name_container, 
        text="Full Name", 
        font=self.small_text,
        text_color=self.text_primary,
        anchor="w"
    ).pack(fill="x", pady=(0, self.space_xs))
    
    self.signup_name = ctk.CTkEntry(
        name_container,
        placeholder_text="Enter your full name",
        width=320,
        height=self.input_height,
        font=self.text_font,
        fg_color="#ffffff",
        border_color=self.border_color,
        border_width=1,
        text_color=self.text_primary,
        corner_radius=self.radius_md,
        placeholder_text_color=self.text_light
    )
    self.signup_name.pack(fill="x")
    
    # Email field
    email_container = ctk.CTkFrame(form_frame, fg_color="transparent")
    email_container.pack(fill="x", pady=(0, self.space_md))
    
    ctk.CTkLabel(
        email_container, 
        text="Email Address", 
        font=self.small_text,
        text_color=self.text_primary,
        anchor="w"
    ).pack(fill="x", pady=(0, self.space_xs))
    
    self.signup_email = ctk.CTkEntry(
        email_container,
        placeholder_text="your.email@example.com",
        width=320,
        height=self.input_height,
        font=self.text_font,
        fg_color="#ffffff",
        border_color=self.border_color,
        border_width=1,
        text_color=self.text_primary,
        corner_radius=self.radius_md,
        placeholder_text_color=self.text_light
    )
    self.signup_email.pack(fill="x")
    
    # Password field
    password_container = ctk.CTkFrame(form_frame, fg_color="transparent")
    password_container.pack(fill="x", pady=(0, self.space_md))
    
    ctk.CTkLabel(
        password_container, 
        text="Password", 
        font=self.small_text,
        text_color=self.text_primary,
        anchor="w"
    ).pack(fill="x", pady=(0, self.space_xs))
    
    self.signup_password = ctk.CTkEntry(
        password_container,
        placeholder_text="Create a strong password",
        show="•",
        width=320,
        height=self.input_height,
        font=self.text_font,
        fg_color="#ffffff",
        border_color=self.border_color,
        border_width=1,
        text_color=self.text_primary,
        corner_radius=self.radius_md,
        placeholder_text_color=self.text_light
    )
    self.signup_password.pack(fill="x")
    
    # Confirm Password field
    confirm_container = ctk.CTkFrame(form_frame, fg_color="transparent")
    confirm_container.pack(fill="x", pady=(0, self.space_xl))
    
    ctk.CTkLabel(
        confirm_container, 
        text="Confirm Password", 
        font=self.small_text,
        text_color=self.text_primary,
        anchor="w"
    ).pack(fill="x", pady=(0, self.space_xs))
    
    self.signup_confirm_password = ctk.CTkEntry(
        confirm_container,
        placeholder_text="Confirm your password",
        show="•",
        width=320,
        height=self.input_height,
        font=self.text_font,
        fg_color="#ffffff",
        border_color=self.border_color,
        border_width=1,
        text_color=self.text_primary,
        corner_radius=self.radius_md,
        placeholder_text_color=self.text_light
    )
    self.signup_confirm_password.pack(fill="x")
    
    # Sign Up button
    signup_btn = ctk.CTkButton(
        form_frame,
        text="Create Account",
        command=self.handle_signup,
        width="100%",
        height=self.button_height,
        font=self.button_font,
        fg_color=self.primary_color,
        hover_color=self.primary_dark,
        text_color="#ffffff",
        corner_radius=self.radius_md,
        border_spacing=self.space_md
    )
    signup_btn.pack(pady=(self.space_xl, self.space_md))
    
    # Login prompt
    login_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
    login_frame.pack()
    
    ctk.CTkLabel(
        login_frame,
        text="Already have an account?",
        font=self.small_text,
        text_color=self.text_secondary
    ).pack(side="left")
    
    login_link = ctk.CTkLabel(
        login_frame,
        text=" Sign in",
        font=(self.small_text[0], self.small_text[1], "bold"),
        text_color=self.primary_color,
        cursor="hand2"
    )
    login_link.pack(side="left")
    login_link.bind("<Button-1>", lambda e: self.show_login())
    
    # Set focus to name field after a short delay
    self.root.after(100, lambda: self.signup_name.focus())
    
    # Bind Enter key to signup
    self.signup_confirm_password.bind("<Return>", lambda e: self.handle_signup())

def handle_signup(self):
    """Handle user signup."""
    name = self.signup_name.get().strip()
    email = self.signup_email.get().strip()
    password = self.signup_password.get()
    confirm_password = self.signup_confirm_password.get()
    
    # Basic validation
    if not name or not email or not password or not confirm_password:
        messagebox.showerror("Error", "All fields are required")
        return
        
    if password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match")
        return
        
    if len(password) < 8:
        messagebox.showerror("Error", "Password must be at least 8 characters long")
        return
    
    try:
        # Show loading state
        self.show_loading("Creating your account...")
        
        # Create user with Firebase Authentication
        user = self.firebase.auth.create_user_with_email_and_password(email, password)
        
        # Create user document in Firestore
        user_data = {
            'uid': user['localId'],
            'email': email,
            'displayName': name,
            'createdAt': datetime.now().isoformat(),
            'role': 'user'  # Default role
        }
        
        # Save additional user data to Firestore
        self.firebase.db.child("users").child(user['localId']).set(user_data)
        
        # Sign in the user
        self.current_user = user
        self.after_login()
        
    except Exception as e:
        error_msg = str(e)
        if "EMAIL_EXISTS" in error_msg:
            messagebox.showerror("Error", "An account with this email already exists")
        elif "INVALID_EMAIL" in error_msg:
            messagebox.showerror("Error", "Please enter a valid email address")
        elif "WEAK_PASSWORD" in error_msg:
            messagebox.showerror("Error", "Password is too weak")
        else:
            messagebox.showerror("Error", f"Failed to create account: {error_msg}")
    finally:
        self.hide_loading()

def logout(self):
    """Handle user logout process."""
    try:
        if hasattr(self, 'current_user') and self.current_user:
            # Log analytics event if analytics is available
            if hasattr(self, 'analytics'):
                try:
                    self.analytics.capture(
                        event_name='user_logout',
                        distinct_id=self.current_user.get('email', 'unknown'),
                        properties={
                            'email': self.current_user.get('email'),
                            'logout_time': datetime.now().isoformat(),
                            'user_id': self.current_user.get('localId')
                        }
                    )
                except Exception as analytics_error:
                    print(f"Error logging analytics for logout: {analytics_error}")
            
            # Clear user data and reset UI
            self.current_user = None
            
            # Clear any existing content
            self.clear_content_frame()
            
            # Show login screen
            self.show_login()
            
            # Clear any Firebase auth state
            if hasattr(self, 'firebase') and hasattr(self.firebase, 'auth'):
                self.firebase.auth.current_user = None
            
    except Exception as e:
        print(f"Error during logout: {e}")
        messagebox.showerror("Logout Error", "An error occurred during logout. Please try again.")
        
        # Try to log the error to analytics
        try:
            if hasattr(self, 'analytics'):
                self.analytics.capture(
                    event_name='logout_error',
                    distinct_id=self.current_user.get('email', 'unknown') if hasattr(self, 'current_user') and self.current_user else 'unknown',
                    properties={
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    },
                    process_person=False
                )
        except Exception as analytics_error:
            print(f"Error logging analytics for logout error: {analytics_error}")
        
        self.load_initial_data()
        
        self.setup_realtime_listeners()
        
    def load_initial_data(self):
        try:
            cadets = self.firebase.db.child("cadets").get().val() or {}
            self.cadets = cadets
            
            events = self.firebase.db.child("events").get().val() or {}
            self.events = events
            
            jobs = self.firebase.db.child("jobs").get().val() or {}
            self.jobs = jobs
            
            fundraisers = self.firebase.db.child("fundraisers").get().val() or {}
            self.fundraisers = fundraisers
            
            contacts = self.firebase.db.child("contacts").get().val() or {}
            self.contacts = contacts
            
            self.update_upcoming_events()
            self.update_dashboard()
            
        except Exception as e:
            print(f"Error loading initial data: {e}")
            messagebox.showerror("Error", f"Failed to load data: {e}")
    
    def setup_realtime_listeners(self):
        try:
            def cadets_callback(message):
                try:
                    if message["event"] == "put" or message["event"] == "patch":
                        data = message["data"] or {}
                        if isinstance(data, list):
                            self.cadets = {item.get('id', idx): item for idx, item in enumerate(data) if item}
                        elif data and not any(key.startswith('-') for key in data.keys()):
                            self.cadets = {'direct': data}
                        else:
                            self.cadets = data
                            
                        self.update_cadets_display()
                        self.update_dashboard()
                except Exception as e:
                    print(f"Error in cadets_callback: {e}")
            
            self.firebase.db.child("cadets").stream(cadets_callback)
            
            def events_callback(message):
                if message["event"] == "put" or message["event"] == "patch":
                    self.events = message["data"] or {}
                    self.update_calendar_display()
                    self.update_upcoming_events()
                    self.update_dashboard()
            
            self.firebase.db.child("events").stream(events_callback)
            
            def jobs_callback(message):
                if message["event"] == "put" or message["event"] == "patch":
                    self.jobs = message["data"] or {}
                    self.update_dashboard()
            
            self.firebase.db.child("jobs").stream(jobs_callback)
            
            def fundraisers_callback(message):
                if message["event"] == "put" or message["event"] == "patch":
                    self.fundraisers = message["data"] or {}
                    self.update_dashboard()
            
            self.firebase.db.child("fundraisers").stream(fundraisers_callback)
            
            def contacts_callback(message):
                if message["event"] == "put" or message["event"] == "patch":
                    self.contacts = message["data"] or {}
            
            self.firebase.db.child("contacts").stream(contacts_callback)
            
        except Exception as e:
            print(f"Error setting up real-time listeners: {e}")
            messagebox.showerror("Error", f"Failed to set up real-time updates: {e}")
    
    def create_main_ui(self):
        self.main_container = ctk.CTkFrame(self.root, fg_color="#f5f5f5")
        self.main_container.pack(fill="both", expand=True)
        
        self.create_sidebar()
        
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="white")
        self.content_frame.pack(side="right", fill="both", expand=True)

    def show_calendar(self):
        self.clear_content_frame()
        self.current_view = 'calendar'
        self.calendar_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(self.calendar_frame, fg_color="white")
        header_frame.pack(fill="x")
        
        ctk.CTkLabel(header_frame, text="Events Calendar", font=("Arial Bold", 24), text_color=self.primary_color).pack(side="left")
        add_event_btn = ctk.CTkButton(header_frame, text="+ Add Event", command=self.add_event_dialog, fg_color=self.success_color, hover_color="#45a049")
        add_event_btn.pack(side="right")
        
        self.calendar_list_frame = ctk.CTkScrollableFrame(self.calendar_frame, fg_color="transparent")
        self.calendar_list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.update_calendar_display()

    def update_calendar_display(self):
        if not hasattr(self, 'calendar_list_frame') or not self.calendar_list_frame.winfo_exists():
            return
            
        for widget in self.calendar_list_frame.winfo_children():
            widget.destroy()
            
        events_list = sorted(self.events.items(), key=lambda item: item[1].get('date', '9999-12-31'))
        
        if events_list:
            row = 0
            for event_id, event in events_list:
                card = ctk.CTkFrame(self.calendar_list_frame, fg_color="#f5f5f5", corner_radius=10)
                card.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
                self.calendar_list_frame.grid_columnconfigure(0, weight=1)
                
                title_label = ctk.CTkLabel(card, text=event.get('title', 'Untitled Event'), font=("Arial Bold", 16), text_color=self.primary_color)
                title_label.pack(side="left", padx=10, pady=10)
                
                date_label = ctk.CTkLabel(card, text=f"{event.get('date', 'N/A')} at {event.get('time', 'N/A')}", font=("Arial", 12), text_color="#555555")
                date_label.pack(side="left", padx=10, pady=10)
                
                button_frame = ctk.CTkFrame(card, fg_color="transparent")
                button_frame.pack(side="right", padx=10)
                
                edit_btn = ctk.CTkButton(button_frame, text="Edit", command=lambda eid=event_id: self.edit_event_dialog(eid), width=80, height=30, fg_color=self.accent_color, hover_color="#7ba4d1")
                edit_btn.pack(side="left", padx=(0, 5))
                
                delete_btn = ctk.CTkButton(button_frame, text="Delete", command=lambda eid=event_id: self.delete_event(eid), width=80, height=30, fg_color=self.danger_color, hover_color="#c43e3e")
                delete_btn.pack(side="left")
                
                row += 1
        else:
            ctk.CTkLabel(self.calendar_list_frame, text="No events scheduled.", font=("Arial", 14), text_color="#555555").pack(pady=20)

        
    def show_dashboard(self):
        self.clear_content_frame()
        self.current_view = 'dashboard'
        self.dashboard_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="white")
        header_frame.pack(fill="x")
        header_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="white")
        header_frame.pack(fill="x")
        
        ctk.CTkLabel(
            header_frame, 
            text="Dashboard", 
            font=("Arial Bold", 24), 
            text_color=self.primary_color
        ).pack(side="left")
        
        refresh_btn = ctk.CTkButton(
            header_frame, 
            text="🔄 Refresh", 
            command=self.update_dashboard,
            width=100,
            fg_color=self.accent_color,
            hover_color="#7ba4d1"
        )
        refresh_btn.pack(side="right")
        
        stats_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))
        
        cadets_card = ctk.CTkFrame(stats_frame, fg_color="#f5f5f5", corner_radius=10)
        cadets_card.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(
            cadets_card, 
            text="Cadets", 
            font=("Arial Bold", 16),
            text_color=self.primary_color
        ).pack(pady=(10, 5))
        
        self.cadets_count_label = ctk.CTkLabel(
            cadets_card, 
            text="0", 
            font=("Arial Bold", 24),
            text_color="#333333"
        )
        self.cadets_count_label.pack(pady=(0, 10))
        
        events_card = ctk.CTkFrame(stats_frame, fg_color="#f5f5f5", corner_radius=10)
        events_card.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(
            events_card, 
            text="Upcoming Events", 
            font=("Arial Bold", 16),
            text_color=self.primary_color
        ).pack(pady=(10, 5))
        
        self.events_count_label = ctk.CTkLabel(
            events_card, 
            text="0", 
            font=("Arial Bold", 24),
            text_color="#333333"
        )
        self.events_count_label.pack(pady=(0, 10))
        
        fundraisers_card = ctk.CTkFrame(stats_frame, fg_color="#f5f5f5", corner_radius=10)
        fundraisers_card.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(
            fundraisers_card, 
            text="Active Fundraisers", 
            font=("Arial Bold", 16),
            text_color=self.primary_color
        ).pack(pady=(10, 5))
        
        self.fundraisers_count_label = ctk.CTkLabel(
            fundraisers_card, 
            text="0", 
            font=("Arial Bold", 24),
            text_color="#333333"
        )
        self.fundraisers_count_label.pack(pady=(0, 10))
        
        activity_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="white")
        activity_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        ctk.CTkLabel(
            activity_frame, 
            text="Recent Activity", 
            font=("Arial Bold", 18),
            text_color=self.primary_color
        ).pack(anchor="w", pady=(0, 10))
        
        self.activity_list = ctk.CTkScrollableFrame(
            activity_frame, 
            fg_color="#f9f9f9",
            corner_radius=10
        )
        self.activity_list.pack(fill="both", expand=True)
        
        self.update_dashboard()

    def show_cadets(self):
        self.clear_content_frame()
        self.current_view = 'cadets'
        self.cadets_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.cadets_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(self.cadets_frame, fg_color="white")
        header_frame.pack(fill="x")
        
        ctk.CTkLabel(
            header_frame, 
            text="Cadet Roster", 
            font=("Arial Bold", 24), 
            text_color=self.primary_color
        ).pack(side="left")
        
        add_btn = ctk.CTkButton(
            header_frame, 
            text="+ Add Cadet", 
            command=self.add_cadet_dialog,
            fg_color=self.success_color,
            hover_color="#45a049"
        )
        add_btn.pack(side="right")
        
        filter_frame = ctk.CTkFrame(self.cadets_frame, fg_color="white")
        filter_frame.pack(fill="x", pady=(10, 0))
        
        search_frame = ctk.CTkFrame(filter_frame, fg_color="white")
        search_frame.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            search_frame, 
            text="Search:", 
            font=("Arial", 12)
        ).pack(side="left", padx=(0, 5))
        
        self.cadet_search_entry = ctk.CTkEntry(
            search_frame, 
            width=200,
            placeholder_text="Search cadets..."
        )
        self.cadet_search_entry.pack(side="left")
        self.cadet_search_entry.bind("<KeyRelease>", lambda e: self.update_cadets_display())
        
        grade_frame = ctk.CTkFrame(filter_frame, fg_color="white")
        grade_frame.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            grade_frame, 
            text="Grade:", 
            font=("Arial", 12)
        ).pack(side="left", padx=(0, 5))
        
        self.grade_var = ctk.StringVar(value="All")
        grade_menu = ctk.CTkOptionMenu(
            grade_frame,
            values=["All", "9", "10", "11", "12"],
            variable=self.grade_var,
            command=lambda _: self.update_cadets_display(),
            width=80
        )
        grade_menu.pack(side="left")
        
        self.cadets_list_frame = ctk.CTkScrollableFrame(
            self.cadets_frame, 
            fg_color="transparent"
        )
        self.cadets_list_frame.pack(fill="both", expand=True, pady=10)
        
        self.update_cadets_display()

    def show_uniforms(self):
        self.clear_content_frame()
        self.current_view = 'uniforms'
        self.uniforms_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.uniforms_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(self.uniforms_frame, fg_color="white")
        header_frame.pack(fill="x")
        
        ctk.CTkLabel(
            header_frame, 
            text="Uniform Management", 
            font=("Arial Bold", 24), 
            text_color=self.primary_color
        ).pack(side="left")
        
        add_btn = ctk.CTkButton(
            header_frame, 
            text="+ Add Uniform", 
            command=self.add_uniform_dialog,
            fg_color=self.success_color,
            hover_color="#45a049"
        )
        add_btn.pack(side="right")
        
        self.uniforms_list_frame = ctk.CTkScrollableFrame(
            self.uniforms_frame, 
            fg_color="transparent"
        )
        self.uniforms_list_frame.pack(fill="both", expand=True, pady=10)
        
        self.update_uniforms_display()

    def edit_fundraiser_dialog(self, fundraiser_id):
        if fundraiser_id not in self.fundraisers:
            messagebox.showerror("Error", "Fundraiser not found.")
            return
            
        fundraiser = self.fundraisers[fundraiser_id]
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Fundraiser")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        fields = [
            ("Name", "entry", fundraiser.get('name', '')),
            ("Description", "text", fundraiser.get('description', '')),
            ("Start Date", "date", fundraiser.get('start_date', '')),
            ("End Date", "date", fundraiser.get('end_date', '')),
            ("Goal Amount", "entry", fundraiser.get('goal_amount', '0')),
            ("Current Amount", "entry", fundraiser.get('current_amount', '0')),
        ]
        
        entries = {}
        for i, (label, field_type, default_value) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=f"{label}:").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            
            if field_type == "entry":
                entry = ctk.CTkEntry(form_frame, width=300)
                entry.insert(0, str(default_value))
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = entry
            elif field_type == "text":
                text = ctk.CTkTextbox(form_frame, width=300, height=100)
                text.insert("1.0", str(default_value))
                text.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = text
            elif field_type == "date":
                date_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
                date_frame.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                
                entry = ctk.CTkEntry(date_frame, width=200)
                entry.insert(0, str(default_value))
                entry.pack(side="left", padx=(0, 5))
                
                def pick_date(entry_widget=entry):
                    def on_date_select():
                        date = cal.get_date()
                        entry_widget.delete(0, tk.END)
                        entry_widget.insert(0, date.strftime("%Y-%m-%d"))
                        top.destroy()
                    
                    top = ctk.CTkToplevel(self.root)
                    top.title("Select Date")
                    top.transient(self.root)
                    top.grab_set()
                    
                    cal = Calendar(top, selectmode='day', date_pattern='y-mm-dd')
                    cal.pack(padx=10, pady=10)
                    
                    btn = ctk.CTkButton(top, text="Select", command=on_date_select)
                    btn.pack(pady=10)
                
                date_btn = ctk.CTkButton(
                    date_frame, 
                    text="📅", 
                    width=30,
                    command=pick_date
                )
                date_btn.pack(side="left")
                entries[label.lower().replace(" ", "_")] = entry
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        def save_fundraiser():
            try:
                fundraiser_data = {}
                for key, widget in entries.items():
                    if isinstance(widget, ctk.CTkTextbox):
                        fundraiser_data[key] = widget.get("1.0", tk.END).strip()
                    else:
                        fundraiser_data[key] = widget.get()
                self.firebase.db.child("fundraisers").child(fundraiser_id).update(fundraiser_data)
                
                messagebox.showinfo("Success", "Fundraiser updated successfully!")
                dialog.destroy()
                self.update_fundraisers_display()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update fundraiser: {str(e)}")
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_fundraiser)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=10)
    
    def show_fundraisers(self):
        self.clear_content_frame()
        self.current_view = 'fundraisers'
        self.fundraisers_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.fundraisers_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(self.fundraisers_frame, fg_color="white")
        header_frame.pack(fill="x")
        
        ctk.CTkLabel(
            header_frame, 
            text="Fundraisers", 
            font=("Arial Bold", 24), 
            text_color=self.primary_color
        ).pack(side="left")
        
        add_btn = ctk.CTkButton(
            header_frame, 
            text="+ Add Fundraiser", 
            command=self.add_fundraiser_dialog,
            fg_color=self.success_color,
            hover_color="#45a049"
        )
        add_btn.pack(side="right")
        
        self.fundraisers_list_frame = ctk.CTkScrollableFrame(
            self.fundraisers_frame, 
            fg_color="transparent"
        )
        self.fundraisers_list_frame.pack(fill="both", expand=True, pady=10)
        
        self.update_fundraisers_display()

    def show_contacts(self):
        self.clear_content_frame()
        self.current_view = 'contacts'
        
        self.contacts_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.contacts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(self.contacts_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header_frame,
            text="Contacts",
            font=("Arial", 24, "bold"),
            text_color=self.primary_color
        ).pack(side="left")
        
        add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add Contact",
            command=self.add_contact_dialog,
            fg_color=self.primary_color,
            hover_color="#002366",
            text_color="white",
            font=("Arial", 12, "bold")
        )
        add_btn.pack(side="right")
        
        self.contacts_list_frame = ctk.CTkScrollableFrame(
            self.contacts_frame, 
            fg_color="transparent"
        )
        self.contacts_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.update_contacts_display()

    def show_reports(self):
        self.clear_content_frame()
        self.current_view = 'reports'
        self.reports_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.reports_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            self.reports_frame, 
            text="Reports", 
            font=("Arial Bold", 24), 
            text_color=self.primary_color
        ).pack(anchor="w", pady=(0, 20))
        
        reports_grid = ctk.CTkFrame(self.reports_frame, fg_color="transparent")
        reports_grid.pack(fill="both", expand=True)
        
        reports = [
            {"title": "Cadet Roster", "description": "Generate a complete list of cadets with contact information"},
            {"title": "Grade Report", "description": "View grade distribution and statistics"},
            {"title": "Attendance", "description": "View attendance records and statistics"},
            {"title": "Community Service", "description": "Track community service hours by cadet"},
            {"title": "Fundraising", "description": "View fundraising progress and participation"},
            {"title": "Custom Report", "description": "Create a custom report with specific criteria"}
        ]
        
        for i, report in enumerate(reports):
            row = i // 2
            col = i % 2
            
            card = ctk.CTkFrame(
                reports_grid, 
                fg_color="#f5f5f5",
                corner_radius=10,
                border_width=1,
                border_color="#e0e0e0"
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            reports_grid.grid_rowconfigure(row, weight=1)
            reports_grid.grid_columnconfigure(col, weight=1)
            
            ctk.CTkLabel(
                card,
                text=report["title"],
                font=("Arial Bold", 16),
                text_color=self.primary_color
            ).pack(anchor="w", padx=15, pady=(15, 5))
            
            ctk.CTkLabel(
                card,
                text=report["description"],
                font=("Arial", 12),
                text_color="#555555",
                wraplength=300,
                justify="left"
            ).pack(anchor="w", padx=15, pady=(0, 15))
            
            ctk.CTkButton(
                card,
                text="Generate",
                command=lambda r=report: self.generate_report(r["title"]),
                width=100,
                fg_color=self.accent_color,
                hover_color="#7ba4d1"
            ).pack(side="right", padx=15, pady=(0, 15))
    
    def show_jobs(self):
        self.clear_content_frame()
        
        main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📋 Job Assignments",
            font=("Arial Bold", 24),
            text_color=self.primary_color
        )
        title_label.pack(side="left")
        
        add_btn = ctk.CTkButton(
            header_frame,
            text="➕ Add Job",
            command=self.add_job_dialog,
            fg_color=self.success_color,
            hover_color="#3d8b40"
        )
        add_btn.pack(side="right", padx=10)
        
        table_frame = ctk.CTkFrame(main_frame)
        table_frame.pack(fill="both", expand=True)
        
        columns = ("cadet", "title", "status", "assigned_date", "due_date", "priority", "actions")
        self.jobs_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        self.jobs_tree.heading("cadet", text="Cadet")
        self.jobs_tree.heading("title", text="Job Title")
        self.jobs_tree.heading("status", text="Status")
        self.jobs_tree.heading("assigned_date", text="Assigned On")
        self.jobs_tree.heading("due_date", text="Due Date")
        self.jobs_tree.heading("priority", text="Priority")
        self.jobs_tree.heading("actions", text="Actions")
        
        self.jobs_tree.column("cadet", width=150)
        self.jobs_tree.column("title", width=200)
        self.jobs_tree.column("status", width=100)
        self.jobs_tree.column("assigned_date", width=120)
        self.jobs_tree.column("due_date", width=120)
        self.jobs_tree.column("priority", width=100)
        self.jobs_tree.column("actions", width=150)
        
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.jobs_tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.jobs_tree.xview)
        self.jobs_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.jobs_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.update_jobs_display()
    
    def add_job_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New Job Assignment")
        dialog.geometry("600x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        fields = [
            ("Cadet", "combobox", "cadet", "", True, "Select a cadet"),
            ("Job Title", "entry", "title", "", True, "Enter job title"),
            ("Description", "text", "description", "", True, "Enter job description"),
            ("Status", "combobox", "status", "Pending", True, ["Pending", "Assigned", "In Progress", "Completed", "Cancelled"]),
            ("Priority", "combobox", "priority", "Medium", True, ["Low", "Medium", "High"]),
            ("Assigned Date", "date", "assigned_date", datetime.now().strftime("%Y-%m-%d"), True),
            ("Notes", "text", "notes", "", False, "Any additional notes...")
        ]
        
        entries = {}
        
        for i, (label, field_type, field_name, default, required, *options) in enumerate(fields):
            label_widget = ctk.CTkLabel(form_frame, text=f"{label}:" + (" *" if required else ""))
            label_widget.grid(row=i, column=0, sticky="w", pady=(10, 2), padx=5)
            
            if field_type == "entry":
                entry = ctk.CTkEntry(form_frame, width=300, placeholder_text=options[0] if options else "")
                entry.insert(0, default)
                entry.grid(row=i, column=1, sticky="ew", pady=5, padx=5, columnspan=2)
                entries[field_name] = entry
            
            elif field_type == "combobox":
                if field_name == "cadet":
                    cadet_list = [f"{cadet.get('last_name', '')}, {cadet.get('first_name', '')}" for cadet in self.cadets.values()]
                    entry = ctk.CTkComboBox(
                        form_frame,
                        values=cadet_list,
                        width=300
                    )
                    entry.set("Select a cadet...")
                else:
                    entry = ctk.CTkComboBox(
                        form_frame,
                        values=options[0] if options else [],
                        width=300
                    )
                    entry.set(default)
                entry.grid(row=i, column=1, sticky="ew", pady=5, padx=5, columnspan=2)
                entries[field_name] = entry
            
            elif field_type == "date":
                entry_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
                entry_frame.grid(row=i, column=1, sticky="ew", pady=5, padx=5, columnspan=2)
                
                entry = ctk.CTkEntry(entry_frame, width=200, placeholder_text="YYYY-MM-DD")
                entry.insert(0, default)
                entry.pack(side="left", fill="x", expand=True)
                
                def pick_date(entry_widget=entry):
                    def on_date_select():
                        try:
                            date = cal.get_date()
                            entry_widget.delete(0, tk.END)
                            entry_widget.insert(0, date.strftime("%Y-%m-%d"))
                            top.destroy()
                        except Exception as e:
                            print(f"Error selecting date: {e}")
                    
                    top = ctk.CTkToplevel(self.root)
                    top.title("Select Date")
                    top.grab_set()
                    
                    try:
                        from tkcalendar import Calendar
                        cal = Calendar(top, selectmode='day')
                        cal.pack(padx=10, pady=10)
                        
                        btn = ctk.CTkButton(top, text="Select", command=on_date_select)
                        btn.pack(pady=10)
                    except ImportError:
                        ctk.CTkLabel(top, text="Please install tkcalendar: pip install tkcalendar").pack(padx=10, pady=10)
                
                ctk.CTkButton(
                    entry_frame, 
                    text="📅", 
                    width=40,
                    command=lambda e=entry: pick_date(e)
                ).pack(side="left")
                
                entry.pack(fill="x", pady=(0, 10))
                entries[field_name] = entry
            
            elif field_type == "text":
                entry = ctk.CTkTextbox(form_frame, height=80, width=300)
                entry.insert("1.0", default)
                entry.grid(row=i, column=1, sticky="ew", pady=5, padx=5, columnspan=2)
                entries[field_name] = entry
            else:
                entry = ctk.CTkEntry(form_frame, width=300)
                entry.insert(0, default)
                entry.grid(row=i, column=1, sticky="ew", pady=5, padx=5, columnspan=2)
                entries[field_name] = entry
            
            i += 1
        
        def save_job():
            try:
                job_data = {}
                for field_name, widget in entries.items():
                    if isinstance(widget, ctk.CTkEntry) or isinstance(widget, ctk.CTkComboBox):
                        job_data[field_name] = widget.get()
                    elif isinstance(widget, ctk.CTkTextbox):
                        job_data[field_name] = widget.get("1.0", "end-1c")
                
                required_fields = [field[2] for field in fields if field[3]]
                missing_fields = [field for field in required_fields if not job_data.get(field)]
                
                if missing_fields:
                    messagebox.showerror("Error", f"Please fill in all required fields: {', '.join(missing_fields)}")
                    return
                
                job_data["created_at"] = datetime.now().isoformat()
                job_data["updated_at"] = job_data["created_at"]
                
                job_ref = self.firebase.db.reference("jobs").push()
                job_ref.set(job_data)
                
                self.update_jobs_display()
                
                dialog.destroy()
                
                messagebox.showinfo("Success", "Job assignment added successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save job: {str(e)}")
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_job)
        save_btn.pack(side="right", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=10)
    
    def update_jobs_display(self):
        if not hasattr(self, 'jobs_tree'):
            return
            
        for item in self.jobs_tree.get_children():
            self.jobs_tree.delete(item)
            
        for job_id, job in self.jobs.items():
            if not isinstance(job, dict):
                continue
                
            action_frame = ctk.CTkFrame(self.jobs_tree, fg_color="transparent")
            
            edit_btn = ctk.CTkButton(
                action_frame,
                text="✏️",
                width=30,
                height=30,
                fg_color="transparent",
                text_color="#1a73e8",
                hover_color="#e8f0fe",
                command=lambda jid=job_id: self.edit_job_dialog(jid)
            )
            edit_btn.pack(side="left", padx=2)
            
            delete_btn = ctk.CTkButton(
                action_frame,
                text="🗑️",
                width=30,
                height=30,
                fg_color="transparent",
                text_color="#d93025",
                hover_color="#fce8e6",
                command=lambda jid=job_id: self.delete_job(jid)
            )
            delete_btn.pack(side="left", padx=2)
            
            item_id = self.jobs_tree.insert("", "end", values=(
                job.get("cadet", "N/A"),
                job.get("title", "No Title"),
                job.get("status", "Pending"),
                job.get("assigned_date", "N/A"),
                job.get("due_date", "N/A"),
                job.get("priority", "Medium"),
            ), tags=(job_id,))
            
            self.jobs_tree.set(item_id, "actions", "")
            self.jobs_tree.window_create(item_id, column="actions", window=action_frame)
    
    def edit_job_dialog(self, job_id):
        job = self.jobs.get(job_id)
        if not job:
            messagebox.showerror("Error", "Job not found")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Job Assignment")
        dialog.geometry("600x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form frame
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Form fields (same as add_job_dialog but with existing values)
        fields = [
            ("Cadet", "combobox", "cadet", job.get("cadet", ""), True, "Select a cadet"),
            ("Job Title", "entry", "title", job.get("title", ""), True, "Enter job title"),
            ("Description", "text", "description", job.get("description", ""), True, "Enter job description"),
            ("Status", "combobox", "status", job.get("status", "Pending"), True, ["Pending", "Assigned", "In Progress", "Completed", "Cancelled"]),
            ("Priority", "combobox", "priority", job.get("priority", "Medium"), True, ["Low", "Medium", "High"]),
            ("Assigned Date", "date", "assigned_date", job.get("assigned_date", datetime.now().strftime("%Y-%m-%d")), True),
            ("Due Date", "date", "due_date", job.get("due_date", ""), True),
            ("Notes", "text", "notes", job.get("notes", ""), False, "Any additional notes...")
        ]
        
        messagebox.showinfo("Info", "Edit functionality would be implemented here")
        dialog.destroy()
    
    def delete_job(self, job_id):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this job assignment?"):
            try:
                self.firebase.db.reference(f"jobs/{job_id}").delete()
                self.update_jobs_display()
                messagebox.showinfo("Success", "Job assignment deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete job: {str(e)}")
    
    def show_settings(self):
        self.clear_content_frame()
        self.current_view = 'settings'
        self.settings_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            self.settings_frame, 
            text="Settings", 
            font=("Arial Bold", 24), 
            text_color=self.primary_color
        ).pack(anchor="w", pady=(0, 20))
        
        tabview = ctk.CTkTabview(self.settings_frame)
        tabview.pack(fill="both", expand=True)
        
        general_tab = tabview.add("General")
        
        ctk.CTkLabel(
            general_tab,
            text="Appearance",
            font=("Arial Bold", 16),
            text_color=self.primary_color
        ).pack(anchor="w", pady=(10, 5))
        
        theme_frame = ctk.CTkFrame(general_tab, fg_color="transparent")
        theme_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            theme_frame,
            text="Theme:",
            font=("Arial", 12)
        ).pack(side="left", padx=(0, 10))
        
        theme_var = ctk.StringVar(value="System")
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["System", "Light", "Dark"],
            variable=theme_var,
            command=self.change_theme,
            width=150
        )
        theme_menu.pack(side="left")
        
        account_tab = tabview.add("Account")
        
        ctk.CTkLabel(
            account_tab,
            text="Account Settings",
            font=("Arial Bold", 16),
            text_color=self.primary_color
        ).pack(anchor="w", pady=(10, 5))
        
        change_pass_btn = ctk.CTkButton(
            account_tab,
            text="Change Password",
            command=self.show_change_password_dialog,
            width=200
        )
        change_pass_btn.pack(pady=10)
        
        signout_btn = ctk.CTkButton(
            account_tab,
            text="Sign Out",
            command=self.logout,
            fg_color="#f5f5f5",
            text_color="#333333",
            hover_color="#e0e0e0",
            border_width=1,
            border_color="#cccccc"
        )
        signout_btn.pack(pady=10)
        
        about_tab = tabview.add("About")
        
        ctk.CTkLabel(
            about_tab,
            text="AFJROTC AMS",
            font=("Arial Bold", 20),
            text_color=self.primary_color
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            about_tab,
            text="Version 1.0.0",
            font=("Arial", 12),
            text_color="#666666"
        ).pack(pady=(0, 20))
        
        if hasattr(self, 'logo_img'):
            logo_label = ctk.CTkLabel(about_tab, image=self.logo_img, text="")
            logo_label.pack(pady=20)
        
        ctk.CTkLabel(
            about_tab,
            text="© 2023 AFJROTC AMS. All rights reserved.",
            font=("Arial", 10),
            text_color="#999999"
        ).pack(side="bottom", pady=20)
    
    def show_help(self):
        """Display the help view"""
        self.clear_content_frame()
        self.current_view = 'help'
        self.help_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        self.help_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            self.help_frame, 
            text="Help & Support", 
            font=("Arial Bold", 24), 
            text_color=self.primary_color
        ).pack(anchor="w", pady=(0, 20))
        
        faq_frame = ctk.CTkFrame(self.help_frame, fg_color="#f9f9f9", corner_radius=10)
        faq_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            faq_frame,
            text="Frequently Asked Questions",
            font=("Arial Bold", 16),
            text_color=self.primary_color
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        faq_items = [
            {
                "question": "How do I add a new cadet?",
                "answer": "Go to the Cadets section and click the 'Add Cadet' button. Fill in the required information and click 'Save'."
            },
            {
                "question": "How do I track community service hours?",
                "answer": "Community service hours are tracked automatically when you add or update a cadet's information. You can view the hours in the Cadets section."
            },
            {
                "question": "How do I create a new event?",
                "answer": "Go to the Calendar section and click the 'Add Event' button. Fill in the event details and click 'Save'."
            },
            {
                "question": "How do I generate reports?",
                "answer": "Go to the Reports section and select the type of report you want to generate. Click 'Generate' to create the report."
            }
        ]
        
        for i, item in enumerate(faq_items):
            faq_item = ctk.CTkFrame(faq_frame, fg_color="white", corner_radius=5)
            faq_item.pack(fill="x", padx=20, pady=5)
            
            question_frame = ctk.CTkFrame(faq_item, fg_color="transparent")
            question_frame.pack(fill="x", pady=(10, 5))
            
            ctk.CTkLabel(
                question_frame,
                text=f"Q: {item['question']}",
                font=("Arial Bold", 12),
                text_color="#333333"
            ).pack(side="left")
            
            ctk.CTkLabel(
                faq_item,
                text=item['answer'],
                font=("Arial", 12),
                text_color="#555555",
                wraplength=800,
                justify="left"
            ).pack(anchor="w", padx=20, pady=(0, 10))
            
            if i < len(faq_items) - 1:
                ctk.CTkFrame(
                    faq_item, 
                    height=1, 
                    fg_color="#e0e0e0"
                ).pack(fill="x", pady=5)
        
        support_frame = ctk.CTkFrame(self.help_frame, fg_color="#f9f9f9", corner_radius=10)
        support_frame.pack(fill="x")
        
        ctk.CTkLabel(
            support_frame,
            text="Need Help?",
            font=("Arial Bold", 16),
            text_color=self.primary_color
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            support_frame,
            text="If you need further assistance, please contact support:",
            font=("Arial", 12),
            text_color="#555555"
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        contact_info = [
            ("📧 Email:", "crowncorestudios@gmail.com"),
            ("📞 Phone:", "(706) 330-0069"),
        ]
        
        for icon, text in contact_info:
            contact_frame = ctk.CTkFrame(support_frame, fg_color="transparent")
            contact_frame.pack(fill="x", padx=20, pady=2)
            
            ctk.CTkLabel(
                contact_frame,
                text=icon,
                font=("Arial", 14)
            ).pack(side="left", padx=(0, 10))
            
            ctk.CTkLabel(
                contact_frame,
                text=text,
                font=("Arial", 12),
                text_color="#333333"
            ).pack(side="left")

    def show_change_password_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Change Password")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        window_width = 400
        window_height = 250
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(
            form_frame,
            text="Current Password:",
            font=("Arial", 12)
        ).pack(anchor="w", pady=(0, 5))
        
        current_password = ctk.CTkEntry(
            form_frame,
            width=300,
            show="•",
            font=("Arial", 12),
            placeholder_text="Enter current password"
        )
        current_password.pack(pady=(0, 10))
        
        ctk.CTkLabel(
            form_frame,
            text="New Password:",
            font=("Arial", 12)
        ).pack(anchor="w", pady=(0, 5))
        
        new_password = ctk.CTkEntry(
            form_frame,
            width=300,
            show="•",
            font=("Arial", 12),
            placeholder_text="Enter new password"
        )
        new_password.pack(pady=(0, 10))
        
        ctk.CTkLabel(
            form_frame,
            text="Confirm New Password:",
            font=("Arial", 12)
        ).pack(anchor="w", pady=(0, 5))
        
        confirm_password = ctk.CTkEntry(
            form_frame,
            width=300,
            show="•",
            font=("Arial", 12),
            placeholder_text="Confirm new password"
        )
        confirm_password.pack(pady=(0, 20))
        
        status_label = ctk.CTkLabel(
            form_frame,
            text="",
            text_color="red",
            font=("Arial", 11)
        )
        status_label.pack(pady=(0, 10))
        
        def change_password():
            current = current_password.get().strip()
            new = new_password.get().strip()
            confirm = confirm_password.get().strip()
            
            if not current or not new or not confirm:
                status_label.configure(text="All fields are required")
                return
                
            if new != confirm:
                status_label.configure(text="New passwords do not match")
                return
                
            if len(new) < 6:
                status_label.configure(text="Password must be at least 6 characters")
                return
                
            try:
                user = self.firebase.auth().sign_in_with_email_and_password(
                    self.current_user['email'],
                    current
                )
                
                self.firebase.auth().update_user(
                    user['idToken'],
                    password=new
                )
                
                messagebox.showinfo(
                    "Success",
                    "Password updated successfully!"
                )
                dialog.destroy()
                
            except Exception as e:
                error_msg = str(e).lower()
                if "invalid password" in error_msg or "wrong password" in error_msg:
                    status_label.configure(text="Incorrect current password")
                else:
                    status_label.configure(text=f"Error: {str(e)}")
        
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            command=dialog.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Change Password",
            width=150,
            fg_color=self.primary_color,
            hover_color="#002366",
            command=change_password
        ).pack(side="right", padx=5)
        
        current_password.focus_set()
        
        dialog.bind('<Return>', lambda e: change_password())

    def update_contacts_display(self):
        if not hasattr(self, 'contacts_list_frame') or not self.contacts_list_frame.winfo_exists():
            return
            
        for widget in self.contacts_list_frame.winfo_children():
            widget.destroy()
            
        if hasattr(self, 'contacts') and self.contacts:
            headers = ["Name", "Organization", "Phone", "Email", "Type", "Actions"]
            for i, header in enumerate(headers):
                ctk.CTkLabel(
                    self.contacts_list_frame,
                    text=header,
                    font=("Arial", 12, "bold"),
                    text_color=self.primary_color
                ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
            
            for idx, (contact_id, contact) in enumerate(self.contacts.items(), 1):
                if not isinstance(contact, dict):
                    continue
                    
                name = f"{contact.get('last_name', '')}, {contact.get('first_name', '')}"
                ctk.CTkLabel(
                    self.contacts_list_frame,
                    text=name.strip(", ") if name.strip(", ") else "N/A",
                    font=("Arial", 12)
                ).grid(row=idx, column=0, padx=5, pady=2, sticky="w")
                
                org = contact.get('organization', 'N/A')
                ctk.CTkLabel(
                    self.contacts_list_frame,
                    text=org,
                    font=("Arial", 12)
                ).grid(row=idx, column=1, padx=5, pady=2, sticky="w")
                
                phone = contact.get('phone', 'N/A')
                ctk.CTkLabel(
                    self.contacts_list_frame,
                    text=phone,
                    font=("Arial", 12)
                ).grid(row=idx, column=2, padx=5, pady=2, sticky="w")
                
                email = contact.get('email', 'N/A')
                ctk.CTkLabel(
                    self.contacts_list_frame,
                    text=email,
                    font=("Arial", 12)
                ).grid(row=idx, column=3, padx=5, pady=2, sticky="w")
                
                contact_type = contact.get('type', 'Other')
                type_color = {
                    'Vendor': '#4CAF50',
                    'School': '#2196F3',
                    'Military': '#9C27B0',
                    'Other': '#607D8B'
                }.get(contact_type, '#607D8B')
                
                ctk.CTkLabel(
                    self.contacts_list_frame,
                    text=contact_type,
                    font=("Arial", 12, "bold"),
                    text_color=type_color
                ).grid(row=idx, column=4, padx=5, pady=2, sticky="w")
                
                btn_frame = ctk.CTkFrame(self.contacts_list_frame, fg_color="transparent")
                btn_frame.grid(row=idx, column=5, padx=5, pady=2, sticky="e")
                
                ctk.CTkButton(
                    btn_frame,
                    text="Edit",
                    width=60,
                    height=25,
                    font=("Arial", 10),
                    command=lambda cid=contact_id: self.edit_contact_dialog(cid)
                ).pack(side="left", padx=2)
                
                ctk.CTkButton(
                    btn_frame,
                    text="Delete",
                    width=60,
                    height=25,
                    font=("Arial", 10),
                    fg_color=self.danger_color,
                    hover_color="#c43e3e",
                    command=lambda cid=contact_id: self.delete_contact(cid)
                ).pack(side="left", padx=2)
        else:
            ctk.CTkLabel(
                self.contacts_list_frame,
                text="No contacts found. Click 'Add Contact' to add a new contact.",
                text_color="#666666",
                font=("Arial", 14)
            ).pack(pady=40)

    def update_fundraisers_display(self):
        if not hasattr(self, 'fundraisers_list_frame') or not self.fundraisers_list_frame.winfo_exists():
            return
            
        for widget in self.fundraisers_list_frame.winfo_children():
            widget.destroy()
            
        if hasattr(self, 'fundraisers') and self.fundraisers:
            headers = ["Name", "Date", "Goal", "Raised", "Progress", "Status", "Actions"]
            for i, header in enumerate(headers):
                ctk.CTkLabel(
                    self.fundraisers_list_frame,
                    text=header,
                    font=("Arial", 12, "bold"),
                    text_color=self.primary_color
                ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
            
            for idx, (fundraiser_id, fundraiser) in enumerate(self.fundraisers.items(), 1):
                if not isinstance(fundraiser, dict):
                    continue
                    
                ctk.CTkLabel(
                    self.fundraisers_list_frame,
                    text=fundraiser.get('name', 'N/A'),
                    font=("Arial", 12)
                ).grid(row=idx, column=0, padx=5, pady=2, sticky="w")
                
                date_str = fundraiser.get('date', 'N/A')
                ctk.CTkLabel(
                    self.fundraisers_list_frame,
                    text=date_str,
                    font=("Arial", 12)
                ).grid(row=idx, column=1, padx=5, pady=2, sticky="w")
                
                goal = fundraiser.get('goal', 0)
                try:
                    goal = float(goal)
                    goal_text = f"${goal:,.2f}"
                except (ValueError, TypeError):
                    goal_text = "N/A"
                    
                ctk.CTkLabel(
                    self.fundraisers_list_frame,
                    text=goal_text,
                    font=("Arial", 12)
                ).grid(row=idx, column=2, padx=5, pady=2, sticky="w")
                
                raised_amt = fundraiser.get('raised', 0)
                try:
                    raised_amt = float(raised_amt)
                    raised_text = f"${raised_amt:,.2f}"
                except (ValueError, TypeError):
                    raised_text = "$0.00"
                    
                ctk.CTkLabel(
                    self.fundraisers_list_frame,
                    text=raised_text,
                    font=("Arial", 12)
                ).grid(row=idx, column=3, padx=5, pady=2, sticky="w")
                
                progress_frame = ctk.CTkFrame(self.fundraisers_list_frame, fg_color="transparent")
                progress_frame.grid(row=idx, column=4, padx=5, pady=2, sticky="nsew")
                
                try:
                    progress = min(raised_amt / goal * 100 if goal > 0 else 0, 100)
                    progress_color = "#4CAF50"  # Green
                    if progress < 50:
                        progress_color = "#F44336"  # Red
                    elif progress < 75:
                        progress_color = "#FFC107"  # Yellow
                        
                    ctk.CTkProgressBar(
                        progress_frame,
                        width=100,
                        height=20,
                        fg_color="#e0e0e0",
                        progress_color=progress_color
                    ).pack(fill="x", expand=True)
                    progress_frame.progress = progress / 100
                    
                    ctk.CTkLabel(
                        progress_frame,
                        text=f"{progress:.1f}%",
                        font=("Arial", 10)
                    ).pack(pady=2)
                except (ValueError, ZeroDivisionError):
                    ctk.CTkLabel(
                        progress_frame,
                        text="N/A",
                        font=("Arial", 12)
                    ).pack()
                
                status = "Active"
                status_color = "#4CAF50" 
                
                try:
                    event_date = datetime.strptime(date_str, "%Y-%m-%d")
                    today = datetime.now()
                    if today > event_date:
                        status = "Completed"
                        status_color = "#9E9E9E"  
                except (ValueError, TypeError):
                    pass
                    
                ctk.CTkLabel(
                    self.fundraisers_list_frame,
                    text=status,
                    font=("Arial", 12, "bold"),
                    text_color=status_color
                ).grid(row=idx, column=5, padx=5, pady=2, sticky="w")
                
                btn_frame = ctk.CTkFrame(self.fundraisers_list_frame, fg_color="transparent")
                btn_frame.grid(row=idx, column=6, padx=5, pady=2, sticky="e")
                
                ctk.CTkButton(
                    btn_frame,
                    text="Edit",
                    width=60,
                    height=25,
                    font=("Arial", 10),
                    command=lambda fid=fundraiser_id: self.edit_fundraiser_dialog(fid)
                ).pack(side="left", padx=2)
                
                ctk.CTkButton(
                    btn_frame,
                    text="Delete",
                    width=60,
                    height=25,
                    font=("Arial", 10),
                    fg_color=self.danger_color,
                    hover_color="#c43e3e",
                    command=lambda fid=fundraiser_id: self.delete_fundraiser(fid)
                ).pack(side="left", padx=2)
        else:
            # Show message if no fundraisers found
            ctk.CTkLabel(
                self.fundraisers_list_frame,
                text="No fundraisers found. Click 'Add Fundraiser' to create a new one.",
                text_color="#666666",
                font=("Arial", 14)
            ).pack(pady=40)

    def update_uniforms_display(self):
        """Update the display of uniforms from the local data cache"""
        if not hasattr(self, 'uniforms_list_frame') or not self.uniforms_list_frame.winfo_exists():
            return
            
        for widget in self.uniforms_list_frame.winfo_children():
            widget.destroy()
            
        if hasattr(self, 'uniforms') and self.uniforms:
            # Create header row
            headers = ["Item", "Size", "Condition", "Available", "Assigned To", "Actions"]
            for i, header in enumerate(headers):
                ctk.CTkLabel(
                    self.uniforms_list_frame,
                    text=header,
                    font=("Arial", 12, "bold"),
                    text_color=self.primary_color
                ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
            
            # Add uniform items
            for idx, (item_id, item) in enumerate(self.uniforms.items(), 1):
                # Skip if item is not a dictionary
                if not isinstance(item, dict):
                    continue
                    
                # Item name
                ctk.CTkLabel(
                    self.uniforms_list_frame,
                    text=item.get('name', 'N/A'),
                    font=("Arial", 12)
                ).grid(row=idx, column=0, padx=5, pady=2, sticky="w")
                
                # Size
                ctk.CTkLabel(
                    self.uniforms_list_frame,
                    text=item.get('size', 'N/A'),
                    font=("Arial", 12)
                ).grid(row=idx, column=1, padx=5, pady=2, sticky="w")
                
                condition = item.get('condition', 'N/A')
                condition_color = "#4CAF50" 
                if condition.lower() == 'poor':
                    condition_color = "#F44336" 
                elif condition.lower() == 'fair':
                    condition_color = "#FFC107"  
                    
                ctk.CTkLabel(
                    self.uniforms_list_frame,
                    text=condition,
                    font=("Arial", 12),
                    text_color=condition_color
                ).grid(row=idx, column=2, padx=5, pady=2, sticky="w")
                
                assigned_to = item.get('assignedTo', '')
                status = "Yes" if not assigned_to else "No"
                status_color = "#4CAF50" if status == "Yes" else "#F44336"
                
                ctk.CTkLabel(
                    self.uniforms_list_frame,
                    text=status,
                    font=("Arial", 12),
                    text_color=status_color
                ).grid(row=idx, column=3, padx=5, pady=2, sticky="w")
                
                assigned_label = ctk.CTkLabel(
                    self.uniforms_list_frame,
                    text=assigned_to if assigned_to else "N/A",
                    font=("Arial", 12)
                )
                assigned_label.grid(row=idx, column=4, padx=5, pady=2, sticky="w")
                
                btn_frame = ctk.CTkFrame(self.uniforms_list_frame, fg_color="transparent")
                btn_frame.grid(row=idx, column=5, padx=5, pady=2, sticky="e")
                
                ctk.CTkButton(
                    btn_frame,
                    text="Edit",
                    width=60,
                    height=25,
                    font=("Arial", 10),
                    command=lambda iid=item_id: self.edit_uniform_dialog(iid)
                ).pack(side="left", padx=2)
                
                ctk.CTkButton(
                    btn_frame,
                    text="Delete",
                    width=60,
                    height=25,
                    font=("Arial", 10),
                    fg_color=self.danger_color,
                    hover_color="#c43e3e",
                    command=lambda iid=item_id: self.delete_uniform(iid)
                ).pack(side="left", padx=2)
        else:
            ctk.CTkLabel(
                self.uniforms_list_frame,
                text="No uniform items found. Click 'Add Uniform' to add a new item.",
                text_color="#666666",
                font=("Arial", 14)
            ).pack(pady=40)

    def update_cadets_display(self):
        try:
            if not hasattr(self, 'cadets_list_frame') or not self.cadets_list_frame.winfo_exists():
                return
                
            for widget in self.cadets_list_frame.winfo_children():
                widget.destroy()
                
                print("Cadets data:", self.cadets)
            
            if not self.cadets:
                self._show_no_cadets_message()
                return
                
            cadets_list = []
            
            if isinstance(self.cadets, dict):
                if all(isinstance(k, str) for k in self.cadets.keys()):
                    cadets_list = [(k, v) for k, v in self.cadets.items() if isinstance(v, (dict, str))]
                
                elif all(k in ['first_name', 'last_name', 'email', 'grade', 'flight'] for k in self.cadets.keys()):
                    cadets_list = [('direct', self.cadets)]
            elif isinstance(self.cadets, list):
                cadets_list = [(i, item) for i, item in enumerate(self.cadets) if isinstance(item, (dict, str))]
            
            if cadets_list:
                def get_sort_key(item):
                    if not isinstance(item[1], dict):
                        return ('', '')
                    return (
                        str(item[1].get('last_name', '') or item[1].get('Last Name', '') or '').lower(),
                        str(item[1].get('first_name', '') or item[1].get('First Name', '') or '').lower()
                    )
                
                cadets_list = sorted(cadets_list, key=get_sort_key)
                
                self._display_cadets_list(cadets_list)
            else:
                self._show_no_cadets_message()
                
        except Exception as e:
            print(f"Error in update_cadets_display: {e}")
            self._show_no_cadets_message()
    
    def _show_no_cadets_message(self):
        if not hasattr(self, 'cadets_list_frame') or not self.cadets_list_frame.winfo_exists():
            return
            
        for widget in self.cadets_list_frame.winfo_children():
            widget.destroy()
            
        message_frame = ctk.CTkFrame(self.cadets_list_frame, fg_color="transparent")
        message_frame.pack(expand=True, pady=40)
        
        ctk.CTkLabel(
            message_frame,
            text="No cadets found.",
            text_color="#666666",
            font=("Arial", 14)
        ).pack(pady=10)
        
        add_button = ctk.CTkButton(
            message_frame,
            text="Add New Cadet",
            command=self.add_cadet_dialog,
            fg_color=self.primary_color,
            hover_color=self.accent_color
        )
        add_button.pack(pady=5)
    
    def _display_cadets_list(self, cadets_list):
        if not hasattr(self, 'cadets_list_frame') or not self.cadets_list_frame.winfo_exists():
            return
            
        for widget in self.cadets_list_frame.winfo_children():
            widget.destroy()
        
        header_frame = ctk.CTkFrame(self.cadets_list_frame, fg_color=self.primary_color)
        header_frame.pack(fill="x", pady=(0, 5))
        
        for i in range(6):
            header_frame.columnconfigure(i, weight=1 if i < 5 else 0)
        
        headers = ["Name", "Grade", "Flight", "CS Hours", "Status", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame, 
                text=header, 
                text_color="white",
                font=("Arial", 12, "bold")
            )
            label.grid(row=0, column=i, padx=10, pady=5, sticky="nsew")
        
        for cadet_id, cadet in cadets_list:
            if not isinstance(cadet, dict):
                continue
                
            row_frame = ctk.CTkFrame(self.cadets_list_frame, fg_color="#f8f9fa", corner_radius=5)
            row_frame.pack(fill="x", pady=2)
            
            content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            content_frame.pack(fill="x", padx=5, pady=5)
            
            for i in range(6):
                content_frame.columnconfigure(i, weight=1 if i < 5 else 0)
            
            last_name = cadet.get('last_name', cadet.get('Last Name', ''))
            first_name = cadet.get('first_name', cadet.get('First Name', ''))
            name_label = ctk.CTkLabel(
                content_frame,
                text=f"{last_name}, {first_name}",
                text_color="#333333",
                font=("Arial", 12)
            )
            name_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            grade = cadet.get('grade', cadet.get('Grade', ''))
            grade_label = ctk.CTkLabel(
                content_frame,
                text=str(grade),
                text_color="#555555",
                font=("Arial", 12)
            )
            grade_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
            
            flight = cadet.get('flight', cadet.get('Flight', ''))
            flight_label = ctk.CTkLabel(
                content_frame,
                text=str(flight),
                text_color="#555555",
                font=("Arial", 12)
            )
            flight_label.grid(row=0, column=2, padx=10, pady=5, sticky="w")
            
            cs_hours = cadet.get('cs_hours', cadet.get('CS Hours', 0))
            cs_label = ctk.CTkLabel(
                content_frame,
                text=str(cs_hours),
                text_color="#555555",
                font=("Arial", 12)
            )
            cs_label.grid(row=0, column=3, padx=10, pady=5, sticky="w")
            
            status = cadet.get('status', cadet.get('Status', 'Active'))
            status_label = ctk.CTkLabel(
                content_frame,
                text=status,
                text_color=self.success_color if status.lower() == 'active' else self.warning_color,
                font=("Arial", 12, "bold")
            )
            status_label.grid(row=0, column=4, padx=10, pady=5, sticky="w")
            
            actions_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=5, padx=5, pady=5, sticky="e")
            
            edit_btn = ctk.CTkButton(
                actions_frame,
                text="✏️",
                width=30,
                height=30,
                fg_color="transparent",
                hover_color="#e9ecef",
                text_color=self.primary_color,
                font=("Arial", 14),
                command=lambda cid=cadet_id: self.edit_cadet_dialog(cid)
            )
            edit_btn.pack(side="left", padx=2)
            
            delete_btn = ctk.CTkButton(
                actions_frame,
                text="🗑️",
                width=30,
                height=30,
                fg_color="transparent",
                hover_color="#e9ecef",
                text_color=self.danger_color,
                font=("Arial", 14),
                command=lambda cid=cadet_id: self.delete_cadet(cid)
            )
            delete_btn.pack(side="left", padx=2)
    
    def calculate_balances(self, transactions):
        total_balance = 0
        month_income = 0
        self._dashboard_update_id = self.root.after(
            30000, 
            lambda: setattr(self, '_dashboard_update_scheduled', False) or self.update_dashboard()
        )
    def add_cadet_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New Cadet")
        dialog.geometry("400x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        fields = [
            ("First Name", "entry"),
            ("Last Name", "entry"),
            ("Grade", "optionmenu", ["9", "10", "11", "12"]),
            ("Flight", "optionmenu", ["Alpha", "Brovo", "Charlie", "Delta"]),
            ("Rank", "entry"),
            ("Email", "entry"),
            ("Phone", "entry"),
        ]
        
        entries = {}
        for i, (label, field_type, *options) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=f"{label}:").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            
            if field_type == "entry":
                entry = ctk.CTkEntry(form_frame, width=200)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = entry
            elif field_type == "optionmenu":
                optionmenu = ctk.CTkOptionMenu(form_frame, values=options[0], width=200)
                optionmenu.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = optionmenu
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        def save_cadet():
            try:
                cadet_data = {
                    key: entry.get() if not isinstance(entry, ctk.CTkOptionMenu) else entry.get()
                    for key, entry in entries.items()
                }
                cadet_data["created_at"] = datetime.now().isoformat()
                cadet_data["updated_at"] = datetime.now().isoformat()
                
                # Save to Firebase
                cadet_ref = self.firebase.db.child("cadets").push(cadet_data)
                messagebox.showinfo("Success", "Cadet added successfully!")
                dialog.destroy()
                self.update_cadets_display()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add cadet: {str(e)}")
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_cadet)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=10)
    
    def edit_uniform_dialog(self, uniform_id):
        if not hasattr(self, 'uniforms') or uniform_id not in self.uniforms:
            messagebox.showerror("Error", "Uniform item not found.")
            return
            
        uniform_data = self.uniforms[uniform_id]
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Uniform Item")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        fields = [
            ("Item Name", "entry", uniform_data.get('name', '')),
            ("Type", "optionmenu", ["Shirt", "Pants", "Jacket", "Shoes", "Hat", "Tie", "Belt", "Other"], uniform_data.get('type', 'Other')),
            ("Size", "entry", uniform_data.get('size', '')),
            ("Condition", "optionmenu", ["New", "Good", "Fair", "Poor", "Unusable"], uniform_data.get('condition', 'Good')),
            ("Assigned To", "entry", uniform_data.get('assignedTo', '')),
            ("Notes", "text", uniform_data.get('notes', '')),
        ]
        
        entries = {}
        for i, (label, field_type, *options) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=f"{label}:").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            
            if field_type == "entry":
                entry = ctk.CTkEntry(form_frame, width=200)
                if len(options) > 0:
                    entry.insert(0, str(options[0]))
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = entry
            elif field_type == "optionmenu":
                optionmenu = ctk.CTkOptionMenu(form_frame, values=options[0], width=200)
                if len(options) > 1:
                    optionmenu.set(options[1])
                optionmenu.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = optionmenu
            elif field_type == "text":
                text = ctk.CTkTextbox(form_frame, width=200, height=60)
                if len(options) > 0:
                    text.insert("1.0", str(options[0]))
                text.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries["notes"] = text  
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=20)
        
        def save_uniform():
            try:
                updated_data = {}
                for key, entry in entries.items():
                    if key == 'notes':
                        updated_data[key] = entry.get("1.0", tk.END).strip()
                    else:
                        updated_data[key] = entry.get() if not isinstance(entry, ctk.CTkOptionMenu) else entry.get()
                
                updated_data["updated_at"] = datetime.now().isoformat()
                
                self.firebase.db.child("uniforms").child(uniform_id).update(updated_data)
                messagebox.showinfo("Success", "Uniform item updated successfully!")
                dialog.destroy()
                
                self.update_uniforms_display()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update uniform item: {str(e)}")
        
        def delete_uniform():
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this uniform item?"):
                try:
                    self.firebase.db.child("uniforms").child(uniform_id).remove()
                    messagebox.showinfo("Success", "Uniform item deleted successfully!")
                    dialog.destroy()
                    self.update_uniforms_display()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete uniform item: {str(e)}")
        
        save_btn = ctk.CTkButton(button_frame, text="Save Changes", command=save_uniform)
        save_btn.pack(side="left", padx=5)
        
        delete_btn = ctk.CTkButton(
            button_frame, 
            text="Delete", 
            command=delete_uniform,
            fg_color=self.danger_color,
            hover_color="#d32f2f"
        )
        delete_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=5)
    
    def add_uniform_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Uniform Item")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        fields = [
            ("Item Name", "entry"),
            ("Type", "optionmenu", ["Shirt", "Pants", "Jacket", "Shoes", "Hat", "Tie", "Belt", "Other"]),
            ("Size", "entry"),
            ("Condition", "optionmenu", ["New", "Good", "Fair", "Poor", "Unusable"]),
            ("Assigned To", "entry"),
            ("Notes", "text"),
        ]
        
        entries = {}
        for i, (label, field_type, *options) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=f"{label}:").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            
            if field_type == "entry":
                entry = ctk.CTkEntry(form_frame, width=200)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = entry
            elif field_type == "optionmenu":
                optionmenu = ctk.CTkOptionMenu(form_frame, values=options[0], width=200)
                optionmenu.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = optionmenu
            elif field_type == "text":
                text = ctk.CTkTextbox(form_frame, width=200, height=60)
                text.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries["notes"] = text  
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=20)
        
        def save_uniform():
            try:
                uniform_data = {}
                for key, entry in entries.items():
                    if key == 'notes':
                        uniform_data[key] = entry.get("1.0", tk.END).strip()
                    else:
                        uniform_data[key] = entry.get() if not isinstance(entry, ctk.CTkOptionMenu) else entry.get()
                
                uniform_data["created_at"] = datetime.now().isoformat()
                uniform_data["updated_at"] = datetime.now().isoformat()
                
                self.firebase.db.child("uniforms").push(uniform_data)
                messagebox.showinfo("Success", "Uniform item added successfully!")
                dialog.destroy()
                
                if hasattr(self, 'show_uniforms'):
                    self.show_uniforms()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add uniform item: {str(e)}")
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_uniform)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=10)
    
    def add_event_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New Event")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        fields = [
            ("Event Title", "entry"),
            ("Event Type", "optionmenu", ["Drill", "PT", "Class", "Meeting", "Community Service", "Other"]),
            ("Start Date/Time", "entry"),
            ("End Date/Time", "entry"),
            ("Location", "entry"),
            ("Description", "text"),
            ("Required Uniform", "entry"),
            ("Points", "entry"),
        ]
        
        entries = {}
        for i, (label, field_type, *options) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=f"{label}:").grid(row=i, column=0, padx=5, pady=5, sticky="ne")
            
            if field_type == "entry":
                entry = ctk.CTkEntry(form_frame, width=300)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = entry
            elif field_type == "optionmenu":
                optionmenu = ctk.CTkOptionMenu(form_frame, values=options[0], width=300)
                optionmenu.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = optionmenu
            elif field_type == "text":
                text = ctk.CTkTextbox(form_frame, width=300, height=100)
                text.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = text
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20, sticky="e")
        
        def save_event():
            try:
                event_data = {}
                for key, entry in entries.items():
                    if isinstance(entry, ctk.CTkTextbox):
                        event_data[key] = entry.get("1.0", "end-1c").strip()
                    elif isinstance(entry, ctk.CTkOptionMenu):
                        event_data[key] = entry.get()
                    else:
                        event_data[key] = entry.get()
                
                try:
                    event_data["start_datetime"] = datetime.strptime(
                        event_data["start_date/time"], "%Y-%m-%d %H:%M"
                    ).isoformat()
                    event_data["end_datetime"] = datetime.strptime(
                        event_data["end_date/time"], "%Y-%m-%d %H:%M"
                    ).isoformat()
                except ValueError as ve:
                    messagebox.showerror("Error", f"Invalid date format. Please use YYYY-MM-DD HH:MM format.\n{str(ve)}")
                    return
                
                event_data["created_at"] = datetime.now().isoformat()
                event_data["updated_at"] = datetime.now().isoformat()
                
                self.firebase.db.child("events").push(event_data)
                messagebox.showinfo("Success", "Event added successfully!")
                dialog.destroy()
                
                if hasattr(self, 'show_calendar'):
                    self.show_calendar()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add event: {str(e)}")
        
        def pick_datetime(entry):
            def on_date_select():
                date = cal.get_date()
                time = f"{hour.get()}:{minute.get()}"
                entry.delete(0, "end")
                entry.insert(0, f"{date} {time}")
                top.destroy()
            
            top = ctk.CTkToplevel(dialog)
            top.title("Select Date and Time")
            
            cal_frame = ctk.CTkFrame(top)
            cal_frame.pack(padx=10, pady=5, fill="x")
            
            time_frame = ctk.CTkFrame(top)
            time_frame.pack(padx=10, pady=5, fill="x")
            
            hour = ctk.CTkOptionMenu(time_frame, values=[f"{h:02d}" for h in range(24)])
            hour.pack(side="left", padx=5)
            minute = ctk.CTkOptionMenu(time_frame, values=[f"{m:02d}" for m in range(0, 60, 5)])
            minute.pack(side="left", padx=5)
            
            btn_frame = ctk.CTkFrame(top, fg_color="transparent")
            btn_frame.pack(pady=10)
            ctk.CTkButton(btn_frame, text="OK", command=on_date_select).pack()
        
        
        ctk.CTkButton(
            form_frame, 
            text="📅", 
            width=30,
            command=lambda: pick_datetime(entries["start_date/time"])
        ).grid(row=2, column=2, padx=5)
        
        ctk.CTkButton(
            form_frame, 
            text="📅", 
            width=30,
            command=lambda: pick_datetime(entries["end_date/time"])
        ).grid(row=3, column=2, padx=5)
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_event)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="left", padx=10)
    
    def add_fundraiser_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New Fundraiser")
        dialog.geometry("500x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        fields = [
            ("Fundraiser Name", "entry"),
            ("Description", "text"),
            ("Start Date", "entry"),
            ("End Date", "entry"),
            ("Goal Amount ($)", "entry"),
            ("Item/Service", "entry"),
            ("Item Price ($)", "entry"),
            ("Contact Person", "entry"),
            ("Contact Email", "entry"),
            ("Contact Phone", "entry"),
            ("Notes", "text"),
        ]
        
        entries = {}
        for i, (label, field_type, *options) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=f"{label}:").grid(row=i, column=0, padx=5, pady=5, sticky="ne")
            
            if field_type == "entry":
                entry = ctk.CTkEntry(form_frame, width=300)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = entry
            elif field_type == "text":
                text = ctk.CTkTextbox(form_frame, width=300, height=60)
                text.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = text
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20, sticky="e")
        
        def save_fundraiser():
            try:
                fundraiser_data = {}
                for key, entry in entries.items():
                    if isinstance(entry, ctk.CTkTextbox):
                        fundraiser_data[key] = entry.get("1.0", "end-1c").strip()
                    else:
                        fundraiser_data[key] = entry.get()
                
                try:
                    fundraiser_data["start_date"] = datetime.strptime(
                        fundraiser_data["start_date"], "%Y-%m-%d"
                    ).date().isoformat()
                    fundraiser_data["end_date"] = datetime.strptime(
                        fundraiser_data["end_date"], "%Y-%m-%d"
                    ).date().isoformat()
                except ValueError as ve:
                    messagebox.showerror("Error", f"Invalid date format. Please use YYYY-MM-DD format.\n{str(ve)}")
                    return
                
                try:
                    fundraiser_data["goal_amount"] = float(fundraiser_data["goal_amount_$"].replace("$", "").strip())
                    fundraiser_data["item_price"] = float(fundraiser_data["item_price_$"].replace("$", "").strip())
                except ValueError:
                    messagebox.showerror("Error", "Please enter valid numbers for goal amount and item price")
                    return
                
                fundraiser_data["created_at"] = datetime.now().isoformat()
                fundraiser_data["updated_at"] = datetime.now().isoformat()
                fundraiser_data["total_raised"] = 0.0
                fundraiser_data["participants"] = 0
                
                self.firebase.db.child("fundraisers").push(fundraiser_data)
                messagebox.showinfo("Success", "Fundraiser added successfully!")
                dialog.destroy()
                
                if hasattr(self, 'show_fundraisers'):
                    self.show_fundraisers()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add fundraiser: {str(e)}")
        
        def pick_date(entry):
            def on_date_select():
                date = cal.get_date()
                entry.delete(0, "end")
                entry.insert(0, date)
                top.destroy()
            
            top = ctk.CTkToplevel(dialog)
            top.title("Select Date")
            
            cal_frame = ctk.CTkFrame(top)
            cal_frame.pack(padx=10, pady=5, fill="x")
            
            btn_frame = ctk.CTkFrame(top, fg_color="transparent")
            btn_frame.pack(pady=10)
            ctk.CTkButton(btn_frame, text="OK", command=on_date_select).pack()
        
        ctk.CTkButton(
            form_frame, 
            text="📅", 
            width=30,
            command=lambda: pick_date(entries["start_date"])
        ).grid(row=2, column=2, padx=5)
        
        ctk.CTkButton(
            form_frame, 
            text="📅", 
            width=30,
            command=lambda: pick_date(entries["end_date"])
        ).grid(row=3, column=2, padx=5)
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_fundraiser)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="left", padx=10)
    
    def add_contact_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add New Contact")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        fields = [
            ("First Name", "entry"),
            ("Last Name", "entry"),
            ("Organization", "entry"),
            ("Position", "entry"),
            ("Email", "entry"),
            ("Phone", "entry"),
            ("Address", "entry"),
            ("City", "entry"),
            ("State", "entry"),
            ("ZIP", "entry"),
            ("Type", "optionmenu", ["Vendor", "Speaker", "Volunteer", "Donor","AMS Dev", "Other"]),
            ("Notes", "text"),
        ]
        
        entries = {}
        for i, (label, field_type, *options) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=f"{label}:").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            
            if field_type == "entry":
                entry = ctk.CTkEntry(form_frame, width=300)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = entry
            elif field_type == "optionmenu":
                optionmenu = ctk.CTkOptionMenu(form_frame, values=options[0], width=300)
                optionmenu.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = optionmenu
            elif field_type == "text":
                text = ctk.CTkTextbox(form_frame, width=300, height=60)
                text.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                entries[label.lower().replace(" ", "_")] = text
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20, sticky="e")
        
        def save_contact():
            try:
                contact_data = {}
                for key, entry in entries.items():
                    if isinstance(entry, ctk.CTkTextbox):
                        contact_data[key] = entry.get("1.0", "end-1c").strip()
                    elif isinstance(entry, ctk.CTkOptionMenu):
                        contact_data[key] = entry.get()
                    else:
                        contact_data[key] = entry.get()
                
                contact_data["created_at"] = datetime.now().isoformat()
                contact_data["updated_at"] = datetime.now().isoformat()
                
                self.firebase.db.child("contacts").push(contact_data)
                messagebox.showinfo("Success", "Contact added successfully!")
                dialog.destroy()
                
                if hasattr(self, 'show_contacts'):
                    self.show_contacts()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add contact: {str(e)}")
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_contact)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="left", padx=10)
    
    def generate_report(self, report_type):
        try:
            report_window = ctk.CTkToplevel(self.root)
            report_window.title(f"Report: {report_type}")
            report_window.geometry("900x600")
            
            text_frame = ctk.CTkFrame(report_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            text_widget = ctk.CTkTextbox(text_frame, wrap="none")
            text_widget.pack(fill="both", expand=True, padx=5, pady=5)
            
            v_scroll = ctk.CTkScrollbar(text_widget, command=text_widget.yview)
            v_scroll.pack(side="right", fill="y")
            text_widget.configure(yscrollcommand=v_scroll.set)
            
            h_scroll = ctk.CTkScrollbar(text_widget, orientation="horizontal", command=text_widget.xview)
            h_scroll.pack(side="bottom", fill="x")
            text_widget.configure(xscrollcommand=h_scroll.set)
            
            if report_type == "Cadet Roster":
                self._generate_cadet_roster(text_widget)
            elif report_type == "Event Attendance":
                self._generate_event_attendance(text_widget)
            elif report_type == "Fundraiser Summary":
                self._generate_fundraiser_summary(text_widget)
            elif report_type == "Uniform Inventory":
                self._generate_uniform_inventory(text_widget)
            elif report_type == "Contact Directory":
                self._generate_contact_directory(text_widget)
            else:
                text_widget.insert("end", f"Report type '{report_type}' is not implemented yet.\n")
            
            button_frame = ctk.CTkFrame(report_window)
            button_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            def export_report():
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{report_type.replace(' ', '_')}_{timestamp}.txt"
                    
                    report_content = text_widget.get("1.0", "end-1c")
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    
                    messagebox.showinfo("Export Successful", f"Report exported to:\n{os.path.abspath(filename)}")
                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")
            
            export_btn = ctk.CTkButton(
                button_frame, 
                text="Export to File",
                command=export_report
            )
            export_btn.pack(side="right", padx=5)
            
            close_btn = ctk.CTkButton(
                button_frame,
                text="Close",
                command=report_window.destroy
            )
            close_btn.pack(side="right", padx=5)
            
        except Exception as e:
            messagebox.showerror("Report Error", f"Failed to generate report: {str(e)}")
    
    def _generate_cadet_roster(self, text_widget):
        try:
            text_widget.insert("end", "AFJROTC CADET ROSTER\n")
            text_widget.insert("end", "=" * 80 + "\n\n")
            text_widget.insert("end", f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            companies = {}
            companies = {}
            for cadet_id, cadet in self.cadets.items():
                company = cadet.get('company', 'U')
                flight = cadet.get('flight', '0')
                
                if company not in companies:
                    companies[company] = {}
                if flight not in companies[company]:
                    companies[company][flight] = []
                
                companies[company][flight].append(cadet)
            
            for company in sorted(companies.keys()):
                text_widget.insert("end", f"COMPANY {company}\n")
                text_widget.insert("end", "-" * 80 + "\n")
                
                for flight in sorted(companies[company].keys()):
                    text_widget.insert("end", f"FLIGHT {flight}:\n")
                    
                    cadets = sorted(
                        companies[company][flight],
                        key=lambda x: (x.get('last_name', ''), x.get('first_name', ''))
                    )
                    
                    for cadet in cadets:
                        text_widget.insert(
                            "end",
                            f"{cadet.get('last_name', 'N/A')}, {cadet.get('first_name', 'N/A')} "
                            f"(Grade: {cadet.get('grade', 'N/A')}, "
                            f"Rank: {cadet.get('rank', 'N/A')})\n"
                        )
                    
                    text_widget.insert("end", "\n")
                
                text_widget.insert("end", "\n")
            
            total_cadets = len(self.cadets)
            text_widget.insert("end", f"TOTAL CADETS: {total_cadets}\n")
            
        except Exception as e:
            text_widget.insert("end", f"\nError generating cadet roster: {str(e)}\n")
    
    def _generate_event_attendance(self, text_widget):
        text_widget.insert("end", "EVENT ATTENDANCE REPORT\n")
        text_widget.insert("end", "=" * 80 + "\n\n")
        text_widget.insert("end", "This report is not yet implemented.\n")
    
    def _generate_fundraiser_summary(self, text_widget):
        text_widget.insert("end", "FUNDRAISER SUMMARY REPORT\n")
        text_widget.insert("end", "=" * 80 + "\n\n")
        text_widget.insert("end", "This report is not yet implemented.\n")
    
    def _generate_uniform_inventory(self, text_widget):
        text_widget.insert("end", "UNIFORM INVENTORY REPORT\n")
        text_widget.insert("end", "=" * 80 + "\n\n")
        text_widget.insert("end", "This report is not yet implemented.\n")
    
    def edit_contact_dialog(self, contact_id):
        if not hasattr(self, 'contacts') or contact_id not in self.contacts:
            messagebox.showerror("Error", "Contact not found")
            return
            
        contact = self.contacts[contact_id]
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Contact")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        fields = [
            ("First Name", "entry"),
            ("Last Name", "entry"),
            ("Organization", "entry"),
            ("Position", "entry"),
            ("Email", "entry"),
            ("Phone", "entry"),
            ("Type", "optionmenu", ["Vendor", "School", "Military", "Other"]),
            ("Notes", "text")
        ]
        
        entries = {}
        
        for i, (label, field_type, *extra) in enumerate(fields):
            ctk.CTkLabel(
                form_frame,
                text=label + ":",
                font=("Arial", 12)
            ).grid(row=i, column=0, padx=5, pady=5, sticky="e")
            
            if field_type == "optionmenu":
                options = extra[0] if extra else []
                default = contact.get(label.lower().replace(" ", "_"), "")
                entry = ctk.CTkOptionMenu(
                    form_frame,
                    values=options,
                    font=("Arial", 12)
                )
                if default in options:
                    entry.set(default)
                elif options:
                    entry.set(options[0])
            elif field_type == "text":
                entry = ctk.CTkTextbox(form_frame, height=80, width=300)
                entry.insert("1.0", contact.get(label.lower().replace(" ", "_"), ""))
            else: 
                entry = ctk.CTkEntry(form_frame, width=300)
                entry.insert(0, contact.get(label.lower().replace(" ", "_"), ""))
            
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            entries[label.lower().replace(" ", "_")] = entry
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=20)
        
        def save_contact():
            try:
                contact_data = {}
                for key, entry in entries.items():
                    if isinstance(entry, ctk.CTkTextbox):
                        contact_data[key] = entry.get("1.0", "end-1c").strip()
                    elif isinstance(entry, ctk.CTkOptionMenu):
                        contact_data[key] = entry.get()
                    else:
                        contact_data[key] = entry.get()
                
                contact_data["updated_at"] = datetime.now().isoformat()
                
                self.firebase.db.child("contacts").child(contact_id).update(contact_data)
                
                if hasattr(self, 'current_user') and self.current_user:
                    analytics.capture(
                        event_name='contact_updated',
                        distinct_id=self.current_user.get('email', 'unknown'),
                        properties={
                            'contact_id': contact_id,
                            'updated_fields': list(contact_data.keys())
                        }
                    )
                
                messagebox.showinfo("Success", "Contact updated successfully!")
                dialog.destroy()
                
                if hasattr(self, 'show_contacts'):
                    self.show_contacts()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update contact: {str(e)}")
        
        save_btn = ctk.CTkButton(button_frame, text="Save Changes", command=save_contact)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="left", padx=10)
    
    def delete_contact(self, contact_id):
        if not hasattr(self, 'contacts') or contact_id not in self.contacts:
            messagebox.showerror("Error", "Contact not found")
            return
            
        if not messagebox.askyesno("Confirm Delete", 
                                 "Are you sure you want to delete this contact? This action cannot be undone."):
            return
            
        try:
            self.firebase.db.child("contacts").child(contact_id).remove()
            
            if hasattr(self, 'current_user') and self.current_user:
                analytics.capture(
                    event_name='contact_deleted',
                    distinct_id=self.current_user.get('email', 'unknown'),
                    properties={'contact_id': contact_id}
                )
            
            messagebox.showinfo("Success", "Contact deleted successfully!")
            
            if hasattr(self, 'show_contacts'):
                self.show_contacts()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete contact: {str(e)}")
    
    def _generate_contact_directory(self, text_widget):
        text_widget.insert("end", "CONTACT DIRECTORY\n")
        text_widget.insert("end", "=" * 80 + "\n\n")
        text_widget.insert("end", "This report is not yet implemented.\n")
    
    def change_theme(self, event=None):
        try:
            current_mode = ctk.get_appearance_mode()
            new_mode = "Dark" if current_mode == "Light" else "Light"
            
            ctk.set_appearance_mode(new_mode)
            
            if hasattr(self, 'settings'):
                self.settings['theme'] = new_mode.lower()
                if hasattr(self, '_save_settings'):
                    self._save_settings()
            
            messagebox.showinfo("Theme Updated", f"Theme changed to {new_mode} mode.")
            
            if hasattr(self, 'main_container'):
                self.main_container.configure(fg_color=("gray90", "gray14") if new_mode == "Light" else ("gray14", "gray90"))
            
        except Exception as e:
            messagebox.showerror("Theme Error", f"Failed to change theme: {str(e)}")
    
    def _update_dashboard_stats(self):
        try:
            if not hasattr(self, 'content_frame') or not self.content_frame:
                return
                
            if hasattr(self, 'cadets'):
                cadet_count = len(self.cadets)
                if hasattr(self, 'cadet_count_label'):
                    self.cadet_count_label.configure(text=str(cadet_count))
            
        except Exception as e:
            print(f"Error updating dashboard stats: {e}")
            self.root.after(30000, self.update_dashboard)

    def update_upcoming_events(self, update_dashboard=False):
        try:
            today = datetime.now().date()
            seven_days_later = today + timedelta(days=7)
            new_upcoming_events = []
            
            for event_id, event in self.events.items():
                try:
                    if not isinstance(event, dict) or 'date' not in event:
                        continue
                        
                    event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                    if today <= event_date <= seven_days_later:
                        new_upcoming_events.append({
                            'id': event_id,
                            'title': event.get('title', 'Untitled Event'),
                            'date': event.get('date', ''),
                            'time': event.get('time', ''),
                            'location': event.get('location', 'TBD')
                        })
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"Skipping invalid event {event_id}: {e}")
                    continue
            
            try:
                new_upcoming_events.sort(key=lambda x: (
                    datetime.strptime(x['date'], '%Y-%m-%d').date(),
                    x.get('time', '23:59')
                ))
            except (KeyError, ValueError) as e:
                print(f"Error sorting events: {e}")
                return
            
            if (hasattr(self, 'upcoming_events') and 
                self.upcoming_events == new_upcoming_events and 
                not update_dashboard):
                return
                
            self.upcoming_events = new_upcoming_events
            
            if hasattr(self, 'upcoming_events_list') and self.upcoming_events_list.winfo_exists():
                try:
                    for widget in self.upcoming_events_list.winfo_children():
                        try:
                            widget.destroy()
                        except:
                            continue
                    
                    for event in self.upcoming_events:
                        try:
                            event_frame = ctk.CTkFrame(self.upcoming_events_list, fg_color=self.bg_color)
                            event_frame.pack(fill="x", pady=5, padx=5)
                            
                            event_date = datetime.strptime(event['date'], '%Y-%m-%d').strftime('%a, %b %d')
                            date_label = ctk.CTkLabel(
                                event_frame,
                                text=event_date,
                                font=("Arial", 12, "bold"),
                                text_color=self.text_color,
                                width=100
                            )
                            date_label.pack(side="left", padx=5)
                            
                            details_frame = ctk.CTkFrame(event_frame, fg_color="transparent")
                            details_frame.pack(side="left", fill="x", expand=True, padx=5)
                            
                            title_label = ctk.CTkLabel(
                                details_frame,
                                text=event.get('title', 'Untitled Event'),
                                font=("Arial", 12, "bold"),
                                text_color=self.text_color,
                                anchor="w"
                            )
                            title_label.pack(fill="x")
                            
                            location_text = f"{event.get('time', '')} • {event.get('location', 'TBD')}" if event.get('time') else event.get('location', 'TBD')
                            location_label = ctk.CTkLabel(
                                details_frame,
                                text=location_text,
                                font=("Arial", 11),
                                text_color=self.text_color,
                                anchor="w"
                            )
                            location_label.pack(fill="x")
                            
                            view_btn = ctk.CTkButton(
                                event_frame,
                                text="View",
                                command=lambda eid=event['id']: self.edit_event_dialog(eid),
                                width=80,
                                height=24,
                                font=("Arial", 10)
                            )
                            view_btn.pack(side="right", padx=5, pady=5)
                        except Exception as widget_error:
                            print(f"Error creating event widget: {widget_error}")
                            continue
                    
                    if not self.upcoming_events:
                        try:
                            ctk.CTkLabel(
                                self.upcoming_events_list,
                                text="No upcoming events in the next 7 days.",
                                font=("Arial", 12, "italic"),
                                text_color=self.text_color
                            ).pack(pady=20)
                        except Exception as label_error:
                            print(f"Error creating 'no events' label: {label_error}")
                            
                except Exception as ui_error:
                    print(f"Error in upcoming events UI: {ui_error}")
            
            if update_dashboard and hasattr(self, 'dashboard_frame') and self.dashboard_frame.winfo_exists():
                try:
                    if not getattr(self, '_updating_dashboard', False):
                        self.root.after(100, self.update_dashboard)
                except Exception as update_error:
                    print(f"Error scheduling dashboard update: {update_error}")
                    
        except Exception as e:
            error_msg = f"Error in update_upcoming_events: {str(e)}"
            print(error_msg)
            if hasattr(self, 'current_user'):
                try:
                    user_id = self.current_user.get('localId', 'unknown')
                    print(f"Dashboard updated with {len(self.cadets)} cadets")
                except Exception as log_error:
                    print(f"Error logging activity: {log_error}")

def update_dashboard(self, force_update=False):
    try:
        if not hasattr(self, 'dashboard_frame') or not self.dashboard_frame.winfo_exists():
            return
            
        if getattr(self, '_updating_dashboard', False):
            return
            
        self._updating_dashboard = True
            
        if hasattr(self, '_dashboard_update_id'):
            try:
                self.root.after_cancel(self._dashboard_update_id)
            except Exception as cancel_error:
                print(f"Error cancelling pending update: {cancel_error}")
        
        try:
            self._update_dashboard_stats()
            
            if hasattr(self, 'update_upcoming_events'):
                self.update_upcoming_events(update_dashboard=False)
            
            if hasattr(self, 'cadets_list_frame') and self.cadets_list_frame.winfo_exists():
                self._update_cadets_list()
                
            if hasattr(self, 'events_list_frame') and self.events_list_frame.winfo_exists():
                self._update_events_list()
                
            if hasattr(self, 'jobs_list_frame') and self.jobs_list_frame.winfo_exists():
                self._update_jobs_list()
                
            if hasattr(self, 'fundraisers_list_frame') and self.fundraisers_list_frame.winfo_exists():
                self._update_fundraisers_list()
            
        except Exception as update_error:
            import traceback
            error_msg = f"Error in dashboard update: {str(update_error)}\n{traceback.format_exc()}"
            print(error_msg)
        
        try:
            self._dashboard_update_id = self.root.after(30000, lambda: self.update_dashboard(force_update))
        except Exception as update_err:
            print(f"Error scheduling next update: {str(update_err)}")
            
    except Exception as err:
        import traceback
        error_msg = f"Error in update_dashboard: {str(err)}\n{traceback.format_exc()}"
        print(error_msg)
        
    finally:
        self._updating_dashboard = False

    def _update_dashboard_stats(self):
        try:
            if not hasattr(self, 'stats_card') or not self.stats_card.winfo_exists():
                return
            
            for widget in self.stats_card.winfo_children():
                if hasattr(widget, '_text') and widget._text != "Quick Stats":
                    widget.destroy()
            
            stats = {
                'total_cadets': 0,
                'grade_counts': {'9': 0, '10': 0, '11': 0, '12': 0},
                'active_events': 0,
                'pending_jobs': 0,
                'active_fundraisers': 0,
                'total_community_service': 0,
                'cadets_needing_hours': 0
            }
            
            if hasattr(self, 'cadets') and isinstance(self.cadets, dict):
                stats['total_cadets'] = len(self.cadets)
                
                for cadet in self.cadets.values():
                    if not isinstance(cadet, dict):
                        continue
                        
                    grade = str(cadet.get('grade', '')).strip()
                    if grade in stats['grade_counts']:
                        stats['grade_counts'][grade] += 1
                    
                    try:
                        hours = float(cadet.get('communityServiceHours', 0))
                        stats['total_community_service'] += hours
                        if hours < 16:
                            stats['cadets_needing_hours'] += 1
                    except (ValueError, TypeError):
                        pass
            
            if hasattr(self, 'events') and isinstance(self.events, dict):
                now = datetime.now()
                for event in self.events.values():
                    if not isinstance(event, dict):
                        continue
                        
                    try:
                        event_date = datetime.strptime(event.get('date', ''), '%Y-%m-%d')
                        if event_date >= now:
                            stats['active_events'] += 1
                    except (ValueError, TypeError):
                        pass
            
            if hasattr(self, 'jobs') and isinstance(self.jobs, dict):
                stats['pending_jobs'] = len([
                    j for j in self.jobs.values() 
                    if isinstance(j, dict) and j.get('status', '').lower() in ['pending', 'in progress']
                ])
            
            if hasattr(self, 'fundraisers') and isinstance(self.fundraisers, dict):
                now = datetime.now()
                for fundraiser in self.fundraisers.values():
                    if not isinstance(fundraiser, dict):
                        continue
                        
                    try:
                        end_date = datetime.strptime(fundraiser.get('endDate', ''), '%Y-%m-%d')
                        if end_date >= now and fundraiser.get('status', '').lower() == 'active':
                            stats['active_fundraisers'] += 1
                    except (ValueError, TypeError):
                        pass
            
            stats_data = [
                ("Total Cadets", stats['total_cadets'], "👥"),
                ("9th Graders", stats['grade_counts']['9'], "9️⃣"),
                ("10th Graders", stats['grade_counts']['10'], "🔟"),
                ("11th Graders", stats['grade_counts']['11'], "1️⃣1️⃣"),
                ("12th Graders", stats['grade_counts']['12'], "1️⃣2️⃣"),
                ("Upcoming Events", stats['active_events'], "📅"),
                (f"Pending Jobs", stats['pending_jobs'], "📋"),
                ("Active Fundraisers", stats['active_fundraisers'], "💰"),
                ("Total CS Hours", f"{stats['total_community_service']:.1f}", "⏱️"),
                ("Cadets Needing Hours", stats['cadets_needing_hours'], "⚠️")
            ]
            
            stats_frame = ctk.CTkFrame(self.stats_card, fg_color="transparent")
            stats_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            stats_count = len(stats_data)
            max_cols = 4  
            min_cols = 2
            
            cols = min(max_cols, max(min_cols, stats_count // 2))
            
            for i in range(cols):
                stats_frame.columnconfigure(i, weight=1, uniform='stats_col')
            
            for i, (label, value, emoji) in enumerate(stats_data):
                row = i // cols
                col = i % cols
                
                stat_card = ctk.CTkFrame(
                    stats_frame, 
                    fg_color="#f0f0f0", 
                    corner_radius=8,
                    border_width=1,
                    border_color="#e0e0e0"
                )
                stat_card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                stat_card.grid_propagate(False)
                
                value_label = ctk.CTkLabel(
                    stat_card,
                    text=f"{emoji} {value}",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.primary_color
                )
                value_label.pack(pady=(12, 2), padx=10, anchor="center")
                
                label_widget = ctk.CTkLabel(
                    stat_card,
                    text=label,
                    font=ctk.CTkFont(size=11),
                    text_color="#666666"
                )
                label_widget.pack(pady=(0, 10), padx=10, anchor="center")
                
                stat_card.grid_rowconfigure(0, weight=1)
                stat_card.grid_columnconfigure(0, weight=1)
                
        except Exception as e:
            print(f"Error updating dashboard stats: {e}")
            import traceback
            traceback.print_exc()
            
            error_frame = ctk.CTkFrame(self.stats_card, fg_color="#ffebee", corner_radius=5)
            error_frame.pack(fill="x", padx=10, pady=5)
            
            error_label = ctk.CTkLabel(
                error_frame,
                text=f"Error loading statistics: {str(e)}",
                text_color="#c62828",
                font=ctk.CTkFont(size=11, weight="bold")
            )
            error_label.pack(padx=10, pady=8)
        
        stats_data = [
            ("Total Cadets", str(total_cadets), "👥"),
            ("Active Events", str(active_events), "📅"),
            ("Pending Jobs", str(pending_jobs), "📋"),
            ("Active Fundraisers", str(active_fundraisers), "💰")
        ]
        
        stats_grid = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        stats_grid.pack(fill="both", expand=True, padx=5, pady=5)
        
        cols = 4
        for i in range(cols):
            stats_grid.columnconfigure(i, weight=1)
        
        for i, (label, value, emoji) in enumerate(stats_data):
            row = i // cols
            col = i % cols
            
            stat_card = ctk.CTkFrame(stats_grid, fg_color="#f0f0f0", corner_radius=8)
            stat_card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            stat_card.grid_propagate(False)
            
            ctk.CTkLabel(
                stat_card,
                text=f"{emoji} {value}",
                font=("Arial", 20, "bold"),
                text_color=self.primary_color
            ).pack(pady=(10, 2))
            
            ctk.CTkLabel()
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
        
    header_frame = ctk.CTkFrame(scrollable_frame, fg_color=self.primary_color, corner_radius=5)
    header_frame.pack(fill="x", pady=(0, 5), padx=5)
        
    headers = ["Name", "Grade", "Flight", "CS Hours", ""]
    col_weights = [3, 1, 1, 1, 1]
        
    for col, (header, weight) in enumerate(zip(headers, col_weights)):
        frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        frame.grid(row=0, column=col, padx=2, pady=2, sticky="nsew")
        header_frame.columnconfigure(col, weight=weight)
            
        label = ctk.CTkLabel(
                frame, 
                text=header, 
                font=("Arial Bold", 12), 
                text_color="white"
            )
        label.pack(fill="x", padx=5, pady=5)
        
        if self.cadets:
            sorted_cadets = sorted(
                self.cadets.items(),
                key=lambda x: (x[1].get('lastName', '').lower(), 
                             x[1].get('firstName', '').lower())
            )
            
            for cadet_id, cadet in sorted_cadets:
                card = ctk.CTkFrame(scrollable_frame, fg_color="#f5f5f5", corner_radius=5)
                card.pack(fill="x", pady=2, padx=5)
                
                for col, weight in enumerate(col_weights):
                    card.columnconfigure(col, weight=weight)
                
                name_frame = ctk.CTkFrame(card, fg_color="transparent")
                name_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
                
                name = f"{cadet.get('rank', '')} {cadet.get('firstName', 'N/A')} {cadet.get('lastName', 'N/A')}".strip()
                name_label = ctk.CTkLabel(
                    name_frame, 
                    text=name, 
                    font=("Arial", 12),
                    anchor="w"
                )
                name_label.pack(fill="x")
                
                grade_frame = ctk.CTkFrame(card, fg_color="transparent")
                grade_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
                
                grade = str(cadet.get('grade', 'N/A'))
                grade_label = ctk.CTkLabel(
                    grade_frame, 
                    text=grade, 
                    font=("Arial", 12)
                )
                grade_label.pack(fill="x")
                
                flight_frame = ctk.CTkFrame(card, fg_color="transparent")
                flight_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
                
                flight = cadet.get('flight', 'N/A')
                flight_label = ctk.CTkLabel(
                    flight_frame, 
                    text=flight, 
                    font=("Arial", 12)
                )
                flight_label.pack(fill="x")
                
                cs_frame = ctk.CTkFrame(card, fg_color="transparent")
                cs_frame.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
                
                cs_hours = float(cadet.get('communityServiceHours', 0))
                cs_color = self.success_color if cs_hours >= 16 else "#555555"
                cs_text = f"{cs_hours:.1f}"
                if cs_hours >= 16:
                    cs_text += " ✓"
                
                cs_label = ctk.CTkLabel(
                    cs_frame, 
                    text=cs_text, 
                    font=("Arial", 12), 
                    text_color=cs_color
                )
                cs_label.pack(fill="x")
                
                button_frame = ctk.CTkFrame(card, fg_color="transparent")
                button_frame.grid(row=0, column=4, padx=5, pady=5, sticky="e")
                
                edit_icon = self.create_icon(button_frame, self.edit_icon_text, "white")
                delete_icon = self.create_icon(button_frame, self.delete_icon_text, "white")
                
                edit_btn = ctk.CTkButton(
                    button_frame, 
                    text="", 
                    image=edit_icon,
                    width=30, 
                    height=30,
                    fg_color=self.accent_color, 
                    hover_color="#7ba4d1",
                    command=lambda cid=cadet_id: self.edit_cadet_dialog(cid)
                )
                edit_btn.pack(side="left", padx=2)
                
                delete_btn = ctk.CTkButton(
                    button_frame, 
                    text="", 
                    image=delete_icon,
                    width=30, 
                    height=30,
                    fg_color=self.danger_color, 
                    hover_color="#c43e3e",
                    command=lambda cid=cadet_id: self.delete_cadet(cid)
                )
                delete_btn.pack(side="left", padx=2)
        else:
            empty_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=40)
            
            empty_label = ctk.CTkLabel(
                empty_frame, 
                text="No cadets found. Click 'Add Cadet' to add a new cadet.", 
                font=("Arial", 14), 
                text_color="#555555"
            )
            empty_label.pack(expand=True)
            
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        self._updating_dashboard = False

    
if __name__ == "__main__":
    root = ctk.CTk()
    app = AFJROTCApp(root)
    root.mainloop()