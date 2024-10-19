import logging
from telethon import TelegramClient
import csv
import os
import json
from dotenv import load_dotenv
import asyncio

# Set up logging
logging.basicConfig(
    filename='scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables for Telegram API credentials
load_dotenv('.env')
api_id = os.getenv('TG_API_ID')
api_hash = os.getenv('TG_API_HASH')
phone = os.getenv('TG_PHONE_NUMBER')

# Function to read channels from a JSON file
def load_channels_from_json(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get('channels', [])
    except Exception as e:
        logging.error(f"Error reading channels from JSON: {e}")
        return []

# Function to scrape data from a single channel
async def scrape_channel(client, channel_username, writer, media_dir, num_messages):
    try:
        entity = await client.get_entity(channel_username)
        channel_title = entity.title
        
        message_count = 0
        async for message in client.iter_messages(entity):
            if message_count >= num_messages:
                break  # Stop after scraping the specified number of messages

            # Check if the message contains media
            media_path = None
            if message.media:
                logging.info(f"Media found in message ID {message.id}.")
                try:
                    # Dynamically get media extension based on MIME type
                    extension = 'jpg'  # Default to jpg
                    if message.media.document:
                        mime_type = message.media.document.mime_type
                        extension = mime_type.split('/')[-1]  # Use MIME type to determine the extension
                    
                    filename = f"{channel_username}_{message.id}.{extension}"
                    media_path = os.path.join(media_dir, filename)
                    
                    # Download media
                    await client.download_media(message.media, media_path)
                    logging.info(f"Downloaded media for message ID {message.id} to {media_path}.")
                except Exception as e:
                    logging.error(f"Error downloading media for message ID {message.id}: {e}")
            else:
                logging.info(f"No media found in message ID {message.id}.")
            
            # Write message details to CSV
            writer.writerow([channel_title, channel_username, message.id, message.message, message.date, media_path])
            logging.info(f"Processed message ID {message.id} from {channel_username}.")

            message_count += 1

        if message_count == 0:
            logging.info(f"No messages found for {channel_username}.")
    except Exception as e:
        logging.error(f"Error while scraping {channel_username}: {e}")

# Initialize the client once with a session file
client = TelegramClient('scraping_session', api_id, api_hash)

# Main function to run the scraper
async def main():
    try:
        await client.start(phone)
        logging.info("Client started successfully.")
        
        media_dir = 'photos'
        # Create media directory if it doesn't exist
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)
            logging.info(f"Created media directory: {media_dir}")
        else:
            logging.info(f"Media directory '{media_dir}' already exists.")
        
        # Load channels from JSON file
        channels = load_channels_from_json('channels.json')  # Adjust this path as needed
        
        num_messages_to_scrape = 20  # Define how many messages to scrape from each channel

        for channel in channels:
            csv_filename = f"{channel[1:]}_data.csv"  # Create CSV file for each channel (removing '@' from name)
            with open(csv_filename, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Channel Title', 'Channel Username', 'Message ID', 'Message', 'Date', 'Media Path'])
                
                await scrape_channel(client, channel, writer, media_dir, num_messages_to_scrape)
                logging.info(f"Scraped data from {channel}.")
    except Exception as e:
        logging.error(f"Error in main function: {e}")

if __name__ == "__main__":
    asyncio.run(main())
