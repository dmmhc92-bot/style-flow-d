import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  TextInput,
  FlatList,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Dimensions,
  Modal,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { useAuthStore } from '../../store/authStore';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface Comment {
  id: string;
  text: string;
  user: {
    id: string;
    full_name: string;
    profile_photo?: string;
  };
  likes_count: number;
  user_liked: boolean;
  is_pinned: boolean;
  created_at: string;
}

interface Post {
  id: string;
  author: {
    id: string;
    full_name: string;
    profile_photo?: string;
    business_name?: string;
  };
  images: string[];
  caption?: string;
  tags: string[];
  likes_count: number;
  comments_count: number;
  saves_count: number;
  shares_count: number;
  user_liked: boolean;
  user_saved: boolean;
  is_shared: boolean;
  original_author?: {
    id: string;
    full_name: string;
    profile_photo?: string;
  };
  original_post?: {
    id: string;
    images: string[];
    caption?: string;
    tags: string[];
  };
  share_caption?: string;
  created_at: string;
}

export default function PostDetailScreen() {
  const router = useRouter();
  const { id, share } = useLocalSearchParams<{ id: string; share?: string }>();
  const { user } = useAuthStore();
  
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState('');
  const [posting, setPosting] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [showShareModal, setShowShareModal] = useState(share === 'true');
  const [shareCaption, setShareCaption] = useState('');
  const [sharing, setSharing] = useState(false);
  const commentInputRef = useRef<TextInput>(null);

  useEffect(() => {
    if (id) {
      loadPost();
      loadComments();
    }
  }, [id]);

  const loadPost = async () => {
    try {
      const response = await api.get(`/posts/${id}`);
      setPost(response.data);
    } catch (error) {
      console.error('Failed to load post:', error);
      Alert.alert('Error', 'Failed to load post');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const loadComments = async () => {
    try {
      const response = await api.get(`/posts/${id}/comments`);
      setComments(response.data);
    } catch (error) {
      console.error('Failed to load comments:', error);
    }
  };

  const handleLike = async () => {
    if (!post) return;
    try {
      const response = await api.post(`/posts/${id}/like`);
      setPost(prev => prev ? {
        ...prev,
        user_liked: response.data.liked,
        likes_count: response.data.likes_count,
      } : null);
    } catch (error) {
      console.error('Failed to like post:', error);
    }
  };

  const handleSave = async () => {
    if (!post) return;
    try {
      const response = await api.post(`/posts/${id}/save`);
      setPost(prev => prev ? {
        ...prev,
        user_saved: response.data.saved,
        saves_count: response.data.saves_count,
      } : null);
    } catch (error) {
      console.error('Failed to save post:', error);
    }
  };

  const handlePostComment = async () => {
    if (!commentText.trim() || posting) return;
    
    setPosting(true);
    try {
      const response = await api.post(`/posts/${id}/comments`, {
        text: commentText.trim(),
      });
      setComments(prev => [response.data, ...prev]);
      setCommentText('');
      setPost(prev => prev ? { ...prev, comments_count: prev.comments_count + 1 } : null);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to post comment');
    } finally {
      setPosting(false);
    }
  };

  const handleLikeComment = async (commentId: string) => {
    try {
      const response = await api.post(`/comments/${commentId}/like`);
      setComments(prev =>
        prev.map(c =>
          c.id === commentId
            ? { ...c, user_liked: response.data.liked, likes_count: response.data.likes_count }
            : c
        )
      );
    } catch (error) {
      console.error('Failed to like comment:', error);
    }
  };

  const handlePinComment = async (commentId: string) => {
    if (!post || post.author.id !== user?.id) return;
    
    try {
      const response = await api.post(`/posts/${id}/comments/${commentId}/pin`);
      setComments(prev => {
        // Unpin all, then set the new pinned one
        const updated = prev.map(c => ({ ...c, is_pinned: false }));
        if (response.data.is_pinned) {
          const pinnedIndex = updated.findIndex(c => c.id === commentId);
          if (pinnedIndex !== -1) {
            updated[pinnedIndex].is_pinned = true;
          }
        }
        return updated.sort((a, b) => {
          if (a.is_pinned) return -1;
          if (b.is_pinned) return 1;
          return 0;
        });
      });
    } catch (error) {
      console.error('Failed to pin comment:', error);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    Alert.alert(
      'Delete Comment',
      'Are you sure you want to delete this comment?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/comments/${commentId}`);
              setComments(prev => prev.filter(c => c.id !== commentId));
              setPost(prev => prev ? { ...prev, comments_count: Math.max(0, prev.comments_count - 1) } : null);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete comment');
            }
          },
        },
      ]
    );
  };

  const handleShare = async () => {
    if (!post || sharing) return;
    
    setSharing(true);
    try {
      await api.post(`/posts/${id}/share`, {
        caption: shareCaption.trim() || undefined,
      });
      Alert.alert('Shared!', 'Post has been shared to your feed.', [
        { text: 'OK', onPress: () => setShowShareModal(false) }
      ]);
      setPost(prev => prev ? { ...prev, shares_count: prev.shares_count + 1 } : null);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to share post');
    } finally {
      setSharing(false);
    }
  };

  const handleDeletePost = () => {
    Alert.alert(
      'Delete Post',
      'Are you sure you want to delete this post? This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/posts/${id}`);
              Alert.alert('Deleted', 'Post has been deleted.', [
                { text: 'OK', onPress: () => router.back() }
              ]);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete post');
            }
          },
        },
      ]
    );
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const renderComment = ({ item }: { item: Comment }) => {
    const canDelete = item.user.id === user?.id || post?.author.id === user?.id;
    const canPin = post?.author.id === user?.id;

    return (
      <View style={[styles.commentItem, item.is_pinned && styles.pinnedComment]}>
        {item.is_pinned && (
          <View style={styles.pinnedBadge}>
            <Ionicons name="pin" size={12} color={Colors.accent} />
            <Text style={styles.pinnedText}>Pinned</Text>
          </View>
        )}
        <TouchableOpacity
          style={styles.commentAvatar}
          onPress={() => router.push(`/discover/${item.user.id}`)}
        >
          {item.user.profile_photo ? (
            <Image
              source={{ uri: item.user.profile_photo.startsWith('data:') ? item.user.profile_photo : `data:image/jpeg;base64,${item.user.profile_photo}` }}
              style={styles.commentAvatarImage}
            />
          ) : (
            <Ionicons name="person" size={16} color={Colors.textSecondary} />
          )}
        </TouchableOpacity>
        <View style={styles.commentContent}>
          <View style={styles.commentHeader}>
            <Text style={styles.commentAuthor}>{item.user.full_name}</Text>
            <Text style={styles.commentTime}>{formatTimeAgo(item.created_at)}</Text>
          </View>
          <Text style={styles.commentText}>{item.text}</Text>
          <View style={styles.commentActions}>
            <TouchableOpacity
              style={styles.commentAction}
              onPress={() => handleLikeComment(item.id)}
            >
              <Ionicons
                name={item.user_liked ? 'heart' : 'heart-outline'}
                size={14}
                color={item.user_liked ? Colors.error : Colors.textSecondary}
              />
              {item.likes_count > 0 && (
                <Text style={styles.commentActionText}>{item.likes_count}</Text>
              )}
            </TouchableOpacity>
            {canPin && (
              <TouchableOpacity
                style={styles.commentAction}
                onPress={() => handlePinComment(item.id)}
              >
                <Ionicons
                  name={item.is_pinned ? 'pin' : 'pin-outline'}
                  size={14}
                  color={item.is_pinned ? Colors.accent : Colors.textSecondary}
                />
              </TouchableOpacity>
            )}
            {canDelete && (
              <TouchableOpacity
                style={styles.commentAction}
                onPress={() => handleDeleteComment(item.id)}
              >
                <Ionicons name="trash-outline" size={14} color={Colors.textSecondary} />
              </TouchableOpacity>
            )}
          </View>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
        </View>
      </SafeAreaView>
    );
  }

  if (!post) return null;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
        keyboardVerticalOffset={0}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Post</Text>
          {post.author.id === user?.id && (
            <TouchableOpacity onPress={handleDeletePost}>
              <Ionicons name="trash-outline" size={22} color={Colors.error} />
            </TouchableOpacity>
          )}
        </View>

        <FlatList
          data={comments}
          renderItem={renderComment}
          keyExtractor={item => item.id}
          ListHeaderComponent={
            <>
              {/* Post Author */}
              <TouchableOpacity
                style={styles.postHeader}
                onPress={() => router.push(`/discover/${post.author.id}`)}
              >
                <View style={styles.authorAvatar}>
                  {post.author.profile_photo ? (
                    <Image
                      source={{ uri: post.author.profile_photo.startsWith('data:') ? post.author.profile_photo : `data:image/jpeg;base64,${post.author.profile_photo}` }}
                      style={styles.avatarImage}
                    />
                  ) : (
                    <Ionicons name="person" size={20} color={Colors.accent} />
                  )}
                </View>
                <View style={styles.authorInfo}>
                  <Text style={styles.authorName}>{post.author.full_name}</Text>
                  {post.author.business_name && (
                    <Text style={styles.authorBusiness}>{post.author.business_name}</Text>
                  )}
                </View>
              </TouchableOpacity>

              {/* Images */}
              <ScrollView
                horizontal
                pagingEnabled
                showsHorizontalScrollIndicator={false}
                onMomentumScrollEnd={(e) => {
                  const index = Math.round(e.nativeEvent.contentOffset.x / SCREEN_WIDTH);
                  setCurrentImageIndex(index);
                }}
              >
                {post.images.map((img, idx) => (
                  <Image
                    key={idx}
                    source={{ uri: img.startsWith('data:') ? img : `data:image/jpeg;base64,${img}` }}
                    style={styles.postImage}
                    resizeMode="cover"
                  />
                ))}
              </ScrollView>

              {/* Image Dots */}
              {post.images.length > 1 && (
                <View style={styles.imageDots}>
                  {post.images.map((_, idx) => (
                    <View
                      key={idx}
                      style={[styles.dot, idx === currentImageIndex && styles.dotActive]}
                    />
                  ))}
                </View>
              )}

              {/* Actions */}
              <View style={styles.postActions}>
                <View style={styles.leftActions}>
                  <TouchableOpacity style={styles.actionButton} onPress={handleLike}>
                    <Ionicons
                      name={post.user_liked ? 'heart' : 'heart-outline'}
                      size={26}
                      color={post.user_liked ? Colors.error : Colors.text}
                    />
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => commentInputRef.current?.focus()}
                  >
                    <Ionicons name="chatbubble-outline" size={24} color={Colors.text} />
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => setShowShareModal(true)}
                  >
                    <Ionicons name="paper-plane-outline" size={24} color={Colors.text} />
                  </TouchableOpacity>
                </View>
                <TouchableOpacity style={styles.actionButton} onPress={handleSave}>
                  <Ionicons
                    name={post.user_saved ? 'bookmark' : 'bookmark-outline'}
                    size={24}
                    color={post.user_saved ? Colors.accent : Colors.text}
                  />
                </TouchableOpacity>
              </View>

              {/* Stats */}
              <View style={styles.statsRow}>
                <Text style={styles.likesCount}>{post.likes_count} likes</Text>
                <Text style={styles.statsText}>{post.shares_count} shares</Text>
              </View>

              {/* Caption */}
              {post.caption && (
                <View style={styles.captionContainer}>
                  <Text style={styles.caption}>
                    <Text style={styles.captionAuthor}>{post.author.full_name} </Text>
                    {post.caption}
                  </Text>
                </View>
              )}

              {/* Tags */}
              {post.tags.length > 0 && (
                <View style={styles.tagsContainer}>
                  {post.tags.map(tag => (
                    <TouchableOpacity key={tag}>
                      <Text style={styles.tag}>#{tag}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}

              {/* Post Time */}
              <Text style={styles.postTime}>{formatTimeAgo(post.created_at)}</Text>

              {/* Comments Header */}
              <View style={styles.commentsHeader}>
                <Text style={styles.commentsTitle}>
                  Comments ({post.comments_count})
                </Text>
              </View>
            </>
          }
          ListEmptyComponent={
            <View style={styles.noComments}>
              <Text style={styles.noCommentsText}>No comments yet. Be the first!</Text>
            </View>
          }
          contentContainerStyle={styles.commentsList}
        />

        {/* Comment Input */}
        <View style={styles.commentInputContainer}>
          <TextInput
            ref={commentInputRef}
            style={styles.commentInput}
            placeholder="Add a comment..."
            placeholderTextColor={Colors.textLight}
            value={commentText}
            onChangeText={setCommentText}
            multiline
            maxLength={300}
          />
          <TouchableOpacity
            style={[styles.sendButton, (!commentText.trim() || posting) && styles.sendButtonDisabled]}
            onPress={handlePostComment}
            disabled={!commentText.trim() || posting}
          >
            {posting ? (
              <ActivityIndicator size="small" color={Colors.accent} />
            ) : (
              <Ionicons name="send" size={20} color={Colors.accent} />
            )}
          </TouchableOpacity>
        </View>

        {/* Share Modal */}
        <Modal
          visible={showShareModal}
          animationType="slide"
          transparent
          onRequestClose={() => setShowShareModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.shareModal}>
              <View style={styles.shareModalHeader}>
                <Text style={styles.shareModalTitle}>Share Post</Text>
                <TouchableOpacity onPress={() => setShowShareModal(false)}>
                  <Ionicons name="close" size={24} color={Colors.text} />
                </TouchableOpacity>
              </View>

              {/* Original Post Preview */}
              <View style={styles.sharePreview}>
                <Image
                  source={{ uri: post.images[0].startsWith('data:') ? post.images[0] : `data:image/jpeg;base64,${post.images[0]}` }}
                  style={styles.sharePreviewImage}
                />
                <View style={styles.sharePreviewInfo}>
                  <Text style={styles.sharePreviewAuthor}>
                    Originally by {post.author.full_name}
                  </Text>
                  {post.caption && (
                    <Text style={styles.sharePreviewCaption} numberOfLines={2}>
                      {post.caption}
                    </Text>
                  )}
                </View>
              </View>

              {/* Share Caption */}
              <TextInput
                style={styles.shareCaptionInput}
                placeholder="Add a message (optional)..."
                placeholderTextColor={Colors.textLight}
                value={shareCaption}
                onChangeText={setShareCaption}
                multiline
                maxLength={200}
              />

              <TouchableOpacity
                style={[styles.shareButton, sharing && styles.shareButtonDisabled]}
                onPress={handleShare}
                disabled={sharing}
              >
                {sharing ? (
                  <ActivityIndicator size="small" color={Colors.buttonText} />
                ) : (
                  <>
                    <Ionicons name="paper-plane" size={20} color={Colors.buttonText} />
                    <Text style={styles.shareButtonText}>Share to Feed</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  postHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
  },
  authorAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  avatarImage: {
    width: '100%',
    height: '100%',
  },
  authorInfo: {
    marginLeft: Spacing.sm,
  },
  authorName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  authorBusiness: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  postImage: {
    width: SCREEN_WIDTH,
    height: SCREEN_WIDTH,
  },
  imageDots: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.textLight,
  },
  dotActive: {
    backgroundColor: Colors.accent,
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  postActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.sm,
  },
  leftActions: {
    flexDirection: 'row',
    gap: Spacing.md,
  },
  actionButton: {
    padding: 4,
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.screenPadding,
    gap: Spacing.md,
  },
  likesCount: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  statsText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  captionContainer: {
    paddingHorizontal: Spacing.screenPadding,
    paddingTop: Spacing.sm,
  },
  caption: {
    fontSize: Typography.body,
    color: Colors.text,
    lineHeight: 20,
  },
  captionAuthor: {
    fontWeight: Typography.semibold,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: Spacing.screenPadding,
    paddingTop: Spacing.xs,
    gap: Spacing.xs,
  },
  tag: {
    fontSize: Typography.caption,
    color: Colors.accent,
  },
  postTime: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    paddingHorizontal: Spacing.screenPadding,
    paddingTop: Spacing.sm,
  },
  commentsHeader: {
    paddingHorizontal: Spacing.screenPadding,
    paddingTop: Spacing.lg,
    paddingBottom: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    marginTop: Spacing.md,
  },
  commentsTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  commentsList: {
    paddingBottom: Spacing.lg,
  },
  noComments: {
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.lg,
    alignItems: 'center',
  },
  noCommentsText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  commentItem: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.sm,
  },
  pinnedComment: {
    backgroundColor: Colors.accent + '10',
  },
  pinnedBadge: {
    position: 'absolute',
    top: 4,
    right: Spacing.screenPadding,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  pinnedText: {
    fontSize: 10,
    color: Colors.accent,
  },
  commentAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  commentAvatarImage: {
    width: '100%',
    height: '100%',
  },
  commentContent: {
    flex: 1,
    marginLeft: Spacing.sm,
  },
  commentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  commentAuthor: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  commentTime: {
    fontSize: Typography.caption,
    color: Colors.textLight,
  },
  commentText: {
    fontSize: Typography.body,
    color: Colors.text,
    marginTop: 2,
    lineHeight: 18,
  },
  commentActions: {
    flexDirection: 'row',
    gap: Spacing.md,
    marginTop: Spacing.xs,
  },
  commentAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  commentActionText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  commentInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: Colors.background,
  },
  commentInput: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 20,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    fontSize: Typography.body,
    color: Colors.text,
    maxHeight: 80,
  },
  sendButton: {
    marginLeft: Spacing.sm,
    padding: Spacing.sm,
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  shareModal: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  shareModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  shareModalTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  sharePreview: {
    flexDirection: 'row',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.sm,
    marginBottom: Spacing.md,
  },
  sharePreviewImage: {
    width: 60,
    height: 60,
    borderRadius: 8,
  },
  sharePreviewInfo: {
    flex: 1,
    marginLeft: Spacing.sm,
    justifyContent: 'center',
  },
  sharePreviewAuthor: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  sharePreviewCaption: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  shareCaptionInput: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
    fontSize: Typography.body,
    color: Colors.text,
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: Spacing.md,
  },
  shareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent,
    paddingVertical: Spacing.md,
    borderRadius: 12,
    gap: Spacing.sm,
  },
  shareButtonDisabled: {
    opacity: 0.6,
  },
  shareButtonText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.buttonText,
  },
});
