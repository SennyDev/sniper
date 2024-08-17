import http.client
import json
import random
import time
import socket
import uuid
from datetime import datetime

# Load configuration from config.json
def load_config(filename='config.json'):
    with open(filename, 'r') as file:
        return json.load(file)

config = load_config()

# File to store key information
KEY_INFO_FILE = 'key_info.json'

# List of rare 2 to 5-letter words for invite codes
RARE_WORDS = [
    "abyss", "blaze", "crisp", "dwarf", "eagle", "flint", "gleam", "haste", "ivory", "jolly",
    "knack", "lunar", "mirth", "noble", "oasis", "pearl", "quilt", "rivet", "sphinx", "truce",
    "ultra", "vivid", "waltz", "yacht", "zesty", "aegis", "bloom", "clash", "douse", "frost",
    "glint", "heart", "icier", "joker", "karma", "lapse", "moist", "niche", "ocean", "plumb",
    "quark", "rusty", "scent", "toxic", "unity", "vowel", "weary", "xenon", "yogic", "zonal",
    "abide", "bliss", "crave", "douse", "eerie", "flame", "gloom", "hover", "juicy", "knoll",
    "lunar", "mirth", "neat", "ocean", "peach", "quill", "rouge", "saber", "tango", "usher",
    "vivid", "witty", "yodel", "zebra", "apex", "boast", "clasp", "drain", "ember", "flint",
    "ghost", "haste", "ice", "jolt", "knee", "lava", "moss", "navy", "opal", "plow",
    "quest", "rage", "seal", "tide", "urge", "vow", "whale", "yarn", "zoom", "area",
    "bark", "charm", "dust", "eagle", "fuse", "gaze", "hike", "icon", "jade", "kind",
    "link", "mark", "nail", "orbit", "peak", "rude", "slate", "tomb", "vent", "wolf",
    "yell", "zone"
]


# Set to track already processed invites
processed_invites = set()

def generate_single_word_invite():
    """Generate an invite code from a rare 2 to 5-letter word."""
    return random.choice(RARE_WORDS)

def check_discord_invite(invite_code):
    """Check if a Discord invite link is valid by making a GET request."""
    try:
        conn = http.client.HTTPSConnection("discord.com")
        conn.request("GET", f"/api/v10/invites/{invite_code}")
        response = conn.getresponse()
        status = response.status
        conn.close()
        return status
    except Exception as e:
        print(f"An error occurred while checking the invite {invite_code}: {e}")
        return None

def get_ip_address():
    """Get the local IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to a public DNS server
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"An error occurred while getting IP address: {e}")
        return "Unknown IP"

def send_to_discord_webhook(webhook_url, message, embed_title, embed_description, embed_color, key=None, ip_address=None):
    """Send an embed message to a Discord webhook using http.client."""
    try:
        conn = http.client.HTTPSConnection("discord.com")

        webhook_id, webhook_token = webhook_url.split("/")[5], webhook_url.split("/")[6]

        payload = json.dumps({
            "content": message,
            "embeds": [
                {
                    "title": embed_title,
                    "description": embed_description,
                    "color": embed_color,
                    "author": {
                        "name": config['embed']['author_name'],
                        "icon_url": config['embed']['author_icon_url']
                    },
                    "thumbnail": {
                        "url": config['embed']['thumbnail_url']
                    },
                    "footer": {
                        "text": config['embed']['footer_text'].format(ip_address=ip_address, key=key) if key and ip_address else config['embed']['footer_text'],
                        "icon_url": config['embed']['footer_icon_url']
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        })

        headers = {'Content-Type': 'application/json'}

        conn.request("POST", f"/api/webhooks/{webhook_id}/{webhook_token}", body=payload, headers=headers)

        response = conn.getresponse()
        status = response.status
        reason = response.reason
        conn.close()

        return status, reason
    except Exception as e:
        print(f"An error occurred while sending the message: {e}")
        return None, str(e)

def load_key_info():
    """Load key information from a file."""
    try:
        with open(KEY_INFO_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding {KEY_INFO_FILE}")
        return {}

def save_key_info(key_info):
    """Save key information to a file."""
    try:
        with open(KEY_INFO_FILE, 'w') as file:
            json.dump(key_info, file, indent=4)
    except Exception as e:
        print(f"An error occurred while saving key information: {e}")

def generate_key():
    """Generate a unique 20-digit key."""
    return str(uuid.uuid4()).replace("-", "")[:20]

def prompt_for_key():
    """Prompt the user to enter a key and validate it."""
    user_key = input("[+] KEY: ").strip()
    
    key_info = load_key_info()
    if user_key in key_info and key_info[user_key]["status"] == "free":
        print("[+] Key validated successfully.")
        return user_key
    else:
        print("[!] Wrong key!")
        return None

def generate_and_check_invites(config, session_key, ip_address, interval=1):
    """Generate random rare 2 to 5-letter Discord invite codes, check their validity, and send results to the Discord webhook."""
    webhook_url = config['webhook_url']

    while True:
        try:
            invite_code = generate_single_word_invite()
            
            if invite_code in processed_invites:
                continue

            status = check_discord_invite(invite_code)

            if status == 404:
                message = "Sniped a Vanity Link!"
                embed_title = config['embed']['title']
                embed_description = config['embed']['description'].format(invite_code=invite_code)
                embed_color = config['embed']['color']
                # Send the result to the Discord webhook
                status, reason = send_to_discord_webhook(webhook_url, message, embed_title, embed_description, embed_color, session_key, ip_address)

                if status is not None:
                    status_text = "pinged @everyone" if random.randint(0, 1) == 1 else "not pinged"
                    print(f"[+] Vanity Check ({status_text}): gg/{invite_code} - Status: {status} Reason: {reason}")
                else:
                    print(f"[!] Failed to send message: {reason}")

            processed_invites.add(invite_code)

            # Wait for the specified interval before checking the next invite
            time.sleep(interval)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

def generate_backup_key():
    """Generate and send a backup key to the webhook."""
    backup_key = generate_key()
    ip_address = get_ip_address()

    # Load existing key info and add backup key
    key_info = load_key_info()
    key_info[backup_key] = {"status": "backup", "ip_address": ip_address}
    save_key_info(key_info)

    # Send backup key information to the webhook
    message = "A backup key has been generated."
    embed_title = "Backup Key Generated"
    embed_description = f"The backup key `{backup_key}` has been generated and is available."
    embed_color = config['embed']['color']
    send_to_discord_webhook(config['webhook_url'], message, embed_title, embed_description, embed_color, backup_key, ip_address)

if __name__ == "__main__":
    # Generate key and send to webhook on launch
    key_info = load_key_info()
    if not key_info:
        session_key = generate_key()
        ip_address = get_ip_address()
        key_info[session_key] = {"status": "free", "ip_address": ip_address}
        save_key_info(key_info)
        send_to_discord_webhook(config['webhook_url'], "A new key has been generated.", "New Key Generated", f"The key `{session_key}` has been generated and is available.", config['embed']['color'], session_key, ip_address)

    while True:
        command = input("Enter command ([1] for key input, [2] for generate backup): ").strip()
        if command == "1":
            user_key = prompt_for_key()
            if user_key:
                ip_address = get_ip_address()
                generate_and_check_invites(config, user_key, ip_address, interval=1)  # Adjust the interval as needed
        elif command == "2":
            generate_backup_key()
        else:
            print("Invalid command. Please enter 1 or 2.")
