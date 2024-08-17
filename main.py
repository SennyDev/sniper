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

# Expanded list of real words for invite codes
REAL_WORDS = [
    "hello", "world", "nice", "dam", "great", "good", "example", "test", "code", "script",
    "bot", "discord", "invite", "link", "fun", "play", "join", "chat", "server", "team",
    "game", "user", "group", "admin", "member", "role", "share", "event", "meeting", "project",
    "update", "notification", "alert", "message", "news", "info", "discussion", "support", "feedback",
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa",
    "lambda", "mu", "nu", "xi", "omicron", "pi", "rho", "sigma", "tau", "upsilon", "phi",
    "chi", "psi", "omega", "apex", "bliss", "crux", "dawn", "edge", "flame", "gaze",
    "halo", "ice", "jolt", "keystone", "lunar", "mystic", "nexus", "opal", "quest", "rift",
    "soul", "tide", "void", "wave", "zenith", "aether", "bolt", "cascade", "drift", "ember",
    "forge", "glow", "horizon", "illusion", "jungle", "krypton", "luminous", "maverick", "neon", "orbit",
    "pulse", "quasar", "ripple", "storm", "thunder", "unity", "vortex", "whisper", "xenon", "yonder", "zen",
    "rizz", "skibidi", "vibe", "clout", "flex", "drip", "mood", "slay", "sus", "pog",
    "lit", "epic", "noob", "meta", "hype", "savage", "cringe", "chad", "genz", "meme",
    "fomo", "dank", "woke", "ghost", "vortex", "nugget", "beast", "glitch", "zombie", "hacker",
    "glow", "zap", "spice", "banger", "buzz", "frost", "neptune", "spartan", "phantom", "chaos",
    "jester", "ranger", "vortex", "vivid", "stellar", "zenith", "flare", "byte", "cipher", "pixel"
]

# Set to track already processed invites
processed_invites = set()

def generate_single_word_invite():
    """Generate an invite code from a single real word."""
    return random.choice(REAL_WORDS)

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

def generate_and_check_invites(config, interval=1):
    """Generate random single-word Discord invite codes, check their validity, and send results to the Discord webhook."""
    webhook_url = config['webhook_url']
    
    # Load existing key info
    key_info = load_key_info()
    
    # Check if a key already exists, otherwise generate one
    if not key_info:
        session_key = generate_key()
        ip_address = get_ip_address()

        # Save the generated key information
        key_info[session_key] = {"status": "free", "ip_address": ip_address}
        save_key_info(key_info)

        # Send key information to the webhook
        message = "A new key has been generated."
        embed_title = "New Key Generated"
        embed_description = f"The key `{session_key}` has been generated and is available for use."
        embed_color = config['embed']['color']
        send_to_discord_webhook(webhook_url, message, embed_title, embed_description, embed_color, session_key, ip_address)
    else:
        session_key = list(key_info.keys())[0]
        ip_address = key_info[session_key]['ip_address']

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
        if command == '1':
            user_key = prompt_for_key()
            if user_key:
                generate_and_check_invites(config, interval=1)  # Adjust the interval as needed
        elif command == '2':
            generate_backup_key()
        else:
            print("[!] Invalid command.")
