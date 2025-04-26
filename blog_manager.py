import mysql.connector
from mysql.connector import Error
import sys
import json
from getpass import getpass

class BlogManager:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',  
                password='Diksha@404',  
                database='blog_db'
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                self.current_user = None
                self.initialize_database()
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            sys.exit(1)

    def initialize_database(self):
        """Create tables if they don't exist"""
        try:
            # First drop tables if they exist (for clean setup)
            self.cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            self.cursor.execute("DROP TABLE IF EXISTS post_tags")
            self.cursor.execute("DROP TABLE IF EXISTS posts")
            self.cursor.execute("DROP TABLE IF EXISTS tags")
            self.cursor.execute("DROP TABLE IF EXISTS users")
            self.cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            # Create users table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create posts table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    user_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create tags table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE
                )
            """)
            
            # Create post_tags junction table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_tags (
                    post_id INT NOT NULL,
                    tag_id INT NOT NULL,
                    PRIMARY KEY (post_id, tag_id),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
            """)
            
            # Create admin user if not exists
            self.cursor.execute("""
                INSERT IGNORE INTO users (username, password)
                VALUES ('admin', 'admin123')
            """)
            
            self.connection.commit()
            print("Database initialized successfully!")
        except Error as e:
            print(f"Error initializing database: {e}")

    def authenticate(self):
        """Authenticate user before allowing operations"""
        username = input("Username: ")
        password = getpass("Password: ")
        
        try:
            self.cursor.execute(
                "SELECT id, username FROM users WHERE username = %s AND password = %s",
                (username, password)
            )
            user = self.cursor.fetchone()
            
            if user:
                self.current_user = user
                print(f"Welcome, {user['username']}!")
                return True
            else:
                print("Authentication failed. Please try again.")
                return False
        except Error as e:
            print(f"Error during authentication: {e}")
            return False

    def register(self):
        """Register a new user"""
        username = input("Choose a username: ")
        password = getpass("Choose a password: ")
        
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )
            self.connection.commit()
            print("Registration successful! Please login.")
            return True
        except Error as e:
            print(f"Error registering user: {e}")
            self.connection.rollback()
            return False

    def create_post(self):
        """Create a new post with tags"""
        if not self.current_user:
            print("Please login first.")
            return
            
        title = input("Enter post title: ")
        content = input("Enter post content: ")
        tags_str = input("Enter comma-separated tags: ")
        
        try:
            # Insert post
            self.cursor.execute(
                "INSERT INTO posts (title, content, user_id) VALUES (%s, %s, %s)",
                (title, content, self.current_user['id'])
            )
            post_id = self.cursor.lastrowid
            
            # Process tags
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            for tag_name in tags:
                # Insert tag if it doesn't exist
                self.cursor.execute(
                    "INSERT IGNORE INTO tags (name) VALUES (%s)",
                    (tag_name,)
                )
                
                # Get tag ID
                self.cursor.execute(
                    "SELECT id FROM tags WHERE name = %s",
                    (tag_name,)
                )
                tag_id = self.cursor.fetchone()['id']
                
                # Link post and tag
                self.cursor.execute(
                    "INSERT IGNORE INTO post_tags (post_id, tag_id) VALUES (%s, %s)",
                    (post_id, tag_id)
                )
            
            self.connection.commit()
            print(f"Post '{title}' created successfully with {len(tags)} tags.")
        except Error as e:
            print(f"Error creating post: {e}")
            self.connection.rollback()

    def list_posts(self, page=1, per_page=5):
        """List all post titles with pagination"""
        try:
            offset = (page - 1) * per_page
            self.cursor.execute(
                "SELECT id, title FROM posts ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (per_page, offset)
            )
            posts = self.cursor.fetchall()
            
            if not posts:
                print("No posts found.")
                return 0
            
            print("\nRecent Posts:")
            for idx, post in enumerate(posts, 1):
                print(f"{idx}. {post['title']} (ID: {post['id']})")
            
            # Show pagination info
            self.cursor.execute("SELECT COUNT(*) as total FROM posts")
            total_posts = self.cursor.fetchone()['total']
            total_pages = (total_posts + per_page - 1) // per_page
            print(f"\nPage {page} of {total_pages} (Total posts: {total_posts})")
            
            return total_pages
        except Error as e:
            print(f"Error listing posts: {e}")
            return 0

    def view_post(self, post_id=None):
        """View specific post content by ID"""
        if not post_id:
            try:
                post_id = int(input("Enter the ID of the post to view: "))
            except ValueError:
                print("Invalid post ID. Please enter a number.")
                return
        
        try:
            self.cursor.execute("""
                SELECT p.id, p.title, p.content, u.username as author, p.created_at
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.id = %s
            """, (post_id,))
            post = self.cursor.fetchone()
            
            if not post:
                print(f"No post found with ID {post_id}")
                return
            
            # Get tags for the post
            self.cursor.execute("""
                SELECT t.name FROM tags t
                JOIN post_tags pt ON t.id = pt.tag_id
                WHERE pt.post_id = %s
            """, (post_id,))
            tags = [tag['name'] for tag in self.cursor.fetchall()]
            
            print(f"\nTitle: {post['title']}")
            print(f"Author: {post['author']}")
            print(f"Date: {post['created_at']}")
            print(f"Tags: {', '.join(tags) if tags else 'No tags'}")
            print("\nContent:")
            print(post['content'])
            
            return post
        except Error as e:
            print(f"Error viewing post: {e}")

    def update_post(self):
        """Update an existing post"""
        if not self.current_user:
            print("Please login first.")
            return
            
        try:
            post_id = int(input("Enter the ID of the post to update: "))
        except ValueError:
            print("Invalid post ID. Please enter a number.")
            return
        
        # Verify post exists and belongs to current user
        self.cursor.execute(
            "SELECT id FROM posts WHERE id = %s AND user_id = %s",
            (post_id, self.current_user['id'])
        )
        if not self.cursor.fetchone():
            print("Post not found or you don't have permission to edit it.")
            return
        
        post = self.view_post(post_id)
        if not post:
            return
        
        new_title = input(f"New title [{post['title']}]: ") or post['title']
        new_content = input(f"New content (press Enter to keep current): ") or post['content']
        new_tags = input("New comma-separated tags (leave blank to keep current): ")
        
        try:
            self.cursor.execute(
                "UPDATE posts SET title = %s, content = %s WHERE id = %s",
                (new_title, new_content, post_id)
            )
            
            if new_tags.strip():
                # Delete existing tags
                self.cursor.execute(
                    "DELETE FROM post_tags WHERE post_id = %s",
                    (post_id,)
                )
                # Add new tags
                tags = [tag.strip() for tag in new_tags.split(',') if tag.strip()]
                for tag_name in tags:
                    # Insert tag if it doesn't exist
                    self.cursor.execute(
                        "INSERT IGNORE INTO tags (name) VALUES (%s)",
                        (tag_name,)
                    )
                    
                    # Get tag ID
                    self.cursor.execute(
                        "SELECT id FROM tags WHERE name = %s",
                        (tag_name,)
                    )
                    tag_id = self.cursor.fetchone()['id']
                    
                    # Link post and tag
                    self.cursor.execute(
                        "INSERT IGNORE INTO post_tags (post_id, tag_id) VALUES (%s, %s)",
                        (post_id, tag_id)
                    )
            
            self.connection.commit()
            print("Post updated successfully!")
        except Error as e:
            print(f"Error updating post: {e}")
            self.connection.rollback()

    def search_by_tag(self):
        """Search posts by tag"""
        tag_name = input("Enter tag to search for: ")
        
        try:
            self.cursor.execute("""
                SELECT p.id, p.title, p.created_at, u.username as author
                FROM posts p
                JOIN post_tags pt ON p.id = pt.post_id
                JOIN tags t ON pt.tag_id = t.id
                JOIN users u ON p.user_id = u.id
                WHERE t.name = %s
                ORDER BY p.created_at DESC
            """, (tag_name,))
            posts = self.cursor.fetchall()
            
            if not posts:
                print(f"No posts found with tag '{tag_name}'")
                return
            
            print(f"\nPosts tagged with '{tag_name}':")
            for post in posts:
                print(f"{post['id']}. {post['title']} (by {post['author']}, {post['created_at']})")
        except Error as e:
            print(f"Error searching by tag: {e}")

    def export_to_json(self):
        """Export all posts to JSON file"""
        filename = input("Enter filename for export (e.g., posts.json): ")
        
        try:
            self.cursor.execute("""
                SELECT p.id, p.title, p.content, u.username as author, 
                       p.created_at, GROUP_CONCAT(t.name) as tags
                FROM posts p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN post_tags pt ON p.id = pt.post_id
                LEFT JOIN tags t ON pt.tag_id = t.id
                GROUP BY p.id
                ORDER BY p.created_at DESC
            """)
            
            posts = []
            for row in self.cursor:
                posts.append({
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'],
                    'author': row['author'],
                    'created_at': str(row['created_at']),
                    'tags': row['tags'].split(',') if row['tags'] else []
                })
            
            with open(filename, 'w') as f:
                json.dump({'posts': posts}, f, indent=2)
            
            print(f"Exported {len(posts)} posts to {filename}")
            return True
        except Error as e:
            print(f"Error exporting posts: {e}")
            return False
        except Exception as e:
            print(f"Error writing to file: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

def display_menu(user_authenticated=False):
    print("\nBlog Post Manager")
    if not user_authenticated:
        print("1. Login")
        print("2. Register")
    else:
        print("1. Create a new post")
        print("2. List all posts")
        print("3. View a specific post")
        print("4. Update a post")
        print("5. Search posts by tag")
        print("6. Export posts to JSON")
        print("7. Logout")
    print("0. Exit")

def main():
    manager = BlogManager()
    
    while True:
        display_menu(manager.current_user is not None)
        choice = input("Enter your choice: ")
        
        if not manager.current_user:
            # Unauthenticated menu
            if choice == '1':
                manager.authenticate()
            elif choice == '2':
                manager.register()
            elif choice == '0':
                print("Exiting Blog Post Manager. Goodbye!")
                manager.close()
                break
            else:
                print("Invalid choice. Please try again.")
        else:
            # Authenticated menu
            if choice == '1':
                manager.create_post()
            elif choice == '2':
                page = 1
                while True:
                    total_pages = manager.list_posts(page)
                    if total_pages == 0:
                        break
                    
                    nav = input("\n[n]ext, [p]revious, [v]iew post, or [q]uit: ").lower()
                    if nav == 'n' and page < total_pages:
                        page += 1
                    elif nav == 'p' and page > 1:
                        page -= 1
                    elif nav == 'v':
                        try:
                            post_id = int(input("Enter post ID to view: "))
                            manager.view_post(post_id)
                        except ValueError:
                            print("Invalid post ID. Please enter a number.")
                    elif nav == 'q':
                        break
            elif choice == '3':
                manager.view_post()
            elif choice == '4':
                manager.update_post()
            elif choice == '5':
                manager.search_by_tag()
            elif choice == '6':
                manager.export_to_json()
            elif choice == '7':
                manager.current_user = None
                print("Logged out successfully.")
            elif choice == '0':
                print("Exiting Blog Post Manager. Goodbye!")
                manager.close()
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()