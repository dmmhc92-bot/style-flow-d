import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Image,
  Dimensions,
  ActivityIndicator,
  ScrollView,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_WIDTH = SCREEN_WIDTH - Spacing.screenPadding * 2;

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
  shared_by?: {
    id: string;
    full_name: string;
    profile_photo?: string;
  };
  share_caption?: string;
  created_at: string;
}

interface TrendTag {
  tag: string;
  post_count: number;
  score: number;
}

type FeedType = 'trending' | 'new' | 'following';

// ImageCarousel as a proper React component (hooks must be in components, not render functions)
const ImageCarousel = ({ 
  images, 
  postId, 
  onPress 
}: { 
  images: string[]; 
  postId: string; 
  onPress: () => void;
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (images.length === 1) {
    return (
      <TouchableOpacity activeOpacity={0.95} onPress={onPress}>
        <Image
          source={{ uri: images[0].startsWith('data:') ? images[0] : `data:image/jpeg;base64,${images[0]}` }}
          style={carouselStyles.postImage}
          resizeMode="cover"
        />
      </TouchableOpacity>
    );
  }

  return (
    <View>
      <ScrollView
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(e) => {
          const index = Math.round(e.nativeEvent.contentOffset.x / CARD_WIDTH);
          setCurrentIndex(index);
        }}
      >
        {images.map((img, idx) => (
          <TouchableOpacity key={idx} activeOpacity={0.95} onPress={onPress}>
            <Image
              source={{ uri: img.startsWith('data:') ? img : `data:image/jpeg;base64,${img}` }}
              style={carouselStyles.postImage}
              resizeMode="cover"
            />
          </TouchableOpacity>
        ))}
      </ScrollView>
      <View style={carouselStyles.carouselDots}>
        {images.map((_, idx) => (
          <View
            key={idx}
            style={[carouselStyles.dot, idx === currentIndex && carouselStyles.dotActive]}
          />
        ))}
      </View>
    </View>
  );
};

// Carousel styles defined separately
const carouselStyles = StyleSheet.create({
  postImage: {
    width: CARD_WIDTH,
    height: CARD_WIDTH,
    borderRadius: Spacing.radiusMedium,
    backgroundColor: Colors.backgroundSecondary,
  },
  carouselDots: {
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
    backgroundColor: Colors.textLight + '60',
  },
  dotActive: {
    backgroundColor: Colors.accent,
    width: 8,
    height: 8,
    borderRadius: 4,
  },
});

export default function FeedScreen() {
  const router = useRouter();
  const [posts, setPosts] = useState<Post[]>([]);
  const [trendingTags, setTrendingTags] = useState<TrendTag[]>([]);
  const [feedType, setFeedType] = useState<FeedType>('trending');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const skipRef = useRef(0);
  const [reportingPostId, setReportingPostId] = useState<string | null>(null);

  const handleReportPost = async (postId: string, reason: string) => {
    try {
      const response = await api.post(`/posts/${postId}/report`, null, {
        params: { reason }
      });
      Alert.alert(
        'Report Submitted',
        response.data.action_taken 
          ? `Report submitted. Action taken: ${response.data.action_taken}`
          : 'Thank you for reporting. Our team will review this post.'
      );
      setReportingPostId(null);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to submit report');
    }
  };

  const showReportOptions = (postId: string) => {
    Alert.alert(
      'Report Post',
      'Why are you reporting this post?',
      [
        { text: 'Harassment', onPress: () => handleReportPost(postId, 'harassment') },
        { text: 'Inappropriate', onPress: () => handleReportPost(postId, 'inappropriate') },
        { text: 'Spam', onPress: () => handleReportPost(postId, 'spam') },
        { text: 'Hate Speech', onPress: () => handleReportPost(postId, 'hate_speech') },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    skipRef.current = 0;
    setHasMore(true);
    loadPosts(true);
  }, [feedType, selectedTag]);

  const loadInitialData = async () => {
    await Promise.all([loadPosts(true), loadTrendingTags()]);
  };

  const loadTrendingTags = async () => {
    try {
      const response = await api.get('/posts/trending-tags');
      setTrendingTags(response.data);
    } catch (error) {
      console.error('Failed to load trending tags:', error);
    }
  };

  const loadPosts = async (reset = false) => {
    if (reset) {
      setLoading(true);
      skipRef.current = 0;
    }

    try {
      const params = new URLSearchParams({
        feed: feedType,
        skip: skipRef.current.toString(),
        limit: '20',
      });
      if (selectedTag) {
        params.append('tag', selectedTag);
      }

      const response = await api.get(`/posts?${params.toString()}`);
      const newPosts = response.data;

      if (reset) {
        setPosts(newPosts);
      } else {
        setPosts(prev => [...prev, ...newPosts]);
      }

      setHasMore(newPosts.length === 20);
      skipRef.current += newPosts.length;
    } catch (error) {
      console.error('Failed to load posts:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    skipRef.current = 0;
    await Promise.all([loadPosts(true), loadTrendingTags()]);
  };

  const handleLoadMore = () => {
    if (!loadingMore && hasMore && !loading) {
      setLoadingMore(true);
      loadPosts(false);
    }
  };

  const handleLike = async (postId: string) => {
    try {
      const response = await api.post(`/posts/${postId}/like`);
      setPosts(prev =>
        prev.map(p =>
          p.id === postId
            ? { ...p, user_liked: response.data.liked, likes_count: response.data.likes_count }
            : p
        )
      );
    } catch (error) {
      console.error('Failed to like post:', error);
    }
  };

  const handleSave = async (postId: string) => {
    try {
      const response = await api.post(`/posts/${postId}/save`);
      setPosts(prev =>
        prev.map(p =>
          p.id === postId
            ? { ...p, user_saved: response.data.saved, saves_count: response.data.saves_count }
            : p
        )
      );
    } catch (error) {
      console.error('Failed to save post:', error);
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;
    return date.toLocaleDateString();
  };

  const renderFeedTabs = () => (
    <View style={styles.feedTabs}>
      {(['trending', 'new', 'following'] as FeedType[]).map(type => (
        <TouchableOpacity
          key={type}
          style={[styles.feedTab, feedType === type && styles.feedTabActive]}
          onPress={() => setFeedType(type)}
        >
          <Ionicons
            name={type === 'trending' ? 'flame' : type === 'new' ? 'time' : 'people'}
            size={16}
            color={feedType === type ? Colors.accent : Colors.textSecondary}
          />
          <Text style={[styles.feedTabText, feedType === type && styles.feedTabTextActive]}>
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderTrendingTags = () => (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      style={styles.tagsContainer}
      contentContainerStyle={styles.tagsContent}
    >
      <TouchableOpacity
        style={[styles.tagChip, !selectedTag && styles.tagChipActive]}
        onPress={() => setSelectedTag(null)}
      >
        <Text style={[styles.tagChipText, !selectedTag && styles.tagChipTextActive]}>All</Text>
      </TouchableOpacity>
      {trendingTags.slice(0, 10).map(tag => (
        <TouchableOpacity
          key={tag.tag}
          style={[styles.tagChip, selectedTag === tag.tag && styles.tagChipActive]}
          onPress={() => setSelectedTag(selectedTag === tag.tag ? null : tag.tag)}
        >
          <Text style={[styles.tagChipText, selectedTag === tag.tag && styles.tagChipTextActive]}>
            #{tag.tag}
          </Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );

  // Image carousel is now a proper component - see ImageCarousel below

  const renderPost = ({ item }: { item: Post }) => (
    <View style={styles.postCard}>
      {/* Shared By Header */}
      {item.is_shared && item.shared_by && (
        <TouchableOpacity
          style={styles.sharedByHeader}
          onPress={() => router.push(`/discover/${item.shared_by?.id}`)}
        >
          <Ionicons name="repeat" size={14} color={Colors.textSecondary} />
          <Text style={styles.sharedByText}>
            Shared by {item.shared_by.full_name}
          </Text>
        </TouchableOpacity>
      )}

      {/* Author Header */}
      <TouchableOpacity
        style={styles.postHeader}
        onPress={() => router.push(`/discover/${item.author.id}`)}
      >
        <View style={styles.authorAvatar}>
          {item.author.profile_photo ? (
            <Image
              source={{ uri: item.author.profile_photo.startsWith('data:') ? item.author.profile_photo : `data:image/jpeg;base64,${item.author.profile_photo}` }}
              style={styles.avatarImage}
            />
          ) : (
            <Ionicons name="person" size={20} color={Colors.accent} />
          )}
        </View>
        <View style={styles.authorInfo}>
          <Text style={styles.authorName}>{item.author.full_name}</Text>
          {item.author.business_name && (
            <Text style={styles.authorBusiness}>{item.author.business_name}</Text>
          )}
        </View>
        <Text style={styles.postTime}>{formatTimeAgo(item.created_at)}</Text>
        <TouchableOpacity
          style={styles.moreButton}
          onPress={() => showReportOptions(item.id)}
        >
          <Ionicons name="ellipsis-horizontal" size={20} color={Colors.textSecondary} />
        </TouchableOpacity>
      </TouchableOpacity>

      {/* Share Caption */}
      {item.share_caption && (
        <Text style={styles.shareCaption}>{item.share_caption}</Text>
      )}

      {/* Original Author (for shared posts) */}
      {item.is_shared && item.original_author && (
        <TouchableOpacity
          style={styles.originalAuthorBadge}
          onPress={() => router.push(`/discover/${item.original_author?.id}`)}
        >
          <Text style={styles.originalAuthorText}>
            Originally by {item.original_author.full_name}
          </Text>
        </TouchableOpacity>
      )}

      {/* Image Carousel */}
      {item.images && item.images.length > 0 && (
        <ImageCarousel 
          images={item.images} 
          postId={item.id} 
          onPress={() => router.push(`/post/${item.id}`)}
        />
      )}

      {/* Actions */}
      <View style={styles.postActions}>
        <View style={styles.leftActions}>
          <TouchableOpacity style={styles.actionButton} onPress={() => handleLike(item.id)}>
            <Ionicons
              name={item.user_liked ? 'heart' : 'heart-outline'}
              size={24}
              color={item.user_liked ? Colors.error : Colors.text}
            />
            <Text style={styles.actionCount}>{item.likes_count}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push(`/post/${item.id}`)}
          >
            <Ionicons name="chatbubble-outline" size={22} color={Colors.text} />
            <Text style={styles.actionCount}>{item.comments_count}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push(`/post/${item.id}?share=true`)}
          >
            <Ionicons name="paper-plane-outline" size={22} color={Colors.text} />
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.actionButton} onPress={() => handleSave(item.id)}>
          <Ionicons
            name={item.user_saved ? 'bookmark' : 'bookmark-outline'}
            size={22}
            color={item.user_saved ? Colors.accent : Colors.text}
          />
        </TouchableOpacity>
      </View>

      {/* Caption */}
      {item.caption && (
        <Text style={styles.caption} numberOfLines={3}>
          <Text style={styles.captionAuthor}>{item.author.full_name} </Text>
          {item.caption}
        </Text>
      )}

      {/* Tags */}
      {item.tags.length > 0 && (
        <View style={styles.postTags}>
          {item.tags.map(tag => (
            <TouchableOpacity
              key={tag}
              onPress={() => setSelectedTag(tag)}
            >
              <Text style={styles.postTag}>#{tag}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* View Comments */}
      {item.comments_count > 0 && (
        <TouchableOpacity onPress={() => router.push(`/post/${item.id}`)}>
          <Text style={styles.viewComments}>
            View all {item.comments_count} comments
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );

  const renderFooter = () => {
    if (!loadingMore) return null;
    return (
      <View style={styles.loadingMore}>
        <ActivityIndicator size="small" color={Colors.accent} />
      </View>
    );
  };

  if (loading && posts.length === 0) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Loading feed...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>StyleFlow</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => router.push('/post/create')}
          >
            <Ionicons name="add-circle-outline" size={26} color={Colors.text} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => router.push('/saved')}
          >
            <Ionicons name="bookmark-outline" size={24} color={Colors.text} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Feed Tabs */}
      {renderFeedTabs()}

      {/* Trending Tags */}
      {renderTrendingTags()}

      {/* Posts Feed */}
      <FlatList
        data={posts}
        renderItem={renderPost}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.feedContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.accent}
          />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="images-outline" size={64} color={Colors.textSecondary} />
            <Text style={styles.emptyTitle}>No posts yet</Text>
            <Text style={styles.emptyText}>
              {feedType === 'following'
                ? 'Follow some stylists to see their posts here!'
                : 'Be the first to share your work!'}
            </Text>
            <TouchableOpacity
              style={styles.createButton}
              onPress={() => router.push('/post/create')}
            >
              <Ionicons name="add" size={20} color={Colors.buttonText} />
              <Text style={styles.createButtonText}>Create Post</Text>
            </TouchableOpacity>
          </View>
        }
      />

      {/* Floating Action Button - Create Post */}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => router.push('/post/create')}
        activeOpacity={0.8}
        accessibilityRole="button"
        accessibilityLabel="Create new post"
      >
        <Ionicons name="add" size={28} color="#FFFFFF" />
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    height: Spacing.headerHeight,
  },
  title: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.accent,
    letterSpacing: -0.5,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  headerButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 20,
  },
  feedTabs: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
  },
  feedTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: Spacing.radiusFull,
    backgroundColor: Colors.backgroundSecondary,
    gap: 6,
  },
  feedTabActive: {
    backgroundColor: Colors.accent + '20',
  },
  feedTabText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    fontWeight: Typography.medium,
  },
  feedTabTextActive: {
    color: Colors.accent,
    fontWeight: Typography.semibold,
  },
  tagsContainer: {
    maxHeight: 44,
  },
  tagsContent: {
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.xs,
  },
  tagChip: {
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: Spacing.radiusFull,
    backgroundColor: Colors.backgroundSecondary,
    marginRight: Spacing.sm,
  },
  tagChipActive: {
    backgroundColor: Colors.accent,
  },
  tagChipText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    fontWeight: Typography.medium,
  },
  tagChipTextActive: {
    color: Colors.buttonText,
    fontWeight: Typography.semibold,
  },
  feedContent: {
    paddingTop: Spacing.sm,
  },
  postCard: {
    marginBottom: Spacing.itemSpacing,
    backgroundColor: Colors.cardBackground,
  },
  sharedByHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingTop: Spacing.sm,
    paddingBottom: Spacing.xs,
    gap: 6,
  },
  sharedByText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  postHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.sm,
  },
  authorAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  avatarImage: {
    width: '100%',
    height: '100%',
  },
  authorInfo: {
    flex: 1,
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
    marginTop: 1,
  },
  postTime: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    marginRight: Spacing.sm,
  },
  moreButton: {
    padding: Spacing.xs,
  },
  shareCaption: {
    fontSize: Typography.body,
    color: Colors.text,
    paddingHorizontal: Spacing.screenPadding,
    paddingBottom: Spacing.sm,
    lineHeight: 20,
  },
  originalAuthorBadge: {
    marginHorizontal: Spacing.screenPadding,
    marginBottom: Spacing.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  originalAuthorText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  postImage: {
    width: CARD_WIDTH,
    height: CARD_WIDTH,
    marginHorizontal: Spacing.screenPadding,
    borderRadius: Spacing.radiusMedium,
  },
  carouselDots: {
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
    backgroundColor: Colors.textLight + '60',
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
    height: 48,
  },
  leftActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.lg,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    padding: 4,
  },
  actionCount: {
    fontSize: Typography.bodySmall,
    color: Colors.text,
    fontWeight: Typography.medium,
  },
  caption: {
    fontSize: Typography.body,
    color: Colors.text,
    paddingHorizontal: Spacing.screenPadding,
    lineHeight: 22,
  },
  captionAuthor: {
    fontWeight: Typography.semibold,
  },
  postTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: Spacing.screenPadding,
    paddingTop: Spacing.xs,
    gap: Spacing.sm,
  },
  postTag: {
    fontSize: Typography.caption,
    color: Colors.accent,
    fontWeight: Typography.medium,
  },
  viewComments: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    paddingHorizontal: Spacing.screenPadding,
    paddingTop: Spacing.sm,
    paddingBottom: Spacing.md,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: Spacing.md,
  },
  loadingText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  loadingMore: {
    paddingVertical: Spacing.xl,
    alignItems: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Spacing.xxl * 2,
    paddingHorizontal: Spacing.xl,
    gap: Spacing.md,
  },
  emptyTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginTop: Spacing.sm,
  },
  emptyText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm + 4,
    borderRadius: Spacing.radiusFull,
    gap: Spacing.xs,
    marginTop: Spacing.md,
  },
  createButtonText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.buttonText,
  },
  fab: {
    position: 'absolute',
    bottom: 100,
    right: Spacing.screenPadding,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    zIndex: 1000,
  },
});
