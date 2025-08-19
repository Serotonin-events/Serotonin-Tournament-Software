#!/usr/bin/env python3
"""
Setup script for Serotonin Tournament Software
This script helps users quickly configure the tournament software
"""

import os
import shutil
import json

def main():
    print("🎮 Serotonin Tournament Software Setup")
    print("=" * 40)
    
    # Check if config files already exist
    config_files = ['nadeo_config.json', 'config.json', 'seeding_config.json']
    existing_files = [f for f in config_files if os.path.exists(f)]
    
    if existing_files:
        print(f"⚠️  Found existing config files: {', '.join(existing_files)}")
        response = input("Do you want to overwrite them? (y/N): ").lower()
        if response != 'y':
            print("Setup cancelled. Existing files preserved.")
            return
    
    # Copy example files
    print("\n📋 Setting up configuration files...")
    for config_file in config_files:
        example_file = f"{config_file.replace('.json', '')}.example.json"
        if os.path.exists(example_file):
            shutil.copy2(example_file, config_file)
            print(f"✅ Created {config_file}")
        else:
            print(f"❌ Missing {example_file}")
    
    # Prompt for basic configuration
    print("\n🔧 Basic Configuration Setup")
    print("-" * 30)
    
    # Tournament name
    tournament_name = input("Tournament name (default: Serotonin Tournament): ").strip()
    if not tournament_name:
        tournament_name = "Serotonin Tournament"
    
    # Update config.json with tournament name
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            config['info']['tournament_name'] = tournament_name
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            print(f"✅ Set tournament name to: {tournament_name}")
        except Exception as e:
            print(f"⚠️  Could not update tournament name: {e}")
    
    # Nadeo API setup
    print("\n🔑 Nadeo API Setup")
    print("You'll need to get your Nadeo API credentials from:")
    print("https://developers.trackmania.com/")
    print("\nFor now, you can leave these blank and configure them later.")
    
    client_id = input("Nadeo Client ID (optional): ").strip()
    client_secret = input("Nadeo Client Secret (optional): ").strip()
    
    if client_id and client_secret:
        if os.path.exists('nadeo_config.json'):
            try:
                with open('nadeo_config.json', 'r') as f:
                    nadeo_config = json.load(f)
                nadeo_config['nadeo_client_id'] = client_id
                nadeo_config['nadeo_client_secret'] = client_secret
                
                with open('nadeo_config.json', 'w') as f:
                    json.dump(nadeo_config, f, indent=4)
                print("✅ Nadeo API credentials configured")
            except Exception as e:
                print(f"⚠️  Could not update Nadeo config: {e}")
    
    print("\n🎉 Setup Complete!")
    print("=" * 40)
    print("Next steps:")
    print("1. Edit config.json to add your players and customize settings")
    print("2. Configure your Nadeo API credentials in nadeo_config.json")
    print("3. Run 'python run_app.py' to start the application")
    print("\n📚 Check README.md for detailed configuration options")
    print("🔒 Remember: Never commit your actual config files to git!")

if __name__ == "__main__":
    main()
