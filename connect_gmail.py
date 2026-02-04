"""
Gmail Connection Helper Script

This script helps you connect your Gmail account to Parlant via Composio.

Usage:
    1. First, create a Gmail Auth Config at https://platform.composio.dev/auth-configs
    2. Copy the Auth Config ID and paste it when prompted (or set COMPOSIO_GMAIL_AUTH_CONFIG_ID in .env)
    3. Run: python connect_gmail.py
    4. Open the URL in your browser to authenticate
    5. After authentication, you can use Gmail tools in Parlant
"""

import os
import webbrowser
from dotenv import load_dotenv
from composio import Composio

load_dotenv()


def connect_gmail():
    """Connect a user's Gmail account via Composio."""
    
    # Get API key
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        print("ERROR: COMPOSIO_API_KEY not found in .env file")
        return
    
    # Get Gmail Auth Config ID
    auth_config_id = os.getenv("COMPOSIO_GMAIL_AUTH_CONFIG_ID")
    
    if not auth_config_id or auth_config_id == "your_gmail_auth_config_id_here":
        print("\n" + "=" * 60)
        print("Gmail Auth Config ID not found!")
        print("=" * 60)
        print("\nTo get your Gmail Auth Config ID:")
        print("1. Go to: https://platform.composio.dev/auth-configs")
        print("2. Click 'Create Auth Config'")
        print("3. Select 'Gmail'")
        print("4. Choose OAuth2 and configure scopes")
        print("5. Click 'Create Auth Configuration'")
        print("6. Copy the Auth Config ID")
        print()
        
        auth_config_id = input("Enter your Gmail Auth Config ID: ").strip()
        
        if not auth_config_id:
            print("No Auth Config ID provided. Exiting.")
            return
    
    # Get user ID
    user_id = input("\nEnter a user ID (e.g., your email or 'test-user'): ").strip()
    if not user_id:
        user_id = "test-user"
    
    print(f"\nConnecting Gmail for user: {user_id}")
    print("-" * 40)
    
    try:
        # Initialize Composio client
        client = Composio(api_key=api_key)
        
        # Create connection request
        connection_request = client.connected_accounts.link(
            user_id=user_id,
            auth_config_id=auth_config_id,
        )
        
        redirect_url = connection_request.redirect_url
        connection_id = connection_request.id
        
        print("\n[SUCCESS] Connection request created!")
        print(f"\nConnection ID: {connection_id}")
        print(f"\nRedirect URL:\n{redirect_url}")
        print("\n" + "=" * 60)
        
        # Ask to open browser
        open_browser = input("\nOpen URL in browser? (y/n): ").strip().lower()
        if open_browser == 'y':
            webbrowser.open(redirect_url)
            print("\nBrowser opened! Complete the authentication process.")
            print("After authenticating, your Gmail will be connected to Parlant.")
        else:
            print("\nCopy and paste the URL above into your browser to authenticate.")
        
        # Wait for connection
        print("\n" + "-" * 40)
        wait = input("\nPress Enter after you've completed authentication in the browser...")
        
        # Check connection status
        print("\nChecking connection status...")
        try:
            connected_account = client.connected_accounts.get(connection_id)
            status = getattr(connected_account, 'status', 'UNKNOWN')
            print(f"Connection Status: {status}")
            
            if status == "ACTIVE":
                print("\n[SUCCESS] Gmail is now connected!")
                print(f"User ID: {user_id}")
                print("\nYou can now use the gmail_send_email tool in Parlant.")
            else:
                print(f"\nConnection status is {status}. It may take a moment to activate.")
                print("Try running this script again to check status.")
        except Exception as e:
            print(f"Could not check status: {e}")
            print("The connection may still be processing. Try using Gmail tools in Parlant.")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create connection: {e}")
        return


def test_gmail_connection():
    """Test if Gmail is connected for a user."""
    
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        print("ERROR: COMPOSIO_API_KEY not found")
        return
    
    user_id = input("Enter user ID to check: ").strip()
    if not user_id:
        user_id = "test-user"
    
    print(f"\nChecking Gmail connection for user: {user_id}")
    
    try:
        client = Composio(api_key=api_key)
        
        connections = client.connected_accounts.list(user_ids=[user_id])
        
        gmail_connections = []
        for conn in connections.items:
            # Check if this is a Gmail connection
            conn_str = str(conn).lower()
            if 'gmail' in conn_str or 'google' in conn_str:
                gmail_connections.append(conn)
        
        if gmail_connections:
            print(f"\nFound {len(gmail_connections)} Gmail connection(s):")
            for conn in gmail_connections:
                status = getattr(conn, 'status', 'UNKNOWN')
                conn_id = getattr(conn, 'id', 'N/A')
                print(f"  - ID: {conn_id}, Status: {status}")
        else:
            print("\nNo Gmail connections found for this user.")
            print("Run 'python connect_gmail.py' to connect Gmail.")
            
    except Exception as e:
        print(f"Error checking connections: {e}")


def list_gmail_tools():
    """List available Gmail tools."""
    
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        print("ERROR: COMPOSIO_API_KEY not found")
        return
    
    print("\nFetching available Gmail tools...")
    
    try:
        client = Composio(api_key=api_key)
        
        tools = client.tools.get_raw_composio_tools(
            toolkits=["GMAIL"],
            limit=20,
        )
        
        print(f"\nFound {len(tools)} Gmail tools:")
        print("-" * 60)
        for tool in tools:
            name = getattr(tool, 'name', 'Unknown')
            slug = getattr(tool, 'slug', 'Unknown')
            desc = (getattr(tool, 'description', '') or '')[:80]
            print(f"\n  {name}")
            print(f"    Slug: {slug}")
            print(f"    {desc}...")
            
    except Exception as e:
        print(f"Error listing tools: {e}")


def main():
    print("\n" + "=" * 60)
    print("   GMAIL CONNECTION HELPER")
    print("=" * 60)
    print("\nOptions:")
    print("  1. Connect Gmail account")
    print("  2. Check Gmail connection status")
    print("  3. List available Gmail tools")
    print("  4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        connect_gmail()
    elif choice == "2":
        test_gmail_connection()
    elif choice == "3":
        list_gmail_tools()
    else:
        print("Goodbye!")


if __name__ == "__main__":
    main()
