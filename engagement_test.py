#!/usr/bin/env python3
"""
StyleFlow Backend Testing Suite - Engagement System (Viral Loop)
Testing all engagement endpoints: posts, likes, saves, shares, comments, trending tags
"""

import requests
import json
import uuid
import base64
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

class EngagementTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.user1_token = None
        self.user1_id = None
        self.user1_email = None
        self.user2_token = None
        self.user2_id = None
        self.user2_email = None
        self.test_post_id = None
        self.test_comment_id = None
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def make_request(self, method, endpoint, data=None, token=None, params=None):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed: {e}")
            return None
    
    def create_test_users(self):
        """Create two test users for engagement testing"""
        self.log("👤 Creating test users...")
        
        # Create User 1
        unique_id1 = str(uuid.uuid4())[:8]
        self.user1_email = f"creator_{unique_id1}@styleflow.com"
        
        response1 = self.make_request("POST", "/auth/signup", {
            "email": self.user1_email,
            "password": "TestPass123!",
            "full_name": "Sarah Creator",
            "business_name": "Sarah's Hair Studio"
        })
        
        if response1 and response1.status_code == 200:
            data1 = response1.json()
            self.user1_token = data1.get("token")
            
            # Get user ID
            me_response1 = self.make_request("GET", "/auth/me", token=self.user1_token)
            if me_response1 and me_response1.status_code == 200:
                user_data1 = me_response1.json()
                self.user1_id = user_data1.get("id")
                self.log(f"✅ User 1 created: {self.user1_email} (ID: {self.user1_id})")
            else:
                self.log("❌ Could not get User 1 ID")
                return False
        else:
            self.log(f"❌ User 1 creation failed: {response1.status_code if response1 else 'No response'}")
            return False
        
        # Create User 2
        unique_id2 = str(uuid.uuid4())[:8]
        self.user2_email = f"follower_{unique_id2}@styleflow.com"
        
        response2 = self.make_request("POST", "/auth/signup", {
            "email": self.user2_email,
            "password": "TestPass123!",
            "full_name": "Mike Follower",
            "business_name": "Mike's Barber Shop"
        })
        
        if response2 and response2.status_code == 200:
            data2 = response2.json()
            self.user2_token = data2.get("token")
            
            # Get user ID
            me_response2 = self.make_request("GET", "/auth/me", token=self.user2_token)
            if me_response2 and me_response2.status_code == 200:
                user_data2 = me_response2.json()
                self.user2_id = user_data2.get("id")
                self.log(f"✅ User 2 created: {self.user2_email} (ID: {self.user2_id})")
            else:
                self.log("❌ Could not get User 2 ID")
                return False
        else:
            self.log(f"❌ User 2 creation failed: {response2.status_code if response2 else 'No response'}")
            return False
        
        # User 2 follows User 1
        follow_response = self.make_request("POST", f"/users/{self.user1_id}/follow", token=self.user2_token)
        if follow_response and follow_response.status_code == 200:
            self.log("✅ User 2 now follows User 1")
        else:
            self.log("❌ Could not establish follow relationship")
        
        return True
    
    def generate_sample_image(self):
        """Generate a small base64 encoded sample image"""
        # Create a simple 1x1 pixel PNG in base64
        # This is a minimal valid PNG image
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
        return base64.b64encode(png_data).decode('utf-8')
    
    def test_post_creation(self):
        """Test post creation with various scenarios"""
        self.log("\n🧪 Testing Post Creation...")
        
        # Test 1: Create post with 1 image
        self.log("Test 1: Create post with 1 image")
        sample_image = self.generate_sample_image()
        
        response = self.make_request("POST", "/posts", {
            "images": [sample_image],
            "caption": "Beautiful balayage transformation! ✨ #balayage #hairtransformation",
            "tags": ["balayage", "hairtransformation"]
        }, token=self.user1_token)
        
        if response and response.status_code == 200:  # Changed from 201 to 200
            data = response.json()
            self.test_post_id = data.get("id")  # Changed from post_id to id
            self.log(f"✅ Post created successfully: {self.test_post_id}")
        else:
            self.log(f"❌ Post creation failed: {response.status_code if response else 'No response'}")
            if response:
                self.log(f"Response: {response.text}")
            return False
        
        # Test 2: Create post with 5 images (max allowed)
        self.log("Test 2: Create post with 5 images (max)")
        response = self.make_request("POST", "/posts", {
            "images": [sample_image] * 5,
            "caption": "Hair color progression showcase! 🌈",
            "tags": ["colorprogression", "showcase"]
        }, token=self.user1_token)
        
        if response and response.status_code == 201:
            self.log("✅ Post with 5 images created successfully")
        else:
            self.log(f"❌ Post with 5 images failed: {response.status_code if response else 'No response'}")
        
        # Test 3: Try to create post with 6 images (should fail)
        self.log("Test 3: Create post with 6 images (should fail)")
        response = self.make_request("POST", "/posts", {
            "images": [sample_image] * 6,
            "caption": "Too many images test",
            "tags": ["test"]
        }, token=self.user1_token)
        
        if response and response.status_code == 400:
            self.log("✅ Correctly rejected post with >5 images")
        else:
            self.log(f"❌ Should reject post with >5 images: {response.status_code if response else 'No response'}")
        
        # Test 4: Try to create post with 0 images (should fail)
        self.log("Test 4: Create post with 0 images (should fail)")
        response = self.make_request("POST", "/posts", {
            "images": [],
            "caption": "No images test",
            "tags": ["test"]
        }, token=self.user1_token)
        
        if response and response.status_code == 400:
            self.log("✅ Correctly rejected post with 0 images")
        else:
            self.log(f"❌ Should reject post with 0 images: {response.status_code if response else 'No response'}")
        
        # Test 5: Test invalid tags (not in predefined list)
        self.log("Test 5: Create post with invalid tags")
        response = self.make_request("POST", "/posts", {
            "images": [sample_image],
            "caption": "Testing invalid tags",
            "tags": ["invalidtag", "anotherbadtag"]
        }, token=self.user1_token)
        
        if response and response.status_code == 400:
            self.log("✅ Correctly rejected post with invalid tags")
        else:
            self.log(f"❌ Should reject post with invalid tags: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_get_posts_feed(self):
        """Test getting posts feed with different filters"""
        self.log("\n🧪 Testing Posts Feed...")
        
        # Test 1: Get trending feed (default)
        self.log("Test 1: Get trending feed")
        response = self.make_request("GET", "/posts", params={"feed": "trending"}, token=self.user1_token)
        
        if response and response.status_code == 200:
            posts = response.json()  # Direct list response
            self.log(f"✅ Trending feed returned {len(posts)} posts")
            
            # Check if our test post is in the feed
            test_post_found = any(post.get("id") == self.test_post_id for post in posts)
            if test_post_found:
                self.log("✅ Test post found in trending feed")
            else:
                self.log("❌ Test post not found in trending feed")
        else:
            self.log(f"❌ Trending feed failed: {response.status_code if response else 'No response'}")
            return False
        
        # Test 2: Get new feed
        self.log("Test 2: Get new feed")
        response = self.make_request("GET", "/posts", params={"feed": "new"}, token=self.user1_token)
        
        if response and response.status_code == 200:
            posts = response.json()  # Direct list response
            self.log(f"✅ New feed returned {len(posts)} posts")
        else:
            self.log(f"❌ New feed failed: {response.status_code if response else 'No response'}")
        
        # Test 3: Get following feed (User 2 should see User 1's posts)
        self.log("Test 3: Get following feed")
        response = self.make_request("GET", "/posts", params={"feed": "following"}, token=self.user2_token)
        
        if response and response.status_code == 200:
            posts = response.json()  # Direct list response
            self.log(f"✅ Following feed returned {len(posts)} posts")
            
            # Check if User 1's post is in User 2's following feed
            user1_post_found = any(post.get("user_id") == self.user1_id for post in posts)
            if user1_post_found:
                self.log("✅ User 1's post found in User 2's following feed")
            else:
                self.log("❌ User 1's post not found in User 2's following feed")
        else:
            self.log(f"❌ Following feed failed: {response.status_code if response else 'No response'}")
        
        # Test 4: Filter by tag
        self.log("Test 4: Filter by tag")
        response = self.make_request("GET", "/posts", params={"tag": "balayage"}, token=self.user1_token)
        
        if response and response.status_code == 200:
            posts = response.json()  # Direct list response
            self.log(f"✅ Tag filter returned {len(posts)} posts")
            
            # All posts should contain the balayage tag
            all_have_tag = all("balayage" in post.get("tags", []) for post in posts)
            if all_have_tag or len(posts) == 0:
                self.log("✅ All posts contain the filtered tag")
            else:
                self.log("❌ Some posts don't contain the filtered tag")
        else:
            self.log(f"❌ Tag filter failed: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_single_post_operations(self):
        """Test single post operations"""
        self.log("\n🧪 Testing Single Post Operations...")
        
        # Test 1: Get single post
        self.log("Test 1: Get single post")
        response = self.make_request("GET", f"/posts/{self.test_post_id}", token=self.user1_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("id") == self.test_post_id:
                self.log("✅ Single post retrieved successfully")
            else:
                self.log(f"❌ Wrong post returned: {data.get('id')} vs {self.test_post_id}")
                return False
        else:
            self.log(f"❌ Single post retrieval failed: {response.status_code if response else 'No response'}")
            return False
        
        # Test 2: Get posts by user
        self.log("Test 2: Get posts by user")
        response = self.make_request("GET", f"/posts/user/{self.user1_id}", token=self.user1_token)
        
        if response and response.status_code == 200:
            posts = response.json()  # Direct list response
            self.log(f"✅ User posts returned {len(posts)} posts")
            
            # All posts should belong to user1
            all_user1_posts = all(post.get("user_id") == self.user1_id for post in posts)
            if all_user1_posts:
                self.log("✅ All posts belong to the correct user")
            else:
                self.log("❌ Some posts don't belong to the correct user")
        else:
            self.log(f"❌ User posts failed: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_post_interactions(self):
        """Test post like and save interactions"""
        self.log("\n🧪 Testing Post Interactions...")
        
        # Test 1: Like a post
        self.log("Test 1: Like a post")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/like", token=self.user2_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("liked") == True and data.get("likes_count") >= 1:
                self.log(f"✅ Post liked successfully (likes: {data.get('likes_count')})")
            else:
                self.log(f"❌ Like response incorrect: {data}")
                return False
        else:
            self.log(f"❌ Post like failed: {response.status_code if response else 'No response'}")
            return False
        
        # Test 2: Unlike the post
        self.log("Test 2: Unlike the post")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/like", token=self.user2_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("liked") == False and data.get("likes_count") >= 0:
                self.log(f"✅ Post unliked successfully (likes: {data.get('likes_count')})")
            else:
                self.log(f"❌ Unlike response incorrect: {data}")
                return False
        else:
            self.log(f"❌ Post unlike failed: {response.status_code if response else 'No response'}")
            return False
        
        # Test 3: Save a post
        self.log("Test 3: Save a post")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/save", token=self.user2_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("saved") == True:
                self.log("✅ Post saved successfully")
            else:
                self.log(f"❌ Save response incorrect: {data}")
                return False
        else:
            self.log(f"❌ Post save failed: {response.status_code if response else 'No response'}")
            return False
        
        # Test 4: Unsave the post
        self.log("Test 4: Unsave the post")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/save", token=self.user2_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("saved") == False:
                self.log("✅ Post unsaved successfully")
            else:
                self.log(f"❌ Unsave response incorrect: {data}")
                return False
        else:
            self.log(f"❌ Post unsave failed: {response.status_code if response else 'No response'}")
            return False
        
        # Test 5: Get saved posts
        self.log("Test 5: Get saved posts")
        # First save the post again
        self.make_request("POST", f"/posts/{self.test_post_id}/save", token=self.user2_token)
        
        response = self.make_request("GET", "/posts/saved", token=self.user2_token)
        
        if response and response.status_code == 200:
            posts = response.json()  # Direct list response
            self.log(f"✅ Saved posts returned {len(posts)} posts")
            
            # Check if our test post is in saved posts
            test_post_saved = any(post.get("id") == self.test_post_id for post in posts)
            if test_post_saved:
                self.log("✅ Test post found in saved posts")
            else:
                self.log("❌ Test post not found in saved posts")
        else:
            self.log(f"❌ Saved posts failed: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_comments_system(self):
        """Test comments system"""
        self.log("\n🧪 Testing Comments System...")
        
        # Test 1: Add a comment
        self.log("Test 1: Add a comment")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/comments", {
            "content": "Amazing work! Love the color blend! 💕"
        }, token=self.user2_token)
        
        if response and response.status_code == 200:  # Changed from 201 to 200
            data = response.json()
            self.test_comment_id = data.get("id")  # Changed from comment_id to id
            self.log(f"✅ Comment added successfully: {self.test_comment_id}")
        else:
            self.log(f"❌ Comment creation failed: {response.status_code if response else 'No response'}")
            if response:
                self.log(f"Response: {response.text}")
            return False
        
        # Test 2: Try to add empty comment (should fail)
        self.log("Test 2: Add empty comment (should fail)")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/comments", {
            "content": ""
        }, token=self.user2_token)
        
        if response and response.status_code == 400:
            self.log("✅ Correctly rejected empty comment")
        else:
            self.log(f"❌ Should reject empty comment: {response.status_code if response else 'No response'}")
        
        # Test 3: Get comments for post
        self.log("Test 3: Get comments for post")
        response = self.make_request("GET", f"/posts/{self.test_post_id}/comments", token=self.user1_token)
        
        if response and response.status_code == 200:
            comments = response.json()  # Direct list response
            self.log(f"✅ Comments retrieved: {len(comments)} comments")
            
            # Check if our test comment is there
            test_comment_found = any(comment.get("id") == self.test_comment_id for comment in comments)
            if test_comment_found:
                self.log("✅ Test comment found in comments list")
            else:
                self.log("❌ Test comment not found in comments list")
        else:
            self.log(f"❌ Get comments failed: {response.status_code if response else 'No response'}")
            return False
        
        # Test 4: Like a comment
        self.log("Test 4: Like a comment")
        response = self.make_request("POST", f"/comments/{self.test_comment_id}/like", token=self.user1_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("liked") == True:
                self.log("✅ Comment liked successfully")
            else:
                self.log(f"❌ Comment like response incorrect: {data}")
        else:
            self.log(f"❌ Comment like failed: {response.status_code if response else 'No response'}")
        
        # Test 5: Pin comment (only post creator can pin)
        self.log("Test 5: Pin comment (post creator)")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/comments/{self.test_comment_id}/pin", token=self.user1_token)
        
        if response and response.status_code == 200:
            self.log("✅ Comment pinned successfully by post creator")
        else:
            self.log(f"❌ Comment pin failed: {response.status_code if response else 'No response'}")
        
        # Test 6: Try to pin comment as non-owner (should fail)
        self.log("Test 6: Pin comment as non-owner (should fail)")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/comments/{self.test_comment_id}/pin", token=self.user2_token)
        
        if response and response.status_code == 403:
            self.log("✅ Correctly rejected pin attempt by non-owner")
        else:
            self.log(f"❌ Should reject pin by non-owner: {response.status_code if response else 'No response'}")
        
        # Test 7: Delete comment (comment author can delete)
        self.log("Test 7: Delete comment (comment author)")
        response = self.make_request("DELETE", f"/comments/{self.test_comment_id}", token=self.user2_token)
        
        if response and response.status_code == 200:
            self.log("✅ Comment deleted successfully by author")
        else:
            self.log(f"❌ Comment deletion failed: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_sharing_system(self):
        """Test post sharing system"""
        self.log("\n🧪 Testing Sharing System...")
        
        # Test 1: Share a post
        self.log("Test 1: Share a post")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/share", {
            "caption": "Check out this amazing transformation by @sarah! 🔥"
        }, token=self.user2_token)
        
        if response and response.status_code == 200:  # Changed from 201 to 200
            data = response.json()
            shared_post_id = data.get("id")  # Changed from shared_post_id to id
            self.log(f"✅ Post shared successfully: {shared_post_id}")
        else:
            self.log(f"❌ Post sharing failed: {response.status_code if response else 'No response'}")
            if response:
                self.log(f"Response: {response.text}")
            return False
        
        # Test 2: Try to share own post (should fail)
        self.log("Test 2: Share own post (should fail)")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/share", {
            "caption": "Sharing my own post"
        }, token=self.user1_token)
        
        if response and response.status_code == 400:
            self.log("✅ Correctly rejected sharing own post")
        else:
            self.log(f"❌ Should reject sharing own post: {response.status_code if response else 'No response'}")
        
        # Test 3: Try to share same post twice (should fail)
        self.log("Test 3: Share same post twice (should fail)")
        response = self.make_request("POST", f"/posts/{self.test_post_id}/share", {
            "caption": "Trying to share again"
        }, token=self.user2_token)
        
        if response and response.status_code == 400:
            self.log("✅ Correctly rejected duplicate share")
        else:
            self.log(f"❌ Should reject duplicate share: {response.status_code if response else 'No response'}")
        
        # Test 4: Verify original post shares count increased
        self.log("Test 4: Verify shares count increased")
        response = self.make_request("GET", f"/posts/{self.test_post_id}", token=self.user1_token)
        
        if response and response.status_code == 200:
            data = response.json()
            shares_count = data.get("shares_count", 0)
            if shares_count >= 1:
                self.log(f"✅ Original post shares count increased: {shares_count}")
            else:
                self.log(f"❌ Shares count not increased: {shares_count}")
        else:
            self.log(f"❌ Could not verify shares count: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_trending_tags(self):
        """Test trending tags endpoint"""
        self.log("\n🧪 Testing Trending Tags...")
        
        response = self.make_request("GET", "/posts/trending-tags", token=self.user1_token)
        
        if response and response.status_code == 200:
            tags = response.json()  # Direct list response
            self.log(f"✅ Trending tags returned {len(tags)} tags")
            
            # Check if our test tags are in the trending list
            if len(tags) > 0:
                self.log(f"   Sample trending tags: {[tag.get('tag') for tag in tags[:5]]}")
                
                # Check if balayage tag is trending (we used it in our test post)
                balayage_found = any(tag.get("tag") == "balayage" for tag in tags)
                if balayage_found:
                    self.log("✅ Test tag 'balayage' found in trending tags")
                else:
                    self.log("❌ Test tag 'balayage' not found in trending tags")
            else:
                self.log("❌ No trending tags returned")
        else:
            self.log(f"❌ Trending tags failed: {response.status_code if response else 'No response'}")
            return False
        
        return True
    
    def test_creator_profile(self):
        """Test enhanced creator profile endpoint"""
        self.log("\n🧪 Testing Creator Profile...")
        
        response = self.make_request("GET", f"/creators/{self.user1_id}/profile", token=self.user2_token)
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check required fields (using 'full_name' instead of 'name')
            required_fields = ["id", "full_name", "business_name", "followers_count", "following_count", "posts_count"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.log("✅ Creator profile returned all required fields")
                self.log(f"   Name: {data.get('full_name')}")
                self.log(f"   Business: {data.get('business_name')}")
                self.log(f"   Followers: {data.get('followers_count')}")
                self.log(f"   Posts: {data.get('posts_count')}")
            else:
                self.log(f"❌ Missing required fields: {missing_fields}")
                return False
        else:
            self.log(f"❌ Creator profile failed: {response.status_code if response else 'No response'}")
            return False
        
        return True
    
    def test_delete_post(self):
        """Test deleting own post"""
        self.log("\n🧪 Testing Post Deletion...")
        
        # Test 1: Delete own post
        self.log("Test 1: Delete own post")
        response = self.make_request("DELETE", f"/posts/{self.test_post_id}", token=self.user1_token)
        
        if response and response.status_code == 200:
            self.log("✅ Post deleted successfully")
            
            # Verify post is gone
            verify_response = self.make_request("GET", f"/posts/{self.test_post_id}", token=self.user1_token)
            if verify_response and verify_response.status_code == 404:
                self.log("✅ Post confirmed deleted (404 on get)")
            else:
                self.log(f"❌ Post still exists after deletion: {verify_response.status_code if verify_response else 'No response'}")
        else:
            self.log(f"❌ Post deletion failed: {response.status_code if response else 'No response'}")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all engagement system tests"""
        self.log("🚀 Starting StyleFlow Engagement System (Viral Loop) Testing...")
        self.log(f"Backend URL: {self.base_url}")
        
        tests = [
            ("Create Test Users", self.create_test_users),
            ("Post Creation & Validation", self.test_post_creation),
            ("Posts Feed (Trending/New/Following)", self.test_get_posts_feed),
            ("Single Post Operations", self.test_single_post_operations),
            ("Post Interactions (Like/Save)", self.test_post_interactions),
            ("Comments System", self.test_comments_system),
            ("Sharing System", self.test_sharing_system),
            ("Trending Tags", self.test_trending_tags),
            ("Creator Profile", self.test_creator_profile),
            ("Post Deletion", self.test_delete_post),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n{'='*60}")
            self.log(f"Running: {test_name}")
            self.log('='*60)
            
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} PASSED")
                else:
                    failed += 1
                    self.log(f"❌ {test_name} FAILED")
            except Exception as e:
                failed += 1
                self.log(f"❌ {test_name} FAILED with exception: {e}")
        
        # Final Results
        self.log(f"\n{'='*60}")
        self.log("🏁 FINAL RESULTS")
        self.log('='*60)
        self.log(f"✅ Passed: {passed}")
        self.log(f"❌ Failed: {failed}")
        self.log(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! Engagement System (Viral Loop) is working perfectly!")
        else:
            self.log(f"⚠️ {failed} test(s) failed. Please review the issues above.")
        
        return failed == 0

if __name__ == "__main__":
    tester = EngagementTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)