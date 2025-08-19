# Serotonin Tournament Software (STS)

A comprehensive tournament management system for Trackmania with bracket management, seeding, and live scoring capabilities.

## Features

- **Double Elimination Brackets**: Manage upper and lower bracket tournaments
- **Live Scoring**: Real-time score updates and bracket progression
- **Seeding System**: Group-based seeding with map scoring
- **Timer System**: Customizable countdown timers for matches
- **Stream Overlays**: Professional graphics for tournament broadcasts
- **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

- Python 3.7 or higher
- Nadeo API credentials (for Trackmania integration)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd STS-Beta-0.0.3
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration files**
   
   Copy the example configuration files and fill in your details:
   ```bash
   cp nadeo_config.example.json nadeo_config.json
   cp config.example.json config.json
   cp seeding_config.example.json seeding_config.json
   ```

4. **Configure Nadeo API credentials**
   
   Edit `nadeo_config.json` with your Nadeo API credentials:
   ```json
   {
       "nadeo_client_id": "YOUR_ACTUAL_CLIENT_ID",
       "nadeo_client_secret": "YOUR_ACTUAL_CLIENT_SECRET"
   }
   ```

5. **Customize tournament settings**
   
   Edit `config.json` with your tournament details:
   - Player information
   - Tournament name and branding
   - Bracket structure
   - Timer settings

## Configuration

### Nadeo Configuration (`nadeo_config.json`)
Contains your Nadeo API credentials for Trackmania integration.

### Tournament Configuration (`config.json`)
Main tournament settings including:
- Player roster
- Bracket structure
- Tournament branding
- Timer configuration

### Seeding Configuration (`seeding_config.json`)
Group-based seeding system with:
- Player groups
- Map rotation
- Score tracking

## Usage

### Starting the Application
```bash
python run_app.py
```

The application will be available at `http://localhost:5000`

### Main Pages

- **Home** (`/`): Tournament overview and navigation
- **Bracket** (`/bracket`): Tournament bracket display
- **Seeding** (`/seeding`): Group seeding and scoring
- **Timer** (`/timer`): Match countdown timer
- **Stream** (`/stream`): Stream overlay graphics
- **Featured** (`/featured`): Featured match display

### Managing Tournaments

1. **Set up players**: Add player information to `config.json`
2. **Configure brackets**: Set up upper/lower bracket structure
3. **Start tournament**: Set `is_started` to `true` in config
4. **Update scores**: Use the web interface to update match scores
5. **Track progression**: Bracket automatically advances winners

## Security Notes

⚠️ **IMPORTANT**: Never commit your actual configuration files to version control!

- The `.gitignore` file prevents sensitive configs from being committed
- Use the `.example.json` files as templates
- Keep your `nadeo_config.json` with real credentials local only
- Consider using environment variables for production deployments

## Development

### Project Structure
```
STS-Beta-0.0.3/
├── app.py                 # Main Flask application
├── run_app.py            # Application entry point
├── requirements.txt      # Python dependencies
├── templates/            # HTML templates
├── static/              # CSS, JS, and static assets
├── *.example.json       # Configuration templates
└── README.md            # This file
```

### Adding New Features
1. Create new routes in `app.py`
2. Add corresponding HTML templates
3. Update navigation as needed
4. Test thoroughly before deployment

## Troubleshooting

### Common Issues

**Configuration not loading**: Ensure all required JSON files exist and are valid JSON
**Nadeo API errors**: Verify your credentials in `nadeo_config.json`
**Bracket not updating**: Check that `is_started` is set to `true`

### Getting Help
- Check the configuration examples
- Verify JSON syntax in your config files
- Ensure all required dependencies are installed

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support contact information here]
