"""Display utilities using Rich library with refined UI design."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.padding import Padding
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from src.features.health_check import AccountHealth

# UI Constants
MENU_WIDTH = 55
LEFT_PADDING = 1
BORDER_STYLE = "cyan"


class Display:
    """Rich-based display utilities for the CLI with strict styling."""

    def __init__(self) -> None:
        self.console = Console()

    def clear(self) -> None:
        """Clear the terminal."""
        self.console.clear()

    def _output(self, renderable: Any, **kwargs: Any) -> None:
        """Print a renderable with consistent left padding."""
        self.console.print(Padding(renderable, (0, 0, 0, LEFT_PADDING)), **kwargs)

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print to console with padding."""
        if args:
            # Wrap content in padding
            content = args[0] if len(args) == 1 else Group(*args)
            self._output(content, **kwargs)
        else:
            self.console.print(**kwargs)

    def _center_text(self, text: str, style: str | None = None) -> Text:
        """Create centered text object."""
        return Text(text, style=style, justify="center")

    def divider(self, char: str = "═") -> None:
        """Print a full-width divider using the specified character."""
        line = char * MENU_WIDTH
        self._output(line, style=BORDER_STYLE)

    def banner(self) -> None:
        """Display application banner with aligned box."""
        from rich import box

        content = Group(
            Align.center(Text("Orca Fleet", style="bold white")),
            Align.center(Text("Multi-Account Telegram Manager v0.2.0", style="cyan")),
            Align.center(
                Text("github.com/pinkorca/orca-fleet", style="blue underline")
            ),
        )

        panel = Panel(
            content,
            width=MENU_WIDTH,
            border_style=BORDER_STYLE,
            padding=(0, 1),
            box=box.DOUBLE,
        )
        self._output(panel)

    def print_section_header(self, title: str) -> None:
        """Print a section header centered with lines."""
        self._output(
            Rule(f"[bold cyan]{title}[/bold cyan]", style="dim cyan"), width=MENU_WIDTH
        )

    def menu(self, title: str, options: list[str]) -> None:
        """Display options in a clean list format."""
        self.console.print()

        for i, option in enumerate(options, 1):
            self._output(f"[{i}] {option}")

    def print_info(self, message: str) -> None:
        """Print info message aligned with the layout."""
        self.print(f"[bold blue]ℹ[/bold blue] {message}")

    def print_success(self, message: str) -> None:
        """Print success message."""
        self.print(f"[bold green]✓[/bold green] {message}")

    def print_error(self, message: str) -> None:
        """Print error message."""
        self.print(f"[bold red]✗[/bold red] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.print(f"[bold yellow]![/bold yellow] {message}")

    def prompt(self, message: str, password: bool = False) -> str:
        """Prompt for user input."""
        self.divider("─")
        pad = " " * LEFT_PADDING
        return Prompt.ask(f"{pad}[bold cyan]?[/bold cyan] {message}", password=password)

    def prompt_choice(self, message: str, max_choice: int) -> int | None:
        """Prompt for a numeric choice."""
        self.divider("═")
        pad = " " * LEFT_PADDING
        try:
            choice = Prompt.ask(f"{pad}{message}")
            num = int(choice)
            if 1 <= num <= max_choice:
                return num
            self.print_error(f"Please enter a number between 1 and {max_choice}")
            return None
        except ValueError:
            self.print_error("Please enter a valid number")
            return None

    def confirm(self, message: str, default: bool = False) -> bool:
        """Ask for confirmation."""
        return Confirm.ask(f"[bold cyan]?[/bold cyan] {message}", default=default)

    def accounts_table(self, phones: list[str]) -> None:
        """Display a table of accounts constrained to menu width."""
        from rich import box

        if not phones:
            self.print_info("No accounts found")
            return

        table = Table(
            title="Managed Accounts",
            border_style="cyan",
            width=MENU_WIDTH,
            box=box.SIMPLE,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("#", style="dim", width=4, justify="center")
        table.add_column("Phone", style="cyan", justify="left")

        for i, phone in enumerate(phones, 1):
            table.add_row(str(i), phone)

        self._output(table)

    def health_table(self, results: list[AccountHealth]) -> None:
        """Display health check results."""
        from rich import box

        from src.features.health_check import AccountStatus

        if not results:
            self.print_info("No accounts to check")
            return

        table = Table(
            title="Account Health Status",
            border_style="cyan",
            width=MENU_WIDTH,
            box=box.SIMPLE,
        )
        table.add_column("Phone", style="cyan")
        table.add_column("Status", width=12)
        table.add_column("Details")

        status_styles = {
            AccountStatus.ACTIVE: ("✓ Active", "bold green"),
            AccountStatus.EXPIRED: ("✗ Expired", "bold red"),
            AccountStatus.BANNED: ("⊘ Banned", "bold red"),
            AccountStatus.ERROR: ("? Error", "bold yellow"),
        }

        for result in results:
            status_text, style = status_styles.get(result.status, ("Unknown", "white"))
            details = result.name or result.message
            table.add_row(result.phone, Text(status_text, style=style), details)

        self._output(table)

    def join_results_table(self, target: str, results: list) -> None:
        """Display bulk join results."""
        from rich import box

        if not results:
            return

        table = Table(
            title=f"Join Results: {target}",
            border_style="cyan",
            width=MENU_WIDTH,
            box=box.SIMPLE,
        )
        table.add_column("Phone", style="cyan")
        table.add_column("Status", width=10)
        table.add_column("Message")

        for result in results:
            if result.success:
                status = Text("✓ OK", style="bold green")
            else:
                status = Text("✗ Fail", style="bold red")
            table.add_row(result.phone, status, result.message)

        self._output(table)

    def leave_results_table(self, target: str, results: list) -> None:
        """Display bulk leave results."""
        from rich import box

        if not results:
            return

        table = Table(
            title=f"Leave Results: {target}",
            border_style="cyan",
            width=MENU_WIDTH,
            box=box.SIMPLE,
        )
        table.add_column("Phone", style="cyan")
        table.add_column("Status", width=10)
        table.add_column("Message")

        for result in results:
            if result.success:
                status = Text("✓ OK", style="bold green")
            else:
                status = Text("✗ Fail", style="bold red")
            table.add_row(result.phone, status, result.message)

        self._output(table)

    def create_progress(self) -> Progress:
        """Create a progress bar context manager."""
        from rich.padding import Padding

        pad_str = " " * LEFT_PADDING
        return Progress(
            TextColumn(pad_str),
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            expand=True,
        )
