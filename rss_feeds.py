import feedparser
import json
import time
import schedule
from datetime import datetime
from typing import Dict, List
import hashlib

class RSSFeedManager:
    def __init__(self, feed_urls: List[str], output_file: str = "rss_data.json"):
        """
        Initialize the RSS Feed Manager
        
        Args:
            feed_urls: List of RSS feed URLs to monitor
            output_file: JSON file path to save the data
        """
        self.feed_urls = feed_urls
        self.output_file = output_file
        self.feeds_data = {}
        
        # Load existing data if file exists
        self.load_existing_data()
    
    def generate_id(self, url: str) -> str:
        """
        Generate a unique hash-based ID from URL using SHA-256
        
        Args:
            url: The URL to hash
            
        Returns:
            A 16-character hash ID
        """
        return hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
    
    def load_existing_data(self):
        """
        Load existing data from JSON file to maintain state and avoid duplicates
        """
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                self.feeds_data = json.load(f)
                
            print(f"Loaded {len(self.feeds_data)} existing entries from {self.output_file}")
            unread_count = sum(1 for entry in self.feeds_data.values() if not entry.get('read', False))
            print(f"  Unread entries: {unread_count}")
                
        except FileNotFoundError:
            print(f"No existing data file found. Starting fresh.")
            self.feeds_data = {}
        except json.JSONDecodeError:
            print(f"Error reading existing data file. Starting fresh.")
            self.feeds_data = {}
    
    def fetch_feeds(self) -> Dict[str, Dict]:
        """
        Fetch all RSS feeds and extract entries with deduplication
        
        Returns:
            Dictionary with hash IDs as keys and entry data as values
        """
        new_entries_count = 0
        updated_entries_count = 0
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching RSS feeds...")
        
        for feed_url in self.feed_urls:
            try:
                # Parse the RSS feed
                feed = feedparser.parse(feed_url)
                feed_title = feed.feed.get('title', 'Unknown Feed')
                
                # Extract entries
                for entry in feed.entries:
                    url = entry.get('link', '')
                    title = entry.get('title', 'No Title')
                    
                    if url:
                        # Generate hash-based ID
                        entry_id = self.generate_id(url)
                        
                        # Check if entry already exists
                        if entry_id not in self.feeds_data:
                            # New entry - add it
                            self.feeds_data[entry_id] = {
                                'url': url,
                                'title': title,
                                'read': False,
                                'feed_source': feed_title,
                                'added_date': datetime.now().isoformat()
                            }
                            new_entries_count += 1
                        else:
                            # Entry exists - update title if changed (preserve read status)
                            if self.feeds_data[entry_id]['title'] != title:
                                self.feeds_data[entry_id]['title'] = title
                                updated_entries_count += 1
                
                print(f"  ✓ Successfully fetched: {feed_url} ({len(feed.entries)} entries)")
                
            except Exception as e:
                print(f"  ✗ Error fetching {feed_url}: {str(e)}")
        
        if new_entries_count > 0:
            print(f"  Added {new_entries_count} new entries")
        if updated_entries_count > 0:
            print(f"  Updated {updated_entries_count} entries")
        if new_entries_count == 0 and updated_entries_count == 0:
            print(f"  No new or updated entries")
            
        return self.feeds_data
    
    def save_to_json(self, data: Dict[str, Dict]):
        """
        Save the feed data to a JSON file
        
        Args:
            data: Dictionary to save
        """
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Data saved to {self.output_file}")
            print(f"  Total entries: {len(data)}")
            unread_count = sum(1 for entry in data.values() if not entry.get('read', False))
            print(f"  Unread entries: {unread_count}")
        except Exception as e:
            print(f"Error saving to JSON: {str(e)}")
    
    def mark_as_read(self, entry_id: str):
        """
        Mark a specific entry as read
        
        Args:
            entry_id: The hash ID of the entry to mark as read
        """
        if entry_id in self.feeds_data:
            self.feeds_data[entry_id]['read'] = True
            self.save_to_json(self.feeds_data)
            print(f"Entry {entry_id} marked as read")
            return True
        else:
            print(f"Entry {entry_id} not found")
            return False
    
    def mark_as_read_by_url(self, url: str):
        """
        Mark an entry as read by its URL
        
        Args:
            url: The URL of the entry to mark as read
        """
        entry_id = self.generate_id(url)
        return self.mark_as_read(entry_id)
    
    def mark_all_as_read(self):
        """
        Mark all entries as read
        """
        for entry_id in self.feeds_data:
            self.feeds_data[entry_id]['read'] = True
        self.save_to_json(self.feeds_data)
        print("All entries marked as read")
    
    def get_unread_entries(self) -> Dict[str, Dict]:
        """
        Get all unread entries
        
        Returns:
            Dictionary of unread entries
        """
        return {k: v for k, v in self.feeds_data.items() if not v.get('read', False)}
    
    def get_entry_by_url(self, url: str) -> Dict:
        """
        Get an entry by its URL
        
        Args:
            url: The URL to look up
            
        Returns:
            Entry data or None if not found
        """
        entry_id = self.generate_id(url)
        return self.feeds_data.get(entry_id)
    
    def search_entries(self, keyword: str) -> Dict[str, Dict]:
        """
        Search entries by keyword in title
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            Dictionary of matching entries
        """
        keyword_lower = keyword.lower()
        return {
            k: v for k, v in self.feeds_data.items() 
            if keyword_lower in v.get('title', '').lower()
        }
    
    def get_entries_by_feed(self, feed_source: str) -> Dict[str, Dict]:
        """
        Get all entries from a specific feed source
        
        Args:
            feed_source: Name of the feed source
            
        Returns:
            Dictionary of entries from that feed
        """
        return {
            k: v for k, v in self.feeds_data.items() 
            if v.get('feed_source', '') == feed_source
        }
    
    def get_statistics(self):
        """
        Print statistics about the feeds
        """
        total = len(self.feeds_data)
        unread = sum(1 for entry in self.feeds_data.values() if not entry.get('read', False))
        read = total - unread
        
        # Count by feed source
        feed_counts = {}
        for entry in self.feeds_data.values():
            source = entry.get('feed_source', 'Unknown')
            feed_counts[source] = feed_counts.get(source, 0) + 1
        
        print("\n" + "=" * 60)
        print("RSS FEED STATISTICS")
        print("=" * 60)
        print(f"Total entries: {total}")
        print(f"Read entries: {read}")
        print(f"Unread entries: {unread}")
        print("\nEntries by feed source:")
        for source, count in sorted(feed_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")
        print("=" * 60 + "\n")
    
    def update_feeds(self):
        """
        Fetch feeds and save to JSON (called on schedule)
        """
        self.feeds_data = self.fetch_feeds()
        self.save_to_json(self.feeds_data)
        print("-" * 60)
    
    def run(self):
        """
        Run the RSS feed manager with 6-hour refresh schedule
        """
        print("RSS Feed Manager Started (Hash-based IDs)")
        print("=" * 60)
        
        # Initial fetch
        self.update_feeds()
        
        # Schedule updates every 6 hours
        schedule.every(6).hours.do(self.update_feeds)
        
        print(f"Scheduled to refresh every 6 hours")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        # Keep the script running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nRSS Feed Manager stopped")


def main():
    rss_feeds = [
        "https://www.ft.com/india?format=rss",
        "https://www.vifindia.org/rss.xml",
        "https://economictimes.indiatimes.com/rssfeeds/1200949414.cms",
        "https://theprint.in/category/diplomacy/feed/",
        "https://www.foreignaffairs.com/feeds/region/India/rss.xml",
        "https://foreignpolicy.com/tag/india/feed/",
        "https://frontline.thehindu.com/world-affairs/feeder/default.rss"
    ]
    
    # Create and run the manager
    manager = RSSFeedManager(rss_feeds, output_file="rss_feeds.json")
    
    # Run the continuous update loop
    manager.run()
    
    # ===== EXAMPLE USAGE (uncomment to use) =====
    
    # Get statistics
    # manager.get_statistics()
    
    # Mark specific entry as read by hash ID
    # manager.mark_as_read("a1b2c3d4e5f6g7h8")
    
    # Mark entry as read by URL
    # manager.mark_as_read_by_url("https://example.com/article")
    
    # Get unread entries
    # unread = manager.get_unread_entries()
    # print(f"\nUnread entries ({len(unread)}):")
    # for entry_id, entry_data in unread.items():
    #     print(f"  [{entry_id}] {entry_data['title']}")
    
    # Search for entries
    # results = manager.search_entries("technology")
    # print(f"\nSearch results: {len(results)} entries")
    
    # Get entries from specific feed
    # bbc_entries = manager.get_entries_by_feed("BBC News")
    # print(f"\nBBC News entries: {len(bbc_entries)}")
    
    # Get entry by URL
    # entry = manager.get_entry_by_url("https://example.com/article")
    # if entry:
    #     print(f"Found: {entry['title']}")


if __name__ == "__main__":
    main()