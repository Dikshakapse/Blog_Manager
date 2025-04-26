# Blog Management System

A command-line interface for managing blog posts with MySQL database integration, featuring user authentication, post management, and tag organization.

## Features

-  User authentication (login/registration)
-  Create, view, update blog posts
-  Tag management for posts
-  Search posts by tags
-  Export posts to JSON format
-  Paginated post listing
-  User-specific post ownership

## Installation

1. **Prerequisites**:
   - Python 3.8+
   - MySQL Server

2. **Setup**:
   ```bash
   git clone https://github.com/DikshaKapse/blog-manager.git
   cd blog-manager
   pip install -r requirements.txt

Usage
Run:
python blog_manager.py

Menu Options:

1.Login/Register: Secure user authentication
2.Create Post: Add new posts with tags
3.List Posts: View all posts with pagination
4.View Post: See full post details by ID
5.Update Post: Edit your existing posts
6.Search by Tag: Find posts by tags
7.Export to JSON: Backup your posts

Database Schema:
Tables:

users: User accounts
posts: Blog posts
tags: Post tags
post_tags: Post-tag relationships
