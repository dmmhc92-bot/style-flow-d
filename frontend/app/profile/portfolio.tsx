import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Alert,
  ActivityIndicator,
  Dimensions,
  Modal,
  TextInput,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import Button from '../../components/Button';
import { SyncStatusBar } from '../../components/SyncStatusBar';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { useAuthStore } from '../../store/authStore';
import { useSyncStatus } from '../../utils/syncService';
import {
  saveLookbookItem,
  getLocalLookbookItems,
  deleteLookbookItem as deleteLocalItem,
  LookbookItem,
} from '../../utils/localVault';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const GRID_GAP = 4;
const GRID_COLUMNS = 3;
const IMAGE_SIZE = (SCREEN_WIDTH - Spacing.screenPadding * 2 - GRID_GAP * (GRID_COLUMNS - 1)) / GRID_COLUMNS;

// Maximum file size: 5MB
const MAX_FILE_SIZE = 5 * 1024 * 1024;

interface PortfolioItem {
  id: string;
  image: string;
  caption?: string;
  created_at?: string;
  is_local?: boolean;  // Flag for local-only items
}

export default function PortfolioScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { isOnline } = useSyncStatus();
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  
  // Modal states
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [caption, setCaption] = useState('');
  
  // View modal
  const [viewingItem, setViewingItem] = useState<PortfolioItem | null>(null);
  
  useEffect(() => {
    loadPortfolio();
  }, []);
  
  const loadPortfolio = async () => {
    try {
      // First, load from local cache for instant display
      if (user?.id) {
        const localItems = await getLocalLookbookItems(user.id);
        const localPortfolio: PortfolioItem[] = localItems
          .filter(item => !item.is_synced)  // Only show unsynced local items
          .map(item => ({
            id: item.id,
            image: item.image_data,
            caption: item.caption,
            created_at: new Date(item.created_at).toISOString(),
            is_local: true,
          }));
        
        // Try to load from server if online
        if (isOnline) {
          const response = await api.get('/profiles/me/hub');
          const serverItems = (response.data.portfolio || []).map((item: any) => ({
            ...item,
            is_local: false,
          }));
          // Merge: local unsynced items first, then server items
          setPortfolio([...localPortfolio, ...serverItems]);
        } else {
          // Offline: show only local items
          setPortfolio(localPortfolio);
        }
      }
    } catch (error) {
      console.error('Failed to load portfolio:', error);
      // If API fails, try to show local items
      if (user?.id) {
        const localItems = await getLocalLookbookItems(user.id);
        const localPortfolio = localItems.map(item => ({
          id: item.id,
          image: item.image_data,
          caption: item.caption,
          created_at: new Date(item.created_at).toISOString(),
          is_local: true,
        }));
        setPortfolio(localPortfolio);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };
  
  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadPortfolio();
  }, [isOnline, user?.id]);
  
  const validateImageSize = (base64String: string): boolean => {
    const estimatedSize = (base64String.length * 3) / 4;
    return estimatedSize <= MAX_FILE_SIZE;
  };
  
  const pickImage = async () => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        Alert.alert('Permission Required', 'Please allow photo library access');
        return;
      }
      
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
        base64: true,
      });
      
      if (!result.canceled && result.assets[0].base64) {
        const base64Data = result.assets[0].base64;
        
        if (!validateImageSize(base64Data)) {
          Alert.alert('Image Too Large', 'Please select an image smaller than 5MB');
          return;
        }
        
        setSelectedImage(`data:image/jpeg;base64,${base64Data}`);
        setShowUploadModal(true);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to select image');
    }
  };
  
  const takePhoto = async () => {
    try {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        Alert.alert('Permission Required', 'Please allow camera access');
        return;
      }
      
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
        base64: true,
      });
      
      if (!result.canceled && result.assets[0].base64) {
        const base64Data = result.assets[0].base64;
        
        if (!validateImageSize(base64Data)) {
          Alert.alert('Image Too Large', 'Please select an image smaller than 5MB');
          return;
        }
        
        setSelectedImage(`data:image/jpeg;base64,${base64Data}`);
        setShowUploadModal(true);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to take photo');
    }
  };
  
  const handleAddPhoto = () => {
    Alert.alert(
      'Add Portfolio Photo',
      'Choose how to add your work',
      [
        { text: 'Take Photo', onPress: takePhoto },
        { text: 'Choose from Library', onPress: pickImage },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };
  
  const uploadImage = async () => {
    if (!selectedImage || !user?.id) return;
    
    setUploading(true);
    
    // OFFLINE-FIRST: Always save locally first
    setUploadProgress('Saving locally...');
    const localId = await saveLookbookItem(user.id, selectedImage, caption.trim());
    
    // Add to local state immediately for instant feedback
    setPortfolio(prev => [{
      id: localId,
      image: selectedImage,
      caption: caption.trim(),
      created_at: new Date().toISOString(),
      is_local: true,
    }, ...prev]);
    
    // If online, try to sync immediately
    if (isOnline) {
      setUploadProgress('Syncing to cloud...');
      try {
        const response = await api.post('/profiles/portfolio', {
          image_base64: selectedImage,
          caption: caption.trim() || null,
        });
        
        if (response.data.success) {
          // Update local item with server ID
          setPortfolio(prev => prev.map(item => 
            item.id === localId 
              ? { ...item, id: response.data.portfolio_id, image: response.data.image_url, is_local: false }
              : item
          ));
        }
      } catch (error: any) {
        // Failed to sync - stays local, will retry later
        console.log('Sync failed, saved locally:', error.message);
      }
    }
    
    setShowUploadModal(false);
    setSelectedImage(null);
    setCaption('');
    setUploading(false);
    setUploadProgress('');
    
    Alert.alert(
      'Success', 
      isOnline ? 'Photo added to your portfolio!' : 'Photo saved! Will sync when online.'
    );
  };
  
  const deleteItem = async (item: PortfolioItem) => {
    Alert.alert(
      'Delete Photo',
      'Are you sure you want to remove this photo from your portfolio?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/profiles/portfolio/${item.id}`);
              setPortfolio(prev => prev.filter(p => p.id !== item.id));
              setViewingItem(null);
              Alert.alert('Deleted', 'Photo removed from portfolio');
            } catch (error: any) {
              Alert.alert('Error', error.response?.data?.detail || 'Failed to delete');
            }
          },
        },
      ]
    );
  };
  
  const renderPortfolioItem = (item: PortfolioItem, index: number) => (
    <TouchableOpacity
      key={item.id}
      style={[
        styles.gridItem,
        (index + 1) % GRID_COLUMNS !== 0 && styles.gridItemMargin
      ]}
      onPress={() => setViewingItem(item)}
      activeOpacity={0.8}
    >
      <Image source={{ uri: item.image }} style={styles.gridImage} />
      {/* Show pending sync indicator for local items */}
      {item.is_local && (
        <View style={styles.syncPendingBadge}>
          <Ionicons name="cloud-upload-outline" size={12} color={Colors.background} />
        </View>
      )}
    </TouchableOpacity>
  );
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Sync Status Bar */}
      <SyncStatusBar />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>My Portfolio</Text>
        <TouchableOpacity style={styles.addButton} onPress={handleAddPhoto}>
          <Ionicons name="add" size={28} color={Colors.accent} />
        </TouchableOpacity>
      </View>
      
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={Colors.accent}
          />
        }
      >
        {/* Stats Bar */}
        <View style={styles.statsBar}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{portfolio.length}</Text>
            <Text style={styles.statLabel}>Photos</Text>
          </View>
          <Text style={styles.statDivider}>•</Text>
          <Text style={styles.statHint}>
            {!isOnline ? 'Offline mode • Edits saved locally' : 'Showcase your best work'}
          </Text>
        </View>
        
        {/* Portfolio Grid */}
        {portfolio.length > 0 ? (
          <View style={styles.grid}>
            {portfolio.map((item, index) => renderPortfolioItem(item, index))}
          </View>
        ) : (
          <View style={styles.emptyState}>
            <View style={styles.emptyIcon}>
              <Ionicons name="images-outline" size={64} color={Colors.accent} />
            </View>
            <Text style={styles.emptyTitle}>No Portfolio Photos Yet</Text>
            <Text style={styles.emptyDescription}>
              Add photos of your best work to attract new clients
            </Text>
            <Button
              title="Add Your First Photo"
              onPress={handleAddPhoto}
              style={styles.emptyButton}
            />
          </View>
        )}
        
        {/* Add More Button (when has photos) */}
        {portfolio.length > 0 && (
          <TouchableOpacity style={styles.addMoreButton} onPress={handleAddPhoto}>
            <Ionicons name="add-circle-outline" size={24} color={Colors.accent} />
            <Text style={styles.addMoreText}>Add More Photos</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
      
      {/* Upload Modal */}
      <Modal
        visible={showUploadModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => {
          if (!uploading) {
            setShowUploadModal(false);
            setSelectedImage(null);
            setCaption('');
          }
        }}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add to Portfolio</Text>
              <TouchableOpacity
                onPress={() => {
                  if (!uploading) {
                    setShowUploadModal(false);
                    setSelectedImage(null);
                    setCaption('');
                  }
                }}
                disabled={uploading}
              >
                <Ionicons name="close" size={24} color={Colors.text} />
              </TouchableOpacity>
            </View>
            
            {selectedImage && (
              <Image source={{ uri: selectedImage }} style={styles.previewImage} />
            )}
            
            <TextInput
              style={styles.captionInput}
              placeholder="Add a caption (optional)"
              placeholderTextColor={Colors.textLight}
              value={caption}
              onChangeText={setCaption}
              multiline
              maxLength={200}
              editable={!uploading}
            />
            
            <Text style={styles.charCount}>{caption.length}/200</Text>
            
            {uploading ? (
              <View style={styles.uploadingContainer}>
                <ActivityIndicator size="small" color={Colors.accent} />
                <Text style={styles.uploadingText}>{uploadProgress}</Text>
              </View>
            ) : (
              <Button
                title="Add to Portfolio"
                onPress={uploadImage}
                style={styles.uploadButton}
              />
            )}
          </View>
        </View>
      </Modal>
      
      {/* View/Delete Modal */}
      <Modal
        visible={!!viewingItem}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setViewingItem(null)}
      >
        <View style={styles.viewModalOverlay}>
          <TouchableOpacity
            style={styles.viewModalClose}
            onPress={() => setViewingItem(null)}
          >
            <Ionicons name="close" size={32} color={Colors.text} />
          </TouchableOpacity>
          
          {viewingItem && (
            <View style={styles.viewModalContent}>
              <Image
                source={{ uri: viewingItem.image }}
                style={styles.viewImage}
                resizeMode="contain"
              />
              
              {viewingItem.caption && (
                <Text style={styles.viewCaption}>{viewingItem.caption}</Text>
              )}
              
              <TouchableOpacity
                style={styles.deleteButton}
                onPress={() => deleteItem(viewingItem)}
              >
                <Ionicons name="trash-outline" size={20} color={Colors.error} />
                <Text style={styles.deleteText}>Delete Photo</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </Modal>
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
    alignItems: 'center',
    justifyContent: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold as any,
    color: Colors.text,
  },
  addButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  statsBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.lg,
    paddingVertical: Spacing.sm,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 4,
  },
  statNumber: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold as any,
    color: Colors.accent,
  },
  statLabel: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  statDivider: {
    color: Colors.textLight,
    marginHorizontal: Spacing.sm,
  },
  statHint: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  gridItem: {
    width: IMAGE_SIZE,
    height: IMAGE_SIZE,
    marginBottom: GRID_GAP,
    borderRadius: 8,
    overflow: 'hidden',
    position: 'relative',
  },
  gridItemMargin: {
    marginRight: GRID_GAP,
  },
  gridImage: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.backgroundSecondary,
  },
  syncPendingBadge: {
    position: 'absolute',
    top: 6,
    right: 6,
    backgroundColor: Colors.accent,
    borderRadius: 10,
    padding: 4,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: Spacing.xxl * 2,
  },
  emptyIcon: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: Colors.accent + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
  },
  emptyTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold as any,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  emptyDescription: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: Spacing.xl,
    paddingHorizontal: Spacing.lg,
  },
  emptyButton: {
    minWidth: 200,
  },
  addMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.lg,
    marginTop: Spacing.md,
    gap: Spacing.sm,
  },
  addMoreText: {
    fontSize: Typography.body,
    color: Colors.accent,
    fontWeight: Typography.medium as any,
  },
  // Upload Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  modalTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold as any,
    color: Colors.text,
  },
  previewImage: {
    width: '100%',
    height: 250,
    borderRadius: 12,
    marginBottom: Spacing.md,
    backgroundColor: Colors.backgroundSecondary,
  },
  captionInput: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
    fontSize: Typography.body,
    color: Colors.text,
    minHeight: 80,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  charCount: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textAlign: 'right',
    marginTop: 4,
    marginBottom: Spacing.md,
  },
  uploadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.md,
    gap: Spacing.sm,
  },
  uploadingText: {
    fontSize: Typography.body,
    color: Colors.accent,
  },
  uploadButton: {
    marginTop: Spacing.sm,
  },
  // View Modal
  viewModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  viewModalClose: {
    position: 'absolute',
    top: 60,
    right: 20,
    zIndex: 10,
    padding: Spacing.sm,
  },
  viewModalContent: {
    width: '100%',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
  },
  viewImage: {
    width: SCREEN_WIDTH - Spacing.screenPadding * 2,
    height: SCREEN_WIDTH - Spacing.screenPadding * 2,
    borderRadius: 12,
  },
  viewCaption: {
    fontSize: Typography.body,
    color: Colors.text,
    textAlign: 'center',
    marginTop: Spacing.lg,
    paddingHorizontal: Spacing.md,
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: Spacing.xl,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.lg,
    backgroundColor: Colors.error + '15',
    borderRadius: 12,
    gap: Spacing.sm,
  },
  deleteText: {
    fontSize: Typography.body,
    color: Colors.error,
    fontWeight: Typography.medium as any,
  },
});
