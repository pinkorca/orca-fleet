# orca-fleet

Multi-account Telegram manager built with Telethon for efficient account orchestration.

Designed to simplify the management of multiple Telegram user accounts, offering a centralized interface for authentication, session handling, and bulk operations.

## Key Features

- **Account Management**: Add function authenticates new accounts with full 2FA support and phone number validation.
- **Session Persistence**: Securely stores and manages Telethon session files, ensuring long-term access without re-login.
- **Health Checks**: validtes connectivity and authorization status for all stored accounts.
- **Bulk Operations**: Automates joining and leaving channels and groups across all managed accounts with built-in rate limiting.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/pinkorca/orca-fleet.git
   cd orca-fleet
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Telegram API credentials:
   - Obtain `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).

## Usage

Run the application:
```bash
python -m src.main
```

The interactive menu provides the following options:

- **Add Account**: Guided login flow for new numbers.
- **List Accounts**: View all managed sessions.
- **Health Check**: Verify status of all accounts (Active, Expired, Banned).
- **Bulk Join**: Join specific channels or groups with all active accounts.
- **Bulk Leave**: Leave specific channels or groups with all active accounts.

## Future Plans

This project is in early development (v0.2.0). Future updates will focus on expanding orchestration capabilities and additional bulk management features.

## Disclaimer

This tool is for educational and personal management purposes only. Users are responsible for complying with Telegram's Terms of Service. Automated actions carries risks; use responsibly.

## License

This project is licensed under the [GPL-3.0 License](LICENSE).
