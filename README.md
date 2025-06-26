# Slurpas Palo Alto PCAP Downloader

A modern, user-friendly tool for continuously downloading packet capture (PCAP) files from one or more Palo Alto firewalls. Built with a clean GUI, parallel downloads, and advanced logging.

## Features
- Download PCAP files (rx, tx, drp) from multiple firewalls in parallel
- Set interval and number of downloads
- Custom file naming with project name, timestamp, and firewall IP/hostname
- Select save directory
- Modern, scrollable GUI with progress bar
- Summary and advanced logging tabs
- Open source, non-commercial use

## Installation

### Requirements
- Python 3.8+
- See `requirements.txt` for dependencies

### Install dependencies
```bash
pip install -r requirements.txt
```

## Running from Source
```bash
python src/main.py
```

## Building a Windows Executable
You can create a standalone `.exe` using [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole src/main.py
```
The resulting `.exe` will be in the `dist/` folder. You can share this file with others who do not have Python installed.

## Usage
- Enter one or more firewall IPs/hostnames (comma-separated)
- Enter your username and password
- Set the interval and number of downloads
- Choose a save directory
- Click "Start Downloading"
- Monitor progress and logs in the GUI

## Security & Disclaimer
- **Run this program at your own risk.**
- No responsibility is taken for any use, data loss, or issues.
- Do not share sensitive information or credentials.
- All code is open for review.
- This project is for non-commercial use only.

## Contributing
Contributions, issues, and pull requests are welcome! Please open an issue or PR on GitHub.

## License
This project is licensed under the [CC BY-NC 4.0 License](LICENSE) and is owned by Slurpas. 