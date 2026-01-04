"""Interactive menu system for orca-fleet."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from src.config import get_config
from src.features.account import AccountManager
from src.features.bulk_join import BulkJoiner
from src.features.health_check import HealthChecker
from src.menu.display import Display
from src.utils.logger import get_logger

if TYPE_CHECKING:
    pass


class MainMenu:
    """Main interactive menu for the application."""

    MENU_OPTIONS = [
        "Add Account",
        "List Accounts",
        "Health Check",
        "Bulk Join Channel/Group",
        "Remove Account",
        "Exit",
    ]

    def __init__(self) -> None:
        self.display = Display()
        self.config = get_config()
        self.account_manager = AccountManager()
        self.health_checker = HealthChecker()
        self.bulk_joiner = BulkJoiner()
        self.logger = get_logger(__name__)
        self._running = True

    def run(self) -> None:
        """Run the main menu loop."""
        asyncio.run(self._run_async())

    async def _run_async(self) -> None:
        """Async main menu loop."""
        self.display.clear()
        self.display.banner()

        # Validate configuration
        if not self.config.is_configured:
            self.display.print_error(
                "API credentials not configured. Please set API_ID and API_HASH in .env file."
            )
            self.display.print_info("Get credentials from: https://my.telegram.org")
            return

        account_count = self.account_manager.get_account_count()
        self.display.print_info(f"Managing {account_count} account(s)")
        self.display.divider()

        while self._running:
            self.display.menu("Main Menu", self.MENU_OPTIONS)

            choice = self.display.prompt_choice("Select option", len(self.MENU_OPTIONS))
            if choice is None:
                continue

            self.display.divider()

            try:
                await self._handle_choice(choice)
            except KeyboardInterrupt:
                self.display.print_warning("Operation cancelled")
            except Exception as e:
                self.logger.exception("Menu error")
                self.display.print_error(f"An error occurred: {e}")

            if self._running:
                self.display.divider()

    async def _handle_choice(self, choice: int) -> None:
        """Handle menu choice."""
        handlers = {
            1: self._add_account,
            2: self._list_accounts,
            3: self._health_check,
            4: self._bulk_join,
            5: self._remove_account,
            6: self._exit,
        }
        handler = handlers.get(choice)
        if handler:
            await handler()

    async def _add_account(self) -> None:
        """Add a new account."""
        self.display.print("[bold]Add New Account[/bold]\n")

        phone = self.display.prompt("Enter phone number (e.g., +1234567890)")
        if not phone:
            self.display.print_warning("Cancelled")
            return

        # Code callback for interactive input
        code_received = False

        def get_code() -> str:
            nonlocal code_received
            self.display.print_success("Verification code sent!")
            code = self.display.prompt("Enter verification code")
            code_received = True
            return code

        def get_2fa() -> str:
            self.display.print_warning("2FA password required")
            return self.display.prompt("Enter 2FA password", password=True)

        self.display.print_info(f"Connecting to Telegram for {phone}...")

        success, message = await self.account_manager.add_account(
            phone=phone,
            get_code=get_code,
            get_2fa_password=get_2fa,
        )

        if success:
            self.display.print_success(message)
        else:
            self.display.print_error(message)

    async def _list_accounts(self) -> None:
        """List all managed accounts."""
        self.display.print("[bold]Managed Accounts[/bold]\n")
        phones = self.account_manager.list_accounts()
        self.display.accounts_table(phones)

    async def _health_check(self) -> None:
        """Check health of all accounts."""
        self.display.print("[bold]Account Health Check[/bold]\n")

        phones = self.account_manager.list_accounts()
        if not phones:
            self.display.print_info("No accounts to check")
            return

        self.display.print_info(f"Checking {len(phones)} account(s)...")

        with self.display.create_progress() as progress:
            task = progress.add_task("Checking...", total=len(phones))

            def update_progress(current: int, total: int) -> None:
                progress.update(task, completed=current)

            results = await self.health_checker.check_all_accounts(
                progress_callback=update_progress
            )

        self.display.print()
        self.display.health_table(results)

        summary = self.health_checker.get_summary(results)
        self.display.print()
        self.display.print_info(
            f"Summary: {summary['active']} active, "
            f"{summary['expired']} expired, "
            f"{summary['banned']} banned, "
            f"{summary['error']} errors"
        )

    async def _bulk_join(self) -> None:
        """Bulk join a channel/group."""
        self.display.print("[bold]Bulk Join Channel/Group[/bold]\n")

        phones = self.account_manager.list_accounts()
        if not phones:
            self.display.print_error("No accounts available. Add accounts first.")
            return

        target = self.display.prompt(
            "Enter channel/group (username, @handle, or t.me link)"
        )
        if not target:
            self.display.print_warning("Cancelled")
            return

        self.display.print_info(f"Joining with {len(phones)} account(s)...")
        self.display.print_info(
            f"Delay between joins: {self.config.join_delay_min}-{self.config.join_delay_max}s"
        )
        self.display.print()

        results_list = []

        with self.display.create_progress() as progress:
            task = progress.add_task("Processing...", total=len(phones))

            def update_progress(current: int, total: int, result) -> None:
                progress.update(task, completed=current)
                results_list.append(result)

            result = await self.bulk_joiner.bulk_join(
                target_input=target,
                progress_callback=update_progress,
            )

        self.display.print()
        self.display.join_results_table(target, result.results)
        self.display.print()
        self.display.print_info(
            f"Completed: {result.successful_count} succeeded, {result.failed_count} failed"
        )

    async def _remove_account(self) -> None:
        """Remove an account."""
        self.display.print("[bold]Remove Account[/bold]\n")

        phones = self.account_manager.list_accounts()
        if not phones:
            self.display.print_info("No accounts to remove")
            return

        self.display.accounts_table(phones)
        self.display.print()

        phone = self.display.prompt("Enter phone number to remove")
        if not phone:
            self.display.print_warning("Cancelled")
            return

        if phone not in phones:
            # Try to match by number without +
            matches = [p for p in phones if phone in p]
            if len(matches) == 1:
                phone = matches[0]
            else:
                self.display.print_error(f"Account {phone} not found")
                return

        if not self.display.confirm(f"Remove account {phone}?"):
            self.display.print_warning("Cancelled")
            return

        success, message = await self.account_manager.remove_account(phone)
        if success:
            self.display.print_success(message)
        else:
            self.display.print_error(message)

    async def _exit(self) -> None:
        """Exit the application."""
        self._running = False
        self.display.print_info("Goodbye!")
