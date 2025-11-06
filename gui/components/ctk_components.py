"""
CustomTkinter components for MarkItDown GUI.

This module provides reusable CustomTkinter components.
"""

import customtkinter as ctk
from typing import Optional, Callable, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CTkTooltip:
    """Tooltip widget for CustomTkinter components."""

    def __init__(
        self,
        widget: ctk.CTkBaseClass,
        text: str,
        delay: float = 0.5,
        **kwargs
    ) -> None:
        """
        Initialize tooltip.
        
        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text
            delay: Delay before showing tooltip (seconds)
            **kwargs: Additional arguments for tooltip window
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window: Optional[ctk.CTkToplevel] = None
        self.tooltip_id: Optional[str] = None
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, event: Any) -> None:
        """Show tooltip after delay."""
        self.tooltip_id = self.widget.after(int(self.delay * 1000), self._show_tooltip)

    def _on_leave(self, event: Any) -> None:
        """Hide tooltip."""
        if self.tooltip_id:
            self.widget.after_cancel(self.tooltip_id)
            self.tooltip_id = None
        self._hide_tooltip()

    def _show_tooltip(self) -> None:
        """Display tooltip window."""
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20

        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(
            self.tooltip_window,
            text=self.text,
            corner_radius=6,
            fg_color=("gray70", "gray30"),
            padx=10,
            pady=5,
        )
        label.pack()

    def _hide_tooltip(self) -> None:
        """Hide tooltip window."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class CTkAnimatedButton(ctk.CTkButton):
    """Button with animation support."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize animated button."""
        self._animation_duration = kwargs.pop("animation_duration", 200)
        super().__init__(*args, **kwargs)
        self._original_fg_color = self.cget("fg_color")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event: Any) -> None:
        """Animate on hover."""
        hover_color = self.cget("hover_color")
        if hover_color:
            self._animate_color(self._original_fg_color, hover_color)

    def _on_leave(self, event: Any) -> None:
        """Animate on leave."""
        self._animate_color(self.cget("hover_color"), self._original_fg_color)

    def _animate_color(self, from_color: tuple, to_color: tuple) -> None:
        """Animate color transition."""
        # Simple animation - can be enhanced
        steps = 10
        delay = self._animation_duration // steps

        def animate_step(step: int) -> None:
            if step <= steps:
                # Interpolate color
                r = int(from_color[0] + (to_color[0] - from_color[0]) * step / steps)
                g = int(from_color[1] + (to_color[1] - from_color[1]) * step / steps)
                b = int(from_color[2] + (to_color[2] - from_color[2]) * step / steps)
                self.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
                self.after(delay, lambda: animate_step(step + 1))

        animate_step(0)


class CTkIconButton(ctk.CTkButton):
    """Button with icon support."""

    def __init__(
        self,
        master: Any,
        icon_path: Optional[str] = None,
        icon_size: tuple = (20, 20),
        **kwargs
    ) -> None:
        """
        Initialize icon button.
        
        Args:
            master: Parent widget
            icon_path: Path to icon image
            icon_size: Icon size (width, height)
            **kwargs: Additional CTkButton arguments
        """
        self.icon_image: Optional[ctk.CTkImage] = None
        if icon_path and Path(icon_path).exists():
            try:
                from PIL import Image
                image = Image.open(icon_path)
                self.icon_image = ctk.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=icon_size
                )
            except Exception as e:
                logger.warning(f"Failed to load icon {icon_path}: {e}")

        if self.icon_image:
            kwargs["image"] = self.icon_image
            if "text" not in kwargs:
                kwargs["text"] = ""

        super().__init__(master, **kwargs)


class CTkSidebar(ctk.CTkFrame):
    """Retractable sidebar with navigation menu."""

    def __init__(
        self,
        master: Any,
        width: int = 250,
        collapsed_width: int = 60,
        **kwargs
    ) -> None:
        """
        Initialize sidebar.
        
        Args:
            master: Parent widget
            width: Expanded width
            collapsed_width: Collapsed width
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.width = width
        self.collapsed_width = collapsed_width
        self.is_collapsed = False
        self._animation_duration = 300

        # Header
        self.header = ctk.CTkFrame(self)
        self.header.pack(fill="x", padx=5, pady=5)

        self.toggle_button = CTkIconButton(
            self.header,
            text="☰",
            command=self.toggle,
            width=40,
            height=40,
        )
        self.toggle_button.pack(side="left", padx=5)

        self.title_label = ctk.CTkLabel(
            self.header,
            text="MarkItDown",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.title_label.pack(side="left", padx=10)

        # Navigation menu
        self.nav_frame = ctk.CTkFrame(self)
        self.nav_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.menu_items: list[dict] = []

    def add_menu_item(
        self,
        text: str,
        command: Optional[Callable] = None,
        icon_path: Optional[str] = None,
    ) -> ctk.CTkButton:
        """
        Add menu item to sidebar.
        
        Args:
            text: Menu item text
            command: Command to execute on click
            icon_path: Optional icon path
            
        Returns:
            Created button widget
        """
        button = CTkIconButton(
            self.nav_frame,
            text=text if not self.is_collapsed else "",
            command=command,
            icon_path=icon_path,
            anchor="w",
            width=self.width - 20 if not self.is_collapsed else self.collapsed_width - 20,
        )
        button.pack(fill="x", padx=5, pady=2)

        self.menu_items.append({
            "button": button,
            "text": text,
            "command": command,
            "icon_path": icon_path,
        })

        return button

    def toggle(self) -> None:
        """Toggle sidebar collapsed/expanded state."""
        self.is_collapsed = not self.is_collapsed
        self._animate_width()

    def _animate_width(self) -> None:
        """Animate sidebar width change."""
        target_width = self.collapsed_width if self.is_collapsed else self.width
        current_width = self.winfo_width()

        steps = 20
        delay = self._animation_duration // steps
        step_size = (target_width - current_width) / steps

        def animate_step(step: int) -> None:
            if step <= steps:
                new_width = int(current_width + step_size * step)
                self.configure(width=new_width)
                # Update menu items
                for item in self.menu_items:
                    item["button"].configure(
                        width=new_width - 20,
                        text="" if self.is_collapsed else item["text"]
                    )
                self.after(delay, lambda: animate_step(step + 1))

        animate_step(0)


class CTkStatusBar(ctk.CTkFrame):
    """Status bar with real-time information."""

    def __init__(self, master: Any, **kwargs) -> None:
        """Initialize status bar."""
        super().__init__(master, **kwargs)
        self.configure(height=30)

        # Left side - status messages
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            anchor="w",
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        # Right side - additional info
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(side="right", padx=10, pady=5)

        self.progress_label = ctk.CTkLabel(
            self.info_frame,
            text="",
            width=100,
        )
        self.progress_label.pack(side="left", padx=5)

    def set_status(self, text: str) -> None:
        """
        Set status message.
        
        Args:
            text: Status text
        """
        self.status_label.configure(text=text)

    def set_progress(self, text: str) -> None:
        """
        Set progress information.
        
        Args:
            text: Progress text
        """
        self.progress_label.configure(text=text)


class CTkTopBar(ctk.CTkFrame):
    """Top bar with user profile and quick settings."""

    def __init__(self, master: Any, **kwargs) -> None:
        """Initialize top bar."""
        super().__init__(master, **kwargs)
        self.configure(height=50)

        # Left side - app title/logo
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.title_frame.pack(side="left", padx=10, pady=5)

        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="MarkItDown",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.title_label.pack(side="left", padx=5)

        # Right side - user profile and settings
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.pack(side="right", padx=10, pady=5)

        # Theme toggle
        self.theme_button = CTkIconButton(
            self.actions_frame,
            text="🌓",
            command=self._toggle_theme,
            width=40,
            height=40,
        )
        self.theme_button.pack(side="right", padx=5)

        # Settings button
        self.settings_button = CTkIconButton(
            self.actions_frame,
            text="⚙️",
            command=self._open_settings,
            width=40,
            height=40,
        )
        self.settings_button.pack(side="right", padx=5)

        # User profile (placeholder)
        self.profile_button = CTkIconButton(
            self.actions_frame,
            text="👤",
            command=self._open_profile,
            width=40,
            height=40,
        )
        self.profile_button.pack(side="right", padx=5)

        self.theme_callback: Optional[Callable] = None
        self.settings_callback: Optional[Callable] = None
        self.profile_callback: Optional[Callable] = None

    def set_theme_callback(self, callback: Callable) -> None:
        """Set theme toggle callback."""
        self.theme_callback = callback

    def set_settings_callback(self, callback: Callable) -> None:
        """Set settings callback."""
        self.settings_callback = callback

    def set_profile_callback(self, callback: Callable) -> None:
        """Set profile callback."""
        self.profile_callback = callback

    def _toggle_theme(self) -> None:
        """Toggle theme."""
        if self.theme_callback:
            self.theme_callback()

    def _open_settings(self) -> None:
        """Open settings."""
        if self.settings_callback:
            self.settings_callback()

    def _open_profile(self) -> None:
        """Open profile."""
        if self.profile_callback:
            self.profile_callback()


class CTkPreviewPanel(ctk.CTkFrame):
    """Preview panel with toggle functionality."""

    def __init__(
        self,
        master: Any,
        width: int = 400,
        **kwargs
    ) -> None:
        """
        Initialize preview panel.
        
        Args:
            master: Parent widget
            width: Panel width
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.width = width
        self.is_visible = True
        self._animation_duration = 300

        # Header
        self.header = ctk.CTkFrame(self)
        self.header.pack(fill="x", padx=5, pady=5)

        self.title_label = ctk.CTkLabel(
            self.header,
            text="Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.title_label.pack(side="left", padx=10)

        self.toggle_button = CTkIconButton(
            self.header,
            text="◀",
            command=self.toggle,
            width=30,
            height=30,
        )
        self.toggle_button.pack(side="right", padx=5)

        # Content area
        self.content = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        self.content.pack(fill="both", expand=True, padx=5, pady=5)

    def toggle(self) -> None:
        """Toggle panel visibility."""
        self.is_visible = not self.is_visible
        self._animate_visibility()

    def _animate_visibility(self) -> None:
        """Animate visibility change."""
        if self.is_visible:
            self.toggle_button.configure(text="◀")
            self.content.pack(fill="both", expand=True, padx=5, pady=5)
        else:
            self.toggle_button.configure(text="▶")
            self.content.pack_forget()

    def set_content(self, text: str) -> None:
        """
        Set preview content.
        
        Args:
            text: Preview text
        """
        self.content.delete("1.0", "end")
        self.content.insert("1.0", text)

    def clear(self) -> None:
        """Clear preview content."""
        self.content.delete("1.0", "end")

