import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Image,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { useTrialAction, TrialBadge } from '../../components/PremiumGate';
import { useTrialStore } from '../../store/trialStore';

const TREND_TAGS = [
  'balayage', 'colortrend', 'transformation', 'mensstyle', 'curlyhair',
  'blondehair', 'brunette', 'redhead', 'highlights', 'lowlights',
  'ombre', 'sombre', 'haircut', 'pixiecut', 'bobcut', 'layers',
  'extensions', 'braids', 'updo', 'wedding', 'editorial', 'natural',
  'vivids', 'pastels', 'colorcorrection', 'keratintreatment', 'textured'
];

export default function CreatePostScreen() {
  const router = useRouter();
  
  // Trial system integration
  const { canPerformAction, performAction, remainingUses, isPremium, PaywallModal } = useTrialAction('postsCreated');
  const { loadUsage } = useTrialStore();
  
  // Load trial usage on mount
  useEffect(() => {
    loadUsage();
  }, []);
  
  const [images, setImages] = useState<string[]>([]);
  const [caption, setCaption] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [showTagSelector, setShowTagSelector] = useState(false);
  const [loading, setLoading] = useState(false);

  const pickImages = async () => {
    if (images.length >= 5) {
      Alert.alert('Maximum Reached', 'You can only add up to 5 images per post.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsMultipleSelection: true,
      selectionLimit: 5 - images.length,
      base64: true,
      quality: 0.7,
    });

    if (!result.canceled && result.assets) {
      const newImages = result.assets
        .filter(asset => asset.base64)
        .map(asset => `data:image/jpeg;base64,${asset.base64}`);
      
      setImages(prev => [...prev, ...newImages].slice(0, 5));
    }
  };

  const removeImage = (index: number) => {
    setImages(prev => prev.filter((_, i) => i !== index));
  };

  const toggleTag = (tag: string) => {
    setSelectedTags(prev => {
      if (prev.includes(tag)) {
        return prev.filter(t => t !== tag);
      }
      if (prev.length >= 5) {
        Alert.alert('Maximum Tags', 'You can select up to 5 tags.');
        return prev;
      }
      return [...prev, tag];
    });
  };

  const handlePost = async () => {
    if (images.length === 0) {
      Alert.alert('No Images', 'Please add at least one image to your post.');
      return;
    }

    // Check trial/subscription status before creating
    if (!canPerformAction) {
      return;
    }

    setLoading(true);
    try {
      // Track this as a premium action
      await performAction();
      
      // Upload images first to get URLs
      const uploadedUrls: string[] = [];
      
      for (const image of images) {
        try {
          const uploadResponse = await api.post('/posts/upload-image', { image });
          if (uploadResponse.data?.url) {
            uploadedUrls.push(uploadResponse.data.url);
          } else {
            uploadedUrls.push(image);
          }
        } catch (uploadError) {
          console.warn('Image upload failed, using original:', uploadError);
          uploadedUrls.push(image);
        }
      }

      // Create post with uploaded URLs
      await api.post('/posts', {
        images: uploadedUrls,
        caption: caption.trim() || undefined,
        tags: selectedTags,
      });

      // Navigate to feed after successful post
      router.replace('/tabs/feed');
    } catch (error: any) {
      console.error('Post creation error:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to create post');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()}>
            <Ionicons name="close" size={28} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>New Post</Text>
          <TouchableOpacity
            style={[styles.postButton, (!images.length || loading) && styles.postButtonDisabled]}
            onPress={handlePost}
            disabled={!images.length || loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color={Colors.buttonText} />
            ) : (
              <Text style={styles.postButtonText}>Share</Text>
            )}
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Image Picker */}
          <View style={styles.imageSection}>
            <Text style={styles.sectionTitle}>Photos ({images.length}/5)</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.imagesRow}>
                {images.map((img, index) => (
                  <View key={index} style={styles.imageContainer}>
                    <Image source={{ uri: img }} style={styles.previewImage} />
                    {index === 0 && (
                      <View style={styles.coverBadge}>
                        <Text style={styles.coverBadgeText}>Cover</Text>
                      </View>
                    )}
                    <TouchableOpacity
                      style={styles.removeImageButton}
                      onPress={() => removeImage(index)}
                    >
                      <Ionicons name="close-circle" size={24} color={Colors.error} />
                    </TouchableOpacity>
                  </View>
                ))}
                {images.length < 5 && (
                  <TouchableOpacity style={styles.addImageButton} onPress={pickImages}>
                    <Ionicons name="add" size={32} color={Colors.accent} />
                    <Text style={styles.addImageText}>Add Photo</Text>
                  </TouchableOpacity>
                )}
              </View>
            </ScrollView>
          </View>

          {/* Caption */}
          <View style={styles.captionSection}>
            <Text style={styles.sectionTitle}>Caption</Text>
            <TextInput
              style={styles.captionInput}
              placeholder="Write a caption for your post..."
              placeholderTextColor={Colors.textLight}
              multiline
              maxLength={500}
              value={caption}
              onChangeText={setCaption}
            />
            <Text style={styles.charCount}>{caption.length}/500</Text>
          </View>

          {/* Tags */}
          <View style={styles.tagsSection}>
            <View style={styles.tagsSectionHeader}>
              <Text style={styles.sectionTitle}>Tags ({selectedTags.length}/5)</Text>
              <TouchableOpacity onPress={() => setShowTagSelector(!showTagSelector)}>
                <Text style={styles.toggleTagsText}>
                  {showTagSelector ? 'Hide' : 'Show all'}
                </Text>
              </TouchableOpacity>
            </View>

            {/* Selected Tags */}
            {selectedTags.length > 0 && (
              <View style={styles.selectedTagsRow}>
                {selectedTags.map(tag => (
                  <TouchableOpacity
                    key={tag}
                    style={styles.selectedTag}
                    onPress={() => toggleTag(tag)}
                  >
                    <Text style={styles.selectedTagText}>#{tag}</Text>
                    <Ionicons name="close" size={14} color={Colors.buttonText} />
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* Tag Selector */}
            {showTagSelector && (
              <View style={styles.tagSelector}>
                <Text style={styles.tagSelectorHint}>Tap to add tags</Text>
                <View style={styles.tagsGrid}>
                  {TREND_TAGS.map(tag => (
                    <TouchableOpacity
                      key={tag}
                      style={[
                        styles.tagOption,
                        selectedTags.includes(tag) && styles.tagOptionSelected,
                      ]}
                      onPress={() => toggleTag(tag)}
                    >
                      <Text
                        style={[
                          styles.tagOptionText,
                          selectedTags.includes(tag) && styles.tagOptionTextSelected,
                        ]}
                      >
                        #{tag}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}
          </View>

          {/* Trial Info */}
          {!isPremium && remainingUses > 0 && (
            <View style={styles.trialInfo}>
              <TrialBadge />
              <Text style={styles.trialText}>{remainingUses} free post{remainingUses !== 1 ? 's' : ''} remaining</Text>
            </View>
          )}

          {/* Tips */}
          <View style={styles.tipsSection}>
            <Ionicons name="bulb-outline" size={20} color={Colors.accent} />
            <Text style={styles.tipsText}>
              Tip: Use trending tags to help more stylists discover your work!
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
      
      {/* Paywall Modal */}
      <PaywallModal />
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
  postButton: {
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    borderRadius: 20,
    minWidth: 70,
    alignItems: 'center',
  },
  postButtonDisabled: {
    opacity: 0.5,
  },
  postButtonText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.buttonText,
  },
  content: {
    flex: 1,
  },
  imageSection: {
    padding: Spacing.screenPadding,
  },
  sectionTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  imagesRow: {
    flexDirection: 'row',
    gap: Spacing.md,
  },
  imageContainer: {
    position: 'relative',
  },
  previewImage: {
    width: 120,
    height: 120,
    borderRadius: 8,
  },
  coverBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: Colors.accent,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  coverBadgeText: {
    fontSize: 10,
    fontWeight: Typography.semibold,
    color: Colors.buttonText,
  },
  removeImageButton: {
    position: 'absolute',
    top: -8,
    right: -8,
    backgroundColor: Colors.background,
    borderRadius: 12,
  },
  addImageButton: {
    width: 120,
    height: 120,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: Colors.accent + '40',
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent + '10',
  },
  addImageText: {
    fontSize: Typography.caption,
    color: Colors.accent,
    marginTop: Spacing.xs,
  },
  captionSection: {
    paddingHorizontal: Spacing.screenPadding,
    paddingBottom: Spacing.md,
  },
  captionInput: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
    fontSize: Typography.body,
    color: Colors.text,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  charCount: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textAlign: 'right',
    marginTop: Spacing.xs,
  },
  tagsSection: {
    paddingHorizontal: Spacing.screenPadding,
    paddingBottom: Spacing.md,
  },
  tagsSectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  toggleTagsText: {
    fontSize: Typography.bodySmall,
    color: Colors.accent,
  },
  selectedTagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  selectedTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: 16,
    gap: 4,
  },
  selectedTagText: {
    fontSize: Typography.bodySmall,
    color: Colors.buttonText,
    fontWeight: Typography.medium,
  },
  tagSelector: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
  },
  tagSelectorHint: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
  },
  tagsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  tagOption: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: 16,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  tagOptionSelected: {
    backgroundColor: Colors.accent + '20',
    borderColor: Colors.accent,
  },
  tagOptionText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  tagOptionTextSelected: {
    color: Colors.accent,
    fontWeight: Typography.medium,
  },
  trialInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: Spacing.screenPadding,
    marginBottom: Spacing.md,
    padding: Spacing.sm,
    backgroundColor: Colors.accent + '10',
    borderRadius: Spacing.radiusMedium,
    gap: Spacing.xs,
  },
  trialText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  tipsSection: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    gap: Spacing.sm,
    backgroundColor: Colors.accent + '10',
    marginHorizontal: Spacing.screenPadding,
    marginBottom: Spacing.lg,
    borderRadius: 12,
  },
  tipsText: {
    flex: 1,
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
});
